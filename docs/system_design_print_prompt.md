# System Design Print Prompt — Urban Digital Twins

| | |
|---|---|
| **Print revision** | v0.2 — 2026-05-25 |
| **Purpose** | A paste-ready prompt for any diagram-generation tool (Eraser, Excalidraw, Figma Make, draw.io AI, Mermaid Live, ChatGPT/Claude) to produce a printable system-design poster for the 2026 Summer Tokyo Workshop · Urban Digital Twins architecture. |
| **Canonical source of truth** | [system_architecture.md](system_architecture.md) — refine that file first, then re-export through this prompt. |

---

## 0. How to use this file

1. Pick the tool you want to print from (section 4).
2. Copy the **Canonical System Description** (section 2) into the tool.
3. Append the tool-specific **Style + Constraints** block (section 3).
4. Render, review against [system_architecture.md](system_architecture.md), iterate.
5. Export to PDF at A1 (poster) or A3 (handout). For digital handouts, export PNG @ 300 dpi.

Keep section 2 as the canonical input. If the architecture changes, update section 2 first, then re-prompt — that way every diagram tool stays in sync.

---

## 1. One-line elevator

> Urban Digital Twins ingests Urban Risk (heat exposure) and Urban Regeneration (cooling envelope) outputs, runs an agent-based decision loop with baseline / reactive / proactive policies, scores the six Xilin metrics, and renders an interactive Folium map plus a Plotly comparison for stakeholders. Stage One uses synthetic placeholders that match the locked Urban Risk/Urban Regeneration schemas; Stage Two swaps in real data and escalates to NVIDIA Omniverse + Isaac Sim on GT CURA HPC.

---

## 2. Canonical System Description (paste this into the diagram tool)

```
SYSTEM: Nihonbashi service-robot digital twin, Urban Digital Twins layer, 2026 Summer Tokyo Workshop.

CONTEXT (three teams + external producers + stakeholders):
- Urban Risk produces: synthetic population with vulnerability, hourly heat-cost raster, occupancy schedule.
- Urban Regeneration produces: N-UBEM building cooling demand, ReOpt energy supply, shelter cooling envelope with emissions intensity.
- Urban Digital Twins (this system) consumes Urban Risk and Urban Regeneration outputs through schema-validated loaders, runs an agent-based decision loop, computes six metrics, and renders visuals.
- External inputs: PLATEAU CityGML LOD2/LOD3 Tokyo geometry, OSM road network, ArcGIS Pro network cleanup by Yi Tai, Phase 1 Starship baseline ABM trace.
- Stakeholders: workshop coordinators (Perry Yang, Subhro, Sei), Urban Risk lead, Urban Regeneration lead (Devesh / shelter team).

GROUP 3 INTERNAL CONTAINERS:
1. Ingestion + schema validators (population.py, heat_field.py, shelter_model.py, scene.py).
2. World-state model in Mesa + Shapely (agents, grid cells, shelter polygons).
3. Policy layer with three scenarios: baseline (no intervention), reactive (threshold-triggered shelter routing), proactive (3-hour lookahead pre-positioning).
4. Six-metric collector: labor_substitution_rate, heat_exposure_reduction, service_continuity, delivery_efficiency, pedestrian_interference, infrastructure_compatibility.
5. Provenance log: one JSONL line per agent decision with rationale and latency.
6. Visualization: Folium interactive Leaflet map, Plotly comparison charts, Streamlit dashboard.

DATA STORES:
- data/from_group1/  (population.csv, heat_field.npy, occupancy.csv)
- data/from_group2/  (shelter_envelope.csv, cooling_capacity.csv, emissions_intensity.csv)
- outputs/figures/auto/  (HTML maps + Plotly charts)
- outputs/reports/   (testbed_comparison.md, provenance.jsonl, residual CSVs)

DECISION LOOP (one simulated hour H):
driver -> simulator.step(H) -> loaders.slice(H) -> world.apply_slice -> policy.decide(agent) for each agent -> world updates -> provenance.log -> metrics.update -> visualize.emit_frame(H).

DEPLOYMENT:
- Local Python 3.11 dev workstation runs the Mesa loop, Folium server (:8000), Streamlit dashboard (:8501).
- Stakeholder browser views the Folium Leaflet map and Plotly charts.
- Stage Two: GT CURA HPC with NVIDIA RTX 4090 runs Omniverse Kit + Isaac Sim for the high-fidelity twin.
- External producers (Urban Risk, Urban Regeneration, ArcGIS Pro) publish files into data/.

STAGE ONE vs STAGE TWO (what swaps):
- scene: synthetic 20x10 grid  -> Yi Tai's SHP-to-SUMO Nihonbashi network.
- population: numpy sampled    -> Urban Risk synthetic-population engine.
- heat field: numpy            -> xarray on Urban Risk raster.
- cooling envelope: piecewise  -> Urban Regeneration N-UBEM + ReOpt.
- policy: threshold rule       -> LLM-driven agentic planner.
- simulator: pure-Python loop  -> Mesa + traci microsim.
- visualization: Folium+Plotly -> NVIDIA Omniverse twin.
- robot validation: (none)     -> NVIDIA Isaac Sim.

FEEDBACK (Urban Digital Twins emits back to Urban Risk/Urban Regeneration):
- cooling_gap_residuals.csv to Urban Regeneration (agents/hours with no feasible shelter).
- exposure_hotspots.csv to Urban Risk (cells with disproportionate vulnerability-weighted exposure).
- policy_stress_points.md to both groups.

ANTI-GOALS:
- Urban Digital Twins does not re-derive heat, energy, or vulnerability.
- Urban Digital Twins does not lock a UI before methodology is validated.
- No silent error swallowing; missing fields raise.
```

---

## 3. Style + Constraints (append after section 2)

```
VISUAL CONVENTIONS:
- Three groups colored distinctly: Urban Risk = warm yellow, Urban Regeneration = teal, Urban Digital Twins = soft amber (this system, slightly bolder border).
- External producers and stakeholders = light blue.
- Data stores = green cylinders or rounded rectangles labeled with the file path.
- Stage Two elements = purple with dashed borders (clearly marked "deferred").
- Solid arrows for Stage One data flow.
- Dashed arrows for feedback channels and Stage Two handoffs.
- Label every arrow with the artifact name (e.g., population.csv) and cadence (hourly / static).

LAYOUT:
- Left-to-right flow: External -> Urban Risk/G2 -> Urban Digital Twins internal -> Visualization -> Stakeholders.
- Place Urban Digital Twins internal containers in a vertical stack: ingestion (top) -> world state -> policy -> metrics + provenance -> visualization (bottom).
- Include a legend in the bottom-right with shape/color meaning.
- Title block at top: "Urban Digital Twins — Nihonbashi Heat-Support Digital Twin · 2026 Summer Tokyo Workshop · v0.2".
- Footer: "Stage One review · 2026-05-25 · Owners: Sam Duong, Yi Tai, Xilin Tang, Murugesan Devesh".

OUTPUT:
- One hero diagram (System Context).
- One zoomed-in Container diagram for Urban Digital Twins internals.
- One sequence/swimlane diagram for the one-hour decision loop.
- Print target: A1 poster + A3 handout. Light theme. High contrast. Sans-serif body font.
```

---

## 4. Tool-specific variants

### 4a. Mermaid (drop-in, no AI needed)

The architecture doc already contains five rendered Mermaid blocks. Open `system_architecture.md` in any Mermaid-aware viewer or paste a block into <https://mermaid.live>:

- System Context — section 2
- Container view — section 3
- Sequence diagram — section 4
- Deployment view — section 5
- Stage One vs Stage Two — section 6

Export each as SVG (for sharp print) or PNG @ 300 dpi.

### 4b. Eraser.io (AI diagram-as-code)

1. Open <https://app.eraser.io/> → New diagram → "Diagram-as-code".
2. Paste section 2 (Canonical System Description) into the chat box.
3. Append: `Generate a Cloud Architecture Diagram in Eraser DSL with three top-level groups (Urban Risk, Urban Regeneration, Urban Digital Twins), show data flows with labels, mark Stage Two elements with style.dashed=true.`
4. Ask Eraser AI to iterate: "Add a separate sequence diagram for the one-hour decision loop."

### 4c. Excalidraw

1. Open <https://excalidraw.com/> → AI Diagram (top-right sparkle icon).
2. Paste section 2 + section 3 (Canonical + Style).
3. Excalidraw's AI returns a Mermaid spec it then sketches; review and adjust by hand for the hand-drawn poster aesthetic.

### 4d. Figma Make

Use the project's `figma` skill flow. Prompt template:

```
Design a single-page A1 architecture poster for the system described below.
Style: clean editorial, light background, two-column header with title + revision block,
hero diagram center, legend bottom-right. Use the brand palette: warm yellow (#fff3b0)
for Urban Risk, teal (#a8dadc) for Urban Regeneration, amber (#ffd166) for Urban Digital Twins, dusty blue (#dfe7fd)
for external, sage green (#c8e6c9) for data stores, lavender (#f5e6ff) dashed for Stage Two.

<paste section 2 here>

<paste section 3 here>

Deliver: hero context diagram, container detail panel, sequence-of-one-hour panel.
```

### 4e. draw.io / diagrams.net AI

1. <https://app.diagrams.net/> → Insert → Advanced → AI.
2. Paste section 2 + section 3.
3. Choose "C4 Container" template. Manually re-route arrows for clarity.

### 4f. ChatGPT / Claude for Mermaid expansion

If you want a single megadiagram (one image, all four perspectives stitched together):

```
Using the system description below, produce ONE Mermaid flowchart that combines:
(a) external producers + Urban Risk + Urban Regeneration sources on the left,
(b) Urban Digital Twins internal pipeline in the middle (ingest -> world -> policy -> metrics -> viz),
(c) stakeholder browser + Stage Two HPC on the right.
Use subgraphs, classDef for colors, dashed lines for Stage Two and feedback edges.
Keep node labels short (<= 4 words). Use TB layout where it improves readability.

<paste section 2>

<paste section 3>
```

---

## 5. Print-and-go checklist

- [ ] Section 2 reviewed against latest `system_architecture.md` — no drift.
- [ ] Urban Risk / Urban Regeneration schemas in section 7 of architecture doc confirmed with Yi Tai and Devesh.
- [ ] Six metric names cross-checked against `docs/methodology.md` and `analysis/metrics.py` (once it exists).
- [ ] Stage Two elements clearly tagged so reviewers don't mistake them for Stage One scope.
- [ ] Title block carries date and revision.
- [ ] Legend explains every shape and line style.
- [ ] Exported to A1 PDF for the room, A3 handout for breakout discussion, PNG for Slack/email.
- [ ] One copy of the PDF stored at `outputs/figures/auto/system_design_v0.2.pdf` (or wherever your slide-export convention puts it).

---

## 6. Update protocol

When the design changes:

1. Edit `system_architecture.md` first (it owns the Mermaid source).
2. Update section 2 of this file to mirror the change in plain English.
3. Bump the print revision in both files.
4. Re-export through whichever tool was used last time.
5. Commit the diff with `docs: bump system design to vX.Y`.
