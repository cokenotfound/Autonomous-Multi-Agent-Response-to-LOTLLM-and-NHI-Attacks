import json
from pathlib import Path
from typing import Iterable, Dict, Any, List

def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    events = []
    if not path.exists():
        return events

    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("JSONL line is not an object")
                events.append(value)
            except Exception as exc:
                events.append({
                    "__read_error__": str(exc),
                    "__line_number__": line_number,
                    "__raw_line__": line,
                })
    return events

def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
