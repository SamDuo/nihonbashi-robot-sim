"""GeoJSON exporters for heat field, shelters, and per-scenario agent traces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from shapely.geometry import mapping

from .scene import GRID_X, GRID_Y, Shelter, cell_polygon, cell_to_latlon


def export_heat_field_geojson(field: np.ndarray, hour: int, out_path: str | Path) -> None:
    """Per-cell heat polygons at a given hour as a FeatureCollection."""
    features = []
    for ix in range(GRID_X):
        for iy in range(GRID_Y):
            poly = cell_polygon(ix, iy)
            val = float(field[hour, ix, iy])
            features.append({
                "type": "Feature",
                "geometry": mapping(poly),
                "properties": {
                    "ix": ix, "iy": iy,
                    "hour": hour,
                    "heat_value": round(val, 4),
                    "heat_bucket": _bucket(val),
                },
            })
    fc = {"type": "FeatureCollection", "features": features,
          "metadata": {"crs": "EPSG:4326", "hour": hour, "grid": [GRID_X, GRID_Y]}}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(fc), encoding="utf-8")


def export_shelters_geojson(shelters: List[Shelter], envelope_table: Dict, out_path: str | Path) -> None:
    features = []
    for sh in shelters:
        caps = [envelope_table.get((sh.building_id, h), {}).get("max_occupants", 0) for h in range(24)]
        features.append({
            "type": "Feature",
            "geometry": mapping(sh.footprint),
            "properties": {
                "building_id": sh.building_id,
                "cell_x": sh.cell[0],
                "cell_y": sh.cell[1],
                "centroid_lat": sh.centroid_lat,
                "centroid_lon": sh.centroid_lon,
                "max_occupants_peak": int(max(caps)) if caps else 0,
                "max_occupants_offhours": int(min(caps)) if caps else 0,
            },
        })
    fc = {"type": "FeatureCollection", "features": features,
          "metadata": {"crs": "EPSG:4326", "n_shelters": len(shelters)}}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(fc), encoding="utf-8")


def export_agents_geojson(exposure_df: pd.DataFrame, hour: int, out_path: str | Path, scenario: str) -> None:
    """Snapshot of every agent at the given hour as Point features."""
    snap = exposure_df[exposure_df["hour"] == hour]
    features = []
    for _, row in snap.iterrows():
        lat, lon = cell_to_latlon(int(row["cell_x"]), int(row["cell_y"]))
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "agent_id": int(row["agent_id"]),
                "scenario": scenario,
                "hour": int(row["hour"]),
                "vulnerability_score": float(row["vulnerability_score"]),
                "age_bucket": row["age_bucket"],
                "raw_heat": float(row["raw_heat"]),
                "effective_exposure": float(row["effective_exposure"]),
                "in_shelter": int(row["in_shelter"]),
                "shelter_building_id": row["shelter_building_id"] or None,
            },
        })
    fc = {"type": "FeatureCollection", "features": features,
          "metadata": {"crs": "EPSG:4326", "scenario": scenario, "hour": hour,
                       "n_agents": len(features)}}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(fc), encoding="utf-8")


def _bucket(v: float) -> str:
    if v < 0.4:
        return "cool"
    if v < 0.9:
        return "warm"
    if v < 1.4:
        return "hot"
    return "extreme"
