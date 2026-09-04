"""
Module 2 - Module 1 Log Importer

Reads Module 1 exported .txt log files from:
    preprocessing/dataset/

and imports them into the Redis Streams expected by Module 2.

Flow:

    Module 1 .txt logs
          ↓
    import_logs.py
          ↓
    Redis Streams
          ↓
    Module 2 preprocessing pipeline
"""

import json
from pathlib import Path

import redis


# ============================================================
# CONFIGURATION
# ============================================================

REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379

# IMPORTANT:
# Your Redis server is using RESP2.
REDIS_PROTOCOL = 2

# Use the existing dataset directory.
INPUT_DIR = Path(__file__).parent / "dataset"

SOURCE_TO_STREAM = {
    "sysmon": "telemetry:sysmon",
    "auditd": "telemetry:auditd",
    "ollama": "telemetry:ollama",
    "iam": "telemetry:iam",
    "vault": "telemetry:vault",
    "api_gateway": "telemetry:api_gateway",
}


# ============================================================
# PARSE TXT FILE
# ============================================================

def parse_txt_file(path: Path) -> list[dict]:
    """
    Parse Module 1 exported Redis-stream text.

    Expected format:

    <redis-entry-id>
    field
    value
    field
    value
    ...

    Returns:
        [
            {
                "redis_id": "...",
                "fields": {...}
            }
        ]
    """

    lines = [
        line.strip()
        for line in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    records = []
    i = 0

    while i < len(lines):

        # First line = Redis stream entry ID
        redis_id = lines[i]
        i += 1

        fields = {}

        # Read field/value pairs
        while i + 1 < len(lines):

            current = lines[i]

            # Detect next Redis stream ID.
            #
            # Example:
            # 1788372698321-0
            # 1788465231899-1
            if (
                "-" in current
                and current.split("-")[0].isdigit()
            ):
                break

            field = lines[i]
            value = lines[i + 1]

            fields[field] = value

            i += 2

        records.append(
            {
                "redis_id": redis_id,
                "fields": fields,
            }
        )

    return records


# ============================================================
# VALIDATE ENVELOPE
# ============================================================

def validate_envelope(fields: dict) -> bool:

    required_fields = [
        "envelope_id",
        "source_type",
        "host",
        "ingested_at",
        "raw_payload",
    ]

    return all(
        field in fields
        for field in required_fields
    )


# ============================================================
# IMPORT ONE FILE
# ============================================================

def import_file(
    redis_client: redis.Redis,
    path: Path,
) -> tuple[int, int]:

    records = parse_txt_file(path)

    imported = 0
    skipped = 0

    print()
    print("=" * 60)
    print(f"FILE: {path.name}")
    print("=" * 60)

    print(f"Records found: {len(records)}")

    for record in records:

        redis_id = record["redis_id"]
        fields = record["fields"]

        # ----------------------------------------------------
        # Validate required envelope fields
        # ----------------------------------------------------

        if not validate_envelope(fields):

            print(
                f"[SKIP] {redis_id} "
                f"- incomplete envelope"
            )

            skipped += 1
            continue

        # ----------------------------------------------------
        # Identify source
        # ----------------------------------------------------

        source_type = fields["source_type"]

        if source_type not in SOURCE_TO_STREAM:

            print(
                f"[SKIP] {redis_id} "
                f"- unknown source_type: {source_type}"
            )

            skipped += 1
            continue

        # ----------------------------------------------------
        # Validate raw JSON payload
        # ----------------------------------------------------

        try:

            json.loads(
                fields["raw_payload"]
            )

        except json.JSONDecodeError:

            print(
                f"[SKIP] {redis_id} "
                f"- raw_payload is invalid JSON"
            )

            skipped += 1
            continue

        # ----------------------------------------------------
        # Build Module 2 envelope
        # ----------------------------------------------------

        envelope = {
            "envelope_id": fields["envelope_id"],
            "source_type": fields["source_type"],
            "host": fields["host"],
            "ingested_at": fields["ingested_at"],
            "raw_payload": fields["raw_payload"],
        }

        # ----------------------------------------------------
        # Determine Redis stream
        # ----------------------------------------------------

        stream = SOURCE_TO_STREAM[source_type]

        # ----------------------------------------------------
        # Write to Redis
        # ----------------------------------------------------

        redis_client.xadd(
            stream,
            envelope,
        )

        imported += 1

        print(
            f"[OK] {source_type:<12} "
            f"-> {stream}"
        )

    return imported, skipped


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 65)
    print("MODULE 2 - MODULE 1 LOG IMPORTER")
    print("=" * 65)

    print()
    print(f"Input directory:")
    print(f"  {INPUT_DIR}")

    # --------------------------------------------------------
    # Check dataset directory
    # --------------------------------------------------------

    if not INPUT_DIR.exists():

        print()
        print("[ERROR] Dataset directory does not exist.")
        print(INPUT_DIR)

        return

    # --------------------------------------------------------
    # Connect to Redis
    # --------------------------------------------------------

    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        protocol=REDIS_PROTOCOL,
        decode_responses=True,
    )

    try:

        redis_client.ping()

        print()
        print("[OK] Redis connected")

    except redis.RedisError as error:

        print()
        print("[ERROR] Redis connection failed:")
        print(error)

        return

    # --------------------------------------------------------
    # Find TXT files
    # --------------------------------------------------------

    txt_files = sorted(
        INPUT_DIR.glob("*.txt")
    )

    if not txt_files:

        print()
        print("[ERROR] No .txt files found.")

        return

    print()
    print("TXT files found:")

    for file in txt_files:
        print(f"  - {file.name}")

    # --------------------------------------------------------
    # Import files
    # --------------------------------------------------------

    total_imported = 0
    total_skipped = 0

    for path in txt_files:

        imported, skipped = import_file(
            redis_client,
            path,
        )

        total_imported += imported
        total_skipped += skipped

    # --------------------------------------------------------
    # Final statistics
    # --------------------------------------------------------

    print()
    print("=" * 65)
    print("IMPORT COMPLETE")
    print("=" * 65)

    print()
    print(f"Imported : {total_imported}")
    print(f"Skipped  : {total_skipped}")

    print()
    print("Redis Stream Counts:")
    print("-" * 50)

    total = 0

    for source_type, stream in SOURCE_TO_STREAM.items():

        count = redis_client.xlen(stream)

        print(
            f"{stream:<30} {count:>5}"
        )

        total += count

    print("-" * 50)
    print(
        f"{'TOTAL':<30} {total:>5}"
    )

    print()
    print("=" * 65)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()