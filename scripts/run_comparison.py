"""Phase 3 A/B comparison runner.

Consumes sim/runs/phase3_initial/{side_a,side_b}/<seed>/ and produces
outputs/reports/phase3_comparison.md.

Owner: Sam (analysis). Stub — flesh out once metrics.py is implemented.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("sim/runs/phase3_initial"),
        help="Root containing side_a/ and side_b/ subfolders",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/reports/phase3_comparison.md"),
    )
    args = parser.parse_args()

    side_a = args.runs_dir / "side_a"
    side_b = args.runs_dir / "side_b"
    if not side_a.is_dir() or not side_b.is_dir():
        raise SystemExit(f"missing side_a or side_b under {args.runs_dir}")

    # TODO: load each replicate, compute the six metrics per analysis/metrics.py,
    # run paired-difference statistics, write the markdown report.
    raise NotImplementedError("Phase 3 deliverable")


if __name__ == "__main__":
    main()
