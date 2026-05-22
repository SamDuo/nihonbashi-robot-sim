"""Stage One testbed entrypoint.

Usage:
    python scripts/run_testbed.py
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from sim.testbed.run import main as run_main
    return run_main(out_root=str(root))


if __name__ == "__main__":
    raise SystemExit(main())
