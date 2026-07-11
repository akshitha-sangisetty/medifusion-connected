import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.auth.routes import get_current_user
from app.models.patient_case import PatientCase as Case
from app.models.user import User

router = APIRouter(prefix="/doctor", tags=["Doctor"])


# GET /doctor/assigned
@router.get("/assigned")
def get_assigned_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not a doctor")

    # Fetch cases that have been processed by AI or are waiting for review
    cases = db.query(Case).filter(Case.status != "new").order_by(Case.id.desc()).all()

    return {
        "cases": [
            {
                "id": c.id,
                "patient_name": c.patient_name,
                "symptoms": c.symptoms,
                "symptom_result": c.symptom_result,
                "xray_result": c.xray_result,
                "doctor_notes": c.doctor_notes,
                "treatment_plan": c.treatment_plan,
                "final_diagnosis": c.final_diagnosis,
                "status": c.status,
            }
            for c in cases
        ]
    }


# POST /doctor/review/{case_id}
@router.post("/review/{case_id}")
async def submit_review(
    case_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not a doctor")

    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Persist the review
    case.doctor_notes = data.get("notes", "")
    case.treatment_plan = data.get("tests", "")
    case.final_diagnosis = data.get("diag", "")
    case.status = "reviewed"
    db.commit()
    db.refresh(case)

    # ── Real-time notification via Socket.IO ──────────────────────────
    # Import here to avoid circular imports at module load time
    from app.socket_manager import sio

    payload = {
        "case_id": case.id,
        "patient_name": case.patient_name,
        "final_diagnosis": case.final_diagnosis,
        "treatment_plan": case.treatment_plan,
        "doctor_notes": case.doctor_notes,
        "status": "reviewed",
    }

    # Emit to the patient's private room so ONLY that patient receives it
    await sio.emit("case_reviewed", payload, room=f"patient_{case.patient_name}")

    # Also notify all connected doctors so their sidebars update
    await sio.emit("doctor_case_updated", {"case_id": case.id, "status": "reviewed"}, room="doctors")

    return {"message": "Review submitted successfully"}
