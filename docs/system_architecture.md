# System Architecture - Group 3 Nihonbashi Digital Twin

**Companion to** `docs/stage1_research_design.md`
**Status:** Draft v0.1 - 2026-05-21

---

## 1. One-paragraph summary

Group 3 is a synthesis layer. It does not generate ground-truth heat exposure (Group 1), and it does not generate building energy or shelter cooling envelopes (Group 2). It ingests those outputs at a documented schema and frequency, drives an agentic decision loop that produces reactive shelter allocations and proactive resource dispatches, and visualizes the loop so stakeholders can interrogate it.

For Stage One (5/25 review), Group 3 runs the loop on synthetic placeholder data that matches the locked G1 and G2 schemas. When the real datasets land, the synthetic generators are swapped for real loaders without changing the rest of the pipeline.

---

## 2. Data-flow diagram

```
+----------------------------------+    +----------------------------------+
|  GROUP 1                         |    |  GROUP 2                         |
|  exposure + vulnerability        |    |  energy + cooling envelope       |
|  - synthetic population          |    |  - N-UBEM cooling demand         |
|  - hourly heat-exposure raster   |    |  - ReOpt energy supply/storage   |
|  - occupancy time-schedule       |    |  - shelter cooling envelope      |
+--------------+-------------------+    +----------------+-----------------+
               |                                         |
        population.csv                            shelter_envelope.csv
        heat_field.npy                            cooling_capacity.csv
        occupancy.csv                             emissions_intensity.csv
               |                                         |
               v                                         v
        +----------------------------------------------------------+
        |  GROUP 3 - Agentic orchestrator + digital twin           |
        |  ingest --> state model --> policy --> actuators         |
        |     ^                          |          |              |
        |     |     provenance log    reactive   proactive         |
        |     |                       allocation  dispatch         |
        |     +----- metric collector <----------+                 |
        +----+-----------------------------------+-----------------+
             |                                                     |
             v                                                     |
        +----------------------------------+                       |
        |  Stakeholder layer               |  feedback to G1/G2 ---+
        |  - matplotlib viz (Stage One)    |  (cooling gap residuals,
        |  - Omniverse twin (Stage Two)    |   policy stress points)
        |  - comparison reports            |
        +----------------------------------+
```

---

## 3. Scene pipeline (uses Yi Tai's SHP -> SUMO work)

```
ArcGIS Pro (Yi)              SUMO netconvert            sim/testbed/scene.py
+----------------+   .shp    +----------------+  .net   +----------------+
| OSM cleanup    | -------> | edges + nodes  | ----->  | grid abstraction|
| route repair   |          | + connections  |         | + shelter nodes |
+----------------+          +----------------+         +----------------+
                                                              |
                                                              v
                                                      synthetic 20x10
                                                      grid for Stage One
                                                      (drop-in real net
                                                       for Stage Two)
```

For Stage One the testbed runs on the synthetic grid. Yi's SHP -> SUMO network plugs in as a scene replacement at Stage Two; the rest of the pipeline does not change.

---

## 4. Interface contracts

### 4a. G1 to G3 contracts

`population.csv` columns: `agent_id`, `age_bucket` (child/adult/elderly), `occupation_class` (worker/commuter/visitor/resident/student), `mobility_class` (mobile/assisted/restricted), `vulnerability_score` in [0,1], `home_grid_cell`, `hour` (0-23), `activity_grid_cell`. One row per agent per hour.

`heat_field.npy`: NumPy array of shape (24, 20, 10) (hours by x by y). Cell value is heat-cost factor in [0, 2].

`occupancy.csv` columns: `building_id`, `hour`, `occupants_total`, `vulnerable_weighted_occupants`.

### 4b. G2 to G3 contracts

`shelter_envelope.csv` columns: `building_id`, `hour`, `max_occupants`, `cooling_kwh`, `emissions_intensity` (kgCO2e/kWh).

### 4c. G3 to stakeholders contracts

- `outputs/reports/testbed_comparison.md` - comparison report
- `outputs/figures/auto/*.png` - matplotlib snapshots and metric charts
- `outputs/figures/auto/sim_24h.gif` - 24-hour animated playback
- `outputs/reports/provenance.jsonl` - per-decision audit log

### 4d. G3 to G1/G2 feedback

- `cooling_gap_residuals.csv` - agents and hours where no feasible shelter exists
- `exposure_hotspots.csv` - grid cells with disproportionate vulnerability-weighted exposure

---

## 5. Component-level architecture

```
sim/testbed/
  scene.py            - grid scene, edges, shelter nodes
  population.py       - synthetic generator + CSV loader (G1 schema)
  heat_field.py       - synthetic generator + NPY loader (G1 schema)
  shelter_model.py    - synthetic envelope + CSV loader (G2 schema)
  policy.py           - baseline / reactive / proactive policies
  simulator.py        - step loop, agent updates
  metrics.py          - 9 outcome metrics + 2 twin metrics
  provenance.py       - JSONL decision log
  visualize.py        - matplotlib heatmap, animation, metric charts
  run.py              - end-to-end driver
```

Each module depends only on numpy / pandas / matplotlib. No SUMO, no Mesa, no Omniverse at Stage One.

---

## 6. Stage One visualization (matplotlib)

| Artifact | What it shows |
|---|---|
| `outputs/figures/auto/heatfield_h14.png` | Top-down 14:00 view: heat field colored, agents as dots, shelters as squares |
| `outputs/figures/auto/sim_24h.gif` | Animated 24-hour playback of the agentic loop |
| `outputs/figures/auto/exposure_timeline.png` | Cumulative population heat exposure over the day, all 3 scenarios |
| `outputs/figures/auto/metric_comparison.png` | Bar chart of the 9 metrics, baseline vs reactive vs proactive |
| `outputs/figures/auto/equity_breakdown.png` | Exposure reduction by vulnerability quartile |

Omniverse / Isaac Sim is Phase 6 of the original methodology and is deferred to Stage Two.

---

## 7. Tech-stack mapping

| Layer | Stage One (5/25) | Stage Two+ |
|---|---|---|
| Scene | Python 20x10 grid | Yi's SHP -> SUMO network |
| Population | sampled with seed | G1 synthetic-population engine |
| Heat field | NumPy synthetic | G1 hourly raster from sensors / model |
| Cooling envelope | piecewise-constant | G2 N-UBEM + ReOpt output |
| Policy | threshold rule | LLM-driven agentic planner |
| Simulator | pure Python loop | Mesa ABM + SUMO microsim |
| Visualization | matplotlib + GIF | NVIDIA Omniverse twin |
| Robot validation | none | NVIDIA Isaac Sim |

---

## 8. Anti-goals

- Group 3 will not re-derive heat fields, energy demand, or vulnerability scores. Missing G1/G2 deliverables become clearly-labeled placeholders that emit residuals.
- Group 3 will not lock a UI framework before the methodology is validated. Stage One ships matplotlib visuals; Omniverse lands in Stage Two.
- The testbed will not swallow errors silently: missing fields raise, bad schema versions raise. Fail loud.
