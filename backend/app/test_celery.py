import time
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.patient_case import PatientCase
from app.workers.tasks import process_case_task

def add_test_case():
    db: Session = SessionLocal()
    try:
        # Add a pending test case
        test_case = PatientCase(symptoms="fever,cough", status="pending")
        db.add(test_case)
        db.commit()
        db.refresh(test_case)
        print(f"Added test case with ID: {test_case.id}")
        return test_case.id
    finally:
        db.close()

def wait_for_task(case_id: int, timeout=20):
    """Poll the database until case is processed or timeout"""
    db: Session = SessionLocal()
    try:
        for _ in range(timeout):
            case: PatientCase = db.query(PatientCase).filter(PatientCase.id == case_id).first()
            if case.status == "processed":
                print(f"Task completed! Case ID: {case.id}")
                print(f"Severity: {case.severity_score}")
                print(f"AI Result: {case.ai_result}")
                return
            time.sleep(1)
        print("Task did not finish within timeout.")
    finally:
        db.close()

if __name__ == "__main__":
    case_id = add_test_case()
    # Trigger Celery task
    process_case_task.delay(case_id)
    print("Task submitted, waiting for completion...")
    wait_for_task(case_id)
