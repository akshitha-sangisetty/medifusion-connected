# workers/tasks.py
from celery import Celery
from app.core.database import SessionLocal  # <-- FIXED
from app.models.patient_case import PatientCase          # <-- FIXED
from app.ai.predictor import deterministic_image_predict, symptoms_to_prediction

celery = Celery(
    "medifusion_tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)

@celery.task
def process_case_task(case_id: int):
    db = SessionLocal()
    case = db.query(PatientCase).filter(PatientCase.id == case_id).first()
    if case is None:
        return None

    xray_result = deterministic_image_predict(case.uploaded_file) if case.uploaded_file else None
    symptom_result = symptoms_to_prediction(case.symptoms) if case.symptoms else None

    case.xray_result = xray_result
    case.symptom_result = symptom_result
    db.commit()
    db.close()
    return case_id
