"""
preprocessing/config.py

MODULE 2 - CONFIGURATION
========================
Loads configuration from environment variables (or .env file) with sensible defaults.
Does not hard-code behavioral parameters.
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Redis Connection
REDIS_HOST: str = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
REDIS_URL: str = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

# Redis Streams (Comma-separated list)
_default_streams = "telemetry:sysmon,telemetry:auditd,telemetry:ollama,telemetry:iam,telemetry:vault,telemetry:api_gateway"
REDIS_STREAMS: List[str] = [s.strip() for s in os.getenv("REDIS_STREAMS", _default_streams).split(",") if s.strip()]

# Batch Configuration
BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "1000"))

# Time Windows
# Represented in seconds. Defaults: 5 minutes (300s) for fixed window, 30 minutes (1800s) for session gap.
TIME_WINDOW_SIZE: int = int(os.getenv("TIME_WINDOW_SIZE", "300"))
SESSION_GAP_THRESHOLD: int = int(os.getenv("SESSION_GAP_THRESHOLD", "1800"))

# Normalization
TIMESTAMP_FORMAT: str = os.getenv("TIMESTAMP_FORMAT", "iso8601")
TIMEZONE_POLICY: str = os.getenv("TIMEZONE_POLICY", "UTC")

# Policies
# DEDUPLICATION_POLICY options: "drop_duplicate", "keep_first", "keep_last"
DEDUPLICATION_POLICY: str = os.getenv("DEDUPLICATION_POLICY", "drop_duplicate")

# INVALID_EVENT_POLICY options: "drop", "quarantine", "raise"
INVALID_EVENT_POLICY: str = os.getenv("INVALID_EVENT_POLICY", "quarantine")
