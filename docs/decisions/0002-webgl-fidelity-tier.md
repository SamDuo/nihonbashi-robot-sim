# ADR 0002 — Add a contract-frozen WebGL high-fidelity twin tier (L2)

**Date:** 2026-06-12
**Status:** accepted

## Context

Stage One ships two visualization tiers: the Streamlit metrics dashboard (L0) and the Cesium + PLATEAU geospatial twin (L1). The Phase 4–6 plan targets Omniverse/Isaac Sim (L3), but that tier is blocked on PACE allocation and LaunchPad access. The team needs a **high-fidelity, real-time, stakeholder-facing twin now** — street-level multi-agent animation, day/night cycle, heat-field overlay, perception-style detection HUD — for the urban-heat-risk study, runnable in a browser on a student laptop with testbed data.

Options considered (full matrix in [high_fidelity_twin_architecture.md](../high_fidelity_twin_architecture.md) §5): extending Cesium, deck.gl, Unity/Unreal, jumping straight to Omniverse, or a custom Three.js renderer.

## Decision

Add an **L2 tier**: a dependency-free Three.js renderer (`outputs/twin_view.html`) behind a **frozen JSON contract** produced by `scripts/export_twin_frames.py`:

- `outputs/twin/scene.json` — static geometry (grid, roads, buildings, shelters)
- `outputs/twin/frames_<scenario>.json` — per-hour heat field, agent tracks, robot tracks, shelter occupancy, headline metrics

The renderer consumes only these files. Geometry is procedural (seeded) in V1; real OSM/PLATEAU footprints and the G1 heat raster replace the exporter's *producers* in Stage Two while the contract — and therefore the renderer — stays unchanged.

L1 (Cesium/PLATEAU) remains the geospatial ground truth. L2 is the experiential/operational view. L3 consumes the same contract via a future USD exporter.

## Consequences

- Renderer and simulator evolve independently; real-data swaps never touch rendering code.
- A second geometry path exists until V2 unifies it from real footprints — accepted and documented.
- Every stylized element (robot interpolation, detection confidences, procedural buildings) is recorded in the architecture doc's honesty ledger and must stay current.
- The detection-HUD visual language is fixed now so Phase 5 can swap in real RTVI/RT-DETR outputs without redesign.
- No build step, no npm: Three.js via CDN import map, consistent with the existing Cesium page.
