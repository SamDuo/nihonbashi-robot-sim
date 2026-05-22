"""Nine outcome metrics + two twin metrics.

Outcome metrics quantify what the system DOES for people (heat, equity, shelter, energy).
Twin metrics quantify the digital-twin loop ITSELF (decision speed, auditability).

NOTE: docs/stage1_research_design.md was empty (0 bytes) when the testbed was assembled
on 2026-05-21. Definitions below are reconstructed from the Group 3 brief and
docs/system_architecture.md sections 4 and 7. If the canonical doc is restored, reconcile
names and update DEFINITIONS to match.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

import numpy as np
import pandas as pd


@dataclass
class OutcomeMetrics:
    cumulative_population_exposure: float
    vulnerability_weighted_exposure: float
    mean_peak_hourly_exposure: float
    sheltered_agent_hours: int
    shelter_utilization_rate: float
    unmet_shelter_demand: int
    cooling_energy_kwh: float
    cooling_emissions_kgco2e: float
    equity_gap_ratio: float


@dataclass
class TwinMetrics:
    mean_decision_latency_ms: float
    provenance_coverage: float


DEFINITIONS: Dict[str, str] = {
    "cumulative_population_exposure":
        "Sum over agents and hours of (heat_value_in_current_cell * (0 if sheltered else 1)). "
        "Lower is better.",
    "vulnerability_weighted_exposure":
        "Same sum but each term multiplied by vulnerability_score. Lower is better.",
    "mean_peak_hourly_exposure":
        "Average over agents of their max hourly exposure across the 24-hour run. Lower is better.",
    "sheltered_agent_hours":
        "Count of (agent, hour) tuples where the agent was inside a shelter. Higher is better.",
    "shelter_utilization_rate":
        "Mean across hours of (occupants_summed / capacity_summed) for all shelters. "
        "Target ~0.6-0.85; >0.95 indicates undersupply.",
    "unmet_shelter_demand":
        "Count of policy decisions that wanted shelter but found none feasible. Lower is better.",
    "cooling_energy_kwh":
        "Sum of cooling_kwh across hours weighted by the fraction of capacity used. "
        "Cost lever; lower is better all else equal.",
    "cooling_emissions_kgco2e":
        "cooling_energy_kwh weighted by hourly emissions_intensity (kgCO2e/kWh).",
    "equity_gap_ratio":
        "Mean exposure of the top vulnerability quartile divided by mean exposure of the bottom quartile. "
        "1.0 = perfect parity; >1 = inequity; proactive policies should drive this toward 1.",
    "mean_decision_latency_ms":
        "Mean wall-clock time per policy decision in milliseconds. Twin-loop health.",
    "provenance_coverage":
        "Provenance events written divided by (agents * hours). 1.0 = every step audited.",
}


def compute_outcome(
    exposure_log: pd.DataFrame,
    shelter_log: pd.DataFrame,
    shelter_envelope: pd.DataFrame,
    decisions: pd.DataFrame,
) -> OutcomeMetrics:
    cum_exp = float(exposure_log["effective_exposure"].sum())
    vuln_weighted = float(
        (exposure_log["effective_exposure"] * exposure_log["vulnerability_score"]).sum()
    )
    peak_per_agent = (
        exposure_log.groupby("agent_id")["effective_exposure"].max()
    )
    mean_peak = float(peak_per_agent.mean())

    sheltered_hours = int((shelter_log["in_shelter"] == 1).sum())

    util_per_hour = (
        shelter_log.groupby("hour")["in_shelter"].sum()
        / shelter_envelope.groupby("hour")["max_occupants"].sum()
    )
    util = float(util_per_hour.fillna(0.0).mean())

    if "rule" in decisions.columns and len(decisions) > 0:
        wanted_but_none = decisions[
            (decisions["wanted_shelter"] == 1) & (decisions["chosen_shelter"].isna())
        ]
        unmet = int(len(wanted_but_none))
    else:
        unmet = 0

    cooling_e = float(
        (shelter_envelope["cooling_kwh"]
         * shelter_envelope["util_fraction"]).sum()
    )
    cooling_co2 = float(
        (shelter_envelope["cooling_kwh"]
         * shelter_envelope["util_fraction"]
         * shelter_envelope["emissions_intensity"]).sum()
    )

    per_agent = exposure_log.groupby(["agent_id", "vulnerability_score"])\
        ["effective_exposure"].sum().reset_index()
    q1 = per_agent["vulnerability_score"].quantile(0.25)
    q3 = per_agent["vulnerability_score"].quantile(0.75)
    bottom = per_agent.loc[per_agent["vulnerability_score"] <= q1, "effective_exposure"].mean()
    top = per_agent.loc[per_agent["vulnerability_score"] >= q3, "effective_exposure"].mean()
    equity = float(top / bottom) if bottom and not np.isnan(bottom) and bottom > 0 else float("nan")

    return OutcomeMetrics(
        cumulative_population_exposure=round(cum_exp, 3),
        vulnerability_weighted_exposure=round(vuln_weighted, 3),
        mean_peak_hourly_exposure=round(mean_peak, 4),
        sheltered_agent_hours=sheltered_hours,
        shelter_utilization_rate=round(util, 4),
        unmet_shelter_demand=unmet,
        cooling_energy_kwh=round(cooling_e, 2),
        cooling_emissions_kgco2e=round(cooling_co2, 3),
        equity_gap_ratio=round(equity, 4) if not np.isnan(equity) else float("nan"),
    )


def compute_twin(latencies_ms: List[float], provenance_events: int, agents: int, hours: int) -> TwinMetrics:
    mean_lat = float(np.mean(latencies_ms)) if latencies_ms else 0.0
    expected = agents * hours
    coverage = float(provenance_events / expected) if expected else 0.0
    return TwinMetrics(
        mean_decision_latency_ms=round(mean_lat, 4),
        provenance_coverage=round(coverage, 4),
    )


def metrics_to_row(scenario: str, outcome: OutcomeMetrics, twin: TwinMetrics) -> Dict[str, object]:
    row = {"scenario": scenario}
    row.update(asdict(outcome))
    row.update(asdict(twin))
    return row
