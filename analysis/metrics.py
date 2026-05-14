"""Phase 3 evaluation metrics.

Each function takes a SUMO/ABM run output (dataframe or path) and returns
a scalar score. All six are documented in docs/phase3_simulation.md.

These are stubs for the team to fill in once Phase 1 results land — the
signatures and units are the contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class RunOutput:
    """Output of a single SUMO/ABM run."""

    trace_path: Path
    config_path: Path

    def load_trace(self) -> pd.DataFrame:
        return pd.read_csv(self.trace_path)


def labor_substitution_rate(run: RunOutput) -> float:
    """Fraction of outdoor delivery / patrol tasks executed by robots.

    Higher is better. Range [0, 1].
    """
    raise NotImplementedError("Phase 1 deliverable")


def heat_exposure_reduction(run: RunOutput, baseline: RunOutput) -> float:
    """Reduction in mean cumulative heat exposure for human-staff agents
    vs. baseline.

    Higher is better. Computed as (baseline_mean - run_mean) / baseline_mean.
    """
    raise NotImplementedError("Phase 1 deliverable")


def service_continuity(run: RunOutput) -> float:
    """Service uptime during the heat-scenario window. Range [0, 1]."""
    raise NotImplementedError("Phase 1 deliverable")


def delivery_efficiency(run: RunOutput) -> float:
    """Throughput: tasks completed per wall hour."""
    raise NotImplementedError("Phase 1 deliverable")


def pedestrian_interference(run: RunOutput) -> float:
    """Composite penalty: mean detour length (m) + mean speed reduction (%)
    + docking-conflict count.

    Lower is better.
    """
    raise NotImplementedError("Phase 1 deliverable")


def infrastructure_compatibility(run: RunOutput) -> float:
    """Penalty for incompatible docking, charging, or service-node use.

    Lower is better. Range [0, +inf].
    """
    raise NotImplementedError("Phase 1 deliverable")


METRICS = {
    "labor_substitution_rate": labor_substitution_rate,
    "heat_exposure_reduction": heat_exposure_reduction,
    "service_continuity": service_continuity,
    "delivery_efficiency": delivery_efficiency,
    "pedestrian_interference": pedestrian_interference,
    "infrastructure_compatibility": infrastructure_compatibility,
}

METRIC_DIRECTIONS = {
    "labor_substitution_rate": "max",
    "heat_exposure_reduction": "max",
    "service_continuity": "max",
    "delivery_efficiency": "max",
    "pedestrian_interference": "min",
    "infrastructure_compatibility": "min",
}
