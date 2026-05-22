"""Per-decision audit log (JSONL)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, IO


class ProvenanceWriter:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh: IO | None = self.path.open("w", encoding="utf-8")
        self._n = 0

    def write(self, event: Dict[str, Any]) -> None:
        if self._fh is None:
            raise RuntimeError("ProvenanceWriter closed")
        self._fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        self._n += 1

    @property
    def count(self) -> int:
        return self._n

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def __enter__(self) -> "ProvenanceWriter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
