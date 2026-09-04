"""
tests/test_event_correlator.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from correlation.event_correlator import EventCorrelator

def test_chronological_ordering_out_of_order():
    correlator = EventCorrelator()
    
    # Simulate events arriving out of order (e.g. from different Redis streams with different latencies)
    events = [
        {
            "is_valid": True,
            "common_event": {"event_id": "3", "timestamp": "2026-09-04T08:00:10Z", "host": "h1", "identity": "u1"}
        },
        {
            "is_valid": True,
            "common_event": {"event_id": "1", "timestamp": "2026-09-04T08:00:00Z", "host": "h1", "identity": "u1"}
        },
        {
            "is_valid": True,
            "common_event": {"event_id": "2", "timestamp": "2026-09-04T08:00:05Z", "host": "h1", "identity": "u1"}
        }
    ]
    
    sorted_events = correlator.process_batch(events)
    
    assert len(sorted_events) == 3
    # Check strict time ordering
    assert sorted_events[0]["event_id"] == "1"
    assert sorted_events[1]["event_id"] == "2"
    assert sorted_events[2]["event_id"] == "3"

def test_correlation_keys():
    correlator = EventCorrelator()
    events = [
        {
            "is_valid": True,
            "common_event": {
                "event_id": "1", 
                "timestamp": "2026-09-04T08:00:00Z", 
                "host": "ws-001", 
                "identity": "alice",
                "parent_pid": 1234
            }
        },
        {
            "is_valid": True,
            "common_event": {
                "event_id": "2", 
                "timestamp": "2026-09-04T08:00:01Z", 
                "host": "ws-002", 
                "identity": None,
                "parent_pid": None
            }
        }
    ]
    
    result = correlator.process_batch(events)
    
    assert result[0]["correlation_key"] == "ws-001|alice"
    assert result[0]["process_link"] == "ws-001|pid:1234"
    
    assert result[1]["correlation_key"] == "ws-002|unknown_identity"
    assert result[1]["process_link"] is None

def test_chained_nhi_scenario_ordering():
    # Simulate the Step 0 NHI chain arriving slightly jumbled
    correlator = EventCorrelator()
    events = [
        {"is_valid": True, "common_event": {"event_id": "ollama", "timestamp": "2026-09-04T08:00:08Z", "source_type": "ollama"}},
        {"is_valid": True, "common_event": {"event_id": "api", "timestamp": "2026-09-04T08:00:04Z", "source_type": "api_gateway"}},
        {"is_valid": True, "common_event": {"event_id": "iam", "timestamp": "2026-09-04T08:00:00Z", "source_type": "iam"}},
        {"is_valid": True, "common_event": {"event_id": "sysmon", "timestamp": "2026-09-04T08:00:06Z", "source_type": "sysmon"}},
        {"is_valid": True, "common_event": {"event_id": "vault", "timestamp": "2026-09-04T08:00:02Z", "source_type": "vault"}},
    ]
    
    result = correlator.process_batch(events)
    
    sources_in_order = [e["source_type"] for e in result]
    expected_chain = ["iam", "vault", "api_gateway", "sysmon", "ollama"]
    
    assert sources_in_order == expected_chain
