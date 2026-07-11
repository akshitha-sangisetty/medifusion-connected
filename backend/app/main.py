import logging
import os

import socketio
from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.predictor import deterministic_image_predict, symptoms_to_prediction
from app.api.auth.routes import router as auth_router, get_current_user
from app.models.user import User
from app.models.base import Base
from app.core.database import engine, get_db
from app.api.patient.routes import router as patient_router
from app.api.predict.routes import router as predict_router
from app.api.lab.routes import router as lab_router
from app.api.doctor.routes import router as doctor_router

# Socket.IO manager (must be imported AFTER all route modules so they can use `sio`)
from app.socket_manager import sio

# ---------------------------
# Logging
# ---------------------------
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ---------------------------
# FastAPI app
# ---------------------------
fastapi_app = FastAPI(title="MediFusion Backend")
fastapi_app.include_router(lab_router)
fastapi_app.include_router(patient_router)
fastapi_app.include_router(doctor_router)
fastapi_app.include_router(predict_router)
fastapi_app.include_router(auth_router)

# ---------------------------
# CORS configuration
# ---------------------------
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Database setup
# ---------------------------
DEV_MODE = os.getenv("DEV_MODE") == "1"

try:
    if DEV_MODE:
        logger.warning("⚠️  DEV_MODE is ON: resetting database...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database reset complete")
    else:
        Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.error("❌ Database setup error: %s", e)

# ---------------------------
# Test model with symptoms
# ---------------------------
class SymptomTest(BaseModel):
    symptoms: list[str]

@fastapi_app.post("/test-ai-symptoms", tags=["AI Test"])
def test_ai_symptoms(data: SymptomTest, current_user: User = Depends(get_current_user)):
    prediction = symptoms_to_prediction(data.symptoms)
    return {"input": data.symptoms, "prediction": prediction}

# ---------------------------
# Test model with image
# ---------------------------
@fastapi_app.post("/test-ai-image", tags=["AI Test"])
async def test_ai_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    image_bytes = await file.read()
    prediction = deterministic_image_predict(image_bytes)
    return {"filename": file.filename, "prediction": prediction}

# ---------------------------
# Root endpoint
# ---------------------------
@fastapi_app.get("/", tags=["Root"])
def root():
    return {"ok": True, "service": "MediFusion Backend"}

# ---------------------------
# Swagger/OpenAPI Security
# ---------------------------
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if fastapi_app.openapi_schema:
        return fastapi_app.openapi_schema
    openapi_schema = get_openapi(
        title=fastapi_app.title,
        version="1.0",
        description="MediFusion Backend API",
        routes=fastapi_app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    if "/auth/me" in openapi_schema["paths"]:
        openapi_schema["paths"]["/auth/me"]["get"]["security"] = [{"OAuth2PasswordBearer": []}]
    fastapi_app.openapi_schema = openapi_schema
    return openapi_schema

fastapi_app.openapi = custom_openapi

# ---------------------------
# Mount Socket.IO onto FastAPI
# Socket.IO handles /socket.io/* routes;
# everything else goes to FastAPI.
# ---------------------------
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
