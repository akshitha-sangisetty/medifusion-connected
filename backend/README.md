# MediFusion Backend (local demo)

## Quick start with Docker
1. Ensure Docker is installed.
2. From `backend/` directory run:

## Experimental chest X-ray triage setup

The trained DenseNet-121 model is not included in the repository. It is a
research artifact and must not be deployed as a diagnostic service.

1. Download `medifusion_densenet_full_best.pt` from the training Google Drive.
2. Create `backend/model_artifacts/` and place the checkpoint inside it.
3. Set these environment variables before starting Docker:

```powershell
$env:MEDIFUSION_MODEL_ARTIFACT_DIR = "$PWD/model_artifacts"
$env:MEDIFUSION_XRAY_MODEL_ENABLED = "1"
docker compose up --build
```

The checkpoint is intentionally ignored by Git. The `POST /predict/image`
endpoint accepts only a single-frame DICOM chest X-ray (`.dcm`). It returns an
experimental possible-pulmonary-opacity review flag, not a diagnosis. When the
model flag is disabled or the artifact is unavailable, the endpoint returns a
clear `503` response instead of a mock clinical prediction.

Use `GET /predict/xray-model-status` to verify model readiness. Do not expose
this feature as a diagnosis, treatment recommendation, or autonomous clinical
decision.
