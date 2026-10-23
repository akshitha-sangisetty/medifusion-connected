import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/medifusion")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
SECRET_KEY = os.getenv("SECRET_KEY")
if ENVIRONMENT == "production" and not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set when ENVIRONMENT=production.")
# A local-only fallback keeps the development workflow simple. It is never
# accepted for a production deployment.
SECRET_KEY = SECRET_KEY or "development-only-secret-not-for-production"
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.getenv("MEDIFUSION_UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
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
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
MODEL_RELEASE_URL = os.getenv("MEDIFUSION_MODEL_RELEASE_URL", "")
MODEL_GITHUB_TOKEN = os.getenv("MEDIFUSION_MODEL_GITHUB_TOKEN", "")
MODEL_CHECKPOINT_SHA256 = os.getenv("MEDIFUSION_MODEL_SHA256", "")


def _configured_origins() -> list[str]:
    """Return explicit browser origins allowed to call the API and Socket.IO."""
    configured = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,https://medifusion-connected.vercel.app",
    )
    return [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]


ALLOWED_ORIGINS = _configured_origins()

os.makedirs(UPLOAD_DIR, exist_ok=True)
