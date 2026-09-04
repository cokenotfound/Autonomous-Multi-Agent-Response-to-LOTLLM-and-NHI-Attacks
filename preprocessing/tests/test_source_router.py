"""
tests/test_source_router.py

Tests the SourceRouter and parsers against Step 0 events.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from redis_reader import RedisBatchReader
from source_router import SourceRouter

@pytest.fixture(scope="module")
def events_from_redis():
    """Fetch events generated in Step 0 from Redis."""
    reader = RedisBatchReader()
    if not reader.connect():
        pytest.skip("Redis not connected")
    return reader.read_batch(block_ms=10)

def test_source_routing(events_from_redis):
    router = SourceRouter()
    
    success_count = 0
    error_count = 0
    parsers_used = set()
    
    for stream, msg_id, envelope in events_from_redis:
        try:
            result = router.route_and_parse(envelope)
            assert "parsed" in result
            assert isinstance(result["parsed"], dict)
            assert result["parser_used"] in [
                "SysmonParser", "AuditdParser", "OllamaParser", 
                "IamParser", "VaultParser", "ApiGatewayParser"
            ]
            parsers_used.add(result["parser_used"])
            success_count += 1
        except ValueError as e:
            # We explicitly injected 3 bad events (missing source_type, missing raw_payload, bad json)
            error_count += 1
            print(f"\nExpected Error Handled: {e}")
            
    # From step 0: we generated 35 events, 3 are intentionally malformed in ways that break routing/parsing
    print(f"\nSuccessfully routed/parsed: {success_count}")
    print(f"Handled routing/parsing errors: {error_count}")
    
    assert success_count == 32
    assert error_count == 3
    assert len(parsers_used) == 6, "Did not use all 6 parsers"

def test_unknown_source_type():
    router = SourceRouter()
    bad_env = {
        "envelope_id": "test-123",
        "source_type": "windows_event_log",
        "host": "ws-001",
        "ingested_at": "2026-09-04T08:00:00",
        "raw_payload": '{"foo": "bar"}'
    }
    with pytest.raises(ValueError, match="Unknown source_type: windows_event_log"):
        router.route_and_parse(bad_env)
