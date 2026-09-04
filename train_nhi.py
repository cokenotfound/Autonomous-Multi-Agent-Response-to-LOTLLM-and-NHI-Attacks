import json
import torch
import os
from detection.nhi.behavioral_model import NHIBehavioralModel

# 1. Load preprocessed feature output
with open("data/preprocessed_output.json", "r") as f:
    preprocessed_data = json.load(f)

# 2. Set feature dimensions
num_features = 3  # logon, file, device activity metrics
hidden_dim = 16

model = NHIBehavioralModel(input_dim=num_features, hidden_dim=hidden_dim)

# 3. Fit statistical fallback on baseline user data
sample_user = "user_01"
dummy_sequence = torch.randn(1, 15, num_features)
model.fallback.fit(sample_user, dummy_sequence.squeeze().numpy())

# 4. Evaluate sample sequence
score, explanations = model.analyze_sequence(sample_user, dummy_sequence)
print(f"Anomaly Score: {score:.4f}")
print("Explanations:", explanations)

# 5. Export trained weights
os.makedirs("models", exist_ok=True)
model.export_models(pt_path="models/nhi_lstm.pt", pkl_path="models/nhi_fallback.pkl")
print("Saved artifacts to 'models/nhi_lstm.pt' and 'models/nhi_fallback.pkl'")