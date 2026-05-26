"""Stage One end-to-end driver.

Builds the synthetic world, runs three policies (baseline / reactive /
proactive), and writes every artifact the visualization plan needs:

  outputs/timeseries/agents.csv          one row per (scenario, agent, hour)
  outputs/timeseries/metrics.csv         scalar + hourly metrics
  outputs/timeseries/population.csv      G1-schema population (24 rows/agent)
  outputs/geo/shelters_<scenario>.geojson  per-scenario shelter usage
  outputs/geo/shelters.geojson           canonical (= proactive)
  outputs/reports/provenance.jsonl       one decision per line
  outputs/reports/cooling_gap_residuals.csv  feedback to G2
  outputs/reports/testbed_comparison.md  human-readable summary
"""
from __future__ import annotations

import csv
import json
import logging
import sys
from pathlib import Path
from typing import Final

from .czml import build_czml
from .heat_field import build_heat_field
from .metrics import compute_all_metrics
from .model import HeatAgent, HeatModel
from .osm_network import load_or_download_network
from .population import (
    AgentProfile, build_population, planned_cell, planned_status,
)
from .provenance import ProvenanceWriter
from .scene import SHELTER_CELLS, cell_centroid_latlng, cell_polygon
from .shelter_model import build_envelope
from .world import World

SCENARIOS: Final[tuple[str, ...]] = ("baseline", "reactive", "proactive")

log = logging.getLogger("testbed")


def _ensure_dirs(root: Path) -> tuple[Path, Path, Path]:
    out_ts = root / "outputs" / "timeseries"
    out_geo = root / "outputs" / "geo"
    out_rep = root / "outputs" / "reports"
    for d in (out_ts, out_geo, out_rep):
        d.mkdir(parents=True, exist_ok=True)
    return out_ts, out_geo, out_rep


def write_population_csv(profiles: list[AgentProfile], out_ts: Path) -> Path:
    path = out_ts / "population.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "agent_id", "age_bucket", "occupation_class", "mobility_class",
            "vulnerability_score", "home_grid_cell", "hour", "activity_grid_cell",
        ])
        for p in profiles:
            for h in range(24):
                w.writerow([
                    p.agent_id, p.age_bucket, p.occupation_class, p.mobility_class,
                    f"{p.vulnerability_score:.3f}",
                    f"g_{p.home_cell[0]}_{p.home_cell[1]}", h,
                    f"g_{planned_cell(p, h)[0]}_{planned_cell(p, h)[1]}",
                ])
    return path


def run_scenario(
    scenario: str, world: World, profiles: list[AgentProfile],
    prov: ProvenanceWriter,
) -> dict:
    world.reset_shelter_usage()
    model = HeatModel(world=world, profiles=profiles, scenario_name=scenario, rng=42)
    agents_by_id: dict[str, HeatAgent] = {a.profile.agent_id: a for a in model.agents}  # type: ignore[attr-defined]
    agent_log: list[dict] = []
    provenance_rows: list[dict] = []
    for hour in range(24):
        model.current_hour = hour
        model.step()
        for aid in sorted(agents_by_id.keys()):
            a = agents_by_id[aid]
            lat, lng = cell_centroid_latlng(*a.current_cell)
            agent_log.append({
                "agent_id": a.profile.agent_id,
                "scenario": scenario,
                "hour": hour,
                "lat": lat,
                "lng": lng,
                "status": a.status,
                "planned_status": planned_status(a.profile, hour),
                "vulnerability_score": a.profile.vulnerability_score,
                "cumulative_exposure": a.cumulative_exposure,
                "displacement": a.last_displacement,
                "cell_x": a.current_cell[0],
                "cell_y": a.current_cell[1],
            })
            prov_row = dict(a.last_rationale)
            prov_row.update({"scenario": scenario, "agent_id": a.profile.agent_id, "hour": hour})
            provenance_rows.append(prov_row)
            prov.log(**prov_row)
    return {
        "agent_log": agent_log,
        "provenance": provenance_rows,
        "n_agents": len(profiles),
        "shelter_occupants": world.shelter_occupants_by_hour(),
    }


def write_agents_csv(runs: dict[str, dict], out_ts: Path) -> Path:
    path = out_ts / "agents.csv"
    fields = [
        "agent_id", "scenario", "hour", "lat", "lng", "status",
        "planned_status", "vulnerability_score", "cumulative_exposure",
        "displacement", "cell_x", "cell_y",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for scenario in SCENARIOS:
            for row in runs[scenario]["agent_log"]:
                w.writerow({k: row[k] for k in fields})
    return path


def write_metrics_csv(
    metric_table: dict[str, dict[str, float]],
    runs: dict[str, dict],
    out_ts: Path,
) -> Path:
    path = out_ts / "metrics.csv"
    rows: list[dict] = []
    for scenario, mvals in metric_table.items():
        for name, value in mvals.items():
            rows.append({"scenario": scenario, "metric_name": name,
                         "value": float(value), "hour": ""})
    for scenario in SCENARIOS:
        log_rows = runs[scenario]["agent_log"]
        n = runs[scenario]["n_agents"]
        per_hour: dict[int, float] = {h: 0.0 for h in range(24)}
        for r in log_rows:
            per_hour[r["hour"]] += r["cumulative_exposure"]
        for h, total in per_hour.items():
            rows.append({"scenario": scenario,
                         "metric_name": "hourly_mean_cumulative_exposure",
                         "value": total / n, "hour": h})
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["scenario", "metric_name", "value", "hour"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


def _shelters_feature_collection(world: World) -> dict:
    occ = world.shelter_occupants_by_hour()
    features = []
    for sid, (cx, cy) in SHELTER_CELLS.items():
        poly = cell_polygon(cx, cy)
        coords = [list(map(list, poly.exterior.coords))]
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": coords},
            "properties": {
                "building_id": sid,
                "cell_x": cx,
                "cell_y": cy,
                "max_occupants_by_hour": {str(h): world.shelter_max(sid, h) for h in range(24)},
                "current_occupants_by_hour": {str(h): occ[sid][h] for h in range(24)},
                "cooling_kwh_by_hour": {str(h): round(world.shelter_cooling_kwh(sid, h), 2) for h in range(24)},
                "emissions_intensity_by_hour": {str(h): round(world.shelter_emissions_intensity(sid, h), 3) for h in range(24)},
            },
        })
    return {"type": "FeatureCollection", "features": features}


def write_shelters_geojson(runs: dict[str, dict], world: World, out_geo: Path) -> list[Path]:
    written: list[Path] = []
    for scenario in SCENARIOS:
        world.reset_shelter_usage()
        for r in runs[scenario]["provenance"]:
            sid = r.get("shelter")
            if sid:
                world.consume_shelter(sid, int(r["hour"]))
        fc = _shelters_feature_collection(world)
        per = out_geo / f"shelters_{scenario}.geojson"
        per.write_text(json.dumps(fc, indent=2), encoding="utf-8")
        written.append(per)
    canonical = out_geo / "shelters.geojson"
    canonical.write_text((out_geo / "shelters_proactive.geojson").read_text(encoding="utf-8"),
                         encoding="utf-8")
    written.append(canonical)
    return written


def write_residuals_csv(runs: dict[str, dict], out_rep: Path) -> Path:
    path = out_rep / "cooling_gap_residuals.csv"
    fields = ["scenario", "agent_id", "hour", "decision", "heat", "vulnerability"]
    rows: list[dict] = []
    for scenario in ("reactive", "proactive"):
        for r in runs[scenario]["provenance"]:
            if r.get("decision") == "stay_no_capacity":
                rows.append({
                    "scenario": scenario,
                    "agent_id": r["agent_id"],
                    "hour": r["hour"],
                    "decision": r["decision"],
                    "heat": round(float(r.get("heat", 0.0)), 3),
                    "vulnerability": round(float(r.get("vulnerability", 0.0)), 3),
                })
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


def write_comparison_md(metric_table: dict[str, dict[str, float]], out_rep: Path) -> Path:
    path = out_rep / "testbed_comparison.md"
    metric_order = [
        "labor_substitution_rate", "heat_exposure_reduction",
        "service_continuity", "delivery_efficiency",
        "pedestrian_interference", "infrastructure_compatibility",
        "cooling_gap_closure_rate", "decision_latency_ms", "decision_auditability",
        "heat_exposure_mean",
    ]
    lines = [
        "# Stage One Testbed Comparison",
        "",
        "Generated by `scripts/run_testbed.py`. Schema: docs/system_architecture.md.",
        "",
        "| Metric | baseline | reactive | proactive |",
        "|---|---:|---:|---:|",
    ]
    for name in metric_order:
        cells = [name]
        for s in SCENARIOS:
            v = metric_table[s].get(name, float("nan"))
            cells.append(f"{v:.3f}" if isinstance(v, float) else str(v))
        lines.append("| " + " | ".join(cells) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main(out_root: str | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    logging.getLogger("mesa").setLevel(logging.WARNING)
    # Suppress Mesa's per-step print() in 3.5.x by neutering its Model.step verbosity.
    import mesa  # noqa: PLC0415
    mesa.Model.steps_per_print = 10**9  # type: ignore[attr-defined]

    root = Path(out_root) if out_root else Path(__file__).resolve().parents[2]
    out_ts, out_geo, out_rep = _ensure_dirs(root)

    log.info("[1/6] Building synthetic world ...")
    heat = build_heat_field(seed=7)
    profiles = build_population(n=100, seed=17)
    shelter_rows = build_envelope(list(SHELTER_CELLS.keys()), seed=11)
    world = World(heat, shelter_rows)
    write_population_csv(profiles, out_ts)

    log.info("[2/6] Running three policies ...")
    runs: dict[str, dict] = {}
    prov_path = out_rep / "provenance.jsonl"
    with ProvenanceWriter(prov_path) as prov:
        for scenario in SCENARIOS:
            runs[scenario] = run_scenario(scenario, world, profiles, prov)
            log.info("    %-9s  %d rows", scenario, len(runs[scenario]["agent_log"]))

    log.info("[3/6] Writing agents.csv + metrics.csv ...")
    write_agents_csv(runs, out_ts)
    metric_table = compute_all_metrics(runs, baseline_key="baseline")
    write_metrics_csv(metric_table, runs, out_ts)

    log.info("[4/6] Writing shelters geojson (per-scenario + canonical) ...")
    write_shelters_geojson(runs, world, out_geo)

    log.info("[5/6] Writing residuals + comparison.md ...")
    write_residuals_csv(runs, out_rep)
    write_comparison_md(metric_table, out_rep)

    log.info("[5.5/6] Building OSM routed CZML per scenario ...")
    try:
        network = load_or_download_network(cache_path=root / "outputs" / "networks" / "nihonbashi_walk.graphml")
        log.info("    network ready (%d nodes)", network.number_of_nodes())
    except Exception as e:
        log.warning("    OSM network unavailable, falling back to straight line interpolation: %s", e)
        network = None
    for scenario in SCENARIOS:
        czml = build_czml(runs, scenario, network=network, multiplier=600, samples_per_hour=6)
        path = out_ts / f"agents_{scenario}.czml"
        path.write_text(json.dumps(czml), encoding="utf-8")
        log.info("    wrote %s (%d packets)", path.name, len(czml))

    log.info("[6/6] Done.")
    log.info("")
    log.info("Outputs:")
    for d in (out_ts, out_geo, out_rep):
        for f in sorted(d.iterdir()):
            log.info("  %s", f.relative_to(root))
    log.info("")
    log.info("Quick metric table:")
    for s in SCENARIOS:
        m = metric_table[s]
        log.info(
            "  %-9s  exposure_mean=%.2f  reduction=%.1f%%  shelter_compat=%.1f%%  latency_ms=%.3f",
            s, m["heat_exposure_mean"], 100 * m.get("heat_exposure_reduction", 0.0),
            100 * m["infrastructure_compatibility"], m["decision_latency_ms"],
        )
    return 0
