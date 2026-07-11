from sqlalchemy import Column, Integer, String, JSON
from app.models.base import Base

class PatientCase(Base):
    __tablename__ = "patient_cases"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String, nullable=False)
    patient_contact = Column(String, nullable=True)
    uploaded_file = Column(String, nullable=True)
    symptoms = Column(String, nullable=True)
    status = Column(String, default="new")

    xray_result = Column(JSON, nullable=True)
    symptom_result = Column(JSON, nullable=True)

    # NEW for Lab
    lab_report = Column(String, nullable=True)
    lab_comments = Column(String, nullable=True)

    # NEW for Doctor
    doctor_notes = Column(String, nullable=True)
    final_diagnosis = Column(String, nullable=True)
    treatment_plan = Column(String, nullable=True)
