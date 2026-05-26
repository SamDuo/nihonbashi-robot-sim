"""Stage One Streamlit dashboard. Urban Digital Twins, Nihonbashi.

Four tabs:
  Digital Twin       CesiumJS view of PLATEAU buildings, shelters, agents.
                     2D Folium fallback in an expander.
  Metrics            scenario comparison. Six methodology metrics, exposure timeline.
  Architecture       inline Mermaid renders of the 5 system design diagrams.
  Re:Earth handoff   file paths and Re:Earth setup checklist.

Run:
    python -m streamlit run analysis/dashboard.py
"""
from __future__ import annotations

import json
from pathlib import Path

import folium
import pandas as pd
import pydeck as pdk
import streamlit as st
from streamlit.components.v1 import html as st_html
from streamlit.components.v1 import iframe as st_iframe

ROOT = Path(__file__).resolve().parents[1]
TS = ROOT / "outputs" / "timeseries"
GEO = ROOT / "outputs" / "geo"
REP = ROOT / "outputs" / "reports"
DIAG = ROOT / "docs" / "diagrams"

NIHONBASHI = {"lat": 35.6845, "lng": 139.7740}
SCENARIO_ORDER = ["baseline", "reactive", "proactive"]
STATUS_RGB = {
    "sheltering": [44, 127, 184],
    "working":    [230, 85, 13],
    "home":       [127, 127, 127],
}
STATUS_HEX = {k: "#%02x%02x%02x" % tuple(v) for k, v in STATUS_RGB.items()}

# PLATEAU Chuo-ku (中央区) LOD2 building tilesets (Project PLATEAU, MLIT 2023 FY).
PLATEAU_TILESETS = {
    "Off": None,
    "Volumes (LOD2 no-texture, fast)":
        "https://assets.cms.plateau.reearth.io/assets/4c/f2436a-e2be-40e2-83da-f1781f36e30b/"
        "13102_chuo-ku_pref_2023_citygml_1_op_bldg_3dtiles_13102_chuo-ku_lod2_no_texture/tileset.json",
    "Textured (LOD2 photographic, heavier)":
        "https://assets.cms.plateau.reearth.io/assets/01/8c112f-4957-409a-9b43-d86308c7b74a/"
        "13102_chuo-ku_pref_2023_citygml_1_op_bldg_3dtiles_13102_chuo-ku_lod2/tileset.json",
}

st.set_page_config(page_title="Urban Digital Twins · Nihonbashi", layout="wide")

# ---------- data ----------

@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict, dict, dict, pd.DataFrame]:
    agents = pd.read_csv(TS / "agents.csv")
    metrics = pd.read_csv(TS / "metrics.csv")
    shelters_by_scenario = {
        s: json.loads((GEO / f"shelters_{s}.geojson").read_text(encoding="utf-8"))
        for s in SCENARIO_ORDER
    }
    residuals = pd.read_csv(REP / "cooling_gap_residuals.csv")
    diagrams = {p.stem: p.read_text(encoding="utf-8") for p in sorted(DIAG.glob("*.mmd"))}
    return agents, metrics, shelters_by_scenario, diagrams, {}, residuals


# ---------- 3D twin via CesiumJS ----------

CESIUM_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8">
<link rel="stylesheet"
      href="https://cesium.com/downloads/cesiumjs/releases/1.123/Build/Cesium/Widgets/widgets.css">
<script src="https://cesium.com/downloads/cesiumjs/releases/1.123/Build/Cesium/Cesium.js"></script>
<style>
  html, body, #cesium { margin:0; padding:0; height:100vh; width:100%;
                        font-family:-apple-system, BlinkMacSystemFont, sans-serif; }
  .cesium-viewer-bottom { display:none; }
  #status {
    position:fixed; top:8px; left:8px; max-width:480px;
    background:rgba(0,0,0,0.78); color:white; padding:8px 12px;
    border-radius:6px; font-size:12px; line-height:1.5; z-index:1000;
    white-space:pre-line;
  }
  .ok  { background: rgba(40,130,40,0.85) !important; }
  .err { background: rgba(180,40,40,0.90) !important; }
</style></head>
<body>
<div id="cesium"></div>
<div id="status">Loading Cesium</div>
<script>
const STATUS = document.getElementById('status');
function setStatus(msg, cls) {
  STATUS.textContent = msg;
  STATUS.className = cls || '';
}

(async () => {
  try {
    Cesium.Ion.defaultAccessToken = '';

    setStatus('Creating OpenStreetMap imagery layer');
    const baseLayer = new Cesium.ImageryLayer(new Cesium.OpenStreetMapImageryProvider({
      url: 'https://tile.openstreetmap.org/'
    }));

    setStatus('Constructing viewer');
    const viewer = new Cesium.Viewer('cesium', {
      baseLayer,
      baseLayerPicker: false, geocoder: false, homeButton: false,
      sceneModePicker: false, navigationHelpButton: false,
      timeline: false, animation: false, fullscreenButton: false,
      infoBox: true, selectionIndicator: true
    });
    viewer.scene.skyBox = undefined;
    viewer.scene.skyAtmosphere = undefined;

    viewer.camera.setView({
      destination: Cesium.Cartesian3.fromDegrees(139.7740, 35.6835, 1200),
      orientation: {
        heading: Cesium.Math.toRadians(20),
        pitch:   Cesium.Math.toRadians(-40),
        roll:    0
      }
    });

    const PLATEAU_URL = __PLATEAU_URL__;
    if (PLATEAU_URL) {
      setStatus('Loading PLATEAU buildings');
      try {
        const tileset = await Cesium.Cesium3DTileset.fromUrl(PLATEAU_URL, {
          maximumScreenSpaceError: 24
        });
        viewer.scene.primitives.add(tileset);
        await viewer.zoomTo(tileset, new Cesium.HeadingPitchRange(
          Cesium.Math.toRadians(20),
          Cesium.Math.toRadians(-40),
          900
        ));
        tileset.allTilesLoaded.addEventListener(() => {
          setStatus('PLATEAU buildings rendered', 'ok');
        });
        tileset.tileFailed.addEventListener(e => {
          setStatus('Tile failed. ' + (e.message || e.url || ''), 'err');
        });
        setStatus('PLATEAU streaming. Tiles arrive progressively.', 'ok');
      } catch (err) {
        setStatus('PLATEAU failed. ' + (err.message || err), 'err');
        console.error(err);
      }
    } else {
      setStatus('PLATEAU disabled. Showing OSM and agents only.', 'ok');
    }

    const shelters = __SHELTERS_JSON__;
    const HOUR = __HOUR__;
    shelters.features.forEach(f => {
      const flat = [];
      f.geometry.coordinates[0].forEach(([lng, lat]) => { flat.push(lng); flat.push(lat); });
      const occ = f.properties.current_occupants_by_hour[String(HOUR)] || 0;
      const cap = f.properties.max_occupants_by_hour[String(HOUR)] || 1;
      const util = cap > 0 ? occ / cap : 0;
      const height = 6 + 0.6 * occ;
      const r = Math.round(26 + 200 * util);
      const g = Math.round(152 - 80 * util);
      const b = Math.round(80 - 60 * util);
      viewer.entities.add({
        name: f.properties.building_id,
        description: 'Building ' + f.properties.building_id +
                     '. Occupancy ' + occ + ' of ' + cap + '.',
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArray(flat),
          material: Cesium.Color.fromBytes(r, g, b, 220),
          extrudedHeight: height,
          outline: true,
          outlineColor: Cesium.Color.fromCssColorString('#0e3b14')
        }
      });
    });

    const agents = __AGENTS_JSON__;
    const STATUS_COLOR = {
      sheltering: Cesium.Color.fromBytes(44, 127, 184),
      working:    Cesium.Color.fromBytes(230, 85, 13),
      home:       Cesium.Color.fromBytes(127, 127, 127)
    };
    agents.forEach(a => {
      viewer.entities.add({
        name: a.agent_id,
        description: 'Agent ' + a.agent_id +
                     '. Status ' + a.status +
                     '. Vulnerability ' + a.vulnerability_score.toFixed(2) + '.',
        position: Cesium.Cartesian3.fromDegrees(a.lng, a.lat, 2),
        point: {
          color: STATUS_COLOR[a.status] || Cesium.Color.BLACK,
          pixelSize: 6 + 10 * a.vulnerability_score,
          outlineColor: Cesium.Color.WHITE,
          outlineWidth: 1,
          heightReference: Cesium.HeightReference.RELATIVE_TO_GROUND
        }
      });
    });

  } catch (e) {
    setStatus('Cesium failed. ' + (e.message || e), 'err');
    console.error(e);
  }
})();
</script>
</body></html>
"""


def build_cesium_html(
    agents: pd.DataFrame,
    shelters_geo: dict,
    hour: int,
    scenario: str,
    plateau_url: str | None,
) -> str:
    snap = agents[(agents["hour"] == hour) & (agents["scenario"] == scenario)]
    rows = snap[["agent_id", "lat", "lng", "status", "vulnerability_score"]].to_dict(orient="records")
    return (
        CESIUM_TEMPLATE
        .replace("__PLATEAU_URL__", json.dumps(plateau_url))
        .replace("__SHELTERS_JSON__", json.dumps(shelters_geo))
        .replace("__HOUR__", str(int(hour)))
        .replace("__AGENTS_JSON__", json.dumps(rows))
    )


# ---------- pydeck (kept as offline fallback) ----------

def build_pydeck(
    agents: pd.DataFrame,
    shelters_geo: dict,
    hour: int,
    scenario: str,
    plateau_url: str | None = None,
) -> pdk.Deck:
    polygons = []
    for feat in shelters_geo["features"]:
        props = feat["properties"]
        cur = props["current_occupants_by_hour"].get(str(hour), 0)
        cap = props["max_occupants_by_hour"].get(str(hour), 0)
        util = cur / cap if cap else 0.0
        polygons.append({
            "polygon": feat["geometry"]["coordinates"][0],
            "name": props["building_id"],
            "current": cur,
            "max": cap,
            "elevation": 4.0 + 0.45 * cur,
            "fill": [
                int(26 + 200 * util),
                int(152 - 80 * util),
                int(80 - 60 * util),
                200,
            ],
        })

    snap = agents[(agents["hour"] == hour) & (agents["scenario"] == scenario)].copy()
    snap["color"] = snap["status"].map(lambda s: STATUS_RGB.get(s, [0, 0, 0]))
    snap["radius_m"] = 1.2 + 1.6 * snap["vulnerability_score"]

    shelter_layer = pdk.Layer(
        "PolygonLayer",
        data=polygons,
        get_polygon="polygon",
        get_elevation="elevation",
        get_fill_color="fill",
        get_line_color=[20, 60, 20, 255],
        line_width_min_pixels=1,
        extruded=True,
        wireframe=True,
        pickable=True,
        auto_highlight=True,
    )

    agent_layer = pdk.Layer(
        "ScatterplotLayer",
        data=snap,
        get_position=["lng", "lat"],
        get_fill_color="color",
        get_radius="radius_m",
        radius_min_pixels=3,
        radius_max_pixels=14,
        pickable=True,
        auto_highlight=True,
        opacity=0.85,
    )

    layers: list[pdk.Layer] = []
    if plateau_url:
        layers.append(pdk.Layer(
            "Tile3DLayer",
            data=plateau_url,
            pickable=False,
            opacity=0.85,
        ))
    layers.extend([shelter_layer, agent_layer])

    return pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(
            latitude=NIHONBASHI["lat"],
            longitude=NIHONBASHI["lng"],
            zoom=17.2,
            pitch=55,
            bearing=20,
        ),
        map_style="light",
        tooltip={
            "html": "<b>{name}</b><br/>occupancy: {current}/{max}<br/>"
                     "<b>{agent_id}</b> · {status} · vuln {vulnerability_score}",
            "style": {"backgroundColor": "rgba(20,20,20,0.85)", "color": "white"},
        },
    )


def build_folium(agents: pd.DataFrame, shelters_geo: dict, hour: int, scenario: str) -> str:
    fmap = folium.Map(
        location=[NIHONBASHI["lat"], NIHONBASHI["lng"]],
        zoom_start=18,
        tiles="cartodbpositron",
    )
    folium.GeoJson(
        shelters_geo,
        style_function=lambda _f: {
            "fillColor": "#1a9850", "color": "#1a9850",
            "weight": 2, "fillOpacity": 0.35,
        },
        tooltip=folium.GeoJsonTooltip(fields=["building_id"]),
    ).add_to(fmap)
    snap = agents[(agents["hour"] == hour) & (agents["scenario"] == scenario)]
    for _, row in snap.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=4 + 4 * float(row["vulnerability_score"]),
            color=STATUS_HEX.get(row["status"], "#000"),
            weight=1,
            fill=True,
            fill_opacity=0.85,
            popup=(
                f"{row['agent_id']} | {row['status']} | "
                f"vuln={row['vulnerability_score']:.2f}"
            ),
        ).add_to(fmap)
    return fmap.get_root().render()


# ---------- metrics ----------

def headline(metrics: pd.DataFrame) -> None:
    cols = st.columns(3)
    for col, scenario in zip(cols, SCENARIO_ORDER):
        sl = metrics[
            (metrics["scenario"] == scenario)
            & (metrics["metric_name"] == "cooling_gap_closure_rate")
            & metrics["hour"].isna()
        ]
        if not len(sl):
            continue
        col.metric(f"{scenario.title()} — cooling gap closure", f"{float(sl['value'].iloc[0]):.1%}")


def six_metric_bars(metrics: pd.DataFrame, scenarios: list[str]) -> None:
    keep = [
        "labor_substitution_rate", "heat_exposure_reduction",
        "service_continuity", "delivery_efficiency",
        "pedestrian_interference", "infrastructure_compatibility",
        "cooling_gap_closure_rate", "decision_auditability",
    ]
    scalar = metrics[
        metrics["hour"].isna()
        & metrics["metric_name"].isin(keep)
        & metrics["scenario"].isin(scenarios)
    ]
    wide = scalar.pivot_table(index="metric_name", columns="scenario", values="value")
    if not wide.empty:
        wide = wide[[c for c in SCENARIO_ORDER if c in wide.columns]]
        st.bar_chart(wide)


def hourly_exposure(metrics: pd.DataFrame, scenarios: list[str]) -> None:
    ex = metrics[
        (metrics["metric_name"] == "hourly_mean_cumulative_exposure")
        & metrics["hour"].notna()
        & metrics["scenario"].isin(scenarios)
    ].copy()
    ex["hour"] = ex["hour"].astype(int)
    wide = ex.pivot_table(index="hour", columns="scenario", values="value")
    if not wide.empty:
        wide = wide[[c for c in SCENARIO_ORDER if c in wide.columns]]
        st.line_chart(wide)


# ---------- mermaid ----------

MERMAID_TEMPLATE = """
<div style="font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background:white; padding:8px;">
  <pre class="mermaid" style="background:white;">__CONTENT__</pre>
</div>
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
  mermaid.initialize({ startOnLoad: true, theme: "default", securityLevel: "loose",
                       flowchart: { useMaxWidth: true, htmlLabels: true } });
</script>
"""


def render_mermaid(content: str, height: int = 540) -> None:
    st_html(MERMAID_TEMPLATE.replace("__CONTENT__", content), height=height, scrolling=True)


# ---------- main ----------

def main() -> None:
    st.title("Urban Digital Twins — Nihonbashi · Stage One Testbed")
    st.caption(
        "Synthetic 20×10 Nihonbashi grid · 100 agents · 24 hours · three policies "
        "(baseline / reactive / proactive). Same outputs feed Re:Earth's 3D PLATEAU twin."
    )

    agents, metrics, shelters_by_scenario, diagrams, _, residuals = load_data()

    tab_twin, tab_metrics = st.tabs(["🌐 Digital Twin", "📊 Metrics"])

    # ------ Digital Twin ------
    with tab_twin:
        left, right = st.columns([1, 2.6])
        with left:
            scenario_pick = st.radio("Scenario", SCENARIO_ORDER, index=2, key="twin_sc")
            hour = st.slider("Hour of day", 0, 23, 14, key="twin_hr")
            plateau_label = st.radio(
                "PLATEAU 3D buildings (Chuo-ku)",
                list(PLATEAU_TILESETS.keys()),
                index=1,
                key="twin_plateau",
                help="MLIT Project PLATEAU 2023 fiscal-year LOD2 tileset for 中央区. "
                     "Streams from Google Cloud Storage; first load may take ~10s.",
            )
            plateau_url = PLATEAU_TILESETS[plateau_label]
            sl = metrics[
                (metrics["scenario"] == scenario_pick)
                & (metrics["metric_name"] == "cooling_gap_closure_rate")
                & metrics["hour"].isna()
            ]
            if len(sl):
                st.metric(
                    "Cooling gap closure (this scenario)",
                    f"{float(sl['value'].iloc[0]):.1%}",
                )
            snap = agents[(agents["hour"] == hour) & (agents["scenario"] == scenario_pick)]
            st.write("**Status mix at this hour**")
            mix = snap["status"].value_counts()
            for s in ["home", "working", "sheltering"]:
                st.write(
                    f"<span style='color:{STATUS_HEX.get(s,'#000')}'>●</span> "
                    f"{s}: **{int(mix.get(s, 0))}**",
                    unsafe_allow_html=True,
                )
            st.markdown(
                "**Legend**\n"
                "- Green polygons = shelters (height ∝ live occupancy)\n"
                "- Polygon color shifts red as utilization rises\n"
                "- Agent dot color = status, dot size ∝ vulnerability"
            )
        with right:
            plateau_qs = (
                "off" if plateau_url is None
                else "textured" if "no_texture" not in (plateau_url or "")
                else "volumes"
            )
            twin_src = (
                f"http://localhost:8889/cesium_view.html"
                f"?scenario={scenario_pick}&hour={int(hour)}&plateau={plateau_qs}"
            )
            st_iframe(twin_src, height=640, scrolling=False)
            st.caption(
                "Twin served by the local data server at localhost:8889. "
                "Press play in the Cesium animation widget at the bottom left to "
                "watch agents move along streets across the day. "
                f"Open in a new tab: [{twin_src}]({twin_src})"
            )

    # ------ Metrics ------
    with tab_metrics:
        headline(metrics)
        scenarios = st.multiselect(
            "Scenarios", SCENARIO_ORDER, default=SCENARIO_ORDER, key="m_scs",
        )
        st.subheader("Methodology metrics — three scenarios side by side")
        six_metric_bars(metrics, scenarios)

        st.subheader("Hourly mean cumulative heat exposure")
        hourly_exposure(metrics, scenarios)

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Cooling gap residuals — feedback to Urban Regeneration")
            if len(residuals):
                st.dataframe(residuals, use_container_width=True)
            else:
                st.success(
                    "No cooling gap residuals — shelter capacity sufficed for every "
                    "vulnerable agent in this run."
                )
        with col_b:
            st.subheader("Provenance — most recent 25 decisions")
            tail = (REP / "provenance.jsonl").read_text(encoding="utf-8").splitlines()[-25:]
            st.code("\n".join(tail), language="json")

if __name__ == "__main__":
    main()
