from sqlalchemy.orm import Session
from app.models.patient_case import PatientCase

def get_patient_cases(db: Session, patient_name: str):
    return db.query(PatientCase).filter(
        PatientCase.patient_name == patient_name
    ).order_by(PatientCase.created_at.desc()).all()
