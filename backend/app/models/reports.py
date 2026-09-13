# app/models/reports.py
# Kept for backward compatibility — new attachment system uses app/models/patient_case.py
from sqlalchemy import Column, Integer, ForeignKey
from app.models.base import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("patient_cases.id"))
