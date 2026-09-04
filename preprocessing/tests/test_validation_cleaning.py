"""
tests/test_validation_cleaning.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from validation.event_validator import EventValidator
from cleaning.event_cleaner import EventCleaner

def test_valid_event():
    validator = EventValidator()
    cleaner = EventCleaner()
    
    envelope = {
        "envelope_id": "id-1",
        "source_type": "iam",
        "host": "ws",
        "ingested_at": "2026-09-04T08:00:00Z",
        "raw_payload": "{}"
    }
    parsed = {"event_type": "authenticate", "success": True, "username": " alice "}
    
    is_valid, reason, obj = validator.validate(envelope, parsed)
    assert is_valid is True
    
    cleaned_obj = cleaner.clean(obj)
    # Check whitespace stripping
    assert cleaned_obj["parsed"]["username"] == "alice"
    # Original raw payload is untouched inside envelope
    assert cleaned_obj["envelope"]["raw_payload"] == "{}"

def test_missing_field():
    validator = EventValidator()
    envelope = {
        "envelope_id": "id-2",
        "source_type": "sysmon",
        "host": "ws",
        "ingested_at": "2026-09-04T08:00:00Z"
    }
    # Missing EventID
    parsed = {"EventType": "ProcessCreate"}
    
    is_valid, reason, obj = validator.validate(envelope, parsed)
    assert is_valid is False
    assert "missing EventID" in reason

def test_invalid_type():
    validator = EventValidator()
    envelope = {
        "envelope_id": "id-3",
        "source_type": "sysmon",
        "host": "ws",
        "ingested_at": "2026-09-04T08:00:00Z"
    }
    # EventID is string instead of int
    parsed = {"EventID": "1", "EventType": "ProcessCreate"}
    
    is_valid, reason, obj = validator.validate(envelope, parsed)
    assert is_valid is False
    assert "EventID must be integer" in reason

def test_invalid_timestamp():
    validator = EventValidator()
    envelope = {
        "envelope_id": "id-4",
        "source_type": "iam",
        "host": "ws",
        "ingested_at": "NOT_A_TIME"
    }
    parsed = {"event_type": "auth", "success": True}
    
    is_valid, reason, obj = validator.validate(envelope, parsed)
    assert is_valid is False
    assert "Invalid timestamp" in reason

def test_duplicate_envelope():
    validator = EventValidator()
    envelope = {
        "envelope_id": "dup-id",
        "source_type": "iam",
        "host": "ws",
        "ingested_at": "2026-09-04T08:00:00Z"
    }
    parsed = {"event_type": "auth", "success": True}
    
    # First time valid
    is_valid, _, _ = validator.validate(envelope, parsed)
    assert is_valid is True
    
    # Second time duplicate
    is_valid, reason, _ = validator.validate(envelope, parsed)
    assert is_valid is False
    assert "Duplicate" in reason

def test_recoverable_cleaning_empty_string():
    validator = EventValidator()
    cleaner = EventCleaner()
    
    envelope = {
        "envelope_id": "id-5",
        "source_type": "iam",
        "host": "ws",
        "ingested_at": "2026-09-04T08:00:00Z"
    }
    # Empty string should become None
    parsed = {"event_type": "auth", "success": True, "token": "   ", "nested": {"key": ""}}
    
    _, _, obj = validator.validate(envelope, parsed)
    cleaned_obj = cleaner.clean(obj)
    
    assert cleaned_obj["parsed"]["token"] is None
    assert cleaned_obj["parsed"]["nested"]["key"] is None
