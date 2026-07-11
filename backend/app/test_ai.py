from ai.model_loader import load_model
from ai.predictor import deterministic_image_predict, symptoms_to_prediction

# Step 1: Load the model (stub for now)
model = load_model()
print("Loaded model:", model)

# Step 2: Test image prediction
# Replace with a real X-ray file path if available
image_path = "/app/uploads/sample_xray.jpg"
image_result = deterministic_image_predict(image_path)
print("Image prediction:", image_result)

# Step 3: Test symptom prediction
symptoms_text = "cough and fever with shortness of breath"
symptom_result = symptoms_to_prediction(symptoms_text)
print("Symptoms prediction:", symptom_result)
