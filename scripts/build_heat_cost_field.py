"""Build the heat-cost field for ABM edges.

Pulls per-parcel heat-scenario labels from the parent Tokyo Studio repo,
joins onto OSM sidewalk segments, writes an edge-attribute CSV consumed
by the SUMO/ABM bridge.

Owner: Sam. Stub — flesh out once Phase 1 scene is locked.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd


HEAT_FACTORS = {
    "cool_baseline": 0.0,
    "moderate": 0.5,
    "high": 1.0,
    "extreme": 1.5,
}


def build_heat_cost(
    sidewalk_gdf: gpd.GeoDataFrame,
    parcel_heat_gdf: gpd.GeoDataFrame,
    base_cost_col: str = "length_m",
) -> pd.DataFrame:
    """Spatial-join parcel heat labels onto sidewalk segments and compute
    a heat-weighted cost per segment.
    """
    if sidewalk_gdf.crs != parcel_heat_gdf.crs:
        parcel_heat_gdf = parcel_heat_gdf.to_crs(sidewalk_gdf.crs)

    sidewalk_centroids = sidewalk_gdf.copy()
    sidewalk_centroids["geometry"] = sidewalk_gdf.geometry.centroid

    joined = gpd.sjoin(
        sidewalk_centroids,
        parcel_heat_gdf[["heat_scenario", "geometry"]],
        how="left",
        predicate="within",
    )
    joined["heat_scenario"] = joined["heat_scenario"].fillna("cool_baseline")
    joined["heat_factor"] = joined["heat_scenario"].map(HEAT_FACTORS)
    joined["heat_cost"] = joined[base_cost_col] * (1.0 + joined["heat_factor"])

    return joined[["edge_id", "heat_scenario", "heat_factor", "heat_cost"]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sidewalks", type=Path, required=True)
    parser.add_argument("--parcel-heat", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    sidewalks = gpd.read_file(args.sidewalks)
    parcels = gpd.read_file(args.parcel_heat)
    out = build_heat_cost(sidewalks, parcels)
    out.to_csv(args.out, index=False)
    print(f"wrote {len(out)} segments to {args.out}")


if __name__ == "__main__":
    main()
