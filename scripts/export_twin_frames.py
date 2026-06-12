"""Export Stage One testbed outputs into compact JSON for the WebGL twin.

Reads the artifacts written by ``scripts/run_testbed.py`` (agents.csv,
population.csv, metrics.csv, shelters_<scenario>.geojson, provenance.jsonl),
rebuilds the deterministic heat field, and writes:

    outputs/twin/scene.json                static geometry + grid metadata
    outputs/twin/frames_<scenario>.json    per-hour agent / robot / heat frames

The viewer (outputs/twin_view.html) is a pure renderer: every entity it draws
comes from these files, so swapping testbed data for the Stage Two real data
(G1 heat raster, G2 shelter envelope, SUMO network) only touches this script.

Buildings are procedurally generated city blocks aligned to the 20x10 testbed
grid (seeded, deterministic). In Stage Two this section is replaced by OSM /
PLATEAU footprint export — the JSON contract ({x, z, w, d, h, kind}) stays.

Usage:
    python scripts/run_testbed.py          # produces outputs/timeseries etc.
    python scripts/export_twin_frames.py   # produces outputs/twin/
"""
from __future__ import annotations

import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sim.testbed.heat_field import build_heat_field  # noqa: E402
from sim.testbed.scene import (  # noqa: E402
    ANCHOR_LAT,
    ANCHOR_LNG,
    CELL_M,
    GRID_H,
    GRID_W,
    SHELTER_CELLS,
)

OUT_ROOT = ROOT / "outputs"
TWIN_DIR = OUT_ROOT / "twin"
SCENARIOS = ("baseline", "reactive", "proactive")

# Visual-layer constants (viewer contract).
NUM_ROBOTS = 6
STATUS_CODES = {"home": 0, "working": 1, "sheltering": 2, "transit": 3}

# Road corridors in grid units. y=5 is the hot pedestrian row in the synthetic
# heat field, so it doubles as the main avenue (Chuo-dori analogue).
AVENUE_Y = 5.0
CROSS_STREET_XS = (4.0, 8.0, 12.0, 16.0)
RING_ROADS_Y = (0.0, 10.0)


def cell_to_m(cx: float, cy: float) -> tuple[float, float]:
    """Grid cell -> local meters; origin at grid SW corner, +x east, +z north."""
    return ((cx + 0.5) * CELL_M, (cy + 0.5) * CELL_M)


def build_roads() -> list[dict]:
    roads = []
    # Main avenue across the full 1000 m extent.
    roads.append({"x0": 0.0, "z0": AVENUE_Y * CELL_M, "x1": GRID_W * CELL_M,
                  "z1": AVENUE_Y * CELL_M, "w": 22.0, "kind": "avenue"})
    for y in RING_ROADS_Y:
        roads.append({"x0": 0.0, "z0": y * CELL_M, "x1": GRID_W * CELL_M,
                      "z1": y * CELL_M, "w": 14.0, "kind": "street"})
    for x in CROSS_STREET_XS:
        roads.append({"x0": x * CELL_M, "z0": 0.0, "x1": x * CELL_M,
                      "z1": GRID_H * CELL_M, "w": 14.0, "kind": "street"})
    return roads


def build_buildings(rng: random.Random) -> list[dict]:
    """Procedural blocks between road corridors. Deterministic (seeded)."""
    xs = [0.0, *CROSS_STREET_XS, float(GRID_W)]
    ys = [0.0, AVENUE_Y, float(GRID_H)]
    shelter_cells = set(SHELTER_CELLS.values())
    buildings: list[dict] = []
    margin = 9.0  # set back from road centerlines (m)
    for xi in range(len(xs) - 1):
        for yi in range(len(ys) - 1):
            bx0 = xs[xi] * CELL_M + margin
            bx1 = xs[xi + 1] * CELL_M - margin
            bz0 = ys[yi] * CELL_M + margin
            bz1 = ys[yi + 1] * CELL_M - margin
            block_w, block_d = bx1 - bx0, bz1 - bz0
            if block_w < 30 or block_d < 30:
                continue
            # Subdivide each block into a small jittered grid of parcels.
            nx = max(1, int(block_w // 55))
            nz = max(1, int(block_d // 55))
            pw, pd = block_w / nx, block_d / nz
            for px in range(nx):
                for pz in range(nz):
                    if rng.random() < 0.12:  # leave some open lots / plazas
                        continue
                    w = pw * rng.uniform(0.55, 0.85)
                    d = pd * rng.uniform(0.55, 0.85)
                    x = bx0 + px * pw + (pw - w) * rng.uniform(0.2, 0.8)
                    z = bz0 + pz * pd + (pd - d) * rng.uniform(0.2, 0.8)
                    cx, cz = x + w / 2, z + d / 2
                    cell = (int(cx // CELL_M), int(cz // CELL_M))
                    if cell in shelter_cells:
                        continue  # shelters get dedicated geometry
                    # Taller toward the center of the scene, Nihonbashi-style
                    # mid/high-rise mix along the avenue.
                    center_bias = 1.0 - abs(cx - GRID_W * CELL_M / 2) / (GRID_W * CELL_M / 2)
                    avenue_bias = 1.0 - min(1.0, abs(cz - AVENUE_Y * CELL_M) / 150.0)
                    base = 10 + 55 * center_bias * rng.random() + 45 * avenue_bias * rng.random()
                    h = round(min(95.0, max(8.0, rng.gauss(base, 9.0))), 1)
                    kind = "tower" if h > 55 else ("midrise" if h > 22 else "lowrise")
                    buildings.append({"x": round(x, 1), "z": round(z, 1),
                                      "w": round(w, 1), "d": round(d, 1),
                                      "h": h, "kind": kind})
    return buildings


def load_agents_csv() -> dict[str, dict[str, list]]:
    """agents.csv -> {scenario: {agent_id: [(hour, cx, cy, status, vuln), ...]}}"""
    per_scenario: dict[str, dict[str, list]] = {s: defaultdict(list) for s in SCENARIOS}
    with open(OUT_ROOT / "timeseries" / "agents.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            per_scenario[row["scenario"]][row["agent_id"]].append(
                (int(row["hour"]), int(row["cell_x"]), int(row["cell_y"]),
                 row["status"], float(row["vulnerability_score"]))
            )
    return per_scenario


def load_profiles() -> dict[str, dict]:
    profiles: dict[str, dict] = {}
    with open(OUT_ROOT / "timeseries" / "population.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            profiles.setdefault(row["agent_id"], {
                "age": row["age_bucket"],
                "mobility": row["mobility_class"],
                "vuln": float(row["vulnerability_score"]),
            })
    return profiles


def load_metrics() -> dict[str, dict[str, float]]:
    metrics: dict[str, dict[str, float]] = {s: {} for s in SCENARIOS}
    with open(OUT_ROOT / "timeseries" / "metrics.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("hour"):
                continue  # headline metrics only
            metrics[row["scenario"]][row["metric_name"]] = round(float(row["value"]), 4)
    return metrics


def load_shelter_occupancy(scenario: str) -> dict[str, list[int]]:
    path = OUT_ROOT / "geo" / f"shelters_{scenario}.geojson"
    occupancy: dict[str, list[int]] = {}
    with open(path) as fh:
        geo = json.load(fh)
    for feat in geo["features"]:
        props = feat["properties"]
        cur = props.get("current_occupants_by_hour", {})
        cap = props.get("max_occupants_by_hour", {})
        occupancy[props["building_id"]] = {
            "occupants": [int(cur.get(str(h), 0)) for h in range(24)],
            "capacity": [int(cap.get(str(h), 0)) for h in range(24)],
        }
    return occupancy


def load_dispatch_tasks() -> dict[str, dict[int, list[dict]]]:
    """provenance.jsonl -> {scenario: {hour: [route_to_shelter decisions]}}"""
    tasks: dict[str, dict[int, list[dict]]] = {s: defaultdict(list) for s in SCENARIOS}
    path = OUT_ROOT / "reports" / "provenance.jsonl"
    if not path.exists():
        return tasks
    with open(path) as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("decision") not in ("route_to_shelter", "preposition_to_shelter"):
                continue
            scen = rec.get("scenario")
            if scen in tasks:
                tasks[scen][int(rec["hour"])].append(rec)
    return tasks


def build_robot_tracks(scenario: str, agent_tracks: dict[str, list],
                       dispatch: dict[int, list[dict]]) -> list[dict]:
    """Derive support-robot tracks from the sim's shelter-routing decisions.

    Robots are the visual stand-in for the Nihonbashi Heat-Support Robot:
    each hour, route_to_shelter decisions become escort tasks assigned
    round-robin to a small fleet based at the three shelters. Positions are
    rendered, not simulated — Stage Two replaces this with cuOpt dispatch.
    """
    shelter_ids = list(SHELTER_CELLS)
    bases = [SHELTER_CELLS[shelter_ids[i % len(shelter_ids)]] for i in range(NUM_ROBOTS)]
    # Index agent cell by hour for pickup locations.
    agent_cell_at = {
        aid: {h: (cx, cy) for (h, cx, cy, _s, _v) in rows}
        for aid, rows in agent_tracks.items()
    }
    robots = [{"id": f"r{i:02d}", "base": list(bases[i]), "cells": []}
              for i in range(NUM_ROBOTS)]
    for hour in range(24):
        jobs = dispatch.get(hour, [])
        assigned: dict[int, tuple[int, int]] = {}
        for j, job in enumerate(jobs):
            pickup = agent_cell_at.get(job.get("agent_id"), {}).get(hour)
            if pickup is not None:
                assigned.setdefault(j % NUM_ROBOTS, pickup)
        for i, rob in enumerate(robots):
            cell = assigned.get(i, tuple(bases[i]))
            busy = 1 if i in assigned else 0
            rob["cells"].append([cell[0], cell[1], busy])
    return robots


def export_scenario(scenario: str, agents: dict[str, list], profiles: dict,
                    heat, metrics: dict, dispatch: dict[int, list[dict]]) -> None:
    agent_payload = []
    for aid in sorted(agents):
        rows = sorted(agents[aid])
        prof = profiles.get(aid, {})
        agent_payload.append({
            "id": aid,
            "vuln": round(prof.get("vuln", rows[0][4]), 3),
            "age": prof.get("age", "adult"),
            "mobility": prof.get("mobility", "mobile"),
            "cells": [[cx, cy, STATUS_CODES.get(status, 0)]
                      for (_h, cx, cy, status, _v) in rows],
        })
    payload = {
        "scenario": scenario,
        "hours": 24,
        "epoch": "2026-05-25T00:00:00Z",
        "heat": [[[round(float(heat[h, x, y]), 3) for y in range(GRID_H)]
                  for x in range(GRID_W)] for h in range(24)],
        "agents": agent_payload,
        "robots": build_robot_tracks(scenario, agents, dispatch),
        "shelters": load_shelter_occupancy(scenario),
        "metrics": metrics.get(scenario, {}),
    }
    out = TWIN_DIR / f"frames_{scenario}.json"
    out.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"  wrote {out.relative_to(ROOT)}  "
          f"({len(agent_payload)} agents, {NUM_ROBOTS} robots)")


def main() -> None:
    TWIN_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(17)

    shelters = []
    for sid, (cx, cy) in SHELTER_CELLS.items():
        x, z = cell_to_m(cx, cy)
        shelters.append({"id": sid, "x": round(x, 1), "z": round(z, 1),
                         "w": 34.0, "d": 30.0, "h": 14.0})
    scene = {
        "grid": {"w": GRID_W, "h": GRID_H, "cell_m": CELL_M,
                 "anchor_lat": ANCHOR_LAT, "anchor_lng": ANCHOR_LNG},
        "extent_m": [GRID_W * CELL_M, GRID_H * CELL_M],
        "roads": build_roads(),
        "buildings": build_buildings(rng),
        "shelters": shelters,
        "avenue_y": AVENUE_Y,
    }
    (TWIN_DIR / "scene.json").write_text(json.dumps(scene, separators=(",", ":")))
    print(f"  wrote outputs/twin/scene.json ({len(scene['buildings'])} buildings)")

    heat = build_heat_field()
    agents_by_scenario = load_agents_csv()
    profiles = load_profiles()
    metrics = load_metrics()
    dispatch = load_dispatch_tasks()
    for scenario in SCENARIOS:
        export_scenario(scenario, agents_by_scenario[scenario], profiles,
                        heat, metrics, dispatch[scenario])
    print("Twin export complete. Serve with scripts/serve_outputs.py and open "
          "http://localhost:8889/twin_view.html")


if __name__ == "__main__":
    main()
