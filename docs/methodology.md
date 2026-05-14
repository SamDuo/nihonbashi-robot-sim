# Six-Stage Research Methodology

Source: Xilin Tang, "Research Methodology: A Six-Stage Toolchain" (May 2026).

The full methodology is a closed loop. This repository executes **Phases 1–3** and prepares parameters for Phase 4. Phases 4–6 happen in a downstream environment that uses CAD tools and NVIDIA Omniverse / Isaac Sim.

---

## Phase map

| Phase | Name | Primary task | Tools |
|---|---|---|---|
| 1 | Literature Review, Concept Map, Baseline ABM | Establish theoretical foundation and abstract the Starship sidewalk robot into ABM-readable parameters; run baseline in Nihonbashi scene | Literature, SUMO, ABM (Mesa) |
| 2 | Product Concept Design | Translate friction points from Phase 1 into a new design hypothesis — the Nihonbashi Heat-Support Robot — with body, modules, interaction cues, and service flow | Generative AI for concept expansion; designer judgment for selection |
| 3 | Scenario + Variable Matrix → Initial SUMO/ABM A/B Simulation | Construct the 200 m street segment scene, build the variable matrix with baseline vs. proposal, run A/B simulation, identify residual issues | SUMO, ABM, GIS heat-risk layer as cost field |
| 4 | AI + CAD Optimization | Convert ABM output into a manufacturable CAD model | Fusion 360, Rhino, Blender + AI assist |
| 5 | ABM Re-simulation Verification | Verify macroscopic gains from the CAD-optimized design | SUMO, ABM |
| 6 | High-Fidelity Scene + Validation | Build the high-fidelity twin and visually validate | NVIDIA Omniverse, Isaac Sim |

---

## Role of each tool (concept map)

- **SUMO + ABM** — macro-level behavioral simulation; emergent system phenomena.
- **GIS heat-risk layer** — provides the scalar field (heat exposure per parcel and per sidewalk segment) consumed by both pedestrian agents and the robot.
- **AI tools** — data analysis, problem induction, design-possibility expansion.
- **Industrial design** — problem interpretation and translation of macro problems into micro variables.
- **CAD (Fusion 360)** — engineering layer; converts conceptual schemes to parametrized models.
- **Omniverse / Isaac Sim** — high-fidelity digital twin for robot-level validation.

---

## Iterative feedback loop (Phases 1–3 close-up)

```
              ┌─────────────────────────────────────────┐
              │  Phase 1: Starship baseline in scene    │
              │           ↓                              │
              │  Identify friction points                │
              │           ↓                              │
              │  Phase 2: Concept design + variables     │
              │           ↓                              │
              │  Phase 3: A/B simulation, baseline vs.   │
              │           proposal, six metrics          │
              │           ↓                              │
              │  Diagnose residuals (designer review)    │
              │           ↓                              │
              │  Update variables ──→ re-run Phase 3     │
              └─────────────────────────────────────────┘
                          ↓ on convergence
                   Hand off to Phase 4 (CAD)
```

**Convergence criteria:**
- Pareto-non-dominated across the six evaluation metrics, OR
- Three iterations without measurable improvement, OR
- Designer override with documented rationale in `docs/decisions/`.

---

## Six evaluation metrics (Phase 1 → 3, propagated to Phases 5–6)

1. **Human Outdoor Labor Substitution Rate** — % of outdoor delivery / patrol / resupply replaced by robots.
2. **Human Heat Exposure Reduction** — reduction in cumulative heat exposure for human staff vs. baseline.
3. **Service Continuity** — service uptime under high-heat conditions.
4. **Resource Delivery Efficiency** — package-delivery throughput across tasks and scenarios.
5. **Pedestrian Interference** — pedestrian detours, reduced speed, docking conflicts.
6. **Infrastructure Compatibility** — robot's fit with existing streets, supply points, charging stations, service nodes.

Each metric has a quantitative definition in `analysis/metrics.py` (Phase 1 deliverable).
