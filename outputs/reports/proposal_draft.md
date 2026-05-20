# Modeling & Visualization Pipeline for the Nihonbashi Service-Robot Study

**Team proposal — Phases 4-6 of the six-stage methodology**

Authors: Sam M. Duong, Xilin Tang, Yi Tai, Qinghao (Advisor: TBD)
Date: 2026-05-14
Repository: https://github.com/SamDuo/nihonbashi-robot-sim
Status: Draft v0.2 — for team review

---

## Page 1 — Executive Summary and Project Context

### Summary

We propose a Modeling & Visualization (M&V) pipeline that converts the converged parameter set from Phases 1-3 into a manufacturable CAD model, a re-validated agent-based simulation, and a high-fidelity Omniverse + Isaac Sim digital twin of the 200-metre Nihonbashi street segment. The pipeline closes the loop that Xilin Tang's six-stage methodology opens at Phase 1: macroscopic ABM gains are translated to micro-scale industrial design, the design is re-checked against the same macroscopic metrics, and the validated robot is dropped into a photoreal twin where motion, sensors, and physical interaction can be evaluated by humans. Within a 12-week sprint, the team will deliver an end-to-end pipeline, a CAD source bundle, a re-validation comparison report, and a stakeholder-facing interactive demo running at 30+ FPS in NVIDIA Omniverse.

### Why M&V matters for this project

Phases 1-3 produce statistical evidence of macroscopic gain: a Pareto-non-dominated comparison of the proposed Heat-Support Robot against a Starship baseline on six metrics. That evidence is rigorous but illegible to non-modelers. Stakeholders — planners, residents, ward officials, GT advisors — need a *visualizable* twin to interpret and challenge the proposal. Industrial designers in turn need to refine form, materials, modules, and sensor placement in a CAD environment that round-trips with the ABM. Without M&V, Phase 1-3 results stay in research notebooks; with it, they reach decision-makers and form the visual + engineering evidence base for any follow-on field deployment.

### Scope and exclusions

This proposal covers Phases 4 (AI + CAD optimization), 5 (ABM re-simulation verification), and 6 (high-fidelity digital twin in NVIDIA Omniverse + robot validation in Isaac Sim) of Xilin Tang's methodology. Phases 1-3 — data test bed, baseline ABM, A/B comparison, and the converged variable matrix — are upstream inputs and are not redone here. Real-world hardware prototyping, on-street piloting, and regulatory engagement (METI sidewalk-robot certification, ward permits) are out of scope; the M&V pipeline produces the evidence that justifies any such follow-on effort.

---

## Page 2 — M&V Pipeline Architecture

### Definition

The M&V pipeline is a four-stage sequence in which each stage produces a typed artifact consumed by the next, with explicit feedback arcs back to upstream stages on failure. The contract between stages is the artifact, not a tribal handoff.

### Four stages

**Stage A — AI + CAD optimization (Phase 4).** Generative AI summarizes Phase 3 friction points and proposes CAD-level modifications (form, module layout, docking strategy, sensor placement). The industrial designer (Xilin) selects, critiques, and integrates against Nihonbashi context and the METI 2023 sidewalk-robot regulation. The result is a parametric Fusion 360 source (with optional Rhino + Grasshopper passes for organic surfaces) that exports as a neutral STEP file plus a parameter mapping back to the variable matrix from Phases 1-3.

**Stage B — ABM re-simulation verification (Phase 5).** CAD-derived geometric and behavioral parameters (width, length, speed, turning radius, docking duration, service modules, sensor field-of-view) are re-abstracted into the ABM. We run a three-tier comparison — Starship baseline, initial Heat-Support proposal, CAD-optimized robot — under identical scenarios, windows, seeds, and metrics. The goal is to confirm that the geometric and material choices made in Stage A do not erase the macroscopic gains established in Phase 3.

**Stage C — High-fidelity scene construction (Phase 6, Part 1).** PLATEAU CityGML LOD1/LOD2 is converted to USD using the Aerial Digital Twin Scene Importer. The scene is augmented with PBR materials (sidewalk surfaces, building facades, signage), animated pedestrian crowds whose density matches the ABM per segment, weather-and-light conditions per heat scenario, and the heat-cost field baked onto sidewalk meshes as a visualizable USD attribute.

**Stage D — Isaac Sim robot validation (Phase 6, Part 2).** The CAD model is imported into NVIDIA Isaac Sim with rigid-body physics, a sensor stack (RGB + depth cameras, 2D lidar, ultrasonic, IMU), and the same pedestrian and service-node populations as Stage C. We validate robot motion (turning radius, slope handling, docking maneuvers), sensor behavior (object detection in shade vs. sun, occlusion under crowd density), and physical interaction (collision avoidance, cargo-module swap, charging-station docking).

### Feedback arcs

A failure in Stage B (gains erased by geometric choices) returns the issue to Stage A as a CAD-parameter change request. A failure in Stage D (motion or sensor limits violated) returns the issue to Stage A with the specific clearance or sensor placement to revisit. The variable matrix is the canonical place where these revisions are recorded.

---

## Page 3 — Asset Inventory and M&V-Specific Gaps

### Inventory (assets available today)

| # | Asset | Source | Format | Quality | Owner |
|---|---|---|---|---|---|
| 1 | PLATEAU CityGML LOD1/LOD2 | PLATEAU VIEW 4.0 | CityGML | ★★★★ | Sam |
| 2 | OSM sidewalk graph | OSMnx | GraphML / `.net.xml` | ★★★★ | Yi Tai |
| 3 | Heat-cost field | Phase 1-3 output | Per-segment scalar | ★★★★ | Sam |
| 4 | Variable matrix | Phase 1-3 output | CSV | ★★★★★ | Xilin |
| 5 | Pedestrian density profiles | Phase 1-3 output | Per-scenario CSV | ★★★★ | Yi Tai |
| 6 | Starship reference geometry | Public spec | Approximate dimensions | ★★ | Yi Tai |
| 7 | Studio renders / mood imagery | Xilin's deck + concept work | Image | ★★★ | Xilin |

### Critical M&V gaps (block delivery)

1. **PLATEAU LOD3 geometry for the 200 m segment.** LOD2 captures roof and rough facade but lacks the facade detail required for photoreal renders. We close this by combining LOD2 with manual modeling of five hero buildings and photogrammetry-from-photos for facade enrichment.
2. **PBR material library.** Tokyo-context-appropriate facades, sidewalks, signage, and street furniture. We source Quixel Megascans curated to Tokyo references; custom signage authored in Substance.
3. **Animated pedestrian crowd library.** USD-compatible characters with retargetable animations. We use Omniverse SimReady characters as the primary source; Mixamo as fallback.
4. **Robot CAD source.** Output of Stage A; gating dependency for Stages B and D. Risk is timing rather than availability.
5. **Sensor specifications for the proposed robot.** Camera model, lidar product class, ultrasonic placement. We base these on Starship's published stack augmented for heat-monitoring use cases.

### Should-have gaps

6. Vehicle and bicycle assets for adjacent street activity (Omniverse SimReady covers this).
7. Audio environment — street ambience and robot cue sounds (Freesound + custom recording).
8. Tokyo-specific HDRI library for time-of-day skybox (Polyhaven + custom captures).
9. Japanese-language signage with correct typography (Substance + Photoshop).

### Acquisition plan

Each gap has a named owner and an ETA in the timeline section. Critical gaps 1-3 begin in week 1 in parallel; gap 4 (robot CAD) follows Stage A, expected complete by week 6; gap 5 (sensor specs) is week 1, gating Stage D. Should-have gaps land between weeks 2 and 6.

---

## Page 4 — Visualization Methodology

### Stage A workflow — Fusion 360 + Rhino

Begin with the converged variable matrix from Phases 1-3. Every variable becomes a Fusion 360 parameter, so changes propagate through the model. Parametric body shell, modular cargo bay (water, medicine, first-aid, guidance), lift-off docking mechanism, top-mounted sensor housing, and interaction-cue surfaces (lighting strip, screen). Rhino + Grasshopper handles organic surfaces (the upper enclosure) where Fusion 360's parametric workflow is less ergonomic. Blender produces the export pass that strips construction history and outputs both STEP for engineering hand-off and USD for downstream Omniverse use.

### Stage C workflow — Omniverse scene assembly

The high-fidelity scene is assembled in USD Composer (NVIDIA Omniverse Kit). PLATEAU CityGML enters via the Aerial Digital Twin Scene Importer. OSM sidewalk geometry is rebuilt as USD meshes with per-segment width baked from the ABM data. Heat-cost values are written as USD attributes on each sidewalk segment so designers can toggle a heat-overlay visualization. PBR materials are applied per building / surface class. Weather rigs (sun angle, ambient intensity, fog) match the four heat scenarios. Animated pedestrians are placed according to per-scenario density CSVs from Phase 1-3.

### Stage D workflow — Isaac Sim validation

The Fusion 360 CAD model is imported into Isaac Sim with rigid-body physics. Sensor stack: RGB and depth cameras (top-mounted), 2D lidar (forward-facing), ultrasonic ring (side and rear), IMU. Validation runs reproduce the Phase 3 simulation scenarios at the agent level — the robot autonomously executes the same task list under the same crowd conditions, but now with full physics and sensor synthesis. We record motion trajectories, sensor outputs, and collision events for comparison against the ABM trajectories from Phase 3. Discrepancies above tolerance flow back to Stage A.

### Real-time playback

The final deliverable runs in Omniverse Kit at 30+ FPS at 1080p on a single RTX 4090. Stakeholders walk the scene with WASD controls, toggle heat overlays, switch between heat scenarios, and observe robot dispatch behavior. A pre-rendered cinematic version (path-traced, 4K, 60 FPS) renders overnight via DGX Cloud BYOL for the formal presentation.

---

## Page 5 — Validation Metrics and Acceptance Criteria

### Geometric fidelity

Hausdorff distance between the final LOD3 building geometry and a reference orthophoto remains below 1.0 m for the hero buildings on the 200 m segment. Across the full segment, 90th-percentile distance stays below 2.0 m. Sidewalk widths in USD match ArcGIS Pro digitization within ±0.2 m.

### Material plausibility

Designer + advisor blind A/B against real photos of the segment: more than 70 percent of viewers cannot reliably distinguish rendered versus real on the hero buildings. Sidewalk materials and signage are evaluated separately under the same criterion.

### Real-time playback

30 or more FPS in Omniverse Kit at 1080p resolution, on a single RTX 4090, with the full crowd and weather rig active. Stakeholder walkthrough must hold this frame rate for the duration of a 5-minute scripted route through the scene.

### Sensor accuracy

Isaac Sim RGB camera output reproduces the color and exposure of a reference camera within ΔE < 5 under matched lighting. Lidar simulated returns match expected return counts within ±10 percent under controlled occlusion tests. Ultrasonic-ring detection range matches manufacturer spec within ±10 cm.

### Motion plausibility

CAD robot motion in Isaac Sim reproduces ABM trajectories from Phase 3 within 0.5 m positional error under the same task list and crowd density. Turning radius, docking time, and avoidance response measured in Isaac Sim are within 10 percent of the corresponding ABM parameter row.

### Re-simulation verdict (Phase 5)

The CAD-optimized robot must remain Pareto-non-dominated against the Starship baseline on the same six metrics from Phase 3, with statistical significance on at least four of six metrics across 50 paired replicates per scenario. If this fails, the residual issues route back to Stage A with documented variable changes.

---

## Page 6 — Timeline, Team, Compute, Risks, Asks

### Twelve-week timeline

| Weeks | Workstream |
|---|---|
| 1 | Tooling install (Omniverse Kit, Isaac Sim, Fusion 360, Substance). Asset-gap kickoff. Sensor-spec lock. |
| 2-3 | PLATEAU → USD scene; PBR material pass; HDRI library; crowd library integration. Review 1 (W3). |
| 4-6 | Stage A: Fusion 360 / Rhino CAD optimization. Round-trip parameter mapping. |
| 5-7 | Stage B: ABM re-simulation with CAD-derived parameters. Three-tier comparison report. Review 2 (W7). |
| 6-9 | Stage D: Isaac Sim robot import; sensor validation; motion validation. |
| 8-10 | High-fidelity scene polish; per-scenario lighting; crowd choreography. |
| 11 | Stakeholder rehearsal; cinematic render passes; comparison report assembly. Review 3 (W11). |
| 12 | Stakeholder demo + final deliverable hand-off. |

### Team and RACI

| Workstream | Sam | Xilin | Yi Tai | Qinghao |
|---|---|---|---|---|
| Asset acquisition + PBR | **R/A** | C | I | I |
| Stage A — CAD optimization | C | **R/A** | I | I |
| Stage B — ABM re-simulation | C | C | **R/A** | C |
| Stage C — Omniverse scene | **R/A** | C | I | C |
| Stage D — Isaac Sim validation | **R** | C | **R/A** | I |
| Visual + sensor metrics | **R/A** | C | C | C |
| Stakeholder demo | **R/A** | C | I | I |
| Slides + reports | **R/A** | C | C | C |

### Compute and software

Two RTX 4090 workstations (Sam + Xilin) with 64 GB RAM and 2 TB NVMe each. DGX Cloud BYOL budget of approximately USD 1,500 for batch rendering and Isaac Sim training spikes. A shared NAS or OneDrive folder of 2 TB for the USD asset library. Software is mostly free under educational or individual licensing: Omniverse Kit, Isaac Sim, Fusion 360 (education), Substance (education), Blender. NVIDIA Inception membership may unlock additional Omniverse Enterprise terms; worth exploring.

### Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Omniverse / Isaac Sim learning curve consumes weeks 1-3 | High | Targeted NVIDIA training; pair with Isaac Lab tutorials; Sam allocates 40 percent of weeks 1-2 to skill-up |
| PLATEAU LOD3 unavailable for Nihonbashi | High | LOD2 + photogrammetry + manual hero buildings; degrade gracefully on background buildings |
| Stage A CAD slips past week 6 | High | Run Stage B with parameter-only abstraction while CAD is in flight; lock CAD by week 7 hard |
| Real-time playback misses 30 FPS target | Medium | Profile early in week 5; degrade material complexity or LOD on background; defer to pre-rendered video if needed |
| Isaac Sim sensor synthesis is too slow for full scenarios | Medium | Run shortened scenario windows for sensor validation; full ABM scenarios stay in Stage B |

### Asks

1. Two RTX 4090 workstations for the duration of the 12-week sprint.
2. DGX Cloud BYOL budget: approximately USD 1,500 for batch render and training spikes.
3. Stakeholder slot of 60 minutes at end of week 12 for the demo session.
4. NVIDIA Inception engagement (if applicable) for educational access to Omniverse Enterprise terms.
5. Shared storage allocation of 2 TB for the USD asset library.

### Decisions requested at proposal review

1. Approve M&V scope (Phases 4-6 of the six-stage methodology), 12-week sprint.
2. Approve hardware and DGX Cloud budget asks.
3. Approve team allocation per the RACI table above.
4. Approve kickoff for week of 2026-05-19.

---

*End of draft v0.2. Comments and revisions welcome via PR against `outputs/reports/proposal_draft.md`.*
