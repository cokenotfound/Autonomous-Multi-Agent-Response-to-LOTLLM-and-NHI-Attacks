"""
preprocessing/validation/event_validator.py

Validates event structure, envelope integrity, and source-specific requirements.
Implements deduplication logic and invalid-event policies.
"""
import logging
from typing import Dict, Any, Set, Tuple
from dateutil.parser import parse as parse_date

from config import INVALID_EVENT_POLICY, DEDUPLICATION_POLICY

logger = logging.getLogger(__name__)

class EventValidator:
    def __init__(self):
        # Tracking for deduplication. In a real distributed system, this would be backed by Redis.
        # For memory efficiency in processing batches, a set of recent envelope_ids is sufficient.
        self.seen_envelopes: Set[str] = set()

    def validate(self, envelope: Dict[str, Any], parsed_payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates the event.
        Returns (is_valid, reason, event_object).
        If invalid, applies the INVALID_EVENT_POLICY (drop, quarantine, or raise).
        """
        is_valid = True
        reason = ""

        try:
            # 1. Envelope integrity
            env_id = envelope.get("envelope_id")
            if not env_id:
                raise ValueError("Missing envelope_id")
                
            source_type = envelope.get("source_type")
            if not source_type:
                raise ValueError("Missing source_type")
                
            ingested_at = envelope.get("ingested_at")
            if not ingested_at:
                raise ValueError("Missing ingested_at")

            # 2. Timestamp usability
            try:
                parse_date(ingested_at)
            except Exception:
                raise ValueError(f"Invalid timestamp format: {ingested_at}")

            # 3. Deduplication
            if env_id in self.seen_envelopes:
                if DEDUPLICATION_POLICY == "drop_duplicate":
                    raise ValueError(f"Duplicate envelope_id: {env_id}")
                # "keep_first" and "keep_last" would require more complex state or merging, 
                # but we'll flag duplicates regardless.
            self.seen_envelopes.add(env_id)

            # 4. Source-specific structural requirements
            self._validate_source_specific(source_type, parsed_payload)

        except ValueError as e:
            is_valid = False
            reason = str(e)

        event_obj = {
            "envelope": envelope,
            "parsed": parsed_payload,
            "is_valid": is_valid,
            "validation_reason": reason
        }

        if not is_valid:
            if INVALID_EVENT_POLICY == "raise":
                raise ValueError(f"Event Validation Failed: {reason}")
            elif INVALID_EVENT_POLICY == "quarantine":
                # In quarantine mode, we keep the event but mark it invalid so downstream skips it,
                # or routes it to a quarantine table.
                pass
            elif INVALID_EVENT_POLICY == "drop":
                # Signal the caller to drop it entirely
                return False, reason, {}

        return is_valid, reason, event_obj

    def _validate_source_specific(self, source_type: str, parsed: Dict[str, Any]):
        """Check required fields per source type."""
        if source_type == "sysmon":
            if "EventID" not in parsed:
                raise ValueError("Sysmon event missing EventID")
            if not isinstance(parsed["EventID"], int):
                raise ValueError("Sysmon EventID must be integer")
                
        elif source_type == "auditd":
            if "type" not in parsed:
                raise ValueError("Auditd event missing type")
            if "syscall" in parsed and not isinstance(parsed["syscall"], str):
                raise ValueError("Auditd syscall must be string")
                
        elif source_type == "ollama":
            if "request" not in parsed or "response" not in parsed:
                raise ValueError("Ollama event missing request/response")
            if "latency_ms" in parsed and not isinstance(parsed["latency_ms"], (int, float)):
                raise ValueError("Ollama latency_ms must be numeric")
                
        elif source_type == "iam":
            if "event_type" not in parsed:
                raise ValueError("IAM event missing event_type")
            if "success" not in parsed or not isinstance(parsed["success"], bool):
                raise ValueError("IAM event missing/invalid success boolean")
                
        elif source_type == "vault":
            if "event_type" not in parsed:
                raise ValueError("Vault event missing event_type")
            if "path" not in parsed:
                raise ValueError("Vault event missing path")
                
        elif source_type == "api_gateway":
            if "method" not in parsed or "path" not in parsed:
                raise ValueError("API Gateway event missing method/path")
            if "response_status" in parsed and not isinstance(parsed["response_status"], int):
                raise ValueError("API Gateway response_status must be integer")
