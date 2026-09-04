"""
tests/test_redis_reader.py

Tests the RedisBatchReader against the actual development data generated in Step 0.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from redis_reader import RedisBatchReader

def test_redis_batch_reader():
    reader = RedisBatchReader()
    
    # 1. Connection status
    connected = reader.connect()
    assert connected is True, "Failed to connect to Redis"
    print("\nRedis Connection: OK")

    # 2. Read events
    events = reader.read_batch(block_ms=10)
    
    # Print stats
    stream_counts = {}
    for stream, msg_id, payload in events:
        stream_counts[stream] = stream_counts.get(stream, 0) + 1
        
        # Verify we received a dictionary representing the envelope
        assert isinstance(payload, dict)
        # We expect at least one of these fields to exist in even malformed test data
        assert any(k in payload for k in ["envelope_id", "source_type", "host", "ingested_at", "raw_payload"])

    print(f"Batch size configured: {reader.batch_size}")
    print(f"Total events read: {len(events)}")
    print("Streams read:")
    for stream, count in stream_counts.items():
        print(f"  {stream}: {count} events")
        
    # We generated 35 events in step 0
    assert len(events) == 35, f"Expected 35 events, got {len(events)}"
    
    # Check all six streams were read
    assert len(stream_counts) == 6, "Did not read from all 6 streams"

