# app/models/reports.py

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("patient_cases.id"))

    # ✅ Correct relationship - do NOT import Case directly
    case = relationship("PatientCase", back_populates="reports")
