"""Manual check for the research-model deployment configuration."""

from app.ai.model_loader import model_status

print("Experimental DICOM triage model status:", model_status())
