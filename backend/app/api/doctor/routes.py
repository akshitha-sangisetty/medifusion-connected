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

    cases = db.query(Case).filter(Case.doctor_id == current_user.id).all()
    return {"cases": cases}


# POST /doctor/review/{case_id}
@router.post("/review/{case_id}")
def submit_review(
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

    case.doctor_comments = data.get("notes", "")
    case.status = "reviewed"
    db.commit()

    return {"message": "Review submitted successfully"}
