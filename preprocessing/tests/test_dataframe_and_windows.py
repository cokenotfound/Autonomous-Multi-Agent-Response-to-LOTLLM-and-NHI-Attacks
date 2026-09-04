"""
tests/test_dataframe_and_windows.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import polars as pl
from dataframe.dataframe_builder import DataFrameBuilder
from windows.fixed_time_windows import FixedTimeWindowBuilder
from windows.session_windows import SessionWindowBuilder

@pytest.fixture
def mock_events():
    return [
        {"event_id": "1", "timestamp": "2026-09-04T08:00:00Z", "correlation_key": "ws-001|alice", "source_type": "iam", "event_type": "auth"},
        {"event_id": "2", "timestamp": "2026-09-04T08:00:05Z", "correlation_key": "ws-001|alice", "source_type": "vault", "event_type": "read"},
        # Gap of 10 seconds -> should be new fixed window if window=5, but same session if gap=15
        {"event_id": "3", "timestamp": "2026-09-04T08:00:15Z", "correlation_key": "ws-001|alice", "source_type": "api", "event_type": "request"},
        
        # Different identity, same time
        {"event_id": "4", "timestamp": "2026-09-04T08:00:00Z", "correlation_key": "ws-002|bob", "source_type": "sysmon", "event_type": "ProcessCreate"},
        
        # Large gap for alice -> new session if gap=15
        {"event_id": "5", "timestamp": "2026-09-04T08:05:00Z", "correlation_key": "ws-001|alice", "source_type": "ollama", "event_type": "generate"},
    ]

def test_dataframe_builder(mock_events):
    builder = DataFrameBuilder()
    df = builder.build(mock_events)
    
    assert isinstance(df, pl.DataFrame)
    assert len(df) == 5
    assert df.schema["timestamp"] == pl.Datetime

def test_fixed_time_windows(mock_events):
    builder = DataFrameBuilder()
    df = builder.build(mock_events)
    
    # 10 second windows
    window_builder = FixedTimeWindowBuilder(window_seconds=10)
    windows = window_builder.build_windows(df)
    
    # Alice has events at 08:00:00, 08:00:05 (window 1)
    # Alice has event at 08:00:15 (window 2)
    # Alice has event at 08:05:00 (window 3)
    # Bob has event at 08:00:00 (window 4)
    # Total fixed windows across all correlation keys = 4
    
    assert len(windows) == 4
    
    # Check the first window for alice (08:00:00 to 08:00:10)
    alice_w1 = windows.filter((pl.col("correlation_key") == "ws-001|alice") & (pl.col("event_count") == 2))
    assert len(alice_w1) == 1
    assert alice_w1["event_id"][0].to_list() == ["1", "2"]

def test_session_windows_gap_threshold(mock_events):
    builder = DataFrameBuilder()
    df = builder.build(mock_events)
    
    # Session gap threshold of 15 seconds
    # Alice: 08:00:00 -> 08:00:05 (diff 5s, same session) -> 08:00:15 (diff 10s, same session) -> 08:05:00 (diff > 15s, NEW session)
    # Bob: 1 event -> 1 session
    # Total sessions = 3
    
    session_builder = SessionWindowBuilder(gap_seconds=15)
    sessions = session_builder.build_windows(df)
    
    assert len(sessions) == 3
    
    alice_sessions = sessions.filter(pl.col("correlation_key") == "ws-001|alice")
    assert len(alice_sessions) == 2
    
    # The first session should have 3 events
    s1 = alice_sessions.filter(pl.col("event_count") == 3)
    assert len(s1) == 1
    assert s1["event_id"][0].to_list() == ["1", "2", "3"]

def test_session_state_across_batches(mock_events):
    builder = DataFrameBuilder()
    session_builder = SessionWindowBuilder(gap_seconds=15)
    
    batch1 = builder.build(mock_events[:2]) # 08:00:00 and 08:00:05 (Alice)
    batch2 = builder.build([mock_events[2]]) # 08:00:15 (Alice, diff 10s from previous batch)
    batch3 = builder.build([mock_events[4]]) # 08:05:00 (Alice, diff large)
    
    # Process batches sequentially
    s1 = session_builder.assign_sessions(batch1)
    s2 = session_builder.assign_sessions(batch2)
    s3 = session_builder.assign_sessions(batch3)
    
    # s1 and s2 should share the SAME session_id for Alice because the gap is 10s < 15s
    assert s1["session_id"][1] == s2["session_id"][0]
    
    # s3 should have a NEW session_id because the gap is 5 minutes > 15s
    assert s3["session_id"][0] != s2["session_id"][0]
