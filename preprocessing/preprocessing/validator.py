from typing import Any, Dict

SUPPORTED_SOURCES = {
    "sysmon", "auditd", "ollama", "iam", "vault", "api_gateway"
}

def validate_event(event: Dict[str, Any]) -> None:
    """Validate the minimum structure needed by Module 2."""
    if not event.get("timestamp"):
        raise ValueError("Missing required field: timestamp")
    if not event.get("source_type"):
        raise ValueError("Missing required field: source_type")

    source = str(event["source_type"]).strip().lower()
    if source not in SUPPORTED_SOURCES:
        raise ValueError(f"Unsupported source_type: {source}")

    # Module 1 requires caller identity for Ollama requests.
    if source == "ollama" and not event.get("identity"):
        raise ValueError("Ollama event is missing mandatory identity")

def validate_batch(events: list[Dict[str, Any]]):
    valid, invalid = [], []
    for event in events:
        try:
            validate_event(event)
            valid.append(event)
        except Exception as exc:
            invalid.append({"error": str(exc), "event": event})
    return valid, invalid
