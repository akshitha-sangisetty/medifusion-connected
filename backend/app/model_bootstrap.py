"""Fetch and verify the approved research checkpoint before API startup.

The checkpoint is never kept in Git. In production, Render provides a private
GitHub release URL and a read-only GitHub token as environment secrets.
"""

from __future__ import annotations

import hashlib
import logging
import os
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import (
    MODEL_CHECKPOINT_SHA256,
    MODEL_GITHUB_TOKEN,
    MODEL_RELEASE_URL,
    XRAY_MODEL_CHECKPOINT,
    XRAY_MODEL_ENABLED,
)

logger = logging.getLogger(__name__)
DOWNLOAD_CHUNK_BYTES = 1024 * 1024


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(DOWNLOAD_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_checkpoint(path: Path) -> bool:
    return path.is_file() and _sha256(path).lower() == MODEL_CHECKPOINT_SHA256.lower()


def ensure_checkpoint() -> Path:
    """Ensure the enabled model's verified checkpoint is available locally."""
    checkpoint_path = Path(XRAY_MODEL_CHECKPOINT)
    if not XRAY_MODEL_ENABLED:
        logger.info("Experimental X-ray model is disabled; skipping checkpoint download.")
        return checkpoint_path

    if not MODEL_CHECKPOINT_SHA256:
        raise RuntimeError(
            "Enabled model requires MEDIFUSION_MODEL_SHA256 to verify the checkpoint."
        )

    if _verify_checkpoint(checkpoint_path):
        logger.info("Verified model checkpoint already exists at %s.", checkpoint_path)
        return checkpoint_path

    if not MODEL_RELEASE_URL or not MODEL_GITHUB_TOKEN:
        raise RuntimeError(
            "No verified checkpoint is present. Set MEDIFUSION_MODEL_RELEASE_URL "
            "and MEDIFUSION_MODEL_GITHUB_TOKEN to download it."
        )

    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading the approved private model release.")
    request = Request(
        MODEL_RELEASE_URL,
        headers={
            "Accept": "application/octet-stream",
            "Authorization": f"Bearer {MODEL_GITHUB_TOKEN}",
            "User-Agent": "medifusion-model-bootstrap",
        },
    )
    temp_path: Path | None = None
    try:
        with urlopen(request, timeout=180) as response:
            with tempfile.NamedTemporaryFile(
                mode="wb", delete=False, dir=checkpoint_path.parent, suffix=".part"
            ) as temporary_file:
                temp_path = Path(temporary_file.name)
                for chunk in iter(lambda: response.read(DOWNLOAD_CHUNK_BYTES), b""):
                    temporary_file.write(chunk)

        if not _verify_checkpoint(temp_path):
            raise RuntimeError("Downloaded checkpoint hash does not match MEDIFUSION_MODEL_SHA256.")
        os.replace(temp_path, checkpoint_path)
        logger.info("Model checkpoint downloaded and verified.")
        return checkpoint_path
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("Could not download the private model release.") from exc
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ensure_checkpoint()
