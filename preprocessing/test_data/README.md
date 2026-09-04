# Module 2 — Development Test Data

## IMPORTANT: This is SYNTHETIC data — NOT real telemetry.

This directory contains the development/test-data generator for Module 2 preprocessing.
It allows Module 2 to be built and tested independently while Module 1 (Ingestion) is
being implemented in parallel.

## Usage

```powershell
# Generate test events (default seed=42, clears streams first)
py -3.13 generate_test_events.py

# Reproducible run with explicit seed
py -3.13 generate_test_events.py --seed 42

# Append to existing streams without clearing
py -3.13 generate_test_events.py --no-clear
```

## Envelope format (matches Module 1)

```json
{
  "envelope_id":  "<uuid4>",
  "source_type":  "sysmon|auditd|ollama|iam|vault|api_gateway",
  "host":         "<hostname>",
  "ingested_at":  "<ISO-8601 UTC>",
  "raw_payload":  "<JSON string>"
}
```

## Streams populated

- telemetry:sysmon
- telemetry:auditd
- telemetry:ollama
- telemetry:iam
- telemetry:vault
- telemetry:api_gateway

## Scenarios covered

| Scenario | Description |
|---|---|
| NHI chained attack | service_bot_01 → IAM → Vault → API → Sysmon → Ollama |
| LOTL chain | cmd.exe → net.exe → wscript.exe → wget |
| Normal activity | alice, bob normal sessions |
| Failed auth | Unauthorized access attempts |
| Invalid events | Missing fields, bad timestamps, malformed JSON |
| Duplicate envelope IDs | For deduplication testing |
| Out-of-order timestamps | For chronological ordering testing |
| Multiple sessions | 2.5h gap between session clusters |
| Multiple identities | alice, bob, service_bot_01, svc-nhi-prod, hacker |
| Multiple hosts | ws-001, ws-002, srv-dc-01, srv-api-01 |
