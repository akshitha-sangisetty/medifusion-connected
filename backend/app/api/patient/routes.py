# app/api/patient/routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.auth.routes import get_current_user
from app.models.patient_case import PatientCase

router = APIRouter(prefix="/patient", tags=["Patient"])


@router.get("/latest")
def get_latest_case(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    latest = (
        db.query(PatientCase)
        .filter(PatientCase.patient_name == current_user.username)
        .order_by(PatientCase.id.desc())
        .first()
    )

    if not latest:
        return {"exists": False}

    analysis = latest.analysis

    return {
        "exists": True,
        "case": {
            "id": latest.id,
            "symptoms": latest.symptoms,
            "status": latest.status,
            "created_at": latest.created_at.isoformat() if latest.created_at else None,

            # AI result — patient sees patient_summary only
            "patient_summary": analysis.patient_summary if analysis else None,
            "raw_prediction_class": analysis.raw_prediction_class if analysis else None,
            "confidence_scores": analysis.confidence_scores if analysis else None,

            # Legacy fields (for backward compat)
            "ai_result": analysis.confidence_scores if analysis else latest.symptom_result,
            "xray_result": latest.xray_result,

            # Doctor review
            "doctor_notes": latest.doctor_notes,
            "final_diagnosis": latest.final_diagnosis,
            "treatment_plan": latest.treatment_plan,

            # Attachments
            "attachments": [
                {
                    "id": a.id,
                    "uploaded_by": a.uploaded_by,
                    "uploader_username": a.uploader_username,
                    "file_path": a.file_path,
                    "file_type": a.file_type,
                    "original_filename": a.original_filename,
                }
                for a in latest.attachments
            ],
        }
    }


@router.get("/cases")
def get_all_cases(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Return all cases for the logged-in patient."""
    cases = (
        db.query(PatientCase)
        .filter(PatientCase.patient_name == current_user.username)
        .order_by(PatientCase.id.desc())
        .all()
    )

    return {
        "cases": [
            {
                "id": c.id,
                "symptoms": c.symptoms,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "patient_summary": c.analysis.patient_summary if c.analysis else None,
                "raw_prediction_class": c.analysis.raw_prediction_class if c.analysis else None,
                "final_diagnosis": c.final_diagnosis,
            }
            for c in cases
        ]
    }
