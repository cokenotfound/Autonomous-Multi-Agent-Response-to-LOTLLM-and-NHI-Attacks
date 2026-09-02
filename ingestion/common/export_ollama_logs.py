import json
import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

stream = "telemetry:ollama"

events = r.xrange(stream, "-", "+")

with open("ingestion/logs/ollama.jsonl", "w") as f:
    for event_id, fields in events:
        record = {
            "event_id": event_id,
            **fields
        }
        f.write(json.dumps(record) + "\n")

print(f"Exported {len(events)} events to ingestion/logs/ollama.jsonl")