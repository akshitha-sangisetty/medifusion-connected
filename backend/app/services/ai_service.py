"""Persist research-only chest X-ray triage results for a case.

This service deliberately supports only the trained binary chest X-ray model.
It does not infer pneumonia, COVID-19, tuberculosis, treatments, or diagnoses
from symptoms.
"""

from pathlib import Path

from sqlalchemy.orm import Session

from app.ai.model_loader import predict_dicom
from app.config import UPLOAD_DIR


def _case_upload_path(filename: str | None) -> Path:
    if not filename:
        raise ValueError("A DICOM chest X-ray is required for experimental triage.")

    # Only use the filename portion persisted by the upload route.
    path = Path(UPLOAD_DIR) / Path(filename).name
    if not path.is_file():
        raise ValueError("The uploaded DICOM file is no longer available for analysis.")
    return path


def _patient_summary() -> str:
    return (
        "An experimental research model processed this DICOM chest X-ray. "
        "Its output is not a diagnosis and is not shown as a medical conclusion. "
        "A qualified clinician or radiologist must review the image."
    )


def _doctor_summary(score: float, threshold: float, flagged: bool) -> str:
    status = "flagged for clinician review" if flagged else "not flagged by the experimental threshold"
    return (
        "Research-only chest X-ray triage result. "
        f"Possible pulmonary-opacity model score: {score:.1%}. "
        f"Experimental review threshold: {threshold:.3f}. "
        f"The image was {status}. "
        "This score is not calibrated for diagnosis, does not exclude disease, and must not guide treatment."
    )


def analyze_case(case_id: int, db: Session):
    """Run the frozen DICOM triage model and persist its research output."""
    from app.models.patient_case import CaseAnalysis, PatientCase

    case = db.query(PatientCase).filter(PatientCase.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    triage = predict_dicom(_case_upload_path(case.uploaded_file))

    label = (
        "Experimental review flag: possible pulmonary opacity"
        if triage.review_flag
        else "Experimental result: not flagged for review"
    )

    existing = db.query(CaseAnalysis).filter(CaseAnalysis.case_id == case_id).first()
    analysis = existing or CaseAnalysis(case_id=case_id)
    if not existing:
        db.add(analysis)

    analysis.patient_summary = _patient_summary()
    analysis.doctor_summary = _doctor_summary(
        triage.possible_pulmonary_opacity_score,
        triage.review_threshold,
        triage.review_flag,
    )
    analysis.confidence_scores = {
        "experimental_triage": True,
        **triage.to_dict(),
        "limitations": "Not a diagnosis; qualified clinician review required.",
    }
    analysis.raw_prediction_class = label

    if case.status == "submitted":
        case.status = "analyzed"

    db.commit()
    db.refresh(analysis)
    return analysis
