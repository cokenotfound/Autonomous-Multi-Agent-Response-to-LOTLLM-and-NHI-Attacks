"""
tests/test_normalization.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from normalization.timestamp_normalizer import TimestampNormalizer
from normalization.field_normalizer import FieldNormalizer

def test_timestamp_normalization():
    ts_norm = TimestampNormalizer()
    
    # 1. Test UTC conversion from ISO with offset
    event_obj = {
        "is_valid": True,
        "envelope": {"source_type": "iam", "ingested_at": "2026-09-04T08:00:00Z"},
        "parsed": {"timestamp": "2026-09-04T10:00:00+02:00"}
    }
    result = ts_norm.normalize(event_obj)
    assert result["normalized_timestamp"] == "2026-09-04T08:00:00+00:00"
    
    # 2. Test auditd timestamp parsing
    event_obj2 = {
        "is_valid": True,
        "envelope": {"source_type": "auditd", "ingested_at": "2026-09-04T08:00:00Z"},
        "parsed": {"msg": "audit(1693814400.123:456)"} # corresponds to 2023-09-04 08:00:00 UTC
    }
    result2 = ts_norm.normalize(event_obj2)
    assert result2["normalized_timestamp"] == "2023-09-04T08:00:00.123000+00:00"

def test_field_normalization_sysmon():
    field_norm = FieldNormalizer()
    event_obj = {
        "is_valid": True,
        "normalized_timestamp": "2026-09-04T08:00:00Z",
        "envelope": {
            "envelope_id": "sysmon-1",
            "source_type": "sysmon",
            "host": "ws-001",
            "ingested_at": "2026-09-04T08:00:00Z",
            "raw_payload": '{"raw": "sysmon_payload"}'
        },
        "parsed": {
            "EventType": "ProcessCreate",
            "User": "DOMAIN\\alice",
            "Image": "C:\\Windows\\System32\\cmd.exe",
            "CommandLine": "cmd.exe /c echo hello",
            "ParentProcessId": 1234
        }
    }
    
    res = field_norm.normalize(event_obj)
    common = res["common_event"]
    
    assert common["event_id"] == "sysmon-1"
    assert common["source_type"] == "sysmon"
    assert common["host"] == "ws-001"
    assert common["identity"] == "alice"  # Domain stripped
    assert common["event_type"] == "ProcessCreate"
    assert common["process_name"] == "cmd.exe"
    assert common["command_line"] == "cmd.exe /c echo hello"
    assert common["parent_pid"] == 1234
    assert common["raw_payload"] == '{"raw": "sysmon_payload"}'
    
    # Unused fields are None
    assert common["model"] is None

def test_field_normalization_ollama():
    field_norm = FieldNormalizer()
    event_obj = {
        "is_valid": True,
        "normalized_timestamp": "2026-09-04T08:00:00Z",
        "envelope": {
            "envelope_id": "ollama-1",
            "source_type": "ollama",
            "host": "ws-001",
            "ingested_at": "2026-09-04T08:00:00Z",
            "raw_payload": '{"raw": "ollama_payload"}'
        },
        "parsed": {
            "event_type": "ollama_request_response",
            "identity": "service_bot_01",
            "latency_ms": 150.5,
            "request": {"body": '{"model": "llama3", "prompt": "hello"}'},
            "response": {"status_code": 200, "body": '{"response": "hi there"}'}
        }
    }
    
    res = field_norm.normalize(event_obj)
    common = res["common_event"]
    
    assert common["identity"] == "service_bot_01"
    assert common["latency_ms"] == 150.5
    assert common["model"] == "llama3"
    assert common["prompt"] == "hello"
    assert common["response"] == "hi there"
    assert common["success"] is True

def test_missing_optional_fields_dont_break():
    field_norm = FieldNormalizer()
    # Missing optional fields in IAM
    event_obj = {
        "is_valid": True,
        "normalized_timestamp": "2026-09-04T08:00:00Z",
        "envelope": {
            "envelope_id": "iam-1",
            "source_type": "iam",
            "host": "ws-001",
            "ingested_at": "2026-09-04T08:00:00Z",
            "raw_payload": '{"raw": "iam_payload"}'
        },
        "parsed": {
            "event_type": "authenticate"
            # Missing username, client_ip, success etc.
        }
    }
    
    res = field_norm.normalize(event_obj)
    common = res["common_event"]
    assert common["event_type"] == "authenticate"
    assert common["identity"] is None
    assert common["success"] is None
