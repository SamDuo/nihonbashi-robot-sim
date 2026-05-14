# Variable Matrix

Canonical home: `data/robot_params/variable_matrix.csv`. This document explains the schema.

## Columns

| Column | Type | Notes |
|---|---|---|
| `category` | enum | `environmental`, `product`, `human_behavior`, `task`, `design_cue` |
| `variable` | str | Variable name (snake_case) |
| `unit` | str | Unit string (e.g. `mm`, `km/h`, `enum`) |
| `baseline_value` | str | Starship value from Phase 1 |
| `proposal_v1_value` | str | Heat-Support Robot v1 from Phase 2 |
| `proposal_v2_value` | str | After iteration 1 of Phase 3 |
| `proposal_v3_value` | str | After iteration 2 of Phase 3 |
| `final_value` | str | After convergence |
| `design_rationale` | str | Why the proposal differs from baseline |
| `friction_point_ids` | csv | Comma-separated friction-point IDs that motivated the change |
| `owner` | str | Who edits this row |

## Category definitions (per Methodology PDF Stage Three)

- **Environmental parameters** — street width, pedestrian density, subway exits, commercial entrances, intersections, service nodes
- **Product attributes** — dimensions, speed, turning radius, docking method, service modules
- **Human behavior** — commuting, shopping, lingering, avoidance, group movement, brief pauses
- **Task conditions** — delivery frequency, service paths, task priority, docking duration
- **Design cues** — lighting, sound, screen info, motion rhythm, waiting-area layout
