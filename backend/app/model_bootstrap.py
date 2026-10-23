"""Fetch and verify the approved research checkpoint before API startup.

The checkpoint is never kept in Git. In production, Render provides a private
GitHub release URL and a read-only GitHub token as environment secrets.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
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


def _download_request(url: str, accept: str) -> Request:
    return Request(
        url,
        headers={
            "Accept": accept,
            "Authorization": f"Bearer {MODEL_GITHUB_TOKEN}",
            "User-Agent": "medifusion-model-bootstrap",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )


def _github_asset_api_url(release_url: str) -> str:
    """Resolve a private browser download URL to its authenticated asset API URL.

    Fine-grained tokens work consistently against GitHub's REST endpoints.
    A normal release URL has the form
    github.com/<owner>/<repo>/releases/download/<tag>/<asset-name>.
    """
    parsed = urlparse(release_url)
    parts = [unquote(part) for part in parsed.path.strip("/").split("/")]
    if parsed.netloc not in {"github.com", "www.github.com"} or len(parts) < 6:
        return release_url
    owner, repository, marker, download, tag = parts[:5]
    asset_name = "/".join(parts[5:])
    if marker != "releases" or download != "download" or not asset_name:
        return release_url

    release_api_url = f"https://api.github.com/repos/{owner}/{repository}/releases/tags/{tag}"
    with urlopen(_download_request(release_api_url, "application/vnd.github+json"), timeout=30) as response:
        release = json.load(response)
    for asset in release.get("assets", []):
        if asset.get("name") == asset_name:
            return asset["url"]
    raise RuntimeError("The configured GitHub release does not contain the expected model asset.")


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
    temp_path: Path | None = None
    try:
        asset_url = _github_asset_api_url(MODEL_RELEASE_URL)
        request = _download_request(asset_url, "application/octet-stream")
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
    except HTTPError as exc:
        if exc.code in {401, 403, 404}:
            raise RuntimeError(
                "GitHub could not authorize the private model release. Verify that "
                "the fine-grained token has Contents: Read-only access to the "
                "medifusion-model-artifacts repository."
            ) from exc
        raise RuntimeError("Could not download the private model release.") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("Could not download the private model release.") from exc
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ensure_checkpoint()
