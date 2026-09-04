"""
preprocessing/normalization/timestamp_normalizer.py

Normalizes timestamps to a consistent format and timezone.
Uses ingested_at or source-specific timestamps.
"""
from typing import Dict, Any
from datetime import datetime, timezone
from dateutil.parser import parse as parse_date
from config import TIMESTAMP_FORMAT, TIMEZONE_POLICY

class TimestampNormalizer:
    def normalize(self, event_obj: Dict[str, Any]) -> Dict[str, Any]:
        if not event_obj.get("is_valid", False):
            return event_obj

        envelope = event_obj["envelope"]
        parsed = event_obj["parsed"]
        source_type = envelope["source_type"]

        # Try to find the most accurate event timestamp from the parsed payload first
        raw_ts = None
        if source_type == "sysmon":
            raw_ts = parsed.get("UtcTime")
        elif source_type == "auditd":
            # auditd time is usually in the msg field like audit(1234567890.123:456)
            msg = parsed.get("msg", "")
            if msg.startswith("audit("):
                try:
                    ts_str = msg.split("(")[1].split(":")[0]
                    raw_ts = datetime.fromtimestamp(float(ts_str), tz=timezone.utc).isoformat()
                except Exception:
                    pass
        else:
            # ollama, iam, vault, api_gateway test data uses 'timestamp'
            raw_ts = parsed.get("timestamp")

        # Fallback to envelope ingested_at if source timestamp is missing/unparseable
        if not raw_ts:
            raw_ts = envelope["ingested_at"]

        # Parse and convert to standard format
        try:
            dt = parse_date(raw_ts)
            if not dt.tzinfo:
                # Assume UTC if no timezone is provided
                dt = dt.replace(tzinfo=timezone.utc)
            
            # Convert to configured timezone policy (default UTC)
            if TIMEZONE_POLICY == "UTC":
                dt = dt.astimezone(timezone.utc)

            # Format timestamp
            if TIMESTAMP_FORMAT.lower() == "iso8601":
                normalized_ts = dt.isoformat()
            else:
                normalized_ts = dt.strftime(TIMESTAMP_FORMAT)
                
            event_obj["normalized_timestamp"] = normalized_ts
            
        except Exception:
            # If all parsing fails, fallback to ingested_at exactly as-is
            event_obj["normalized_timestamp"] = envelope["ingested_at"]

        return event_obj
