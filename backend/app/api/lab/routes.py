# app/api/lab/routes.py
import os

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.patient_case import PatientCase, Attachment
from app.models.user import User
from app.api.auth.routes import get_current_user
from app.config import UPLOAD_DIR

router = APIRouter(prefix="/lab", tags=["Lab"])


def require_lab(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "lab":
        raise HTTPException(status_code=403, detail="Only lab technicians can access this endpoint")
    return current_user


# ------------------------------------------
# Look up a patient's latest case by patient username / ID
# ------------------------------------------
@router.get("/lookup-patient")
def lookup_patient(
    patient_username: str,
    db: Session = Depends(get_db),
    lab_user: User = Depends(require_lab)
):
    """
    Lab tech enters a patient username to find their latest case.
    Returns case id + basic info so the lab tech can attach a report.
    """
    # Find the patient user
    patient = db.query(User).filter(User.username == patient_username, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get their most recent case
    case = (
        db.query(PatientCase)
        .filter(PatientCase.patient_name == patient_username)
        .order_by(PatientCase.id.desc())
        .first()
    )

    if not case:
        raise HTTPException(status_code=404, detail="No cases found for this patient")

    analysis = case.analysis
    return {
        "patient_id": patient.id,
        "patient_username": patient.username,
        "patient_full_name": patient.full_name,
        "case_id": case.id,
        "case_status": case.status,
        "symptoms": case.symptoms,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "ai_prediction": analysis.raw_prediction_class if analysis else None,
        "existing_attachments": [
            {
                "id": a.id,
                "uploaded_by": a.uploaded_by,
                "original_filename": a.original_filename,
                "file_type": a.file_type,
            }
            for a in case.attachments
        ],
    }


# ------------------------------------------
# Upload official lab report to a case
# ------------------------------------------
@router.post("/upload-report")
async def upload_report(
    case_id: int = Form(...),
    comments: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    lab_user: User = Depends(require_lab)
):
    case = db.query(PatientCase).filter(PatientCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Save file to disk
    ext = os.path.splitext(file.filename)[1]
    filename = f"lab_{lab_user.id}_case_{case_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Save attachment record
    attachment = Attachment(
        case_id=case_id,
        uploaded_by="lab_tech",
        uploader_username=lab_user.username,
        file_path=filename,
        file_type=file.content_type,
        original_filename=file.filename,
    )
    db.add(attachment)

    # Also update legacy field + comments for backward compat
    case.lab_report = filename
    case.lab_comments = comments

    db.commit()
    db.refresh(attachment)

    return {
        "message": "Report uploaded successfully",
        "case_id": case_id,
        "attachment_id": attachment.id,
        "file": filename,
    }


# ------------------------------------------
# Get all cases that have lab reports attached
# ------------------------------------------
@router.get("/my-uploads")
def get_my_uploads(
    db: Session = Depends(get_db),
    lab_user: User = Depends(require_lab)
):
    """Returns all attachments uploaded by this lab technician."""
    attachments = (
        db.query(Attachment)
        .filter(
            Attachment.uploaded_by == "lab_tech",
            Attachment.uploader_username == lab_user.username
        )
        .order_by(Attachment.id.desc())
        .all()
    )

    return {
        "uploads": [
            {
                "id": a.id,
                "case_id": a.case_id,
                "original_filename": a.original_filename,
                "file_type": a.file_type,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in attachments
        ]
    }
