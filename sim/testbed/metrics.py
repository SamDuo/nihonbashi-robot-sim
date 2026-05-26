"""Six methodology metrics + two twin metrics, computed per scenario.

Source of truth for metric names: docs/methodology.md and
docs/phase3_simulation.md.
"""
import numpy as np


def _scenario_metrics(run: dict) -> dict[str, float]:
    rows = run["agent_log"]
    rationales = run["provenance"]

    final = [r for r in rows if r["hour"] == 23]
    mean_exposure = float(np.mean([r["cumulative_exposure"] for r in final])) if final else 0.0

    total_rows = len(rows) or 1
    sheltered = sum(1 for r in rows if r["status"] == "sheltering")
    labor_sub = sheltered / total_rows

    working_window = [r for r in rows if r["planned_status"] == "working"]
    served = sum(1 for r in working_window if r["status"] in ("working", "sheltering"))
    service_cont = (served / len(working_window)) if working_window else 1.0

    wall_ms = float(sum(r.get("latency_ms", 0.0) for r in rationales)) or 1.0
    delivery_eff = served / wall_ms * 1000.0

    interference = float(np.mean([r["displacement"] for r in rows])) if rows else 0.0

    overflow = sum(1 for r in rationales if r.get("decision") == "stay_no_capacity")
    compat = 1.0 - overflow / total_rows

    latencies = [r["latency_ms"] for r in rationales if "latency_ms" in r]
    mean_latency = float(np.mean(latencies)) if latencies else 0.0
    auditability = (
        sum(1 for r in rationales if "policy" in r and "decision" in r) / len(rationales)
    ) if rationales else 0.0

    return {
        "labor_substitution_rate": labor_sub,
        "heat_exposure_mean": mean_exposure,
        "service_continuity": service_cont,
        "delivery_efficiency": delivery_eff,
        "pedestrian_interference": interference,
        "infrastructure_compatibility": compat,
        "decision_latency_ms": mean_latency,
        "decision_auditability": auditability,
    }


def compute_all_metrics(runs: dict[str, dict], baseline_key: str = "baseline") -> dict[str, dict[str, float]]:
    out = {k: _scenario_metrics(v) for k, v in runs.items()}
    if baseline_key in out:
        bexp = out[baseline_key]["heat_exposure_mean"] or 1e-9
        for k, m in out.items():
            m["heat_exposure_reduction"] = max(0.0, (bexp - m["heat_exposure_mean"]) / bexp)
            m["cooling_gap_closure_rate"] = m["heat_exposure_reduction"]
    return out
