import torch
import torch.nn as nn
from .baseline_fallback import NHIBaselineFallback
from .explain import extract_top_features

class LSTMAutoencoder(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers=2):
        super(LSTMAutoencoder, self).__init__()
        self.encoder = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.decoder = nn.LSTM(hidden_dim, input_dim, num_layers, batch_first=True)

    def forward(self, x):
        _, (hidden, _) = self.encoder(x)
        hidden_repeated = hidden[-1].unsqueeze(1).repeat(1, x.size(1), 1)
        reconstructed, _ = self.decoder(hidden_repeated)
        return reconstructed

class NHIBehavioralModel:
    def __init__(self, input_dim, hidden_dim, min_seq_length=10):
        self.autoencoder = LSTMAutoencoder(input_dim, hidden_dim)
        self.fallback = NHIBaselineFallback()
        self.min_seq_length = min_seq_length
        self.feature_names = [f"Feature_{i}" for i in range(input_dim)]

    def analyze_sequence(self, user_id, sequence_tensor):
        # Route to statistical baseline if sequence is too short
        if sequence_tensor.size(1) < self.min_seq_length:
            score = self.fallback.score(user_id, sequence_tensor.numpy())
            return score, ["Sequence too short. Used statistical fallback."]
        
        # Route to Deep Learning Autoencoder
        self.autoencoder.eval()
        with torch.no_grad():
            reconstructed = self.autoencoder(sequence_tensor)
            mse_loss = nn.MSELoss()(reconstructed, sequence_tensor)
            score = min(mse_loss.item(), 1.0) 

            explanations = extract_top_features(
                sequence_tensor.squeeze().numpy(), 
                reconstructed.squeeze().numpy(), 
                self.feature_names
            )
            
        return score, explanations

    def export_models(self, pt_path="nhi_lstm.pt", pkl_path="nhi_fallback.pkl"):
        torch.save(self.autoencoder.state_dict(), pt_path)
        self.fallback.save(pkl_path)