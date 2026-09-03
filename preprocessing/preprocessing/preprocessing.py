from pathlib import Path
from typing import Dict, List, Any

import polars as pl

from .config import (
    RAW_DIR,
    PREPROCESSED_DIR,
    FIXED_WINDOW_DIR,
    SESSION_WINDOW_DIR,
    ERROR_DIR,
    WINDOW_CONFIG,
)
from .parser import parse_envelope
from .validator import validate_batch
from .normalizer import normalize_event
from .dataframe_builder import events_to_dataframe
from .windowing.fixed_time_window import create_fixed_time_windows
from .windowing.session_time_window import create_session_time_windows
from .io_utils import read_jsonl, write_jsonl

SOURCE_TYPES = (
    "sysmon", "auditd", "ollama", "iam", "vault", "api_gateway"
)

def process_source(source_type: str) -> Dict[str, Any]:
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"Unknown source: {source_type}")

    source_dir = RAW_DIR / source_type
    raw_events = []
    for path in sorted(source_dir.glob("*.jsonl")):
        raw_events.extend(read_jsonl(path))

    parsed = []
    errors = []

    for event in raw_events:
        if "__read_error__" in event:
            errors.append(event)
            continue
        try:
            parsed.append(parse_envelope(event))
        except Exception as exc:
            errors.append({"error": str(exc), "event": event})

    valid, invalid = validate_batch(parsed)
    errors.extend(invalid)

    normalized_objects = []
    for event in valid:
        try:
            normalized_objects.append(normalize_event(event))
        except Exception as exc:
            errors.append({"error": str(exc), "event": event})

    # Explicit Polars stage required by the project design.
    df = events_to_dataframe(normalized_objects)

    normalized_rows = df.to_dicts() if not df.is_empty() else []

    preprocessed_path = PREPROCESSED_DIR / source_type / "events.jsonl"
    write_jsonl(preprocessed_path, normalized_rows)

    # Explicit fixed-time window stage.
    fixed_windows = create_fixed_time_windows(
        normalized_rows,
        WINDOW_CONFIG.fixed_window_seconds,
    )
    fixed_path = FIXED_WINDOW_DIR / f"{source_type}.jsonl"
    write_jsonl(fixed_path, fixed_windows)

    # Explicit session-time window stage.
    session_windows = create_session_time_windows(
        normalized_rows,
        WINDOW_CONFIG.session_gap_seconds,
    )
    session_path = SESSION_WINDOW_DIR / f"{source_type}.jsonl"
    write_jsonl(session_path, session_windows)

    error_path = ERROR_DIR / f"{source_type}.jsonl"
    write_jsonl(error_path, errors)

    return {
        "source_type": source_type,
        "raw_event_count": len(raw_events),
        "valid_event_count": len(normalized_rows),
        "error_count": len(errors),
        "fixed_window_count": len(fixed_windows),
        "session_window_count": len(session_windows),
        "preprocessed_file": str(preprocessed_path),
        "fixed_window_file": str(fixed_path),
        "session_window_file": str(session_path),
        "error_file": str(error_path),
    }

def run_all_sources() -> List[Dict[str, Any]]:
    return [process_source(source) for source in SOURCE_TYPES]
