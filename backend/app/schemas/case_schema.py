from pydantic import BaseModel
from typing import Optional, Dict

class CaseCreate(BaseModel):
    patient_name: str
    patient_contact: Optional[str]
    symptoms: Optional[str]

class CaseOut(BaseModel):
    id: int
    patient_name: str
    patient_contact: Optional[str]
    uploaded_file: Optional[str]
    symptoms: Optional[str]
    xray_result: Optional[Dict]       # Matches Case.xray_result
    symptom_result: Optional[Dict]    # Matches Case.symptom_result
    status: str

    class Config:
        orm_mode = True
