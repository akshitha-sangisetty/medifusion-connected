import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/medifusion")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
MODEL_ARTIFACT_DIR = os.getenv(
    "MEDIFUSION_MODEL_ARTIFACT_DIR",
    os.path.join(os.path.dirname(BASE_DIR), "model_artifacts"),
)
XRAY_MODEL_CHECKPOINT = os.getenv(
    "MEDIFUSION_XRAY_CHECKPOINT",
    os.path.join(MODEL_ARTIFACT_DIR, "medifusion_densenet_full_best.pt"),
)
XRAY_MODEL_ENABLED = os.getenv("MEDIFUSION_XRAY_MODEL_ENABLED", "0") == "1"
XRAY_TRIAGE_THRESHOLD = float(os.getenv("MEDIFUSION_XRAY_TRIAGE_THRESHOLD", "0.360"))

os.makedirs(UPLOAD_DIR, exist_ok=True)

print("UPLOAD DIR:", UPLOAD_DIR)
