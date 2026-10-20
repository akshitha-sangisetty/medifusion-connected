"""Build a patient-safe training manifest for the RSNA lung-opacity dataset.

The script uses only the dataset's *Calculated* labels:
  L_v8n = Lung Opacity (positive)
  L_o8w = Normal (negative)
  L_yd0 = No Lung Opacity / Not Normal (negative)

It does not train a model. By default it checks the first 500 images. Use
--full only after the sample output has been reviewed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

LOCAL_PACKAGES = Path(__file__).parent / ".packages"
if LOCAL_PACKAGES.is_dir():
    sys.path.insert(0, str(LOCAL_PACKAGES))

import pydicom

IMAGES_DIR = Path(r"C:\rsna\mdai_rsna_project_x9N20BZa_images_2018-07-20-153330")
ANNOTATIONS_PATH = Path(
    r"C:\rsna_annotations\pneumonia-challenge-annotations-adjudicated-kaggle_2018.json"
)
OUTPUT_DIR = Path(__file__).parent / "artifacts"

POSITIVE_LABEL = "L_v8n"
NEGATIVE_LABELS = {"L_o8w", "L_yd0"}


def split_for_patient(patient_id: str) -> str:
    """Assign one stable split per patient, preventing patient leakage."""
    bucket = int(hashlib.sha256(patient_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "validation"
    return "test"


def labels_by_study() -> dict[str, dict[str, object]]:
    with ANNOTATIONS_PATH.open("r", encoding="utf-8") as annotation_file:
        source = json.load(annotation_file)

    records: dict[str, dict[str, object]] = defaultdict(
        lambda: {"has_opacity": False, "has_negative_label": False, "bbox_count": 0}
    )
    for annotation in source["datasets"][0]["annotations"]:
        label_id = annotation["labelId"]
        study_uid = annotation["StudyInstanceUID"]
        if label_id == POSITIVE_LABEL:
            records[study_uid]["has_opacity"] = True
            records[study_uid]["bbox_count"] = int(records[study_uid]["bbox_count"]) + 1
        elif label_id in NEGATIVE_LABELS:
            records[study_uid]["has_negative_label"] = True
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Process all images instead of a 500-image sample.")
    args = parser.parse_args()

    if not IMAGES_DIR.is_dir() or not ANNOTATIONS_PATH.is_file():
        raise FileNotFoundError("RSNA images or annotations were not found at the documented paths.")

    annotation_index = labels_by_study()
    limit = None if args.full else 500
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_name = "rsna_manifest_full.csv" if args.full else "rsna_manifest_sample.csv"
    output_path = OUTPUT_DIR / output_name

    processed = matched = positives = negatives = skipped = 0
    with output_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(
            manifest_file,
            fieldnames=["image_path", "patient_id", "study_uid", "target", "bbox_count", "split"],
        )
        writer.writeheader()

        for image_path in IMAGES_DIR.rglob("*.dcm"):
            if limit is not None and processed >= limit:
                break
            processed += 1
            if processed % 1000 == 0:
                print(f"Processed {processed:,} DICOM files...", flush=True)
            metadata = pydicom.dcmread(image_path, stop_before_pixels=True)
            study_uid = str(metadata.StudyInstanceUID)
            patient_id = str(metadata.PatientID)
            label = annotation_index.get(study_uid)
            if not label:
                skipped += 1
                continue

            target = 1 if label["has_opacity"] else 0
            if target:
                positives += 1
            elif label["has_negative_label"]:
                negatives += 1
            else:
                skipped += 1
                continue

            matched += 1
            writer.writerow(
                {
                    "image_path": str(image_path),
                    "patient_id": patient_id,
                    "study_uid": study_uid,
                    "target": target,
                    "bbox_count": label["bbox_count"],
                    "split": split_for_patient(patient_id),
                }
            )

    print(f"Wrote: {output_path}")
    print(f"DICOM files checked: {processed:,}")
    print(f"Labelled images written: {matched:,}")
    print(f"Positive / lung-opacity images: {positives:,}")
    print(f"Negative images: {negatives:,}")
    print(f"Skipped (no usable calculated label): {skipped:,}")


if __name__ == "__main__":
    main()
