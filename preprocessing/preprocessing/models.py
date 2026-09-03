from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

@dataclass
class NormalizedEvent:
    event_id: str
    timestamp: str
    source_type: str
    host: Optional[str] = None
    identity: Optional[str] = None
    event_type: Optional[str] = None
    action: Optional[str] = None
    process_name: Optional[str] = None
    process_path: Optional[str] = None
    parent_process: Optional[str] = None
    parent_pid: Optional[str] = None
    command_line: Optional[str] = None
    resource: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    success: Optional[bool] = None
    model: Optional[str] = None
    prompt: Optional[str] = None
    response: Optional[str] = None
    latency_ms: Optional[float] = None
    ingested_at: Optional[str] = None
    raw_payload: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
