import json
import uuid
from datetime import datetime, timezone

import redis


REDIS_HOST = "localhost"
REDIS_PORT = 6379


STREAMS = {
    "sysmon": "telemetry:sysmon",
    "auditd": "telemetry:auditd",
    "ollama": "telemetry:ollama",
    "iam": "telemetry:iam",
    "vault": "telemetry:vault",
    "api_gateway": "telemetry:api_gateway",
}


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
)


def publish(source_type: str, raw_payload, host: str = "localhost"):
    """
    Publish one raw telemetry event to the appropriate Redis Stream.
    """

    if source_type not in STREAMS:
        raise ValueError(f"Unknown source type: {source_type}")

    envelope = {
        "envelope_id": str(uuid.uuid4()),
        "source_type": source_type,
        "host": host,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "raw_payload": (
            raw_payload
            if isinstance(raw_payload, str)
            else json.dumps(raw_payload)
        ),
    }

    stream_name = STREAMS[source_type]

    event_id = redis_client.xadd(
        stream_name,
        envelope,
        maxlen=1_000_000,
        approximate=True,
    )

    return event_id


if __name__ == "__main__":
    event_id = publish(
        "ollama",
        {
            "model": "test-model",
            "prompt": "Redis ingestion test",
        },
        host="localhost",
    )

    print(f"Published event: {event_id}")