# Visualization Plan — Stage One Showcase (5/25)

| | |
|---|---|
| **Decision** | Re:Earth (3D twin) + Streamlit (metrics dashboard) |
| **Status** | Locked 2026-05-25 |
| **Replaces** | "Folium + Plotly only" mention in `system_architecture.md` v0.1 |
| **Companion docs** | [system_architecture.md](system_architecture.md) · [system_design_print_prompt.md](system_design_print_prompt.md) |

---

## 1. Why this stack

The showcase has to read as a **digital twin**, not a slide. Three constraints drove the choice:

1. **Real Tokyo geometry, today.** Nihonbashi sits in Chuo Ward, which Japan's MLIT publishes as **PLATEAU 3D Tiles** — free, public, Cesium-compatible. We do not need to model buildings.
2. **No NVIDIA Omniverse, no GPU.** Stage Two will go to Omniverse on GT CURA HPC; Stage One must run in a stakeholder's browser.
3. **Author in hours, not days.** Re:Earth's drag-and-drop authoring (CSV → time-animated points, GeoJSON → polygons, PLATEAU plugin → 3D buildings) compresses the build.

Re:Earth (by Eukarya, Tokyo) is open source, runs on CesiumJS under the hood, ships with a PLATEAU plugin, and supports a **Story Mode** that lets us script a guided walkthrough for the review — Perry / Subhro / Sei get a self-paced tour with one shared link.

Streamlit handles what Re:Earth is bad at: clicking a scenario toggle and immediately seeing the **six-metric comparison** update. Both pieces consume the same simulator output, so the work is not doubled.

---

## 2. Architecture (where Re:Earth + Streamlit fit)

```
                   simulator (Mesa, local Python)
                    |              |              |
        agents.csv  |  shelters.   |   metrics.csv
        (per hour)  |  geojson     |   (per scenario)
                    |              |              |
                    v              v              v
        +---------------------+      +---------------------+
        |  Re:Earth scene     |      |  Streamlit app      |
        |   - PLATEAU 3D      |      |   - scenario toggle |
        |   - heat raster     |      |   - 6-metric bars   |
        |   - agent timeline  |      |   - exposure curve  |
        |   - shelter clicks  |      |   - residuals table |
        |   - story mode      |      |   - provenance tail |
        +----------+----------+      +----------+----------+
                   |                            |
                   v                            v
              public Re:Earth link        localhost:8501
                       \                  /
                        v                v
                  stakeholder browser (5/25)
```

Both panels share the **same CSVs the simulator already needs to emit** — no duplicate work.

---

## 3. Data contracts (what the simulator must emit)

These three artifacts are the only viz inputs.

### 3a. `outputs/timeseries/agents.csv`

| Column | Type | Notes |
|---|---|---|
| `agent_id` | string | matches `population.csv` from Urban Risk |
| `scenario` | enum | `baseline` / `reactive` / `proactive` |
| `hour` | int [0,23] | simulated hour |
| `lat` | float | WGS84 |
| `lng` | float | WGS84 |
| `status` | enum | `home` / `commuting` / `working` / `sheltering` / `dispatched` |
| `vulnerability_score` | float [0,1] | copied from Urban Risk |
| `cumulative_exposure` | float | running heat-cost sum at hour H |

Re:Earth ingests this directly; map `hour` to its time field, color by `status` or `vulnerability_score`.

### 3b. `outputs/timeseries/metrics.csv`

| Column | Type | Notes |
|---|---|---|
| `scenario` | enum | `baseline` / `reactive` / `proactive` |
| `metric_name` | enum | one of the six methodology metrics + 2 twin metrics |
| `value` | float | metric value |
| `hour` | int (nullable) | `null` if metric is end-of-day only |

Streamlit reads this and pivots for the bar chart and timeline.

### 3c. `outputs/geo/shelters.geojson`

GeoJSON FeatureCollection. Each feature is a building polygon with properties:

```json
{
  "building_id": "shelter_03",
  "max_occupants": 120,
  "current_occupants_by_hour": {"0": 0, "1": 0, ..., "14": 87},
  "cooling_kwh_by_hour": {"0": 0, ..., "14": 410},
  "emissions_kgco2e_by_hour": {"0": 0, ..., "14": 168}
}
```

Re:Earth renders these as clickable polygons with a popup pulled from `properties`.

### 3d. Optional — heat layer

Two paths, pick one:

- **Cheap**: write the hourly heat raster to PNG tiles (one per hour, `outputs/geo/heat/h{H}.png`) with a fixed world bounding box, then add as an Image Layer in Re:Earth with time animation.
- **Better**: write a GeoJSON of hex polygons (one feature per cell, value in `properties.heat`) and color in Re:Earth.

Both fit on the existing simulator output path; pick whichever the heat field lands in first.

---

## 4. Re:Earth setup (one-time, ~30 min)

1. Sign in at <https://reearth.io> (free; can also self-host via the Re:Earth Visualizer docker image if data sovereignty matters).
2. Create a new project → name `nihonbashi-stage-one`.
3. Install the **PLATEAU plugin** from the Marketplace.
4. In Layers, add:
   - **PLATEAU Tokyo Chuo Ward** (LOD2 or LOD3) — pick from the plugin's wizard.
   - **Agents** — Add Layer → CSV → paste `agents.csv` URL or upload. Set `lat`/`lng` columns, time field = `hour`, style by `status` or `vulnerability_score`.
   - **Shelters** — Add Layer → GeoJSON → upload `shelters.geojson`. Style polygons by current occupant ratio.
   - **Heat layer** — Add Layer → Image (per-hour PNG) or GeoJSON hex grid.
5. **Story** tab → create a story with these pages:
   - Page 1 — overview camera on Nihonbashi at 06:00, no agents yet.
   - Page 2 — pan in, time animates to 14:00, heat layer brightens.
   - Page 3 — click a shelter, popup visible, occupancy bar.
   - Page 4 — switch scenario layer (baseline → reactive → proactive).
   - Page 5 — final wide shot with the "Cooling Gap closure rate" caption.
6. **Publish** → copy the public link. This is the showcase URL.

---

## 5. Streamlit setup (one-time, ~30 min)

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt   # streamlit + plotly already pinned
```

App skeleton at `analysis/dashboard.py`:

```python
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Nihonbashi Stage One", layout="wide")
st.title("Urban Digital Twins — Stage One testbed")

metrics = pd.read_csv("outputs/timeseries/metrics.csv")
scenarios = st.multiselect(
    "Scenarios", metrics["scenario"].unique().tolist(),
    default=metrics["scenario"].unique().tolist(),
)
view = metrics[metrics["scenario"].isin(scenarios)]

end_of_day = view[view["hour"].isna()]
bar = px.bar(end_of_day, x="metric_name", y="value", color="scenario", barmode="group")
st.plotly_chart(bar, use_container_width=True)

hourly = view.dropna(subset=["hour"])
line = px.line(hourly, x="hour", y="value", color="scenario",
               facet_col="metric_name", facet_col_wrap=3)
st.plotly_chart(line, use_container_width=True)

st.subheader("Residuals")
st.dataframe(pd.read_csv("outputs/reports/cooling_gap_residuals.csv"))
```

Run:

```powershell
streamlit run analysis/dashboard.py
```

Stakeholders open <http://localhost:8501> (or we deploy to Streamlit Community Cloud for a public link — also free).

---

## 6. Showcase script (3 minutes for the 5/25 review)

| Time | Action | Tool | Talking point |
|---|---|---|---|
| 0:00 | Open Re:Earth published link | Re:Earth | "This is Chuo Ward in PLATEAU LOD2 — real Tokyo geometry, no modeling work." |
| 0:30 | Press play | Re:Earth | "Watch agents start commuting at 06:00. Color = vulnerability." |
| 1:00 | Pan to 14:00 | Re:Earth | "Heat layer peaks. In the baseline scenario, agents stay in place." |
| 1:30 | Toggle to reactive | Re:Earth | "Threshold-triggered shelter routing. See the flow into the three shelters." |
| 2:00 | Click a shelter | Re:Earth | "Occupancy popup. Urban Regeneration's cooling envelope says this one tops at 120 occupants." |
| 2:30 | Switch to Streamlit | Streamlit | "Same run, six metrics. Cooling Gap closure rate: baseline 0%, reactive 42%, proactive 68%." |
| 3:00 | Residuals table | Streamlit | "These are the agents and hours where no feasible shelter existed — feedback to Urban Regeneration." |

---

## 7. Fallback ladder (if Re:Earth fails on the day)

1. **Re:Earth slow / login issue** → switch to the Folium 2D map embedded inside the same Streamlit app. The agents.csv and shelters.geojson already work for Folium too (see `analysis/dashboard.py` — add a `folium_static` block).
2. **Streamlit local fails** → fall back to static Plotly HTML written to `outputs/figures/auto/*.html` and open directly in a browser.
3. **All viz fails** → present `outputs/reports/testbed_comparison.md` (markdown comparison table) and the screen-captured Mermaid diagrams from `system_architecture.md`.

The simulator writes its outputs regardless of which layer renders them.

---

## 8. Stage Two upgrade path

When Stage Two starts:

- The same `agents.csv` schema can be replayed inside Omniverse (USD timesample animation).
- The PLATEAU 3D Tiles in Re:Earth become PLATEAU CityGML LOD3 inside Omniverse Kit.
- The Streamlit dashboard is kept — it remains the analytics layer over both Stage One and Stage Two simulator runs.

Nothing in this plan is throwaway.

---

## 9. Open items before 5/25

- [ ] Confirm Re:Earth account + PLATEAU plugin availability (10 min check today).
- [ ] Lock the agents.csv schema with the simulator owner (Sam / Yi Tai).
- [ ] Get one shelter polygon set (even three placeholder polygons works for the demo).
- [ ] Decide heat layer path: image tiles vs hex GeoJSON. Image tiles are faster to author.
- [ ] Pre-record a 30-second screencap of the Re:Earth scene as a hard backup if the live link refuses to load in the review room.
