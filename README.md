# Nihonbashi Robot Simulation

Urban digital twin for heat-risk-aware service robots in Nihonbashi, Tokyo.

This repository covers **Phases 1–3** of the six-stage research methodology: baseline ABM testing of an existing product (Starship), conceptual design of the Nihonbashi Heat-Support Robot, and a first SUMO/ABM A/B simulation cycle with iterative feedback. Phases 4–6 (AI + CAD optimization, re-validation, Omniverse / Isaac Sim + NVIDIA Smart City AI Blueprint deploy) are planned in [docs/phase4_nvidia_blueprint_plan.md](docs/phase4_nvidia_blueprint_plan.md) and executed in a downstream environment once Phase 3 converges.

---

## Standing

| Stage | Status | Artifacts |
|---|---|---|
| Stage One testbed (Mesa + Shapely + OSM walking network) | ✅ Runnable end-to-end | [sim/testbed/](sim/testbed/), [scripts/run_testbed.py](scripts/run_testbed.py) |
| Streamlit dashboard + PLATEAU Cesium twin | ✅ Runnable locally | [analysis/dashboard.py](analysis/dashboard.py), [outputs/cesium_view.html](outputs/cesium_view.html), [scripts/serve_outputs.py](scripts/serve_outputs.py) |
| High-fidelity WebGL twin (L2: day/night, heat overlay, detection HUD) | ✅ Runnable locally (testbed data) | [outputs/twin_view.html](outputs/twin_view.html), [scripts/export_twin_frames.py](scripts/export_twin_frames.py), [docs/high_fidelity_twin_architecture.md](docs/high_fidelity_twin_architecture.md) |
| Six-metric A/B comparison (baseline / reactive / proactive) | ✅ Synthetic data; ready for real G1/G2 swap | Regenerated into `outputs/timeseries/metrics.csv` |
| System architecture v0.3 + Mermaid diagrams | ✅ Stage One review locked | [docs/system_architecture.md](docs/system_architecture.md), [docs/diagrams/](docs/diagrams/) |
| Phase 4–6 plan (NVIDIA Smart City AI Blueprint mapping) | 🟡 Draft for review | [docs/phase4_nvidia_blueprint_plan.md](docs/phase4_nvidia_blueprint_plan.md) |
| Phase 4 — Omniverse / Cosmos-Transfer rendering + TAO training | ⬜ Pending PACE allocation + LaunchPad access | — |
| Phase 5–6 — Blueprint deploy (RTVI + Behavior Analytics + agents) | ⬜ Pending Phase 4 outputs | — |

---

## Project objective

Validate, through agent-based simulation in a digital-twin Nihonbashi scene, whether a heat-risk-aware service robot reduces human heat exposure and improves service continuity during extreme-heat events without increasing pedestrian friction.

---

## Phases in scope

| Phase | Name | Owner | Output |
|---|---|---|---|
| 1 | Starship Baseline ABM Test | Yi Tai (ABM), Sam (heat-risk layer), Qinghao (thermal theory) | Baseline result set; ranked friction-point list |
| 2 | Nihonbashi Heat-Support Robot Concept + Variable Matrix | Xilin (industrial design), Yi Tai (variables), Sam (data layer) | Variable matrix CSV; concept renders; ABM-readable parameters |
| 3 | Initial SUMO/ABM A/B Simulation + Iteration | Yi Tai (sim), Sam (analysis), Xilin (design feedback) | A/B comparison report; design-requirement update list |

---

## Repository layout

```
nihonbashi-robot-sim/
├── docs/                      Methodology, phase plans, decision log, glossary
├── data/                      Heat risk, pedestrian, network, robot parameters
├── sim/                       SUMO + ABM source and simulation runs
├── analysis/                  Notebooks, metrics, comparison dashboard
├── design/                    Concept, CAD, moodboard
├── outputs/                   Slide decks, reports, figures
└── scripts/                   Pipeline glue scripts
```

See `docs/methodology.md` for the six-stage workflow and `CONTRIBUTING.md` for branch / commit policy.

---

## Quick start

```powershell
git clone https://github.com/SamDuo/nihonbashi-robot-sim.git
cd nihonbashi-robot-sim
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the Stage One Mesa testbed and serve the Streamlit / Cesium digital twin:

```powershell
python scripts/run_testbed.py             # writes outputs/ (CZML, geojson, metrics)
python scripts/export_twin_frames.py      # writes outputs/twin/ (WebGL twin data)
python scripts/serve_outputs.py           # CORS server on :8889 (Cesium + WebGL twins)
python -m streamlit run analysis/dashboard.py    # dashboard on :8501
```

Then open `http://localhost:8501` for the dashboard, hit the Cesium twin at
`http://localhost:8889/cesium_view.html?scenario=proactive&hour=14&plateau=volumes`,
or the high-fidelity WebGL twin at
`http://localhost:8889/twin_view.html?scenario=proactive&hour=13`.

See `docs/phase1_baseline.md` for the run protocol, `docs/methodology.md` for the six-stage workflow,
and `docs/phase4_nvidia_blueprint_plan.md` for the Phase 4–6 deployment plan.

---

## Team and ownership

| Member | Area | Folders |
|---|---|---|
| Xilin Tang | Industrial design, methodology | `design/`, `docs/methodology.md` |
| Yi Tai | ABM / SUMO modeling,  GIS digital-twin orchestration, analysis pipeline | `sim/abm/`, `sim/sumo/`, `analysis/metrics.py` |
| Qinghao | Thermal-risk theory, heat-exposure model | `data/heat_risk/`, heat-science portions of `docs/phase1_baseline.md` |
| Sam Duong | ABM / SUMO modeling, GIS digital-twin orchestration, analysis pipeline | `data/`, `scripts/`, `analysis/`, `outputs/slides/` |

---

## Related repositories

- [`GT-Summer-Tokyo-Studio/2026-Summer-Tokyo-Studio`](https://github.com/GT-Summer-Tokyo-Studio/2026-Summer-Tokyo-Studio) — parent studio repository, hosts GIS layers, route planner, and ArcGIS Online publishing pipeline. This repo consumes its heat-risk GIS outputs.

---

## License

MIT (see `LICENSE`). Research data layers may carry separate licenses — see `data/README.md`.
