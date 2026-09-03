from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PREPROCESSED_DIR = PROJECT_ROOT / "data" / "preprocessed"
FIXED_WINDOW_DIR = PROJECT_ROOT / "data" / "windows" / "fixed"
SESSION_WINDOW_DIR = PROJECT_ROOT / "data" / "windows" / "session"
ERROR_DIR = PROJECT_ROOT / "data" / "errors"

STREAMS = {
    "sysmon": "telemetry:sysmon",
    "auditd": "telemetry:auditd",
    "ollama": "telemetry:ollama",
    "iam": "telemetry:iam",
    "vault": "telemetry:vault",
    "api_gateway": "telemetry:api_gateway",
}

# The project requires fixed-time and session windows but does not prescribe
# numeric values. Keep these implementation parameters configurable.
@dataclass(frozen=True)
class WindowConfig:
    fixed_window_seconds: int = 60
    session_gap_seconds: int = 300

@dataclass(frozen=True)
class RedisConfig:
    url: str = "redis://localhost:6379/0"
    batch_size: int = 100

WINDOW_CONFIG = WindowConfig()
REDIS_CONFIG = RedisConfig()
