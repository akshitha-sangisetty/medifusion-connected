# =============================================================
# ai_service.py  —  Mock AI Analysis Service
#
# This module is the ONLY place AI inference happens.
# To swap in the real trained model later, replace the body of
# `analyze_case()` without touching any other file in the app.
# =============================================================
import random
from sqlalchemy.orm import Session


# ------------------------------------------------------------------
# Mock inference — replace this function's body when the real model
# is ready.  The signature and return shape must stay the same.
# ------------------------------------------------------------------
def _run_model(symptoms: str | None, image_path: str | None) -> dict:
    """
    Mock model: picks a random class and generates plausible
    confidence scores that sum to ~1.0.
    Returns: { class_name: float, ... }
    """
    classes = ["Normal", "Pneumonia", "COVID-19", "Tuberculosis"]

    # Seed with symptoms text for reproducibility per patient
    seed_text = (symptoms or "") + (image_path or "")
    rng = random.Random(hash(seed_text) % (2**32))

    # Pick winning class
    winner = rng.choice(classes)

    # Generate raw scores then softmax-ish normalise
    raw = {c: rng.uniform(0.05, 0.3) for c in classes}
    raw[winner] = rng.uniform(0.55, 0.90)
    total = sum(raw.values())
    scores = {c: round(v / total, 4) for c, v in raw.items()}

    return scores


# ------------------------------------------------------------------
# Summaries per class
# ------------------------------------------------------------------
_PATIENT_SUMMARIES = {
    "Normal": (
        "Good news — your analysis looks normal. "
        "No significant signs of infection or disease were detected. "
        "Continue monitoring any symptoms and follow up with your doctor if they persist."
    ),
    "Pneumonia": (
        "Your analysis suggests possible signs of pneumonia. "
        "This means there may be inflammation in your lungs. "
        "Please consult your doctor as soon as possible for a proper evaluation."
    ),
    "COVID-19": (
        "Your analysis shows patterns that may be associated with COVID-19. "
        "Please self-isolate and contact your doctor or a COVID-19 helpline immediately."
    ),
    "Tuberculosis": (
        "Your analysis shows patterns that may be associated with tuberculosis (TB). "
        "This is treatable — please see a doctor urgently so proper tests can be arranged."
    ),
}

_DOCTOR_SUMMARIES = {
    "Normal": (
        "AI classification: Normal. "
        "Confidence: {conf:.1f}%. No significant radiological or symptomatic markers detected. "
        "Recommend clinical correlation and patient follow-up if symptoms persist."
    ),
    "Pneumonia": (
        "AI classification: Pneumonia (confidence: {conf:.1f}%). "
        "Analysis indicates possible consolidation or infiltrates. "
        "Recommend chest X-ray confirmation, CBC, CRP, and empiric antibiotic therapy pending culture results."
    ),
    "COVID-19": (
        "AI classification: COVID-19 (confidence: {conf:.1f}%). "
        "Pattern consistent with bilateral ground-glass opacities. "
        "Recommend RT-PCR confirmation, O2 saturation monitoring, and isolation protocol."
    ),
    "Tuberculosis": (
        "AI classification: Tuberculosis (confidence: {conf:.1f}%). "
        "Analysis suggests upper lobe involvement consistent with TB presentation. "
        "Recommend sputum AFB smear, GeneXpert MTB/RIF, and immediate infection control measures."
    ),
}


# ------------------------------------------------------------------
# Public API — this is the only function other modules should call
# ------------------------------------------------------------------
def analyze_case(case_id: int, db: Session) -> dict:
    """
    Run AI analysis on a case and persist the result.

    Returns the CaseAnalysis ORM object after committing to DB.
    If analysis already exists it is overwritten.
    """
    from app.models.patient_case import PatientCase, CaseAnalysis

    case = db.query(PatientCase).filter(PatientCase.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    # Run mock model
    scores = _run_model(case.symptoms, case.uploaded_file)
    predicted_class = max(scores, key=scores.get)
    confidence = scores[predicted_class] * 100

    patient_summary = _PATIENT_SUMMARIES[predicted_class]
    doctor_summary = _DOCTOR_SUMMARIES[predicted_class].format(conf=confidence)

    # Upsert analysis row
    existing = db.query(CaseAnalysis).filter(CaseAnalysis.case_id == case_id).first()
    if existing:
        analysis = existing
    else:
        analysis = CaseAnalysis(case_id=case_id)
        db.add(analysis)

    analysis.patient_summary = patient_summary
    analysis.doctor_summary = doctor_summary
    analysis.confidence_scores = scores
    analysis.raw_prediction_class = predicted_class

    # Advance case status
    if case.status == "submitted":
        case.status = "analyzed"

    db.commit()
    db.refresh(analysis)
    return analysis
