"""Stage One testbed entrypoint.

Usage:
    python scripts/run_testbed.py
    NIHONBASHI_OUT_ROOT=/c/temp/nihonbashi-outputs python scripts/run_testbed.py

Set NIHONBASHI_OUT_ROOT to redirect outputs/ off the OneDrive-synced repo
when local storage quota is tight.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    out_root = os.environ.get("NIHONBASHI_OUT_ROOT", str(root))
    from sim.testbed.run import main as run_main
    return run_main(out_root=out_root)


if __name__ == "__main__":
    raise SystemExit(main())
