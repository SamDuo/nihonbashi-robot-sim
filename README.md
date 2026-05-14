# Nihonbashi Robot Simulation

Urban digital twin for heat-risk-aware service robots in Nihonbashi, Tokyo.

This repository covers **Phases 1–3** of the six-stage research methodology authored by Xilin Tang: baseline ABM testing of an existing product (Starship), conceptual design of the Nihonbashi Heat-Support Robot, and a first SUMO/ABM A/B simulation cycle with iterative feedback. Phases 4–6 (AI + CAD optimization, re-validation, Omniverse / Isaac Sim high-fidelity validation) are tracked here but executed in a downstream repository once Phase 3 converges.

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
git clone <repo-url>
cd nihonbashi-robot-sim
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then read `docs/phase1_baseline.md` to see the current run protocol.

---

## Team and ownership

| Member | Area | Folders |
|---|---|---|
| Xilin Tang | Industrial design, methodology | `design/`, `docs/methodology.md` |
| Yi Tai | ABM / SUMO modeling | `sim/abm/`, `sim/sumo/`, `analysis/metrics.py` |
| Qinghao | Thermal-risk theory, heat-exposure model | `data/heat_risk/`, heat-science portions of `docs/phase1_baseline.md` |
| Sam Duong | GIS digital-twin orchestration, analysis pipeline | `data/`, `scripts/`, `analysis/`, `outputs/slides/` |

---

## Related repositories

- [`GT-Summer-Tokyo-Studio/2026-Summer-Tokyo-Studio`](https://github.com/GT-Summer-Tokyo-Studio/2026-Summer-Tokyo-Studio) — parent studio repository, hosts GIS layers, route planner, and ArcGIS Online publishing pipeline. This repo consumes its heat-risk GIS outputs.

---

## License

MIT (see `LICENSE`). Research data layers may carry separate licenses — see `data/README.md`.
