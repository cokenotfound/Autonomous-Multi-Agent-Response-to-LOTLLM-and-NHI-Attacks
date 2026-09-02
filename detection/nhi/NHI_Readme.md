# NHI Subsystem: Research, Analysis, and Architectural Justification

## 1. Objective 
The core objective is identifying sequence-based anomalies without relying on static rules or requiring labeled malicious data, while maintaining extremely low latency for real-time containment.

## 2. Model Selection
we selected an LSTM (Long Short-Term Memory) Sequence Autoencoder.

### Alternative Models Considered & Rejected:
1. **Large Language Models (LLMs)**: While excellent at parsing command syntax (used in our LOTLLM module), LLMs are overkill and computationally too slow for analyzing numerical time-series and high-frequency API logs. They consume massive VRAM and introduce unacceptable latency for real-time behavioral tracking.
2. **Isolation Forest / One-Class SVM**: These are fast, traditional machine learning models for anomaly detection. However, they analyze data points in isolation. They look at a single API call and ask, "Is this weird?" They fail to capture the temporal sequence (e.g., API Call A followed by B is normal, but B followed by A is a sign of exfiltration).
3. **Transformers (Encoder-only)**: Highly effective for sequences, but often require fixed-length, long contexts which pad memory usage. LSTMs are more memory-efficient for continuous streaming event data.

### Justification for LSTM Autoencoder:
* **Temporal Memory**: LSTMs possess a hidden state that carries context from previous time steps. They inherently understand that the order of events matters.
* **Unsupervised Learning**: We only need to train the model on benign telemetry (which is abundant and easy to generate in our testbed). It learns to compress and reconstruct normal behavior.
* **Mathematical Interpretability**: The output is the Reconstruction Error (Mean Squared Error). This allows us to instantly trace back which specific feature (e.g., payload size vs. endpoint URI) failed to reconstruct properly, providing the "Per-Feature Explanation" required by the orchestration layer without needing computationally heavy explainers like SHAP.

## 3. The "Cold Start" Problem and Statistical Fallback
A known vulnerability in deep learning anomaly detection is the "cold start" or low-history entity problem. If a new service account is created, the LSTM has no sequence history to evaluate, leading to wild, unreliable reconstruction errors (NaNs or false positives).

To counter this, we implemented a **Class-Level Baseline Fallback**.
* If an entity has fewer than N events, or the input contains unseen categorical variables, the system bypasses the LSTM.
* It falls back to a fast, robust statistical model (using scikit-learn Standard Scaler and Z-Score tracking) evaluating aggregate metrics for that class of identity.
* This ensures the system never has a blind spot, providing continuous monitoring while the deep learning model gathers enough temporal data to take over.

## 4. Output 
The training pipeline results in two serialized artifacts for the execution environment:
1. `nhi_lstm_autoencoder.pt`: The PyTorch dictionary containing the trained encoder and decoder weights.
2. `nhi_statistical_fallback.pkl`: The Pickled scikit-learn standard scaler and baseline metrics used for the statistical fallback, which is easily loaded into memory during inference.
