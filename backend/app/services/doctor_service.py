from sqlalchemy.orm import Session
from app.models.patient_case import PatientCase


def get_new_processed_cases(db: Session):
    return db.query(PatientCase).filter(PatientCase.status == "processed", PatientCase.reviewed_by_doctor == False).order_by(PatientCase.created_at.desc()).all()
