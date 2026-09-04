"""
tests/test_config.py

Tests for Module 2 configuration loading.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import (
    REDIS_HOST, REDIS_PORT, REDIS_STREAMS, BATCH_SIZE,
    TIME_WINDOW_SIZE, SESSION_GAP_THRESHOLD,
    TIMESTAMP_FORMAT, TIMEZONE_POLICY,
    DEDUPLICATION_POLICY, INVALID_EVENT_POLICY
)

def test_redis_connection_defaults():
    assert isinstance(REDIS_HOST, str)
    assert isinstance(REDIS_PORT, int)

def test_six_streams_configured():
    assert len(REDIS_STREAMS) == 6
    expected_streams = {
        "telemetry:sysmon",
        "telemetry:auditd",
        "telemetry:ollama",
        "telemetry:iam",
        "telemetry:vault",
        "telemetry:api_gateway",
    }
    assert set(REDIS_STREAMS) == expected_streams

def test_batch_size_is_int():
    assert isinstance(BATCH_SIZE, int)
    assert BATCH_SIZE > 0

def test_window_parameters_are_ints():
    assert isinstance(TIME_WINDOW_SIZE, int)
    assert isinstance(SESSION_GAP_THRESHOLD, int)
    assert TIME_WINDOW_SIZE > 0
    assert SESSION_GAP_THRESHOLD > 0

def test_normalization_policies():
    assert isinstance(TIMESTAMP_FORMAT, str)
    assert isinstance(TIMEZONE_POLICY, str)

def test_handling_policies_configured():
    assert DEDUPLICATION_POLICY in ("drop_duplicate", "keep_first", "keep_last")
    assert INVALID_EVENT_POLICY in ("drop", "quarantine", "raise")
