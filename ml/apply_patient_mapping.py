"""Create the final patient-safe RSNA manifest from the RSNA-to-NIH mapping."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
INPUT_MANIFEST = ARTIFACTS_DIR / "rsna_manifest_full.csv"
OUTPUT_MANIFEST = ARTIFACTS_DIR / "rsna_manifest_patient_safe.csv"
MAPPING_PATH = Path(r"C:\rsna_mapping\pneumonia-challenge-dataset-mappings_2018.json")


SPLITS = ("train", "validation", "test")
SPLIT_RATIOS = {"train": 0.80, "validation": 0.10, "test": 0.10}


def assign_balanced_patient_splits(rows: list[dict[str, str]]) -> dict[str, str]:
    """Assign whole patients while approximately preserving class proportions."""
    patient_counts: dict[str, Counter[str]] = {}
    total = Counter()
    for row in rows:
        patient_id = row["patient_id"]
        patient_counts.setdefault(patient_id, Counter())[row["target"]] += 1
        total[row["target"]] += 1

    targets = {
        split: {target: total[target] * SPLIT_RATIOS[split] for target in ("0", "1")}
        for split in SPLITS
    }
    assigned = {split: Counter() for split in SPLITS}
    assignments: dict[str, str] = {}

    # Larger patients go first so their images are distributed deliberately.
    patients = sorted(
        patient_counts,
        key=lambda patient_id: (
            -(patient_counts[patient_id]["0"] + patient_counts[patient_id]["1"]),
            patient_id,
        ),
    )
    for patient_id in patients:
        counts = patient_counts[patient_id]

        def cost(split: str) -> tuple[float, float]:
            ratios = [
                (assigned[split][target] + counts[target]) / max(targets[split][target], 1)
                for target in ("0", "1")
            ]
            return max(ratios), sum(ratios)

        split = min(SPLITS, key=cost)
        assignments[patient_id] = split
        assigned[split].update(counts)
    return assignments


def main() -> None:
    if not INPUT_MANIFEST.is_file() or not MAPPING_PATH.is_file():
        raise FileNotFoundError("The full manifest or RSNA mapping file is missing.")

    with MAPPING_PATH.open("r", encoding="utf-8") as mapping_file:
        mapping = json.load(mapping_file)
    patient_by_study = {
        row["StudyInstanceUID"]: row["img_id"].split("_", maxsplit=1)[0]
        for row in mapping
    }

    mapped_rows: list[dict[str, str]] = []
    unmatched = 0
    with INPUT_MANIFEST.open("r", newline="", encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        for row in reader:
            patient_id = patient_by_study.get(row["study_uid"])
            if patient_id is None:
                unmatched += 1
                continue
            row["patient_id"] = patient_id
            mapped_rows.append(row)

    if unmatched:
        raise ValueError(f"{unmatched} manifest rows had no matching original NIH patient ID.")

    assignments = assign_balanced_patient_splits(mapped_rows)
    counts: Counter[tuple[str, str]] = Counter()
    with OUTPUT_MANIFEST.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=mapped_rows[0].keys())
        writer.writeheader()
        for row in mapped_rows:
            row["split"] = assignments[row["patient_id"]]
            writer.writerow(row)
            counts[(row["split"], row["target"])] += 1

    print(f"Wrote: {OUTPUT_MANIFEST}")
    print(f"Images: {sum(counts.values()):,}")
    print(f"Unique original NIH patients: {len(assignments):,}")
    for split in ("train", "validation", "test"):
        print(
            f"{split}: {counts[(split, '1')]:,} positive, "
            f"{counts[(split, '0')]:,} negative"
        )


if __name__ == "__main__":
    main()
