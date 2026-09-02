def extract_top_features(sequence, reconstructed_sequence, feature_names):
    """Identifies specific features driving the anomaly score."""
    feature_errors = {}
    
    for i, feature in enumerate(feature_names):
        mse = ((sequence[:, i] - reconstructed_sequence[:, i])**2).mean()
        feature_errors[feature] = mse
    
    sorted_features = sorted(feature_errors.items(), key=lambda x: x[1], reverse=True)
    
    explanations = [
        f"Anomaly driven by {feat} (Error: {err:.4f})"
        for feat, err in sorted_features[:3]
    ]
    
    return explanations