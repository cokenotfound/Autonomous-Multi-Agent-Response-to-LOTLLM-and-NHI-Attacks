"""
preprocessing/cleaning/event_cleaner.py

Cleans parsed events.
Handles:
- Unwanted whitespace stripping
- Empty string -> None conversion
- Recoverable malformed representations
IMPORTANT: Raw payload is preserved in the envelope.
"""
from typing import Dict, Any

class EventCleaner:
    def clean(self, event_obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cleans the parsed payload within the event object in-place.
        Returns the modified event_obj.
        """
        if not event_obj.get("is_valid", False):
            # Don't clean invalid events that were quarantined
            return event_obj

        parsed = event_obj["parsed"]
        event_obj["parsed"] = self._clean_dict(parsed)
        return event_obj

    def _clean_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = {}
        for k, v in data.items():
            if isinstance(v, str):
                v_strip = v.strip()
                # Convert empty strings to None
                cleaned[k] = None if not v_strip else v_strip
            elif isinstance(v, dict):
                cleaned[k] = self._clean_dict(v)
            elif isinstance(v, list):
                cleaned[k] = self._clean_list(v)
            else:
                cleaned[k] = v
        return cleaned

    def _clean_list(self, data: list) -> list:
        cleaned = []
        for v in data:
            if isinstance(v, str):
                v_strip = v.strip()
                cleaned.append(None if not v_strip else v_strip)
            elif isinstance(v, dict):
                cleaned.append(self._clean_dict(v))
            elif isinstance(v, list):
                cleaned.append(self._clean_list(v))
            else:
                cleaned.append(v)
        return cleaned
