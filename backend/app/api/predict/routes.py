# app/api/predict/routes.py
import os
import tempfile

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.patient_case import PatientCase, Attachment
from app.api.auth.routes import get_current_user
from app.models.user import User
from app.services.ai_service import analyze_case
from app.config import UPLOAD_DIR

router = APIRouter(prefix="/predict", tags=["Predict"])


# ---------------------------
# Predict from symptoms
# ---------------------------
class SymptomInput(BaseModel):
    symptoms: list[str] = Field(..., example=["cough", "fever", "shortness of breath"])


@router.post("/symptoms")
def predict_from_symptoms(
    data: SymptomInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create case
    case = PatientCase(
        patient_id=current_user.id,
        patient_name=current_user.username,
        symptoms=", ".join(data.symptoms),
        status="submitted"
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    # Run AI analysis immediately
    analysis = analyze_case(case.id, db)

    return {
        "case_id": case.id,
        "status": case.status,
        "patient_summary": analysis.patient_summary,
        "prediction": analysis.raw_prediction_class,
        "confidence_scores": analysis.confidence_scores,
    }


# ---------------------------
# Predict from image upload
# ---------------------------
@router.post("/image")
async def predict_from_image(
    file: UploadFile = File(..., description="Upload a chest X-ray image"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        content = await file.read()

        # Save file
        ext = os.path.splitext(file.filename)[1]
        filename = f"patient_{current_user.id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(content)

        # Create case
        case = PatientCase(
            patient_id=current_user.id,
            patient_name=current_user.username,
            uploaded_file=filename,
            status="submitted"
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        # Save attachment record
        attachment = Attachment(
            case_id=case.id,
            uploaded_by="patient",
            uploader_username=current_user.username,
            file_path=filename,
            file_type=file.content_type,
            original_filename=file.filename,
        )
        db.add(attachment)
        db.commit()

        # Run AI analysis
        analysis = analyze_case(case.id, db)

        return {
            "case_id": case.id,
            "status": case.status,
            "patient_summary": analysis.patient_summary,
            "prediction": analysis.raw_prediction_class,
            "confidence_scores": analysis.confidence_scores,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------
# Get case results
# ---------------------------
@router.get("/case/{case_id}")
def get_case_prediction(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(PatientCase).filter(PatientCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.patient_name != current_user.username and current_user.role not in ("doctor", "lab"):
        raise HTTPException(status_code=403, detail="Not authorized to view this case")

    analysis = case.analysis
    return {
        "case_id": case.id,
        "status": case.status,
        "symptoms": case.symptoms,
        "patient_summary": analysis.patient_summary if analysis else None,
        "doctor_summary": analysis.doctor_summary if analysis else None,
        "confidence_scores": analysis.confidence_scores if analysis else None,
        "raw_prediction_class": analysis.raw_prediction_class if analysis else None,
        "attachments": [
            {
                "id": a.id,
                "uploaded_by": a.uploaded_by,
                "uploader_username": a.uploader_username,
                "file_path": a.file_path,
                "file_type": a.file_type,
                "original_filename": a.original_filename,
            }
            for a in case.attachments
        ],
    }
