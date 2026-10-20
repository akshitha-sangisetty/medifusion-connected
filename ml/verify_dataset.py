"""Verify the local RSNA image and annotation downloads.

This script reads only metadata and one sample image; it does not train a model.
Run from the project root:
    .\\ml\\.venv\\Scripts\\python.exe .\\ml\\verify_dataset.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Dependencies are stored locally because the system Python installation does
# not provide a usable virtual-environment bootstrap on this machine.
LOCAL_PACKAGES = Path(__file__).parent / ".packages"
if LOCAL_PACKAGES.is_dir():
    sys.path.insert(0, str(LOCAL_PACKAGES))

import pydicom

IMAGES_DIR = Path(r"C:\rsna\mdai_rsna_project_x9N20BZa_images_2018-07-20-153330")
ANNOTATIONS_PATH = Path(
    r"C:\rsna_annotations\pneumonia-challenge-annotations-adjudicated-kaggle_2018.json"
)


def find_sample_dicom(images_dir: Path) -> Path:
    try:
        return next(images_dir.rglob("*.dcm"))
    except StopIteration as exc:
        raise FileNotFoundError(f"No .dcm image found below {images_dir}") from exc


def main() -> None:
    if not IMAGES_DIR.is_dir():
        raise FileNotFoundError(f"Images folder not found: {IMAGES_DIR}")
    if not ANNOTATIONS_PATH.is_file():
        raise FileNotFoundError(f"Annotations file not found: {ANNOTATIONS_PATH}")

    sample_path = find_sample_dicom(IMAGES_DIR)
    image = pydicom.dcmread(sample_path, stop_before_pixels=True)

    with ANNOTATIONS_PATH.open("r", encoding="utf-8") as annotation_file:
        annotations = json.load(annotation_file)

    label_groups = annotations.get("labelGroups", [])
    label_names = [
        label["name"]
        for group in label_groups
        for label in group.get("labels", [])
    ]
    annotation_count = sum(
        len(dataset.get("annotations", []))
        for dataset in annotations.get("datasets", [])
    )

    print("RSNA dataset verification passed")
    print(f"Sample image: {sample_path}")
    print(f"Patient ID: {image.get('PatientID', 'missing')}")
    print(f"Study UID: {image.get('StudyInstanceUID', 'missing')}")
    print(f"Image dimensions: {image.get('Rows', 'missing')} x {image.get('Columns', 'missing')}")
    print(f"Annotation records: {annotation_count:,}")
    print("Available labels:")
    for name in sorted(set(label_names)):
        print(f"  - {name}")


if __name__ == "__main__":
    main()
