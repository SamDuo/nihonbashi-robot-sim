# System Architecture — Urban Digital Twins · Nihonbashi

| | |
|---|---|
| **Print revision** | v0.3 — 2026-05-25 |
| **Status** | Ready for Stage One review (5/25) |
| **Owners** | Sam Duong (M&V / orchestration), Yi Tai (ABM + SHP→SUMO scene), Xilin Tang (methodology), Murugesan Devesh (Urban Regeneration bridge / shelter modeling) |
| **Companion docs** | [methodology.md](methodology.md) · [stage1_research_design.md](stage1_research_design.md) · [visualization_plan.md](visualization_plan.md) · [system_design_print_prompt.md](system_design_print_prompt.md) |
| **Viz stack (Stage One)** | **Re:Earth** (browser, PLATEAU 3D Tokyo) + **Streamlit** (metrics dashboard). See [visualization_plan.md](visualization_plan.md). |
| **Diagram source** | Mermaid (renders in GitHub, Notion, VS Code, Obsidian, draw.io, GitLab). For one-click rendering see <https://mermaid.live>. |

---

## 1. One-paragraph summary

Urban Digital Twins is the **synthesis and decision layer** of the 2026 Summer Tokyo Workshop's Nihonbashi study. We do **not** generate the ground-truth heat-exposure field (Urban Risk) or the building cooling envelopes (Urban Regeneration). Urban Digital Twins ingests both teams' outputs against a documented schema, runs an **agent-based decision loop** that produces reactive shelter allocations and proactive resource dispatches, computes the **six evaluation metrics** from the Xilin methodology, and renders an **interactive Folium map** plus a Plotly comparison report. For Stage One (5/25), the loop runs on synthetic placeholder data that matches the locked Urban Risk/Urban Regeneration schemas; the loaders swap when real data lands, and nothing else changes.

---

## 2. System Context (who talks to whom)

```mermaid
flowchart LR
  classDef group fill:#fff3b0,stroke:#5a4a00,color:#1a1a1a,stroke-width:1.5px
  classDef ext fill:#dfe7fd,stroke:#1a3a8f,color:#1a1a1a
  classDef stage2 fill:#f5e6ff,stroke:#5a1a8f,color:#1a1a1a,stroke-dasharray: 4 3
  classDef store fill:#e8f5e9,stroke:#1b5e20,color:#1a1a1a

  subgraph EXT[External producers and reference data]
    PLATEAU[PLATEAU CityGML<br/>LOD2/LOD3 Tokyo]:::ext
    OSM[OSM road network]:::ext
    ARCGIS[ArcGIS Pro<br/>Yi Tai network cleanup]:::ext
    PHASE1[Phase 1 Starship baseline<br/>ABM trace]:::ext
  end

  subgraph G1[Urban Risk — exposure and vulnerability]
    G1POP[Synthetic population<br/>+ vulnerability]:::group
    G1HEAT[Hourly heat-cost raster]:::group
    G1OCC[Occupancy schedule]:::group
  end

  subgraph G2[Urban Regeneration — energy and cooling envelope]
    G2NUBEM[N-UBEM cooling demand]:::group
    G2REOPT[ReOpt energy supply]:::group
    G2ENV[Shelter cooling envelope<br/>+ emissions intensity]:::group
  end

  subgraph G3[Urban Digital Twins — synthesis and decision layer]
    G3ING[Ingestion + schema validators]:::group
    G3WORLD[World-state model<br/>Mesa + Shapely]:::group
    G3POL[Policy<br/>baseline / reactive / proactive]:::group
    G3METRIC[Six-metric collector]:::group
    G3PROV[(Provenance log<br/>JSONL)]:::store
    G3VIZ[Folium map + Plotly charts<br/>+ Streamlit dashboard]:::group
  end

  subgraph S2[Stage Two — high-fidelity twin]
    OMNI[NVIDIA Omniverse Kit]:::stage2
    ISAAC[NVIDIA Isaac Sim]:::stage2
    CURA[GT CURA HPC<br/>RTX 4090]:::stage2
  end

  STAKE[Workshop stakeholders<br/>Perry Yang · Subhro · Sei · group leads]:::ext

  PLATEAU --> G1POP
  OSM --> ARCGIS
  ARCGIS -->|SHP / .net.xml| G3WORLD
  PHASE1 -->|baseline params| G3POL

  G1POP -->|population.csv| G3ING
  G1HEAT -->|heat_field.npy| G3ING
  G1OCC -->|occupancy.csv| G3ING
  G2ENV -->|shelter_envelope.csv| G3ING
  G2NUBEM -->|cooling_capacity.csv| G3ING
  G2REOPT -->|emissions_intensity.csv| G3ING

  G3ING --> G3WORLD --> G3POL --> G3METRIC --> G3VIZ
  G3POL --> G3PROV
  G3VIZ --> STAKE

  G3METRIC -.->|cooling-gap residuals<br/>exposure hotspots| G1POP
  G3METRIC -.->|policy stress points| G2ENV

  G3WORLD -.->|Stage Two scene handoff| OMNI
  OMNI --> ISAAC
  OMNI --- CURA
  ISAAC --- CURA
```

**Legend** — solid arrow = Stage One data flow; dashed arrow = feedback or Stage Two handoff; yellow = team subsystem; blue = external; green = data store; purple-dashed = Stage Two (deferred).

---

## 3. Container view — inside Urban Digital Twins

```mermaid
flowchart TB
  classDef loader fill:#e3f2fd,stroke:#0d47a1,color:#0a0a0a
  classDef core fill:#fff3b0,stroke:#5a4a00,color:#0a0a0a
  classDef policy fill:#ffe0b2,stroke:#bf360c,color:#0a0a0a
  classDef out fill:#c8e6c9,stroke:#1b5e20,color:#0a0a0a
  classDef store fill:#eceff1,stroke:#37474f,color:#0a0a0a

  subgraph LOAD[sim/testbed loaders — schema-validated]
    L1[population.py<br/>Urban Risk schema]:::loader
    L2[heat_field.py<br/>Urban Risk schema]:::loader
    L3[shelter_model.py<br/>Urban Regeneration schema]:::loader
    L4[scene.py<br/>SHP / synthetic grid]:::loader
  end

  subgraph CORE[Core simulation — Mesa + Shapely]
    M1[World state<br/>agents · cells · shelters]:::core
    M2[simulator.py<br/>step loop, 1-hour ticks]:::core
  end

  subgraph POL[Policy layer — three scenarios]
    P1[Baseline<br/>no intervention]:::policy
    P2[Reactive<br/>threshold-triggered shelter routing]:::policy
    P3[Proactive<br/>3-hour lookahead pre-positioning]:::policy
  end

  subgraph OUT[Outputs]
    O1[metrics.py<br/>six metrics + twin metrics]:::out
    O2[provenance.py<br/>per-decision JSONL]:::out
    O3[visualize.py<br/>Folium map · Plotly · Streamlit]:::out
  end

  subgraph STORE[Stage One file layout]
    D1[(data/from_group1/)]:::store
    D2[(data/from_group2/)]:::store
    D3[(outputs/figures/auto/)]:::store
    D4[(outputs/reports/)]:::store
  end

  D1 --> L1 & L2
  D2 --> L3
  L4 --> M1
  L1 & L2 & L3 --> M1
  M1 --> M2 --> P1 & P2 & P3
  P1 & P2 & P3 --> O1
  P1 & P2 & P3 --> O2
  O1 --> O3
  O3 --> D3
  O1 --> D4
  O2 --> D4
```

---

## 4. Decision-loop sequence — one simulated hour

```mermaid
sequenceDiagram
  autonumber
  participant Driver as scripts/run_testbed.py
  participant Sim as simulator.py
  participant Load as loaders (pop / heat / shelter)
  participant World as world state (Mesa)
  participant Pol as policy
  participant Met as metrics collector
  participant Prov as provenance.py
  participant Viz as visualize.py

  Driver->>Sim: step(hour H, scenario S)
  Sim->>Load: slice(H)
  Load-->>Sim: population_H, heat_H, shelter_H
  Sim->>World: apply_slice(...)
  loop for each agent
    World->>Pol: decide(agent, world, S)
    Pol-->>World: action {stay | route_to_shelter | dispatch}
    Pol->>Prov: log(agent, action, rationale, latency)
  end
  World-->>Sim: state_H
  Sim->>Met: update(state_H)
  Met-->>Sim: running metrics
  Sim->>Viz: emit_frame(H, state_H)
  Sim-->>Driver: hour H done
```

---

## 5. Deployment view — where each thing runs

```mermaid
flowchart LR
  classDef local fill:#fff3b0,stroke:#5a4a00,color:#0a0a0a
  classDef browser fill:#dfe7fd,stroke:#1a3a8f,color:#0a0a0a
  classDef hpc fill:#f5e6ff,stroke:#5a1a8f,color:#0a0a0a,stroke-dasharray: 4 3
  classDef ext fill:#c8e6c9,stroke:#1b5e20,color:#0a0a0a

  subgraph LOCAL[Local dev workstation — Stage One]
    PY[Python 3.11<br/>Mesa · Shapely · pandas · numpy]:::local
    FOL[Folium server<br/>:8000]:::local
    ST[Streamlit dashboard<br/>:8501]:::local
  end

  subgraph BROW[Stakeholder browser]
    LEAF[Leaflet map<br/>via Folium HTML]:::browser
    PLOT[Plotly metric charts]:::browser
  end

  subgraph CURA[GT CURA HPC — Stage Two]
    OMNI2[Omniverse Kit · RTX 4090]:::hpc
    ISAAC2[Isaac Sim]:::hpc
  end

  subgraph EXT[External producers]
    G1[Urban Risk outputs]:::ext
    G2[Urban Regeneration outputs]:::ext
    ARC[ArcGIS Pro<br/>Yi Tai SHP]:::ext
  end

  G1 --> PY
  G2 --> PY
  ARC --> PY
  PY --> FOL --> LEAF
  PY --> ST --> PLOT
  PY -.->|USD scene handoff| OMNI2 --> ISAAC2
```

---

## 6. Stage One vs Stage Two — what swaps

```mermaid
flowchart LR
  classDef s1 fill:#fff3b0,stroke:#5a4a00,color:#0a0a0a
  classDef s2 fill:#f5e6ff,stroke:#5a1a8f,color:#0a0a0a,stroke-dasharray: 4 3

  subgraph S1[Stage One — 5/25 review]
    A1[Synthetic 20x10 grid scene]:::s1
    A2[Sampled synthetic population]:::s1
    A3[NumPy heat field]:::s1
    A4[Piecewise-constant shelter envelope]:::s1
    A5[Threshold-rule policy]:::s1
    A6[Pure-Python step loop]:::s1
    A7[Folium + Plotly + Streamlit]:::s1
  end

  subgraph S2[Stage Two — post-handoff]
    B1[Yi Tai SHP to SUMO Nihonbashi network]:::s2
    B2[Urban Risk synthetic-population engine output]:::s2
    B3[Urban Risk hourly raster from sensors / model]:::s2
    B4[Urban Regeneration N-UBEM + ReOpt output]:::s2
    B5[LLM-authored constraints<br/>+ NVIDIA cuOpt routing solver]:::s2
    B6[Mesa ABM + SUMO microsim co-sim]:::s2
    B7[NVIDIA Omniverse twin + Isaac Sim]:::s2
  end

  A1 -.->|drop-in| B1
  A2 -.->|drop-in| B2
  A3 -.->|drop-in| B3
  A4 -.->|drop-in| B4
  A5 -.->|extend| B5
  A6 -.->|extend| B6
  A7 -.->|escalate| B7
```

---

## 7. Interface contracts

### 7a. Urban Risk → Urban Digital Twins

| File | Format | Required columns / shape | Cadence |
|---|---|---|---|
| `population.csv` | CSV, UTF-8 | `agent_id`, `age_bucket` (child/adult/elderly), `occupation_class` (worker/commuter/visitor/resident/student), `mobility_class` (mobile/assisted/restricted), `vulnerability_score` [0,1], `home_grid_cell`, `hour` [0,23], `activity_grid_cell` | One row per agent per hour |
| `heat_field.npy` | NumPy `.npy` | shape `(24, 20, 10)` — hours × x × y, value = heat-cost factor in [0, 2] | Hourly raster |
| `occupancy.csv` | CSV | `building_id`, `hour`, `occupants_total`, `vulnerable_weighted_occupants` | Hourly |

### 7b. Urban Regeneration → Urban Digital Twins

| File | Format | Required columns | Cadence |
|---|---|---|---|
| `shelter_envelope.csv` | CSV | `building_id`, `hour`, `max_occupants`, `cooling_kwh`, `emissions_intensity` (kgCO2e/kWh) | Hourly |
| `cooling_capacity.csv` | CSV | `building_id`, `nominal_capacity_kw`, `derating_curve_id` | Static per scenario |

### 7c. Urban Digital Twins → Stakeholders

| Artifact | Purpose |
|---|---|
| `outputs/figures/auto/map_h14.html` | Folium interactive map snapshot at 14:00 |
| `outputs/figures/auto/sim_24h.html` | Folium timestepped overlay for the day |
| `outputs/figures/auto/metric_comparison.html` | Plotly six-metric bar chart, three scenarios |
| `outputs/figures/auto/exposure_timeline.html` | Plotly cumulative exposure over the day |
| `outputs/reports/testbed_comparison.md` | Written comparison report |
| `outputs/reports/provenance.jsonl` | Per-decision audit log |

### 7d. Urban Digital Twins → Urban Risk / Urban Regeneration (feedback)

| Artifact | Consumer |
|---|---|
| `cooling_gap_residuals.csv` | Urban Regeneration — agents and hours with no feasible shelter |
| `exposure_hotspots.csv` | Urban Risk — grid cells with disproportionate vulnerability-weighted exposure |
| `policy_stress_points.md` | Both groups — locations where the agentic loop runs out of feasible actions |

---

## 8. Component module map (`sim/testbed/`)

| Module | Responsibility | Stage One stack | Stage Two stack |
|---|---|---|---|
| `scene.py` | Geometry + adjacency | Shapely + synthetic grid | Shapely + geopandas on Yi's SHP / SUMO `.net.xml` |
| `population.py` | Agent loader + synth generator | pandas + numpy | reads Urban Risk engine output |
| `heat_field.py` | Heat-cost grid | numpy | xarray + rasterio on Urban Risk raster |
| `shelter_model.py` | Envelope + feasibility | pandas | reads Urban Regeneration N-UBEM/ReOpt output |
| `policy.py` | Three policies | rule-based | LLM-authored constraints + **NVIDIA cuOpt routing solver** (GPU vehicle-routing with time windows, vulnerability-weighted priorities, heat-cost edge weights) |
| `simulator.py` | Step loop | Mesa scheduler | Mesa + traci (SUMO) |
| `metrics.py` | Six + twin metrics | numpy + pandas | unchanged |
| `provenance.py` | Decision log | JSONL | unchanged |
| `visualize.py` | Map + charts + dashboard | Folium + Plotly + Streamlit | Omniverse Kit (USD) |
| `run.py` | Driver | argparse | snakemake / nextflow |

Every module raises on missing/bad schema fields. No silent fallbacks.

---

## 9. Tech-stack summary

| Layer | Stage One (5/25) | Stage Two+ |
|---|---|---|
| Scene | Shapely + synthetic 20×10 grid | Yi's SHP → SUMO `.net.xml` |
| ABM | Mesa | Mesa + traci ↔ SUMO microsim |
| Population | numpy / pandas synth | Urban Risk synthetic-population engine |
| Heat field | numpy | xarray + rasterio on Urban Risk raster |
| Cooling envelope | piecewise-constant | Urban Regeneration N-UBEM + ReOpt |
| Policy | threshold rule | LLM-authored constraints → **NVIDIA cuOpt** routing solver (see [cuopt_integration_plan.md](cuopt_integration_plan.md)) |
| Visualization | Folium + Plotly + Streamlit | NVIDIA Omniverse Kit |
| Robot validation | (none) | NVIDIA Isaac Sim |
| Compute | local Python | GT CURA HPC (RTX 4090) |

---

## 10. Anti-goals

- Urban Digital Twins will **not** re-derive heat fields, energy demand, or vulnerability scores. Missing Urban Risk/Urban Regeneration deliverables become **clearly-labeled placeholders** that emit residuals.
- Urban Digital Twins will **not** lock a UI framework before the methodology is validated. Stage One ships Folium + Plotly; Omniverse lands in Stage Two.
- The testbed will **not** swallow errors silently: missing fields raise, bad schema versions raise. Fail loud.

---

## 11. Appendix — printing & rendering

- **Render Mermaid to PNG/SVG for posters:** paste each `mermaid` block into <https://mermaid.live> and export. Suggested poster size: A1, light background, default Mermaid theme. For dark prints set `%%{init: { 'theme': 'dark' }}%%` at the top of each block.
- **Render the whole document to PDF:** open in VS Code with the *Markdown Preview Mermaid Support* extension, then "Export PDF" via *Markdown PDF*. GitHub also renders Mermaid natively in the markdown preview.
- **For AI-generated polished diagrams** (Eraser, Excalidraw, Figma Make, draw.io): use [system_design_print_prompt.md](system_design_print_prompt.md) as the input prompt.
