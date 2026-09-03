from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Dict, Any

def parse_timestamp(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def create_fixed_time_windows(
    events: Iterable[Dict[str, Any]],
    window_seconds: int,
) -> List[Dict[str, Any]]:
    """
    Explicit fixed-window algorithm.

    window_start = floor((timestamp - epoch) / W) * W + epoch
    window_end   = window_start + W

    Windows are clock-aligned, so batch boundaries do not change window IDs.
    """
    if window_seconds <= 0:
        raise ValueError("window_seconds must be > 0")

    ordered = sorted(events, key=lambda e: parse_timestamp(e["timestamp"]))
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    windows: Dict[str, Dict[str, Any]] = {}

    for event in ordered:
        ts = parse_timestamp(event["timestamp"])
        elapsed = (ts - epoch).total_seconds()
        start_offset = int(elapsed // window_seconds) * window_seconds
        start = epoch + timedelta(seconds=start_offset)
        end = start + timedelta(seconds=window_seconds)

        window_id = f"fixed_{start.strftime('%Y%m%dT%H%M%SZ')}_{window_seconds}s"

        if window_id not in windows:
            windows[window_id] = {
                "window_id": window_id,
                "window_type": "fixed_time",
                "start_time": start.isoformat().replace("+00:00", "Z"),
                "end_time": end.isoformat().replace("+00:00", "Z"),
                "event_count": 0,
                "events": [],
            }

        windows[window_id]["events"].append(event)
        windows[window_id]["event_count"] += 1

    return list(windows.values())
