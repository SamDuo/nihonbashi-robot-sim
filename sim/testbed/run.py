"""End-to-end driver for the Mesa+Shapely+Folium testbed."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from .gis_export import (
    export_agents_geojson,
    export_heat_field_geojson,
    export_shelters_geojson,
)
from .heat_field import generate_synthetic as gen_heat
from .metrics import DEFINITIONS, compute_outcome, compute_twin, metrics_to_row
from .model import NihonbashiModel
from .population import generate_synthetic as gen_population
from .scene import build_shelters
from .shelter_model import generate_envelope
from .visualize import (
    build_browser_twin,
    plot_equity_breakdown,
    plot_exposure_timeline,
    plot_metric_comparison,
)


HEADLINE_HOUR = 14
SCENARIOS = ("baseline", "reactive", "proactive")


def main(out_root: str = ".", n_agents: int = 240, seed_offset: int = 0) -> int:
    out = Path(out_root)
    reports = out / "outputs" / "reports"
    gis = out / "outputs" / "gis"
    figures = out / "outputs" / "figures" / "auto"
    for d in (reports, gis, figures):
        d.mkdir(parents=True, exist_ok=True)

    heat = gen_heat(seed=7 + seed_offset)
    shelters = build_shelters()
    envelope_df, envelope_table = generate_envelope(shelters, seed=23 + seed_offset)
    agents_spec, population_df = gen_population(n_agents=n_agents, seed=11 + seed_offset)

    population_df.to_csv(reports / "population.csv", index=False)
    envelope_df.to_csv(reports / "shelter_envelope.csv", index=False)
    np.save(reports / "heat_field.npy", heat)

    export_heat_field_geojson(heat, HEADLINE_HOUR, gis / f"heat_field_h{HEADLINE_HOUR:02d}.geojson")
    export_shelters_geojson(shelters, envelope_table, gis / "shelters.geojson")

    metrics_rows = []
    snapshots: Dict[str, pd.DataFrame] = {}
    exposure_logs: Dict[str, pd.DataFrame] = {}

    for scenario in SCENARIOS:
        prov_path = reports / f"provenance_{scenario}.jsonl"
        model = NihonbashiModel(
            agents=agents_spec,
            shelters=shelters,
            envelope_table=envelope_table,
            heat_field=heat,
            policy_name=scenario,
            provenance_path=str(prov_path),
            seed=42 + seed_offset,
        )
        model.run_24h()

        exposure_df = model.exposure_df()
        shelter_df = model.shelter_df()
        decisions_df = model.decisions_df()

        exposure_df.to_csv(reports / f"exposure_log_{scenario}.csv", index=False)
        decisions_df.to_csv(reports / f"decisions_{scenario}.csv", index=False)

        env_with_use = envelope_df.copy()
        util_per_hour = (
            shelter_df[shelter_df["in_shelter"] == 1]
            .groupby("hour").size()
            .reindex(range(24), fill_value=0)
        )
        cap_per_hour = envelope_df.groupby("hour")["max_occupants"].sum()
        util_frac_hour = (util_per_hour / cap_per_hour).fillna(0.0).clip(0.0, 1.0)
        env_with_use["util_fraction"] = env_with_use["hour"].map(util_frac_hour)

        outcome = compute_outcome(
            exposure_log=exposure_df,
            shelter_log=shelter_df,
            shelter_envelope=env_with_use,
            decisions=decisions_df,
        )
        twin = compute_twin(
            latencies_ms=model.latencies_ms,
            provenance_events=model.prov.count,
            agents=n_agents,
            hours=24,
        )
        metrics_rows.append(metrics_to_row(scenario, outcome, twin))
        snapshots[scenario] = exposure_df
        exposure_logs[scenario] = exposure_df

        export_agents_geojson(
            exposure_df,
            HEADLINE_HOUR,
            gis / f"agents_{scenario}_h{HEADLINE_HOUR:02d}.geojson",
            scenario,
        )

    metrics_df = pd.DataFrame(metrics_rows)
    metrics_df.to_csv(reports / "testbed_metrics.csv", index=False)

    build_browser_twin(heat, shelters, snapshots, HEADLINE_HOUR, reports / "browser_twin.html")
    plot_metric_comparison(metrics_df, figures / "metric_comparison.png")
    plot_equity_breakdown(exposure_logs, figures / "equity_breakdown.png")
    plot_exposure_timeline(exposure_logs, figures / "exposure_timeline.png")

    _write_comparison_md(metrics_df, reports / "testbed_comparison.md")
    return 0


def _write_comparison_md(metrics_df: pd.DataFrame, path: Path) -> None:
    lines = [
        "# Testbed comparison — Stage One (5/25)",
        "",
        "Three policies on synthetic G1/G2 data matching docs/system_architecture.md sections 4a-4b.",
        "",
        "## Metrics table",
        "",
        metrics_df.to_markdown(index=False),
        "",
        "## Metric definitions",
        "",
    ]
    for name, definition in DEFINITIONS.items():
        lines.append(f"- **{name}** — {definition}")
    lines += [
        "",
        "## How to read it",
        "",
        "- Lower is better for: cumulative_population_exposure, vulnerability_weighted_exposure, "
        "mean_peak_hourly_exposure, unmet_shelter_demand, cooling_energy_kwh, "
        "cooling_emissions_kgco2e, equity_gap_ratio (closer to 1.0), mean_decision_latency_ms.",
        "- Higher is better for: sheltered_agent_hours, provenance_coverage.",
        "- shelter_utilization_rate has a target band (≈ 0.6–0.85). Above 0.95 indicates undersupply; "
        "below 0.3 indicates the policy isn't moving the right people.",
        "",
        "## Headline visual",
        "",
        "`outputs/reports/browser_twin.html` is the Folium twin. Open it locally; toggle scenarios "
        "from the layer control. Anchored to Nihonbashi 35.6840-35.6852°N, 139.7735-139.7747°E.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
