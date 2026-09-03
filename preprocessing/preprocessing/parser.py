import json
from typing import Any, Dict

def parse_payload(raw_payload: Any) -> Dict[str, Any]:
    """Convert a JSON string/bytes/dict into a Python dictionary."""
    if isinstance(raw_payload, dict):
        return raw_payload
    if isinstance(raw_payload, bytes):
        raw_payload = raw_payload.decode("utf-8", errors="replace")
    if isinstance(raw_payload, str):
        value = raw_payload.strip()
        if not value:
            raise ValueError("Empty raw payload")
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise ValueError("JSON payload must be an object")
        return parsed
    raise TypeError(f"Unsupported payload type: {type(raw_payload).__name__}")

def parse_envelope(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse the Module 1 common envelope:
    envelope_id, source_type, host, ingested_at, raw_payload.
    """
    if "raw_payload" not in event:
        return dict(event)

    payload = parse_payload(event["raw_payload"])
    merged = dict(payload)
    for key in ("envelope_id", "source_type", "host", "ingested_at"):
        if key in event:
            merged[key] = event[key]
    return merged
