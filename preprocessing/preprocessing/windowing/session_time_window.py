from datetime import datetime, timezone
from typing import Iterable, List, Dict, Any, Tuple

from .fixed_time_window import parse_timestamp

def make_session_key(
    event: Dict[str, Any],
    key_fields: Tuple[str, ...] = ("identity", "host"),
) -> Tuple[str, ...]:
    return tuple(
        str(event.get(field)).strip()
        if event.get(field) not in (None, "")
        else "<unknown>"
        for field in key_fields
    )

def create_session_time_windows(
    events: Iterable[Dict[str, Any]],
    session_gap_seconds: int,
    key_fields: Tuple[str, ...] = ("identity", "host"),
) -> List[Dict[str, Any]]:
    """
    Explicit session-window algorithm.

    For each identity/host key:
        gap = current_timestamp - previous_timestamp

    If gap <= session_gap_seconds:
        current event stays in the same session.

    If gap > session_gap_seconds:
        close the old session and start a new session.
    """
    if session_gap_seconds <= 0:
        raise ValueError("session_gap_seconds must be > 0")

    grouped: Dict[Tuple[str, ...], List[Dict[str, Any]]] = {}
    for event in events:
        key = make_session_key(event, key_fields)
        grouped.setdefault(key, []).append(event)

    sessions = []
    session_number = 0

    for key, group in grouped.items():
        group.sort(key=lambda e: parse_timestamp(e["timestamp"]))
        current = []
        previous_time = None

        for event in group:
            current_time = parse_timestamp(event["timestamp"])

            if previous_time is not None:
                gap = (current_time - previous_time).total_seconds()

                if gap > session_gap_seconds:
                    session_number += 1
                    sessions.append(build_session(session_number, key, current, key_fields))
                    current = []

            current.append(event)
            previous_time = current_time

        if current:
            session_number += 1
            sessions.append(build_session(session_number, key, current, key_fields))

    sessions.sort(key=lambda x: x["start_time"])
    return sessions

def build_session(
    session_number: int,
    key: Tuple[str, ...],
    events: List[Dict[str, Any]],
    key_fields: Tuple[str, ...],
) -> Dict[str, Any]:
    start = parse_timestamp(events[0]["timestamp"])
    end = parse_timestamp(events[-1]["timestamp"])

    return {
        "window_id": f"session_{session_number:06d}",
        "window_type": "session",
        "session_key": dict(zip(key_fields, key)),
        "start_time": start.isoformat().replace("+00:00", "Z"),
        "end_time": end.isoformat().replace("+00:00", "Z"),
        "event_count": len(events),
        "events": list(events),
    }
