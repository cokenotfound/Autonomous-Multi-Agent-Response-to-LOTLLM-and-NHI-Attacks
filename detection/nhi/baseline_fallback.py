import numpy as np
import pickle

class NHIBaselineFallback:
    """Statistical fallback for low-history credentials."""
    def __init__(self, moving_avg_window=5, z_score_threshold=3.0):
        self.window = moving_avg_window
        self.threshold = z_score_threshold
        self.historical_stats = {}

    def fit(self, user_id, sequence):
        mean = np.mean(sequence)
        std = np.std(sequence) + 1e-6
        self.historical_stats[user_id] = {'mean': mean, 'std': std}

    def score(self, user_id, sequence):
        if user_id not in self.historical_stats:
            return 1.0 # Maximum anomaly score for unknown entities

        stats = self.historical_stats[user_id]
        current_mean = np.mean(sequence)
        z_score = abs(current_mean - stats['mean']) / stats['std']
        return min(z_score / self.threshold, 1.0)

    def save(self, filepath):
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)