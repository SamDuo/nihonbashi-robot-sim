# Team Proposal Deck — Modeling & Visualization Pipeline for the Nihonbashi Service-Robot Study

**Slide count:** 20
**Visual template:** Xilin Tang, `Research_XilinTang_0512.pdf`
**Scope:** Phases 4-6 of the six-stage methodology — AI + CAD optimization, ABM re-simulation, high-fidelity digital twin in NVIDIA Omniverse + Isaac Sim. Phases 1-3 (data test bed, baseline ABM, A/B comparison) are inputs to this pipeline.

---

## Slide 1 — Cover

**Title:** Modeling & Visualization Pipeline for the Nihonbashi Service-Robot Study
**Subtitle:** Team proposal — Phases 4-6. Translate macroscopic ABM gains into a manufacturable CAD model and a high-fidelity Omniverse digital twin that planners, designers, and stakeholders can interact with.
**Authors:** Sam M. Duong · Xilin Tang · Yi Tai · Qinghao · Advisor TBD
**Date:** 2026-05-14
**Section tag:** *Proposal Cover*
**Source:** Builds on Xilin Tang's six-stage methodology; consumes outputs of Phases 1-3.

## Slide 2 — Executive Summary
- Translate the converged variable matrix from Phases 1-3 into a manufacturable CAD model
- Re-import CAD-derived parameters into SUMO + ABM to verify macroscopic gains hold
- Construct a high-fidelity Omniverse / Isaac Sim digital twin of the 200 m Nihonbashi scene
- Validate robot motion, sensor behavior, and physical interaction inside the twin
- Deliver a stakeholder-facing interactive demo (real-time playback at 30+ FPS) and a comparison report
- Identify and close M&V-specific asset gaps (LOD3 geometry, materials, sensor specs, USD assets)

## Slide 3 — The M&V Challenge
- Macroscopic ABM gains in Phases 1-3 are statistical — they do not communicate to non-modelers
- Industrial-design CAD is intuitive but disconnected from system-level evidence
- Stakeholders (planners, residents, city officials) need a *visualizable* twin to evaluate proposals
- Modeling and Visualization is the bridge: parametric CAD ↔ ABM re-validation ↔ photoreal Omniverse twin
- Without M&V, Phase 1-3 results stay in research notebooks; with it, they reach decision-makers

## Slide 4 — Where This Fits
- **Input — Phases 1-3 (this repo, completed earlier):**
  - Converged variable matrix (`data/robot_params/variable_matrix.csv`)
  - Ranked friction-point list
  - Baseline + final-proposal Pareto comparison
- **This proposal — Phases 4-6:**
  - Phase 4 — AI + CAD optimization (Fusion 360 / Rhino / Blender)
  - Phase 5 — ABM re-simulation verification (SUMO + Mesa)
  - Phase 6 — High-fidelity scene + Isaac Sim validation (NVIDIA Omniverse)
- **Output — for stakeholders:**
  - Interactive Omniverse demo session
  - Photoreal renders + walkthrough video
  - CAD source + USD asset bundle

## Slide 5 — What Is the M&V Pipeline?
- A four-stage pipeline that converts a parameter matrix into a visualizable, validated twin
- Stage A — Parametric CAD from variable matrix (Phase 4)
- Stage B — Re-abstract CAD parameters back into ABM, verify gains hold (Phase 5)
- Stage C — Assemble high-fidelity USD scene of Nihonbashi 200 m segment (Phase 6 part 1)
- Stage D — Drop robot into Isaac Sim, validate motion + sensors + physics (Phase 6 part 2)
- Each stage produces an artifact that the next stage consumes — no manual re-work

## Slide 6 — M&V Pipeline Architecture
- Visual: horizontal pipeline diagram, 4 stages with arrows
- Stage A: Variable matrix → Fusion 360 / Rhino → CAD model (.f3d, .stp)
- Stage B: CAD parameters → SUMO + Mesa → run report (`outputs/reports/phase5_revalidation.md`)
- Stage C: PLATEAU CityGML + OSM + materials → USD assets → Omniverse scene
- Stage D: USD scene + robot CAD → Isaac Sim → motion + sensor + physics validation
- Feedback arrow: failures at B or D loop back to Stage A with documented residuals

## Slide 7 — Inputs from Phases 1-3
- Variable matrix (17 rows × 5 columns) — the canonical parameter contract
- Ranked friction-point list with severity and spatial location
- Pareto-non-dominated proposal vs. Starship baseline
- Heat-cost field per sidewalk segment (already joined)
- Run-config provenance for reproducibility
- All committed in the upstream `nihonbashi-robot-sim` repo (this same repo)

## Slide 8 — Phase 4: AI + CAD Optimization
- AI step — summarize residual friction points, propose CAD-level modifications (form, module placement, docking strategy)
- Designer step — Xilin selects, critiques, integrates against Nihonbashi context + METI 2023 rules
- CAD step — Fusion 360 / Rhino parametric model with explicit dimensions, structural relationships, modular cargo bays, manufacturability
- Output — `.f3d` source + `.stp` neutral export + parameter mapping back to ABM variable matrix
- Acceptance — every variable in the matrix has a corresponding CAD parameter; manufacturability review passes

## Slide 9 — Phase 5: ABM Re-simulation Verification
- Re-abstract CAD-derived robot into ABM parameters (width, length, speed, turning radius, docking duration, service modules)
- Three-tier comparison: Starship baseline (Phase 1) · initial Heat-Support proposal (Phase 2/3) · CAD-optimized robot (Phase 4)
- Same scenarios, same windows, same seeds, same metrics — only the proposal changes
- Goal: confirm CAD geometry choices do not erase macroscopic gains identified in Phase 3
- Output — `outputs/reports/phase5_revalidation.md` with the three-way Pareto comparison

## Slide 10 — Phase 6 (Part 1): High-Fidelity Scene
- Convert PLATEAU CityGML LOD1/LOD2 to USD via the Aerial Digital Twin Scene Importer (NVIDIA Omniverse)
- Augment with PBR materials, signage, street furniture, vegetation, lighting rigs
- Bake heat-cost field as a USD attribute on sidewalk meshes for visualization
- Populate with animated pedestrian crowds matching the ABM density per segment
- Add weather conditions (cloud cover, sun angle, ambient light) per heat scenario
- Output — `scene/nihonbashi_200m.usd` ready for real-time playback

## Slide 11 — Phase 6 (Part 2): Isaac Sim Robot Validation
- Import the Phase 4 CAD into Isaac Sim with rigid-body physics + sensor stack
- Sensors: cameras (RGB + depth), 2D lidar, ultrasonic, IMU — matching planned robot sensor suite
- Validate motion: turning radius, slope handling, docking maneuvers
- Validate sensor behavior: object detection under shade vs. sun, occlusion by pedestrians, low-contrast pedestrian clothing
- Validate physical interaction: collision avoidance, cargo-module swap, charging-station docking
- Output — Isaac Sim scene + recorded validation runs (USD + MP4)

## Slide 12 — Asset Inventory: What We Have
- 7-row table: asset / source / format / coverage / quality / owner
- PLATEAU CityGML LOD1/LOD2 — PLATEAU VIEW 4.0 — CityGML — full district — ★★★★ — Sam
- OSM sidewalk graph — OSMnx — GraphML / .net.xml — full district — ★★★★ — Yi Tai
- Heat-cost field — Phase 1-3 output — per-segment scalar — full segment — ★★★★ — Sam
- Variable matrix — Phase 1-3 output — CSV — final column — ★★★★★ — Xilin
- Pedestrian density profiles — Phase 1-3 output — per-scenario CSV — 12 combos — ★★★★ — Yi Tai
- Starship reference geometry — public spec — approximate — snapshot — ★★ — Yi Tai
- Existing studio renders — Xilin's deck — image — illustrative only — ★★★ — Xilin

## Slide 13 — M&V Asset Gaps
- **Critical:**
  1. PLATEAU LOD3 geometry for the 200 m segment (LOD2 lacks facade detail for photoreal renders)
  2. PBR material library for building facades, sidewalks, signage (Japanese-context-appropriate)
  3. Animated pedestrian crowd library compatible with Omniverse / USD
  4. Robot CAD source (output of Phase 4; gating dependency)
  5. Sensor specifications for the proposed robot (cameras, lidar model, ultrasonic) — fidelity targets
- **Should-have:**
  6. Vehicle and bicycle assets for adjacent street activity
  7. Audio environment (street ambience, robot cue sounds)
  8. Tokyo time-of-day skybox / HDRI library
  9. Sign-language / Japanese text on signage

## Slide 14 — Asset Acquisition Plan
- Gap 1 LOD3 — combine PLATEAU LOD2 + manual modeling of hero buildings + photogrammetry-from-photos for facade detail — Sam — weeks 2-4
- Gap 2 PBR materials — Quixel Megascans (Tokyo-context curated) + Substance for custom signage — Xilin — week 2
- Gap 3 Crowd library — Omniverse SimReady characters + custom retarget; fallback Mixamo via Maya bridge — Sam — week 3
- Gap 4 Robot CAD — depends on Phase 4 completion (week 4-6 of this scope) — Xilin — gating
- Gap 5 Sensor specs — Starship reference + proposal-specific augmentation — Yi Tai — week 1
- Gap 6 Vehicle/bike — Omniverse SimReady library — Sam — week 3
- Gap 7 Audio — Freesound + custom-recorded cues — Xilin — week 6
- Gap 8 HDRI — Polyhaven Tokyo HDRI set + custom captures — Sam — week 2
- Gap 9 Signage — manual via Substance Designer / Photoshop — Xilin — week 4

## Slide 15 — Visualization Fidelity Metrics
- Visual: how "good" is each rendering pass?
- Geometric fidelity — Hausdorff distance between PLATEAU LOD3 and reference orthophoto < 1.0 m
- Material plausibility — designer + advisor blind A/B against real photos; > 70 % cannot tell
- Real-time playback — 30+ FPS in Omniverse Kit at 1080p on a single RTX 4090
- Sensor accuracy — Isaac Sim camera output reproduces real-camera color and exposure within ΔE < 5
- Crowd believability — pedestrian density and motion match observed Nihonbashi GPS within ±15 %
- Robot motion plausibility — turning radius, docking, avoidance match Phase 5 ABM trajectories within 0.5 m

## Slide 16 — Tooling Stack
- **CAD:** Fusion 360 (parametric primary) · Rhino + Grasshopper (organic surfaces) · Blender (cleanup, export)
- **3D format:** USD / OpenUSD as the lingua franca; .stp for engineering hand-off
- **Scene assembly:** NVIDIA Omniverse Kit · USD Composer · Aerial Digital Twin Scene Importer
- **Robot simulation:** NVIDIA Isaac Sim (PhysX, sensors, RL hooks) · Isaac Lab for policy training
- **Materials:** Adobe Substance Designer / Painter · Quixel Megascans
- **Connectors:** OSMnx → Blender → USD · PLATEAU → USD · ArcGIS → Omniverse (CityEngine bridge)
- **Versioning:** Git LFS for binaries; OneDrive for > 50 MB assets

## Slide 17 — Hardware & Compute
- Minimum dev workstation: RTX 4090, 64 GB RAM, 2 TB NVMe — one per active developer (Sam + Xilin)
- Recommended: RTX 6000 Ada Generation for headroom on path-traced renders + Isaac Sim simultaneous sessions
- Cloud option: NVIDIA DGX Cloud BYOL for batch high-resolution render passes + parallel Isaac Sim training runs
- Storage: 500 GB local SSD per developer + 2 TB shared NAS / OneDrive for USD asset library
- Software licenses: Omniverse Kit + Isaac Sim (free for individual / educational); Fusion 360 (educational); Substance (educational)

## Slide 18 — Team & RACI
- **Sam (M&V lead):** Omniverse pipeline, USD asset bridge, scene assembly, real-time playback, stakeholder demo
- **Xilin (Design lead):** Fusion 360 / Rhino CAD, materials, signage, robot industrial design refinement
- **Yi Tai (ABM re-sim):** Phase 5 re-validation runs, sensor-spec definition, motion-plausibility metric
- **Qinghao (Domain):** Thermal validation, lighting / weather conditions per heat scenario, scientific advisor
- RACI table on next slide

## Slide 19 — 12-Week Timeline
- Week 1: Asset gap closure kickoff; tooling install; LOD3 + PBR strategy lock
- Weeks 2-3: PLATEAU → USD scene assembly; PBR material pass; crowd library integration
- Weeks 4-6: Phase 4 CAD optimization in Fusion 360 (gates Phase 5)
- Weeks 5-7: Phase 5 ABM re-simulation with CAD-derived parameters
- Weeks 6-9: Isaac Sim robot import + sensor validation + motion validation
- Weeks 8-10: High-fidelity scene polish; lighting rig per scenario; crowd choreography
- Week 11: Stakeholder rehearsal; render passes for video; comparison report assembly
- Week 12: Stakeholder demo session + final deliverable hand-off
- Three milestone reviews: W3 (scene+crowd), W7 (Phase 5 verdict), W11 (Isaac Sim sign-off)

## Slide 20 — Risks, Asks, Decisions
- **Risks:**
  - Omniverse / Isaac Sim learning curve consumes weeks 1-3 → mitigation: targeted NVIDIA training + pair with Isaac Lab tutorials
  - PLATEAU LOD3 unavailable for Nihonbashi → mitigation: LOD2 + photogrammetry + manual hero buildings
  - GPU constraints → mitigation: DGX Cloud BYOL for spike loads
  - Phase 4 CAD slips → Phase 5 + 6 cascade → mitigation: parameter-only Phase 5 dry run while CAD is in flight
- **Asks:**
  - Two RTX 4090 workstations (Sam + Xilin) for the 12-week sprint
  - DGX Cloud BYOL budget: ~$1,500 for batch rendering + Isaac Sim training spikes
  - Omniverse Enterprise discussion with NVIDIA Inception (if applicable)
  - Substance + Megascans access (often via Adobe Creative Cloud educational)
  - Stakeholder slot of 60 min at end of week 12 for demo session
- **Decisions:**
  - Approve M&V scope (Phases 4-6), 12-week sprint
  - Approve hardware + budget asks
  - Approve kickoff for week of 2026-05-19
