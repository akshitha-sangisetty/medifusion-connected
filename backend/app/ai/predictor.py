import hashlib
from PIL import Image
import io

def deterministic_image_predict(image_bytes: bytes) -> dict:
    """
    Deterministic pseudo-AI based on image bytes.
    Accepts raw bytes instead of a file path.
    Labels: normal, pneumonia, covid-like, effusion
    """
    if not image_bytes:
        return {"label": "unknown", "prob": 0.0}

    labels = ["normal", "pneumonia", "covid-like", "effusion"]

    # ✅ Hash the bytes directly
    h = hashlib.sha256(image_bytes).hexdigest()

    # ✅ Pick label and probability from hash
    idx = int(h[:8], 16) % len(labels)
    prob = (int(h[8:16], 16) % 10000) / 10000.0  # 0.0 - 0.9999

    return {"label": labels[idx], "prob": round(prob, 4)}


def symptoms_to_prediction(symptoms_text) -> dict:
    """
    Converts symptoms (string or list) to a deterministic pseudo-prediction.
    """
    if isinstance(symptoms_text, list):
        txt = " ".join(symptoms_text).lower()
    else:
        txt = (symptoms_text or "").lower()

    score = 0.0
    if "cough" in txt:
        score += 0.2
    if "fever" in txt:
        score += 0.25
    if "breath" in txt or "dyspnea" in txt or "shortness" in txt:
        score += 0.35
    if "chest" in txt or "pain" in txt:
        score += 0.15

    if score == 0:
        return {"label": "normal", "prob": 0.05}

    label = "pneumonia" if score >= 0.5 else "covid-like"
    prob = min(0.95, score + 0.1)
    return {"label": label, "prob": round(prob, 4)}
