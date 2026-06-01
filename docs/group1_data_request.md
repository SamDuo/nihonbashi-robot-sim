# Group 1 (Urban Risk) — Data Request for Nihonbashi DT integration

| | |
|---|---|
| **From** | Group 3 — Urban Digital Twins (Sam Duong) |
| **To** | Group 1 — Urban Risk (Qinghao + team) |
| **Date** | 2026-06-01 |
| **Status** | Stage One demo runs on synthetic data. To produce a real research result we need to swap in Group 1's actual outputs. Schemas are already locked, loaders are written — drop-in replacement, no code change. |
| **Repo** | https://github.com/SamDuo/nihonbashi-robot-sim |

---

## What we ingest from Group 1 (three files)

Schema is locked in [`docs/system_architecture.md` §7a](system_architecture.md) and consumed by `sim/testbed/population.py`, `sim/testbed/heat_field.py`, and the planned occupancy hook in `world.py`. The Stage One synthetic generators already match these schemas — so as soon as your file lands, the testbed picks it up.

### 1. `population.csv` — synthetic / sampled population with vulnerability scoring

| Column | Type | Domain / unit | Notes |
|---|---|---|---|
| `agent_id` | string | unique per row of *agent identity* (one ID covers all 24 hours of that person) | e.g. `a000`–`a09999` for 10 k agents |
| `age_bucket` | enum | `child` / `adult` / `elderly` | Group 1 to confirm bucket boundaries |
| `occupation_class` | enum | `worker` / `commuter` / `visitor` / `resident` / `student` | Drives the daily activity pattern |
| `mobility_class` | enum | `mobile` / `assisted` / `restricted` | Used to flag vulnerable agents in the policy layer |
| `vulnerability_score` | float | `[0.0, 1.0]` | Composite from your vulnerability index (health, income, housing, age, mobility). Higher = more at risk |
| `home_grid_cell` | string | `g_<x>_<y>` or `chome_<code>` | See "Grid alignment" below |
| `hour` | int | `[0, 23]` | 24 rows per agent |
| `activity_grid_cell` | string | same encoding as `home_grid_cell` | Where this agent expects to be at this hour |

**Cadence:** one row per agent per hour. For Stage Two we are targeting **~10 000 agents** for Nihonbashi (Chuo-ku slice). A 1 000-agent sample is acceptable for first integration.

**Use:** drives the ABM. Each agent's vulnerability + mobility + planned activity drives whether the policy layer (`baseline` / `reactive` / `proactive`) routes them to a shelter.

### 2. `heat_field.npy` (or NetCDF / GeoTIFF) — hourly heat-cost raster

| Property | Value |
|---|---|
| Shape (Stage One) | `(24, 20, 10)` — hours × grid_x × grid_y on our 1 000 m × 500 m, 50 m-cell grid |
| Shape (Stage Two target) | UTCI raster at **5 m resolution** for full Chuo-ku slice, 24-hour cycle |
| Value semantics | **heat-cost factor**, dimensionless, range `[0.0, ~2.0]`. A value of 1.0 ≈ neutral; >1 means agent accumulates exposure faster. We compute the cost factor in our loader if Group 1 supplies raw UTCI (°C) or Heat Index (°F) instead — see "Acceptable substitutions" below. |
| Coordinate system | EPSG:6677 (JGD2011 / Japan Plane Rectangular CS IX) or EPSG:4326 lat/lng |
| Anchor | Nihonbashi SW corner `(35.6810°N, 139.7720°E)` — but Group 1's native extent is fine, we'll clip |

**Acceptable substitutions** (in order of preference):

1. NumPy `.npy` matching shape `(24, X, Y)` with heat-cost factor — drop-in, fastest.
2. GeoTIFF stack (one tile per hour) with raw **UTCI in °C** — our loader converts via published thermal-comfort thresholds.
3. NetCDF with `time × lat × lng` dimensions on **Heat Index (°F)** — also fine, same conversion.
4. CSV of per-grid-cell per-hour values — only as fallback for very coarse rasters.

**Use:** the heat-cost grid is the scalar field that pedestrian agents accumulate exposure from, and that the policy layer's 4-hour lookahead reads to decide whether to pre-position vulnerable agents to a cooled shelter.

### 3. `occupancy.csv` — hourly building / parcel occupancy

| Column | Type | Notes |
|---|---|---|
| `building_id` | string | Should match the `building_id` Group 2 (Urban Regeneration) uses for shelter envelopes — coordinate before sending |
| `hour` | int | `[0, 23]` |
| `occupants_total` | int | All people expected inside the building this hour |
| `vulnerable_weighted_occupants` | float | `Σ (occupants × vulnerability_score)` for occupants of this building this hour |

**Cadence:** hourly per building. Initial set should cover the ~3 candidate cooling shelters in our scene (`shelter_north`, `shelter_mid`, `shelter_south`); long-term every building inside the Chuo-ku clip.

**Use:** baseline occupancy lets us measure whether the proactive policy *displaces* normal building use, not just fills empty space. Critical for the "infrastructure compatibility" metric.

---

## Grid alignment — please confirm before delivery

Our Stage One scene is anchored on **Nihonbashi Bridge area, Chuo-ku** with a **20 × 10 grid of 50 m cells** = 1 000 m × 500 m extent (`sim/testbed/scene.py`). Anchor:

- SW corner: 35.6810 °N, 139.7720 °E
- NE corner: 35.6855 °N, 139.7826 °E
- All cells inside Chuo-ku (east of Sotobori-dori), covered by the PLATEAU Chuo-ku LOD2 3D Tiles

**Two ways Group 1 can align:**

- **Option A (preferred):** match the same 20 × 10 grid at 50 m resolution. We resample your finer UTCI raster down to this grid in our loader.
- **Option B:** deliver at your native resolution (e.g. UTCI 5 m) with a clear CRS + extent; we clip and resample on ingest.

---

## Reference & supplementary data (nice-to-have, not blocking)

These would let us validate Group 1's modelled raster against observations:

| Layer | Source | Format |
|---|---|---|
| **JMA AMeDAS** station observations within Chuo-ku + Chiyoda-ku | Japan Meteorological Agency | CSV time-series |
| **Landsat 8 / 9 thermal band** surface temperature | USGS, JAXA | GeoTIFF |
| **Heat-island intensity** layer (observed − rural baseline) | Group 1 derived | GeoTIFF |
| **Tokyo Open Data pedestrian counts** | Tokyo Metropolitan Gov | CSV per intersection |

---

## Acceptance criteria — what "good enough to integrate" means

For Stage Two integration we need, at minimum:

- [ ] One **representative day's** heat field (24 hours covering one of: `cool_baseline`, `moderate`, `high`, or `extreme` heat scenario from your Random Forest classifier).
- [ ] A **synthetic population of at least 1 000 agents** matching the schema above, with vulnerability scoring already applied.
- [ ] Occupancy rows for **at least the three candidate shelter buildings** for the same 24-hour window.
- [ ] CRS, grid alignment, and units explicitly documented (we'll add to `data/heat_risk/README.md`).
- [ ] An obvious named version (e.g. `nihonbashi_heatfield_2026-08-15_extreme_v1.npy`) so the loader can record provenance.

If the full set is too heavy for a first drop, the **minimum viable subset** is:

1. `heat_field.npy` for one extreme-heat day at 50 m resolution on our grid.
2. `population.csv` for 1 000 agents.
3. We'll keep the synthetic occupancy stub until full data lands.

That gets the testbed running on real exposure values within hours of receiving the files.

---

## What Group 1 gets back from us (feedback loop)

Per the locked contract ([`system_architecture.md` §7d](system_architecture.md)):

- **`exposure_hotspots.csv`** — grid cells where the simulated population accumulates disproportionate vulnerability-weighted exposure. This is your QA loop: cells where our DT says "people are getting cooked" should agree with your input raster.
- **`cooling_gap_residuals.csv`** — agents and hours with no feasible shelter (helps Group 1 prioritize which heat hotspots most need new cooling capacity).

---

## Logistics

- **Delivery channel:** anywhere works — shared OneDrive, ArcGIS Online layer, direct file drop. We'll mirror into `data/heat_risk/` in the repo (gitignored if large; `data/heat_risk/README.md` records provenance).
- **Format conversion:** if your native pipeline emits something else (xarray Datasets, .grib, .nc), we handle the conversion in the loader — don't reformat on your side.
- **Schema questions / changes:** open an issue against [SamDuo/nihonbashi-robot-sim](https://github.com/SamDuo/nihonbashi-robot-sim) or message Sam.

---

## TL;DR for an email or chat

> Group 1 — we need three files to drop our Nihonbashi DT off synthetic data:
> 1. `population.csv` — ~1 000+ agents × 24 hours, with vulnerability_score column.
> 2. `heat_field.npy` (or GeoTIFF/NetCDF) — 24-hour heat raster on our 50 m grid over Chuo-ku, one representative extreme-heat day.
> 3. `occupancy.csv` — hourly occupant counts + vulnerable-weighted occupants for at least 3 candidate shelters.
>
> Schemas are locked in [`docs/system_architecture.md` §7a](https://github.com/SamDuo/nihonbashi-robot-sim/blob/main/docs/system_architecture.md). Loaders are written, drop-in replacement, no code change. Even a 1 000-agent / one-day MVP unblocks the team. Detailed spec in [`docs/group1_data_request.md`](https://github.com/SamDuo/nihonbashi-robot-sim/blob/main/docs/group1_data_request.md).
