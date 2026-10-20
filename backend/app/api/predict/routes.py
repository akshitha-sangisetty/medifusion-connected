# app/api/predict/routes.py
import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.patient_case import PatientCase, Attachment
from app.api.auth.routes import get_current_user
from app.models.user import User
from app.services.ai_service import analyze_case
from app.config import UPLOAD_DIR
from app.ai.model_loader import (
    UnsupportedXrayError,
    XrayModelUnavailable,
    load_model,
    model_status,
    validate_dicom_bytes,
)

router = APIRouter(prefix="/predict", tags=["Predict"])


@router.get("/xray-model-status")
def xray_model_status():
    """Expose only safe readiness metadata for the research model."""
    status = model_status()
    return {
        "ready": status["enabled"] and status["checkpoint_present"],
        "enabled": status["enabled"],
        "checkpoint_present": status["checkpoint_present"],
        "model_version": status["model_version"],
        "review_threshold": status["review_threshold"],
        "input": status["input"],
        "research_only": True,
    }


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

    return {
        "case_id": case.id,
        "status": case.status,
        "patient_summary": (
            "Symptoms were recorded. No AI diagnosis was performed. "
            "The experimental MediFusion model accepts a DICOM chest X-ray only."
        ),
        "prediction": None,
        "confidence_scores": None,
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
        # The model was trained only on DICOM chest X-rays. Do not silently run
        # a different image type through this research model.
        suffix = Path(file.filename or "").suffix.lower()
        if suffix != ".dcm":
            raise HTTPException(
                status_code=422,
                detail="Experimental triage accepts a DICOM chest X-ray file with a .dcm extension only.",
            )

        # Fail before creating a patient case if the deployment was not given
        # the approved artifact or if its state dictionary cannot be loaded.
        load_model()
        content = await file.read()
        validate_dicom_bytes(content)

        # Preserve only a generated filename; never trust a client-provided path.
        filename = f"patient_{current_user.id}_{uuid4().hex}{suffix}"
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
            "research_only": True,
            "triage": analysis.confidence_scores,
        }

    except XrayModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except UnsupportedXrayError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
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
