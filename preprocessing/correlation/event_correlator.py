"""
preprocessing/correlation/event_correlator.py

Provides cross-stream correlation and chronological ordering.
Sorts events by normalized timestamp and optionally tags them with correlation
keys to assist downstream detection.
"""
from typing import List, Dict, Any
from datetime import datetime
from dateutil.parser import parse as parse_date

class EventCorrelator:
    def process_batch(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes a list of normalized event objects.
        1. Filters out invalid events (if they made it this far)
        2. Sorts strictly by chronological timestamp (NOT Redis arrival order)
        3. Annotates correlation keys (host, identity, process relationships)
        Returns the sorted and annotated list of common_event dictionaries.
        """
        valid_events = []
        for e in events:
            if not e.get("is_valid", False):
                continue
            common = e.get("common_event")
            if not common:
                continue
            valid_events.append(common)

        # 1. Sort chronologically
        # We parse the timestamp string back to a datetime object just for sorting
        def _sort_key(evt):
            try:
                return parse_date(evt["timestamp"])
            except Exception:
                # Fallback to epoch 0 if completely unparseable
                return datetime.fromtimestamp(0)

        valid_events.sort(key=_sort_key)

        # 2. Enrich with correlation keys (making relationships visible)
        for evt in valid_events:
            # Create a basic correlation key: Host + Identity
            host = evt.get("host") or "unknown_host"
            identity = evt.get("identity") or "unknown_identity"
            evt["correlation_key"] = f"{host}|{identity}"
            
            # Highlight process chain linkage
            if evt.get("parent_pid"):
                evt["process_link"] = f"{host}|pid:{evt.get('parent_pid')}"
            else:
                evt["process_link"] = None

        return valid_events
