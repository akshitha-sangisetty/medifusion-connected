# app/api/doctor/routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.auth.routes import get_current_user
from app.models.patient_case import PatientCase
from app.models.user import User

router = APIRouter(prefix="/doctor", tags=["Doctor"])


def require_doctor(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not a doctor")
    return current_user


def _serialize_case(c: PatientCase) -> dict:
    analysis = c.analysis
    return {
        "id": c.id,
        "patient_name": c.patient_name,
        "symptoms": c.symptoms,
        "status": c.status,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        # AI analysis
        "patient_summary": analysis.patient_summary if analysis else None,
        "doctor_summary": analysis.doctor_summary if analysis else None,
        "confidence_scores": analysis.confidence_scores if analysis else None,
        "raw_prediction_class": analysis.raw_prediction_class if analysis else None,
        # Legacy fields (backward compat)
        "symptom_result": c.symptom_result,
        "xray_result": c.xray_result,
        # Doctor review
        "doctor_notes": c.doctor_notes,
        "treatment_plan": c.treatment_plan,
        "final_diagnosis": c.final_diagnosis,
        # Attachments (patient + lab)
        "attachments": [
            {
                "id": a.id,
                "uploaded_by": a.uploaded_by,
                "uploader_username": a.uploader_username,
                "original_filename": a.original_filename,
                "file_path": a.file_path,
                "file_type": a.file_type,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in c.attachments
        ],
    }


# GET /doctor/assigned
@router.get("/assigned")
def get_assigned_cases(
    db: Session = Depends(get_db),
    doctor: User = Depends(require_doctor)
):
    cases = (
        db.query(PatientCase)
        .filter(PatientCase.status != "submitted")
        .order_by(PatientCase.id.desc())
        .all()
    )
    return {"cases": [_serialize_case(c) for c in cases]}


# GET /doctor/case/{case_id}
@router.get("/case/{case_id}")
def get_case_detail(
    case_id: int,
    db: Session = Depends(get_db),
    doctor: User = Depends(require_doctor)
):
    case = db.query(PatientCase).filter(PatientCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return _serialize_case(case)


# POST /doctor/review/{case_id}
@router.post("/review/{case_id}")
async def submit_review(
    case_id: int,
    data: dict,
    db: Session = Depends(get_db),
    doctor: User = Depends(require_doctor)
):
    case = db.query(PatientCase).filter(PatientCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.doctor_notes = data.get("notes", "")
    case.treatment_plan = data.get("tests", "")
    case.final_diagnosis = data.get("diag", "")
    case.status = "reviewed"
    db.commit()
    db.refresh(case)

    # Real-time notification via Socket.IO
    from app.socket_manager import sio

    payload = {
        "case_id": case.id,
        "patient_name": case.patient_name,
        "final_diagnosis": case.final_diagnosis,
        "treatment_plan": case.treatment_plan,
        "doctor_notes": case.doctor_notes,
        "patient_summary": case.analysis.patient_summary if case.analysis else None,
        "status": "reviewed",
    }

    await sio.emit("case_reviewed", payload, room=f"patient_{case.patient_name}")
    await sio.emit("doctor_case_updated", {"case_id": case.id, "status": "reviewed"}, room="doctors")

    return {"message": "Review submitted successfully"}
