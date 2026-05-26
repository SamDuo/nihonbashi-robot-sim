"""JSONL provenance log writer.

One line per (scenario, agent, hour) decision. Keeps the auditability
metric honest and gives stakeholders a queryable record.
"""
import json
from pathlib import Path


class ProvenanceWriter:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._f = open(self.path, "w", encoding="utf-8")

    def log(self, **fields) -> None:
        self._f.write(json.dumps(fields, default=str) + "\n")

    def close(self) -> None:
        self._f.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
