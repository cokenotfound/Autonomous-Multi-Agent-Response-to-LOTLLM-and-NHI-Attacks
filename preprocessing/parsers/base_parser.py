"""
Base parser interface for Module 2.
"""
import json
from typing import Any, Dict

class BaseParser:
    def parse(self, raw_payload: str) -> Dict[str, Any]:
        """Parses the raw JSON string into a structured dictionary."""
        try:
            return json.loads(raw_payload)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON payload: {e}")
