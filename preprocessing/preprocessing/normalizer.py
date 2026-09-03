from datetime import datetime, timezone
from typing import Any, Dict, Optional
import hashlib
import json

from .models import NormalizedEvent

def clean_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None

def normalize_timestamp(value: Any) -> str:
    """Return an ISO-8601 UTC timestamp."""
    if isinstance(value, (int, float)):
        number = float(value)
        seconds = number / 1000.0 if number > 10_000_000_000 else number
        return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat().replace("+00:00", "Z")

    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")

def make_event_id(event: Dict[str, Any]) -> str:
    existing = clean_string(event.get("event_id") or event.get("envelope_id") or event.get("id"))
    if existing:
        return existing
    canonical = json.dumps(event, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def first(event: Dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in event and event[name] not in (None, ""):
            return event[name]
    return None

def normalize_event(event: Dict[str, Any]) -> NormalizedEvent:
    source = clean_string(event.get("source_type")).lower()

    latency = event.get("latency_ms")
    latency_ms = float(latency) if latency not in (None, "") else None

    return NormalizedEvent(
        event_id=make_event_id(event),
        timestamp=normalize_timestamp(event["timestamp"]),
        source_type=source,
        host=clean_string(first(event, "host", "hostname", "computer")),
        identity=clean_string(first(event, "identity", "service_identity", "principal")),
        event_type=clean_string(first(event, "event_type", "event_name", "type")),
        action=clean_string(first(event, "action", "event_name")),
        process_name=clean_string(first(event, "process_name", "Image", "image", "process")),
        process_path=clean_string(first(event, "process_path", "Image")),
        parent_process=clean_string(first(event, "parent_process", "ParentImage")),
        parent_pid=clean_string(first(event, "parent_pid", "ParentProcessId")),
        command_line=clean_string(first(event, "command_line", "CommandLine", "command", "cmdline")),
        resource=clean_string(first(event, "resource", "resource_path", "secret_path")),
        source_ip=clean_string(first(event, "source_ip", "src_ip", "client_ip")),
        user_agent=clean_string(first(event, "user_agent", "UserAgent")),
        success=event.get("success"),
        model=clean_string(first(event, "model")),
        prompt=clean_string(first(event, "prompt")),
        response=clean_string(first(event, "response")),
        latency_ms=latency_ms,
        ingested_at=clean_string(event.get("ingested_at")),
        raw_payload=event,
    )
