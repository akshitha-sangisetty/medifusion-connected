"""Inference for the research-only MediFusion chest X-ray triage model.

The exported checkpoint is intentionally not stored in Git. Deployments must
explicitly opt in by mounting the checkpoint and setting
``MEDIFUSION_XRAY_MODEL_ENABLED=1``. Without that opt-in, image triage is
unavailable rather than falling back to a mock clinical prediction.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path

import numpy as np
import pydicom
import torch
import torch.nn as nn
import torch.nn.functional as functional
from torchvision.models import densenet121

from app.config import (
    XRAY_MODEL_CHECKPOINT,
    XRAY_MODEL_ENABLED,
    XRAY_TRIAGE_THRESHOLD,
)

MODEL_VERSION = "medifusion-densenet121-rsna-opacity-v1"
INPUT_SIZE = 224


class XrayModelUnavailable(RuntimeError):
    """Raised when this deployment has not explicitly enabled the checkpoint."""


class UnsupportedXrayError(ValueError):
    """Raised for an upload outside the model's DICOM-only research scope."""


@dataclass(frozen=True)
class XrayTriageResult:
    model_version: str
    possible_pulmonary_opacity_score: float
    review_threshold: float
    review_flag: bool

    def to_dict(self) -> dict:
        return asdict(self)


def model_status() -> dict:
    """Return configuration status without loading the checkpoint into memory."""
    checkpoint = Path(XRAY_MODEL_CHECKPOINT)
    return {
        "enabled": XRAY_MODEL_ENABLED,
        "checkpoint_present": checkpoint.is_file(),
        "checkpoint_path": str(checkpoint),
        "model_version": MODEL_VERSION,
        "review_threshold": XRAY_TRIAGE_THRESHOLD,
        "input": "single-frame DICOM chest X-ray only",
    }


def ensure_model_ready() -> None:
    status = model_status()
    if not status["enabled"]:
        raise XrayModelUnavailable(
            "Experimental chest X-ray triage is disabled. "
            "Set MEDIFUSION_XRAY_MODEL_ENABLED=1 only after mounting the approved checkpoint."
        )
    if not status["checkpoint_present"]:
        raise XrayModelUnavailable(
            "Experimental chest X-ray checkpoint was not found at "
            f"{status['checkpoint_path']}."
        )


def validate_dicom_bytes(content: bytes) -> None:
    """Validate uploads before persisting a case or loading the neural network."""
    if not content:
        raise UnsupportedXrayError("The uploaded DICOM file is empty.")
    try:
        dataset = pydicom.dcmread(BytesIO(content), force=False)
        if not hasattr(dataset, "PixelData"):
            raise UnsupportedXrayError("The DICOM file has no pixel data.")
    except UnsupportedXrayError:
        raise
    except Exception as exc:
        raise UnsupportedXrayError(
            "This research model accepts a valid DICOM chest X-ray (.dcm) only."
        ) from exc


def _dicom_to_tensor(file_path: str | Path) -> torch.Tensor:
    try:
        dataset = pydicom.dcmread(str(file_path), force=False)
        image = dataset.pixel_array.astype(np.float32)
    except Exception as exc:
        raise UnsupportedXrayError(
            "The uploaded file could not be read as a DICOM chest X-ray."
        ) from exc

    if image.ndim != 2:
        raise UnsupportedXrayError(
            "This research model accepts a single-frame, two-dimensional chest X-ray only."
        )

    slope = float(getattr(dataset, "RescaleSlope", 1.0))
    intercept = float(getattr(dataset, "RescaleIntercept", 0.0))
    image = image * slope + intercept

    if getattr(dataset, "PhotometricInterpretation", "") == "MONOCHROME1":
        image = image.max() - image

    low, high = np.percentile(image, [1, 99])
    image = np.clip((image - low) / max(high - low, 1e-6), 0, 1)

    tensor = torch.from_numpy(image).unsqueeze(0).unsqueeze(0)
    tensor = functional.interpolate(
        tensor,
        size=(INPUT_SIZE, INPUT_SIZE),
        mode="bilinear",
        align_corners=False,
    )
    tensor = tensor.repeat(1, 3, 1, 1)

    mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
    return (tensor - mean) / std


class PulmonaryOpacityTriageModel:
    def __init__(self, checkpoint_path: str | Path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = densenet121(weights=None)
        self.model.classifier = nn.Linear(self.model.classifier.in_features, 1)

        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        state_dict = checkpoint.get("model_state_dict", checkpoint)
        self.model.load_state_dict(state_dict, strict=True)
        self.model.to(self.device)
        self.model.eval()

    def predict(self, file_path: str | Path) -> XrayTriageResult:
        image = _dicom_to_tensor(file_path).to(self.device)
        with torch.inference_mode():
            logit = self.model(image).squeeze().item()

        score = float(torch.sigmoid(torch.tensor(logit)).item())
        return XrayTriageResult(
            model_version=MODEL_VERSION,
            possible_pulmonary_opacity_score=round(score, 4),
            review_threshold=XRAY_TRIAGE_THRESHOLD,
            review_flag=score >= XRAY_TRIAGE_THRESHOLD,
        )


@lru_cache(maxsize=1)
def load_model() -> PulmonaryOpacityTriageModel:
    """Load the approved checkpoint once per API process."""
    ensure_model_ready()
    return PulmonaryOpacityTriageModel(XRAY_MODEL_CHECKPOINT)


def predict_dicom(file_path: str | Path) -> XrayTriageResult:
    return load_model().predict(file_path)
