# app/api/ai/routes.py
from fastapi import APIRouter, HTTPException, UploadFile, File

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/predict-from-image")
async def predict_image(file: UploadFile = File(...)):
    """Retained only to return a clear response to obsolete clients."""
    raise HTTPException(
        status_code=410,
        detail="This endpoint was retired. Use the authenticated /predict/image endpoint.",
    )
