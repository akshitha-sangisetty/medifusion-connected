"""Legacy mock-prediction interface intentionally disabled.

Clinical-looking mock results must never be substituted for the trained,
research-only DICOM model.
"""


def deterministic_image_predict(_image_bytes: bytes) -> dict:
    raise RuntimeError(
        "Mock image predictions are disabled. Use the approved DICOM triage model instead."
    )


def symptoms_to_prediction(_symptoms_text) -> dict:
    raise RuntimeError(
        "Symptom-based mock predictions are disabled; no diagnosis is available."
    )
