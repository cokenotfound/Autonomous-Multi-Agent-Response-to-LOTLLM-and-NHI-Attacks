# Behavioral Detection and Autonomous Multi-Agent Response to Chained Living-off-the-Land and Non-Human Identity Attacks

This README documents the build in phases. Each phase lists its steps, the libraries/tools it depends on, and the concrete deliverable you should have in hand before moving to the next phase.

---

## Phase 1: Dataset Synthesis

**Directory:** `data/generation/`

### Steps
1. Set up the workspace and isolated (network-disabled) VM/container for safe real-execution testing.
2. Write the technique library — YAML definitions of 3-5 MITRE ATT&CK techniques (LotL, NHI, and a custom LOLLM technique).
3. Build the benign noise generator — realistic normal activity to hide attacks inside.
4. Build the scenario composer — inserts one technique instance into a benign activity stream.
5. Build the real executor — actually performs a small seed set of scenarios inside the isolated VM, capturing genuine telemetry (never executes LOLLM-generated code for real; captures and statically inspects it instead).
6. Build the synthetic executor — once validated against Step 5, generates volume directly in schema-shaped form, without real execution.
7. Build the labeler — attaches benign/adversarial + technique-ID + scenario-run-ID to every event.
8. Scale up generation to a realistic class-imbalanced dataset (attacks as a small minority, not 50/50).
9. Split into train/validation/test **by scenario run ID**, not by individual event, to avoid leakage.
10. Sanity-check: class counts, manual spot-checks, schema conformance.

### Libraries
`pyyaml` · `faker` · `pandas` · `scikit-learn` (for the train/val/test split) · `redis` · `docker` (Python SDK, for sandboxed real-execution runs) · `ollama` (Python client, for the LOLLM scenario)

### Deliverable
A labeled, partitioned dataset — **not a single flat CSV**. Because events need to preserve per-identity sequence/order (not just independent rows), the deliverable is:
- `data/labeled/train/*.jsonl`, `val/*.jsonl`, `test/*.jsonl` — one JSON object per event, grouped by `scenario_run_id`, each event carrying `{timestamp, identity_id, action, source_type, label, technique_id, scenario_run_id}`.
- A small `data/labeled/real_seed/*.jsonl` subset containing the genuinely-executed examples from Step 5, kept separate as your validation reference.
- A short `dataset_summary.md` (auto-generated) reporting event counts per class/technique and split sizes.

*(If a flat table is needed for quick inspection, export a CSV view via `pandas` — but treat JSONL as the source of truth, CSV as a convenience export.)*

---

## Phase 2: Ingestion Points & Data Sources

**Directory:** `ingestion/`

### Steps
1. Configure real endpoint sources: Sysmon (Windows) and Auditd (Linux) logging rules.
2. Configure Ollama/llama.cpp request logging.
3. Build mock identity/API services (IAM, API gateway, secrets vault) as small FastAPI apps with shared logging middleware.
4. Configure Fluent Bit/Filebeat to tail real source logs and ship to Redis Streams.
5. Wire mock services to publish directly to Redis Streams (no file-tailing needed for these).
6. Verify end-to-end: trigger one action per source type, confirm it lands on the queue.

### Libraries
`fastapi` · `uvicorn` · `redis-py` · `pydantic` — plus config-only tools: Sysmon, Auditd, Fluent Bit/Filebeat, Ollama (no Python code for these, configuration files only)

### Deliverable
- A running ingestion layer: 3 mock services (`mock_iam.py`, `mock_gateway.py`, `mock_vault.py`) deployable via `docker-compose up`.
- Verified shipper configs (`sysmon_config.xml`, `audit.rules`, `fluentbit.conf`) tested against at least one real VM.
- A sample capture file (`ingestion/sample_capture.jsonl`) showing raw events actually observed on the Redis stream from each of the four source types — this is your evidence the pipeline works, used to sanity-check Phase 3's adapters against real (not just synthetic) input.

---

## Phase 3: Data Preprocessing

**Directory:** `preprocessing/`

### Steps
1. Define the unified normalized event schema as a Pydantic model.
2. Build the base adapter interface (`parse(raw_event) -> normalized_schema`).
3. Implement one adapter subclass per source type (Sysmon, Auditd, identity/API, LLM runtime).
4. Build the time-based windowing function.
5. Build the session-based windowing function (login/token-issuance to logout/expiry).
6. Unit test both windowing strategies against known synthetic sequences from Phase 1.

### Libraries
`pydantic` · `pandas`

### Deliverable
- `preprocessing/adapters/` — one tested adapter per source type.
- `preprocessing/schema.py` — the canonical normalized event definition, imported by every later phase.
- A processed, windowed version of the Phase 1 dataset: `data/windowed/*.jsonl`, each record now a full per-identity sequence (both time- and session-based versions), ready for feature extraction.

---

## Phase 4: LOTLLM Feature Detection & Sandboxing

**Directory:** `detection/lotllm/`

### Steps
1. Build features for the LotL command classifier (embeddings + LOLBAS-weighted signal, not a hard filter).
2. Train a baseline (scikit-learn) LotL classifier; compare against a rule-only baseline.
3. Upgrade to a PyTorch embedding-based classifier if the baseline underperforms.
4. Build features and train the LOLLM prompt detector, using the Phase 1 LOLLM scenario data.
5. Build the stateless, network-isolated sandbox executor (Docker-based, rebuilt from a clean snapshot per run).
6. Build the conditional trigger logic (sandbox runs only when either classifier crosses threshold).
7. Build the fusion function combining static + dynamic scores into one LOTLLM confidence score.
8. Evaluate: precision/recall for each sub-detector, plus sandbox-triggered vs. non-triggered latency, reported separately.

### Libraries
`scikit-learn` (baselines) · `pytorch` · `transformers` (HuggingFace) · `docker` (Python SDK)

### Deliverable
- Trained model checkpoints: `detection/lotllm/lotl_classifier/model.pt`, `detection/lotllm/lollm_detector/model.pt`.
- `detection/lotllm/fusion.py` — the tested fusion function.
- An evaluation report `evaluation/lotllm_metrics.csv` — precision, recall, F1, and latency (split by sandbox-triggered vs. not) against the Phase 1 held-out test set.

---

## Phase 5: NHI Behavioral Detection (Deep Learning)

**Directory:** `detection/nhi/`

### Steps
1. Build identity-context + action-sequence features from the windowed Phase 3 data.
2. Train the sequence autoencoder on **benign** action sequences only.
3. Build the class-level baseline fallback for identities with insufficient individual history.
4. Sweep reconstruction-error thresholds on a held-out validation split (precision-recall curve, not a hand-picked cutoff).
5. Build the per-feature explanation function (which dimensions contributed most to the reconstruction error).
6. Evaluate against the rule-based static baseline (privilege/credential-age thresholds) to demonstrate the behavioral model adds value.

### Libraries
`pytorch` · `numpy` · `scikit-learn` (for the precision-recall sweep and baseline comparison)

### Deliverable
- Trained model checkpoint: `detection/nhi/behavioral_model/model.pt`.
- `detection/nhi/baseline_fallback.py` and `detection/nhi/explain.py` — tested and callable standalone.
- The selected operating threshold, saved as `detection/nhi/threshold.json`, chosen from the validation-set sweep.
- An evaluation report `evaluation/nhi_metrics.csv` — precision/recall/F1 against the Phase 1 held-out test set, compared against the static rule-based baseline.

---

## Phase 6: Agents Interface

**Directory:** `agents/`

### Steps
1. Prototype both CrewAI and LangGraph on a small toy 2-agent voting example; pick one based on the result.
2. Build agent wrapper classes around the Phase 4 and Phase 5 models' outputs.
3. Build the symmetric temporal correlation check (either NHI-then-LOTLLM or LOTLLM-then-NHI ordering).
4. Build the disagreement check.
5. Build the RAG layer: curated MITRE ATT&CK index in Chroma/FAISS, restricted to team-controlled static content.
6. Build the voting/decision function implementing the full pseudocode (disagreement → correlation-gated containment → escalate → dismiss).
7. Tune weights/thresholds on a held-out validation split, separate from the Phase 4/5 test sets.
8. Integration test: run a full simulated attack chain end-to-end through Phases 1→6.

### Libraries
`crewai` or `langgraph` (whichever wins the Step 1 prototype) · `chromadb` or `faiss-cpu` · `langchain` (or hand-rolled retrieval glue)

### Deliverable
- `agents/voting.py` — the tested, tunable decision function.
- `agents/orchestration.py` — the working CrewAI/LangGraph graph wiring both agents together.
- A tuned config file `agents/thresholds.json` (theta_contain, theta_escalate, theta_disagree, boost_factor, delta_t, w_lotllm, w_nhi).
- An end-to-end integration test result: a simulated chained attack correctly reaching `HARD_CONTAINMENT`, and a benign session correctly reaching `DISMISS`.

---

## Phase 7: Response

**Directory:** `response/`

### Steps
1. Build the mock containment executor (logs simulated actions, never touches real infra).
2. Add simulated failure conditions (rate limits, permission errors) to exercise the logic realistically.
3. Wire soft quarantine vs. hard containment branching to the Phase 6 decision output.

### Libraries
`fastapi` (if exposed as a service) — otherwise plain Python

### Deliverable
- `response/containment_executor.py`, tested against both soft and hard containment decisions.
- An action log `response/action_log.jsonl` demonstrating logged (simulated) responses for a batch of test decisions.

---

## Phase 8: Dashboard

**Directory:** `dashboard/`

### Steps
1. Set up Supabase project: `decisions`, `agent_scores`, `thresholds` tables, Realtime enabled.
2. Build the React frontend: decision timeline, evidence view, plain-language explanation rendering, config panel.
3. Wire Module 5/7 outputs to write into Supabase.
4. Deploy frontend to Vercel.
5. Verify the feedback loop: a config-panel threshold change is read back by Phase 6's voting logic.

### Libraries
`react` · `@supabase/supabase-js` · Vercel (hosting, no library)

### Deliverable
- A deployed, reachable dashboard URL (Vercel).
- `dashboard/supabase/schema.sql` — the finalized table schema.
- A working feedback loop, demonstrated by changing a threshold in the UI and observing a subsequent decision change.

---

## Phase 9: Evaluation & Write-Up

**Directory:** `evaluation/`

### Steps
1. Run the full Phase 1 test set through the entire pipeline (Phases 2→7).
2. Compute end-to-end precision/recall/false-positive rate and decision-to-containment latency.
3. Compare fused (identity-context + action-sequence) detection against each standalone baseline.
4. Compile results into tables/charts for the methodology and results sections.

### Libraries
`pandas` · `scikit-learn.metrics` · `matplotlib` or `seaborn` (for charts)

### Deliverable
- `evaluation/final_report.csv` — all metrics, per module and end-to-end.
- Charts (precision-recall curves, latency distributions) ready to drop into the paper.
- A written results summary tying each number back to Objectives 1-4.

---

## Summary Table

| Phase | Deliverable Format |
|---|---|
| 1. Dataset Synthesis | Labeled JSONL dataset (train/val/test, split by scenario run) |
| 2. Ingestion Points | Running ingestion services + sample raw capture (JSONL) |
| 3. Data Preprocessing | Normalized + windowed JSONL dataset |
| 4. LOTLLM Detection | Trained model checkpoints (.pt) + metrics CSV |
| 5. NHI Detection | Trained model checkpoint (.pt) + threshold JSON + metrics CSV |
| 6. Agents Interface | Working voting pipeline + tuned threshold config |
| 7. Response | Containment executor + action log (JSONL) |
| 8. Dashboard | Deployed Vercel app + Supabase schema |
| 9. Evaluation | Final metrics CSV + charts + results write-up |
