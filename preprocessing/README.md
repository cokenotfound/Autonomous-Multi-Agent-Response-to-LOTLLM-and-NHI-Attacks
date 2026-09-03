# Module 2 — Preprocessing Python Implementation

## Structure

```text
MODULE_2_PREPROCESSING_CODE/
├── run_preprocessing.py
├── requirements.txt
├── preprocessing/
│   ├── config.py
│   ├── models.py
│   ├── parser.py
│   ├── validator.py
│   ├── normalizer.py
│   ├── dataframe_builder.py
│   ├── io_utils.py
│   ├── redis_reader.py
│   ├── preprocessing.py
│   └── windowing/
│       ├── fixed_time_window.py
│       └── session_time_window.py
└── data/
    ├── raw/
    │   ├── sysmon/
    │   ├── auditd/
    │   ├── ollama/
    │   ├── iam/
    │   ├── vault/
    │   └── api_gateway/
    ├── preprocessed/
    │   └── <same six source directories>
    ├── windows/
    │   ├── fixed/
    │   └── session/
    └── errors/
```

## Fixed-time window logic

For window size `W`:

```text
window_start = floor((timestamp - epoch) / W) * W + epoch
window_end   = window_start + W
```

Example with `W = 60`:

```text
10:00:00 <= event < 10:01:00  → Window 1
10:01:00 <= event < 10:02:00  → Window 2
```

The project requires fixed-time windows but does not specify their numeric duration. Therefore `--fixed-window` is configurable.

## Session-time window logic

For each session key (default: `identity + host`):

```text
gap = current_event_timestamp - previous_event_timestamp
```

If:

```text
gap <= session_gap_seconds
```

the event remains in the current session.

If:

```text
gap > session_gap_seconds
```

the previous session is closed and a new session begins.

The project requires activity-gap-based sessions but does not specify the numeric threshold. Therefore `--session-gap` is configurable.

## Run

```bash
pip install -r requirements.txt
python run_preprocessing.py
```

Or:

```bash
python run_preprocessing.py --fixed-window 60 --session-gap 300
```

The `60` and `300` values are implementation examples, not project-mandated values.

## File-based testing

Put one JSON object per line into:

```text
data/raw/sysmon/*.jsonl
data/raw/auditd/*.jsonl
data/raw/ollama/*.jsonl
data/raw/iam/*.jsonl
data/raw/vault/*.jsonl
data/raw/api_gateway/*.jsonl
```

Then run the main script.

## Redis

`preprocessing/redis_reader.py` contains the Redis Stream reader for:

```text
telemetry:sysmon
telemetry:auditd
telemetry:ollama
telemetry:iam
telemetry:vault
telemetry:api_gateway
```

The file-based runner is kept separate so the preprocessing and windowing logic can be tested without a running Redis instance.
