from __future__ import annotations

import json
from pathlib import Path


def write_json(path: Path, obj) -> None:
    """Pretty JSON, UTF-8, LF line endings on every platform."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))
