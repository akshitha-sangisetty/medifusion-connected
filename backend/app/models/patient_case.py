from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class PatientCase(Base):
    __tablename__ = "patient_cases"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    patient_name = Column(String, nullable=False)
    patient_contact = Column(String, nullable=True)
    symptoms = Column(String, nullable=True)
    # status: submitted | analyzed | reviewed
    status = Column(String, default="submitted")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Legacy fields (kept so old data still works)
    uploaded_file = Column(String, nullable=True)
    xray_result = Column(JSON, nullable=True)
    symptom_result = Column(JSON, nullable=True)

    # Doctor review
    doctor_notes = Column(String, nullable=True)
    final_diagnosis = Column(String, nullable=True)
    treatment_plan = Column(String, nullable=True)

    # Relationships
    attachments = relationship("Attachment", back_populates="case", cascade="all, delete-orphan")
    analysis = relationship("CaseAnalysis", back_populates="case", uselist=False, cascade="all, delete-orphan")


class Attachment(Base):
    """Stores files uploaded by either the patient or a lab technician."""
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("patient_cases.id"), nullable=False)
    uploaded_by = Column(String, nullable=False)   # "patient" or "lab_tech"
    uploader_username = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=True)       # e.g. "image/png", "application/pdf"
    original_filename = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("PatientCase", back_populates="attachments")


class CaseAnalysis(Base):
    """Stores AI analysis results for a case."""
    __tablename__ = "case_analyses"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("patient_cases.id"), nullable=False, unique=True)
    patient_summary = Column(String, nullable=True)   # plain language for patient
    doctor_summary = Column(String, nullable=True)    # detailed for doctor
    confidence_scores = Column(JSON, nullable=True)   # e.g. {"Normal":0.1,"Pneumonia":0.85,...}
    raw_prediction_class = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("PatientCase", back_populates="analysis")
