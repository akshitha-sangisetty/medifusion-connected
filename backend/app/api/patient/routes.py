from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth.routes import get_current_user
from app.models.patient_case import PatientCase

router = APIRouter(prefix="/patient", tags=["Patient"])


# ---------------------------------------------
# Get latest case of logged-in patient
# ---------------------------------------------
@router.get("/latest")
def get_latest_case(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user.id

    latest = (
        db.query(PatientCase)
        .filter(PatientCase.patient_name == current_user.username)
        .order_by(PatientCase.id.desc())
        .first()
    )

    if not latest:
        return {"exists": False}

    return {
        "exists": True,
        "case": {
            "id": latest.id,
            "symptoms": latest.symptoms,
            "ai_result": latest.symptom_result,
            "xray_result": latest.xray_result,
            "status": latest.status,
            "doctor_notes": latest.doctor_notes,
            "final_diagnosis": latest.final_diagnosis,
            "treatment_plan": latest.treatment_plan
        }
    }
