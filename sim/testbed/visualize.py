"""Folium HTML twin (the headline 5/25 visual) + matplotlib diagnostic charts."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import folium
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from folium.plugins import MarkerCluster

from .scene import GRID_X, GRID_Y, LAT_MAX, LAT_MIN, LON_MAX, LON_MIN, Shelter, cell_polygon, cell_to_latlon


HEAT_COLOR = {
    "cool":    "#2c7bb6",
    "warm":    "#ffffbf",
    "hot":     "#fdae61",
    "extreme": "#d7191c",
}


def _bucket(v: float) -> str:
    if v < 0.4:
        return "cool"
    if v < 0.9:
        return "warm"
    if v < 1.4:
        return "hot"
    return "extreme"


def build_browser_twin(
    heat_field: np.ndarray,
    shelters: List[Shelter],
    snapshots: Dict[str, pd.DataFrame],
    headline_hour: int,
    out_path: str | Path,
) -> None:
    """Folium map: heat polygons (headline hour) + shelter footprints + per-scenario agent layers."""
    center = ((LAT_MIN + LAT_MAX) / 2.0, (LON_MIN + LON_MAX) / 2.0)
    m = folium.Map(location=center, zoom_start=18, tiles="CartoDB positron", control_scale=True)

    folium.Rectangle(
        bounds=[(LAT_MIN, LON_MIN), (LAT_MAX, LON_MAX)],
        color="#444", weight=2, fill=False,
        tooltip="Nihonbashi 200m segment (study area)",
    ).add_to(m)

    heat_layer = folium.FeatureGroup(name=f"Heat field h={headline_hour:02d}:00", show=True)
    for ix in range(GRID_X):
        for iy in range(GRID_Y):
            poly = cell_polygon(ix, iy)
            val = float(heat_field[headline_hour, ix, iy])
            coords = [(y, x) for x, y in list(poly.exterior.coords)]
            folium.Polygon(
                locations=coords,
                color=None,
                fill=True,
                fill_color=HEAT_COLOR[_bucket(val)],
                fill_opacity=0.55,
                weight=0,
                tooltip=f"cell ({ix},{iy}) heat={val:.2f}",
            ).add_to(heat_layer)
    heat_layer.add_to(m)

    shelter_layer = folium.FeatureGroup(name="Shelters (G2 envelope)", show=True)
    for sh in shelters:
        coords = [(y, x) for x, y in list(sh.footprint.exterior.coords)]
        folium.Polygon(
            locations=coords, color="#1a9850", weight=2,
            fill=True, fill_color="#1a9850", fill_opacity=0.45,
            tooltip=f"{sh.building_id} (cell {sh.cell})",
        ).add_to(shelter_layer)
        folium.Marker(
            location=(sh.centroid_lat, sh.centroid_lon),
            icon=folium.Icon(color="green", icon="home", prefix="fa"),
            tooltip=sh.building_id,
        ).add_to(shelter_layer)
    shelter_layer.add_to(m)

    scenario_colors = {"baseline": "#999999", "reactive": "#377eb8", "proactive": "#e41a1c"}
    for scenario, df in snapshots.items():
        snap = df[df["hour"] == headline_hour]
        layer = folium.FeatureGroup(name=f"Agents h={headline_hour:02d} ({scenario})",
                                    show=(scenario == "proactive"))
        cluster = MarkerCluster().add_to(layer)
        for _, row in snap.iterrows():
            lat, lon = cell_to_latlon(int(row["cell_x"]), int(row["cell_y"]))
            in_shelter = int(row["in_shelter"]) == 1
            vuln = float(row["vulnerability_score"])
            r = 3 + 5 * vuln
            color = "#1a9850" if in_shelter else scenario_colors[scenario]
            folium.CircleMarker(
                location=(lat, lon),
                radius=r,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                weight=1,
                tooltip=(f"agent {int(row['agent_id'])} | {scenario} | "
                         f"vuln={vuln:.2f} | heat={float(row['raw_heat']):.2f} | "
                         f"exposure={float(row['effective_exposure']):.2f} | "
                         f"{'SHELTERED' if in_shelter else 'EXPOSED'}"),
            ).add_to(cluster)
        layer.add_to(m)

    legend_html = """
    <div style='position: fixed; bottom: 24px; left: 24px; z-index: 9999;
                background: white; padding: 10px 12px; border: 1px solid #888;
                font-family: sans-serif; font-size: 12px; line-height: 1.4;'>
      <strong>Group 3 Nihonbashi twin — Stage One 5/25</strong><br>
      Heat: <span style='color:#2c7bb6'>cool</span>
            <span style='color:#ffffbf;background:#888'>&nbsp;warm&nbsp;</span>
            <span style='color:#fdae61'>hot</span>
            <span style='color:#d7191c'>extreme</span><br>
      Agent dot size ∝ vulnerability_score. Green = sheltered.<br>
      Toggle scenarios with the layer control (top right).
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl(collapsed=False).add_to(m)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    m.save(str(out_path))


def plot_metric_comparison(metrics_df: pd.DataFrame, out_path: str | Path) -> None:
    cols = [
        "cumulative_population_exposure",
        "vulnerability_weighted_exposure",
        "mean_peak_hourly_exposure",
        "sheltered_agent_hours",
        "shelter_utilization_rate",
        "unmet_shelter_demand",
        "cooling_energy_kwh",
        "cooling_emissions_kgco2e",
        "equity_gap_ratio",
    ]
    fig, axes = plt.subplots(3, 3, figsize=(13, 9))
    axes = axes.ravel()
    palette = {"baseline": "#999999", "reactive": "#377eb8", "proactive": "#e41a1c"}
    for ax, col in zip(axes, cols):
        vals = [metrics_df.loc[metrics_df["scenario"] == s, col].iloc[0]
                for s in ["baseline", "reactive", "proactive"]]
        ax.bar(["baseline", "reactive", "proactive"], vals,
               color=[palette[s] for s in ["baseline", "reactive", "proactive"]])
        ax.set_title(col, fontsize=10)
        ax.tick_params(axis="x", labelsize=8)
        ax.tick_params(axis="y", labelsize=8)
    plt.suptitle("9 outcome metrics — Stage One testbed", fontsize=13)
    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_equity_breakdown(per_scenario_exposure: Dict[str, pd.DataFrame], out_path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    quartile_labels = ["Q1 (least vuln)", "Q2", "Q3", "Q4 (most vuln)"]
    palette = {"baseline": "#999999", "reactive": "#377eb8", "proactive": "#e41a1c"}
    width = 0.26
    x = np.arange(4)
    for i, (scenario, df) in enumerate(per_scenario_exposure.items()):
        per_agent = df.groupby(["agent_id", "vulnerability_score"])\
            ["effective_exposure"].sum().reset_index()
        per_agent["q"] = pd.qcut(per_agent["vulnerability_score"], 4, labels=False, duplicates="drop")
        vals = per_agent.groupby("q")["effective_exposure"].mean().values
        if len(vals) < 4:
            vals = np.concatenate([vals, np.zeros(4 - len(vals))])
        ax.bar(x + (i - 1) * width, vals, width, label=scenario, color=palette.get(scenario, "#777"))
    ax.set_xticks(x)
    ax.set_xticklabels(quartile_labels)
    ax.set_ylabel("Mean cumulative effective exposure per agent")
    ax.set_title("Equity breakdown by vulnerability quartile")
    ax.legend()
    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_exposure_timeline(per_scenario_exposure: Dict[str, pd.DataFrame], out_path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    palette = {"baseline": "#999999", "reactive": "#377eb8", "proactive": "#e41a1c"}
    for scenario, df in per_scenario_exposure.items():
        hourly = df.groupby("hour")["effective_exposure"].sum()
        ax.plot(hourly.index, hourly.values, label=scenario,
                color=palette.get(scenario, "#777"), linewidth=2.2)
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Total effective exposure (all agents)")
    ax.set_title("24h exposure timeline by scenario")
    ax.set_xticks(range(0, 24, 2))
    ax.grid(alpha=0.3)
    ax.legend()
    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=130)
    plt.close(fig)
