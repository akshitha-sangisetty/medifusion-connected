# app/api/lab/routes.py

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
import os
from app.core.database import get_db
from app.models.patient_case import PatientCase
from app.redis_client import redis_client
from app.api.auth.routes import get_current_user
from app.models.user import User
from app.config import UPLOAD_DIR

router = APIRouter(prefix="/lab", tags=["Lab"])


# ------------------------------
# Helper: Check if user is lab
# ------------------------------
def require_lab(user: User = Depends(get_current_user)):
    if user.role != "lab":
        raise HTTPException(status_code=403, detail="Only lab technicians can upload reports")
    return user


# ------------------------------
# Upload Lab Report
# ------------------------------
@router.post("/upload-report")
async def upload_report(
    case_id: int = Form(...),
    comments: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_lab)
):
    # Validate Case Exists
    case = db.query(PatientCase).filter(PatientCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case ID not found")

    # Save uploaded file
    ext = os.path.splitext(file.filename)[1]
    filename = f"lab_report_case_{case_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Update case with report info
    case.lab_report = filename
    case.lab_comments = comments
    case.status = "lab_uploaded"

    db.add(case)
    db.commit()
    db.refresh(case)

    return {
        "message": "Report uploaded successfully",
        "case_id": case_id,
        "file": filename
    }
