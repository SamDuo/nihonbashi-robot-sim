# Phase 1 — Starship Baseline ABM Test Protocol

**Owners:** Yi Tai (ABM) · Sam Duong (heat-risk layer) · Qinghao (thermal theory)
**Status:** scoping
**Deliverables:**
1. Starship parameter abstraction (`data/robot_params/starship_baseline.csv`)
2. Baseline simulation environment for a 200 m Nihonbashi street segment (`sim/sumo/nihonbashi_200m/`)
3. Run results across four heat scenarios × three traffic windows (`sim/runs/phase1_baseline/`)
4. Ranked friction-point list feeding Phase 2 (`docs/phase1_friction_points.md`, generated)

---

## 1. Starship parameter abstraction

Source: Starship Technologies public specifications + Xilin's Phase 1 slide.

| Parameter | Value | Unit | Notes |
|---|---|---|---|
| Body width | 569 | mm | Front |
| Body length | 697 | mm | Side |
| Body height | 616 (1187 with flag) | mm | Flag adds 571 mm |
| Max speed | 6 | km/h | Sidewalk-class |
| Turning radius | ~0.8 | m | Differential drive |
| Payload | 10 | kg | Estimate from public specs |
| Docking duration | 30 | s | At service node |
| Avoidance behavior | reactive | enum | "stop and replan" |
| Service frequency | 12 | tasks/hr | Per robot, peak |
| Charging logic | return-to-hub | enum | At 20 % battery |

All values get committed to `data/robot_params/starship_baseline.csv` as the canonical row, with a `source_url` column.

---

## 2. Scene — 200 m Nihonbashi street segment

Selected segment: TBD — Yi Tai to confirm. Candidates: section north of Nihonbashi Bridge along Chuo-dori; alternative near Mitsukoshi-mae station exit. Must include:

- A commercial entrance
- A subway exit
- Two service nodes
- One docking area
- A primary pedestrian flow path

Built from OSM via `osmnx` (see `scripts/build_abm_baseline.py`), exported to SUMO `.net.xml`. Heat-risk layer joined onto sidewalk segments — see Section 4.

---

## 3. Test scenarios (4) × traffic windows (3)

**Heat scenarios** (from the Random Forest classifier in the parent Tokyo Studio repo):

- `cool_baseline` — May/June reference, no heat advisory
- `moderate` — Heat Index 80-90 °F
- `high` — Heat Index 90-105 °F
- `extreme` — Heat Index > 105 °F (validated heatwave day)

**Traffic windows:**

- `morning_peak` — 07:30–09:00 commute
- `midday_delivery` — 12:00–13:30 delivery + lunch crowd
- `afternoon_heat` — 14:00–16:00 (overlaps `high` and `extreme`)

12 combinations × at least **50 replicates** per combination with distinct RNG seeds. Total: 600 runs minimum. Run config and seeds committed to `sim/runs/phase1_baseline/run_config.json`.

---

## 4. Heat-risk layer → ABM cost field

This is the bridge from the parent Tokyo Studio repo (Random Forest heat-scenario classifier on NWS Heat Index) into the ABM.

Pipeline:

1. Pull the per-parcel heat-scenario label from the parent repo's classifier output.
2. Join onto OSM sidewalk segments by spatial intersection (centroid of segment).
3. Compute a continuous `heat_cost` per segment: `heat_cost = base_cost × (1 + heat_factor)` where `heat_factor ∈ {0.0, 0.5, 1.0, 1.5}` for cool / moderate / high / extreme.
4. Write to ABM as edge attribute.
5. Pedestrian agents use `heat_cost` in route choice (weighted Dijkstra). Robot uses it for service-path optimization. Per-agent `heat_exposure` accumulator integrates `heat_cost × dwell_time` along the trajectory.

Script: `scripts/build_heat_cost_field.py` (Sam).

---

## 5. Friction points to watch

From Xilin's Phase 1 slide 10 ("Define Problem Requirements") and Methodology PDF Stage Four:

- Pedestrian detours caused by docking
- Mainline / robot trajectory intersections
- Docking conflicts at service nodes
- Speed mismatches with pedestrian crowd
- Task delays under high pedestrian density
- Heat-exposure overlap (robot serving in shade vs. heat island)

Each observation gets a row in the auto-generated `docs/phase1_friction_points.md` with `metric`, `value`, `scenario`, `severity`.

---

## 6. Hand-off to Phase 2

Phase 2 consumes:
- The ranked friction-point list
- The baseline run summary statistics
- The variable matrix with Starship column populated

It produces the second column ("Nihonbashi Heat-Support Robot proposal") of the variable matrix.
