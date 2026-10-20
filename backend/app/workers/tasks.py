# workers/tasks.py
from celery import Celery

celery = Celery(
    "medifusion_tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)

@celery.task
def process_case_task(case_id: int):
    """Legacy task retained for queue compatibility; no mock inference is run."""
    return {
        "case_id": case_id,
        "processed": False,
        "reason": "Mock prediction tasks are disabled. DICOM triage runs synchronously in /predict/image.",
    }
