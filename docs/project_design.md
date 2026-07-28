# Project Design

## From Georeferenced Digital Twin to Omniverse: What Fidelity Does a Block-Scale Urban Energy Decision Actually Require?

### A calibration and fidelity-evaluation study of an energy, heat, and mobility twin of Nihonbashi, Tokyo

**Student:** Sam Duong
**Advisor:** Dr. Perry Yang, Georgia Institute of Technology (Eco Urban Lab, performance-driven urbanism)
**Course:** Graduate independent study, field study deliverable
**Prepared:** July 28, 2026 | **Due:** July 31, 2026
**Publication track:** CUPUM 2027 book chapter, "Future Cities in the Era of AI" (TU Delft OPEN)

---

## 1. Abstract

This project asks a narrow, measurable question about a block in Nihonbashi, Tokyo: does replacing flat archetype and pro-rata energy assumptions with per-building energy use intensity and mobility-derived occupancy materially change the cost-optimal sizing of distributed solar and battery storage, at the building and at the block scale? The study is built on a working, browser-deployable digital twin of 22 buildings that already couples building geometry, retrofit parameters, a district supply optimization, a heat-cost field, and pedestrian mobility ping data. Diagnostic work completed for this design document produced a preliminary result that reframes the project: the per-building energy values currently in the twin are not a model output at all but a single district total divided pro rata by floor area, and 48.1 percent of that district total is electric vehicle and bus charging, not building load. Real per-building intensities exist in the studio workbooks and are unused. Correcting this is the first phase of the work. The second phase reframes the project's fidelity ladder, from web twin to game-engine or Omniverse simulation, as an evaluation framework rather than a migration roadmap: the study is designed to report, for each of three concrete urban design decisions, the lowest fidelity tier at which the decision stops changing. One of those decisions (D-3) requires the L3 tier, whose GPU access is not yet secured, so a tier may be reported as unexecuted with a stated argument about what it would have added rather than as an executed comparison. The contribution the author independently owns is the integration pipeline, the twin itself, the calibration and reconciliation method, and the fidelity evaluation. Teammate-produced datasets are used with an explicit and currently unresolved attribution boundary, described in Section 12.

---

## 2. Hero figure slot

> **FIGURE 0 (to be produced Day 1, placed here).** A two-panel screenshot of the working twin. Left panel: the block colored by corrected per-building energy intensity in the Cesium energy view. Right panel: the same block in the high-fidelity PLATEAU city view with the heat field on. Caption states the block, the building count, the data vintage, and the georeferencing basis: the default LOD2 city path places every vertex by its true ECEF position, so the buildings share the street frame by construction, and the Cesium view streams the official PLATEAU tileset in its own geodetic frame. The caption also notes that the visual confirmation against the OSM road centerlines is still pending.

Live views in this repository, both browser-runnable with no build step:

| View | File | What it shows |
|---|---|---|
| Energy twin (Cesium, primary) | `outputs/energy_cesium_view.html` | 22 study buildings in real WGS84 position, on a designed streetscape base with georeferenced PLATEAU LOD2 context (Bing imagery via `?base=bing`, Google photoreal tiles via `?tiles=google`); metric and demand and supply toggles, hourly occupancy scrub |
| Energy twin (three.js, offline) | `outputs/energy_view.html` | Same scene with no map-tile, terrain, or Cesium Ion-token dependency (three.js itself is loaded from the unpkg CDN), used for headless QA |
| High-fidelity city twin | `outputs/cesium_view.html`, `outputs/twin_view.html` | PLATEAU LOD2 city mesh, streetscape, heat field, robot agent testbed |
| Landing redirect | `outputs/index.html` | Redirects to the energy view; deployed to a static host (Vercel) |

The repository contains no `vercel.json` and no `.vercel` directory, so the hosting project name is not recorded anywhere in the code. Both the public deployment URL and the deployment project name must be confirmed against the hosting dashboard and pasted into this table before the July 31 upload.

---

## 3. Research questions and success criteria

### 3.1 Primary question (falsifiable, measurable)

> **Does per-building energy use intensity derived from the studio's simulation workbooks, combined with mobility-ping-derived occupancy schedules, materially change the cost-optimal PV and battery sizing for a Nihonbashi block, relative to the flat pro-rata and flat-schedule assumptions currently embedded in the twin?**

"Materially" is defined in advance so the question can fail:

| Criterion | Threshold for "yes, it matters" |
|---|---|
| Block-scale PV sizing | Cost-optimal PV capacity changes by more than 10 percent from the current 417 kW |
| Block-scale storage sizing | Cost-optimal storage energy changes by more than 10 percent from the current 783 kWh |
| Building-scale ranking | The rank order of the 22 buildings by energy intensity changes for more than 5 buildings, measured by Spearman rank correlation below 0.9 against the pro-rata ordering |
| Retrofit priority | The set of the top 5 retrofit candidates by absolute annual savings changes by at least 2 members |

If none of these thresholds is crossed, the answer is "no", and that is a publishable negative result: it would say that at block scale a pro-rata split is a defensible approximation for supply sizing, which is a useful finding for practitioners.

### 3.2 Secondary question (methods)

> **At which fidelity tier does the answer to a given urban energy decision stop changing?**

For each of the three design decisions in Section 4, the study reports the lowest tier in the L1 to L3 ladder (Section 7) at which the recommended action is stable. The deliverable is a decision-by-tier matrix, not a claim that higher fidelity is better.

### 3.3 What this project does not claim

It does not claim a validated building energy model. There is no metered kWh ground truth for these buildings. It does not claim that agentic or LLM-driven scenario exploration is novel; two 2025 to 2026 papers already do that (Section 13). It does not claim a real-time or operational twin.

---

## 4. Design decisions this twin is meant to answer

The test of an urban twin is whether a designer or a district manager would act differently after looking at it. Three decisions are in scope, each mapped to a planned figure.

| # | Decision question | Who asks it | Figure |
|---|---|---|---|
| D-1 | Given a fixed retrofit budget, which of the 22 buildings should be renovated first? | Block owner, district regeneration council | F1, F2 |
| D-2 | How much solar and battery should the block procure collectively, and does the answer depend on modeling who is actually inside the buildings? | District energy operator | F3, F5 |
| D-3 | Does the retrofit and electrification program make the street warmer or cooler for pedestrians and delivery robots, once rejected heat is accounted for? | Urban designer, public-space planner | F6 (outlook) |

D-1 and D-2 are answerable with Phase A work described in Section 8. D-3 requires the closed loop described in Section 5 and is scoped as outlook for the CUPUM chapter.

---

## 5. Contribution, stated honestly

The earlier framing of this project claimed novelty by conjunction: first to combine archetype building energy modeling, supply optimization, a heat field, and mobility-derived occupancy in one georeferenced scene. That framing does not survive review. Combining four existing things is integration work, not a research contribution, and reviewers say so.

What is actually defensible:

1. **A reproducible dataset-coupling and reconciliation method.** The diagnostic in Section 6 is the evidence. Taking heterogeneous studio artifacts (spreadsheet retrofit sheets, per-building hourly workbooks, a REopt results JSON, an 8760-hour vehicle charging series, a mobility ping layer in a projected CRS, PLATEAU geometry) and reconciling them into a single per-building record with stated units and passing consistency assertions is the substantive work. Most district twin papers assert this step; almost none audit it.

2. **A calibration of occupancy from mobility pings, with its failure mode characterized.** The ping-derived schedules are usable for shape, not magnitude, and roughly 24 of 136 buildings with data show a night-over-day inversion attributable to overnight dwell bias, under the test that the mean of hours 22:00 to 05:00 exceeds the mean of hours 09:00 to 17:00. The count is criterion-dependent and ranges from 15 to 27 across reasonable definitions of the inversion test, so the definition is stated wherever the number appears. Documenting when this data source fails is more useful than claiming it works.

3. **A fidelity evaluation framework.** Section 7 reframes the L1 to L3 ladder as an experiment: for a given decision, does the answer change when you add a tier? This is the part that generalizes beyond Nihonbashi.

**One genuine closed loop, named.** The current system is mostly co-location: several layers share a coordinate frame and a viewer, but information does not flow between them. The research work is to close exactly one loop end to end:

> retrofit scenario (WWR and R-value change) → building cooling load change → anthropogenic heat rejected to the street canyon → street-level heat cost field → pedestrian and delivery-robot route choice and exposure

Today, steps 1 and 2 exist as spreadsheet columns, step 4 exists as a precomputed field, and step 5 exists as a Mesa agent testbed, but steps 2 to 3 and 3 to 4 are not connected. Closing them is the honest statement of what remains to be built. Until it is closed, the twin is a coordinated viewer, not a coupled model, and this document says so.

---

## 6. Preliminary result: the data integrity audit

This section is the strongest evidence of rigor in the document. All numbers below were computed directly from repository files during preparation of this design and are reproducible.

### 6.1 Per-building energy in the twin is a pro-rata split, not a model output

Every one of the 22 buildings in `data/energy/energy_dataset.json` satisfies

```
annual_energy_kwh = gfa_m2 × 49.92954090210394
```

exactly. The spread of that ratio across all 22 buildings is 1.4e-14, which is floating-point noise. The constant is not arbitrary:

```
1,264,013 kWh ÷ 25,315.9347585096 m² = 49.92954090210394 kWh/m²
```

The numerator is `ElectricLoad.annual_calculated_kwh` from `data/energy/TS_ND_1_nihonbashi_building_EV_PV_BESS_results.json` (line 96692), which is 1,264,013.09 kWh, rounded to the whole kWh before the division — `energy_scene.json` records `meta.total_annual_energy_kwh = 1264013` exactly. Dividing the unrounded 1,264,013.09 instead gives 49.9295444572, so the rounding step is part of the reconstruction. The denominator is the block's total gross floor area. In other words, one district total was divided by total floor area and multiplied back out per building. Every building therefore has an identical energy intensity, and the twin's "energy intensity" metric layer carries no information.

### 6.2 Half of the "building energy" is vehicle charging

The REopt total decomposes exactly:

| Component | Annual kWh | Share |
|---|---|---|
| District building load (sum of the 22 `Nihonbashi_District` hourly workbooks) | 655,461.23 | 51.9 % |
| EV and bus charging (`annual_total_car_bus_energy_8760h.csv`) | 608,551.86 | 48.1 % |
| **Total (= REopt `annual_calculated_kwh`)** | **1,264,013.09** | 100 % |

The sum is exact. So 48.1 percent of what the twin currently attributes to building energy is transport charging. Any per-building energy figure or per-building CO2 attribution derived from this total is inflated by roughly a factor of two, and the split is uniform across buildings regardless of whether a building has any charging infrastructure.

### 6.3 Real per-building intensities exist and are unused

`data/energy/Index_energy.xlsx` has three sheets, `baseline`, `s1`, and `s2`, each with an `EUI` column at zero-based index 10. Building 2070, for example:

| Sheet | WWR | R-value | EUI (kWh/m²/yr) |
|---|---|---|---|
| baseline | 0.15 | 0.90 | 409.831 |
| s1 | 0.12 | 0.90 | 396.158 |
| s2 | 0.12 | 1.26 | 349.354 |

`scripts/export_energy_scene.py` lines 46 to 47 read only the `window ratio` and `r-value` columns from these sheets. A repository-wide search finds zero code references to that EUI column anywhere. (The string "EUI" does appear once, at `energy_cesium_view.html:413`, but only as the display label for the `intensity` field — that is, for the pro-rata constant, which makes the point sharper rather than weaker.) The building ID sets in `Index_energy.xlsx` and `energy_dataset.json` are identical (22 and 22, no asymmetric difference), so the join is trivially available.

### 6.4 The scenario reductions in the viewer contradict the sheets

The twin applies flat global multipliers: `energy_view.html` line 206 and `energy_cesium_view.html` line 385 both scale every building by `1 - annual_reduction_pct/100`, with s1 at minus 5 percent and s2 at minus 15 percent.

The EUI sheets imply something different:

| Scenario | Viewer multiplier | GFA-weighted reduction from EUI sheets | Per-building range (s2) |
|---|---|---|---|
| s1 | -5.00 % | -3.64 % | not computed |
| s2 | -15.00 % | -8.17 % | 0.00 % to -14.76 % |

The flat assumption nearly doubles the s2 block reduction and, more importantly, erases the fact that one building (2563) gains nothing at all from the s2 package, and that the best case is -14.76 %, still below the flat -15 %. The companion `annual_reduction_kwh` fields in `energy_scene.json` (16,076 and 49,544 kWh) are also inconsistent with the percentage fields against the stated total, so both representations need to be rebuilt from the sheets.

### 6.5 Occupancy inversion is inherited from the source, not an extraction bug

Building 2070's `occupancy_hourly` array peaks at 100.0 at midnight and dips to 40.476 at 13:00 and 14:00. This is a faithful copy of `pct_of_daily_max` in the source CSV, not a parsing error. It is also not universal: roughly 24 of the 136 buildings with data are night-over-day inverted, using the test that the mean of hours 22:00 to 05:00 exceeds the mean of hours 09:00 to 17:00. That count is sensitive to the definition and ranges from 15 to 27 depending on which window pair and which margin are chosen, so the test above is the one carried through the figures. The 167-building aggregate has a normal daytime peak at hour 15. The underlying ping data is sound: 25,254 pings from 812 devices on a single day, 2018-08-08, with 76.3 percent of pings between 08:00 and 17:00 and a peak hour of 12. The most likely cause of the inverted subset is overnight dwell bias in the raw per-building ping counts, where a device parked near a building all night produces more pings than transient daytime visitors. The correct treatment is to use ping schedules as shape priors for buildings that pass a daytime-dominance test and fall back to archetype schedules elsewhere, and to report how many buildings fall in each bucket.

### 6.6 Imputation gaps

In `data/energy/bldg_hourly_total_imputed 1.csv`, the 744 rows flagged `imputed=True` have empty count cells. For 31 buildings, including study buildings 2563, 3067, and 4560, all 24 hours are empty. Only the profile shape survives for those buildings; the magnitude is unusable. This must be surfaced per building in any figure that uses occupancy.

### 6.7 Geometry defects propagate into energy

| Building | Height (m) | nfloor | m per floor | GFA (m²) |
|---|---|---|---|---|
| 2563 | 30.0 | 2 | 15.0 | 82 |
| 3067 | 24.6 | 2 | 12.3 | 51 |
| 2070 | 29.7 | 5 | 5.94 | 411 |

Because GFA is computed as footprint area times nfloor, buildings 2563 and 3067 receive absurdly small floor areas, and under the pro-rata scheme that error passes straight into their energy values. This is a defect in `data/energy/tokyo_bldg_smaller_block.geojson`, not in the extraction code. Building 2070 at 5.94 m per floor is borderline and should be flagged rather than corrected.

### 6.8 Coordinate frame issues

The mobility pings are stored in EPSG:6677 (JGD2011 / Japan Plane Rectangular CS IX). The energy scene uses an ad hoc local equirectangular frame anchored at the block centroid (`scripts/export_energy_scene.py` lines 70 to 76, anchor 35.68818 N, 139.77910 E), with metres per degree approximated by constants. A proper `pyproj` transform is needed to place pings correctly in the scene and in any USD export. `pyproj` 3.7.2 is installed and available.

### 6.9 Heating dominance is real but implausible

Heating-dominated end use appears in 19 of the 22 source workbooks, under the criterion that annual heating exceeds annual cooling plus lighting combined. Under the weaker criterion that heating exceeds cooling alone, all 22 workbooks are heating dominated, so the count depends on which test is used and the stricter one is reported here. The REopt monthly load is winter-peaked: January 150.8 MWh against July 86.0 MWh, with a December value of 141.6 MWh and an annual minimum of 75.8 MWh in June. This is not a parsing artifact. It is nonetheless implausible for Tokyo offices, where cooling normally dominates, and it has a direct consequence: the existing PV and battery sizing (417 kW PV, 100 kW / 783 kWh storage) was optimized against a winter-peaking load, which is close to the worst case for solar self-consumption. This is a question for the studio team about how the workbook models were configured, and it must be resolved before any REopt re-run.

### 6.10 Root cause and the unresolved units question

`data/energy/energy_dataset.json` has no generator script anywhere in the repository. It appeared fully formed in commit `2f70684`. The pro-rata bug therefore cannot be fixed by re-running anything currently in `scripts/`; a new generator must be written.

One discrepancy remains unresolved and is flagged as a blocker rather than papered over. The `Index_energy` baseline EUIs range from 185.1 to 994.9 kWh/m²/yr. The workbook-derived intensity for building 2070 is approximately 65 kWh/m²/yr, and the pro-rata constant is 49.93 kWh/m²/yr. At block level the discrepancy is a factor of 11.5: Σ(EUI × GFA) over the 22 buildings is 7,566,804 kWh against 655,461 kWh from the hourly workbooks. Per building the ratio is not uniform, ranging from 2.4× (building 2563) to 47× (building 4050), which itself argues against a single unit conversion being the whole story. Plausible explanations include a source-versus-site energy definition, a per-floor-area versus per-footprint-area denominator, a different unit (MJ/m² would account for a factor near 3.6), or a conditioned-area convention. **This must be resolved with the studio team before any figure ships or any REopt re-run is performed.** Until it is resolved, figures use the EUI values for relative comparison and ranking only, with the absolute scale explicitly labeled as unverified.

---

## 7. The fidelity ladder as an evaluation framework

The ladder below is not a migration plan. It is the independent variable of the secondary research question. Each tier is a level of representational fidelity; the experiment is to ask, for each decision in Section 4, whether moving up a tier changes the recommended action.

| Tier | Representation | Physics and behavior | Cost to build | Decisions it can plausibly settle |
|---|---|---|---|---|
| **L1** | Tabular and 2D. Per-building records, spreadsheets, charts. | None. Annual and monthly aggregates. | Days | D-1 retrofit priority; block-total supply sizing |
| **L2** | Web 3D twin. CesiumJS on real terrain, PLATEAU LOD2 geometry, hourly scrubbing, scenario toggles. Working today. | Precomputed fields. No solver in the loop. | Weeks. Already paid. | D-2 with spatial context; communication and stakeholder review; shading and adjacency screening |
| **L3** | Game-engine or Omniverse simulation tier. Physically based rendering, ray-traced or simulated solar and thermal exchange, agent physics, sensor simulation. | Simulation in the loop. Robot policies, pedestrian agents, radiative exchange. | Months. Requires GPU access not yet secured. | D-3 street-level heat exposure; robot and pedestrian routing under physical constraints |

The honest hypothesis, to be tested rather than assumed, is that D-1 is settled at L1, D-2 is settled at L1 or L2, and only D-3 requires L3. If that is what the study finds, the finding is "most district energy decisions do not require a game engine", which is more useful to the field than a migration success story.

### 7.1 L3 platform comparison, platform-agnostic

Two credible paths exist to the L3 tier. The project commits to whichever access materializes first and reports the choice as a constraint, not a preference.

| | NVIDIA Omniverse / Isaac Sim | Official PLATEAU Unity and Unreal SDKs |
|---|---|---|
| Reference stack | NVIDIA Smart City Blueprint (2025 to 2026): SimReady assets, synthetic data generation, AI agents | MLIT PLATEAU SDK, purpose-built for Japanese city GML |
| Georeferencing | Must be solved by the author. USD has no built-in geodetic frame. | Solved. The SDK ingests CityGML with its coordinate reference system intact |
| Hardware | RTX-class GPU required. A PACE allocation for this does **not** currently exist and has not been requested. | Consumer hardware. Runs on the existing laptop. No PACE dependency |
| Robot simulation | Isaac Sim gives physically simulated robot policies, sensor models, and domain randomization | Unity ML-Agents or an external planner. Weaker physical realism for robots |
| Risk | Access risk is the single largest schedule risk in this project | Low. Licensing and tooling are public |
| Strategic value | Aligns with an industry reference architecture; strong for the "Era of AI" framing | Aligns with the PLATEAU ecosystem and Japanese municipal practice; strong for local relevance |

The USD exporter work described in Section 8 (Day 2) is deliberately platform-agnostic: USD is the interchange format for the Omniverse path and is importable, with effort, into both Unity and Unreal. It is a hedge, not a commitment.

---

## 8. Method and phases, with corrected dates

### 8.1 Phase 0: magnitude reconciliation (July 27 to 31, 2026)

The execution plan in Section 19. Its purpose is to make the twin's numbers defensible before anything is shown to an advisor or an editor. The reconciliation half-day is complete and is reported as the data integrity audit in Section 6; the remainder runs July 28 to 31.

### 8.2 Phase A: calibration and the primary result (August to September 2026)

1. Rebuild the per-building energy record from `Index_energy` EUIs, with the units discrepancy resolved with the studio team, and with the EV and bus load separated from building load as a distinct scene layer.
2. Build occupancy schedules from the ping data for the subset of buildings that pass a daytime-dominance test; fall back to archetype schedules elsewhere; report the split.
3. Re-run or re-scale the supply optimization under three load constructions: pro-rata flat, EUI-corrected, and EUI-corrected plus ping occupancy. Report the change in cost-optimal PV and storage against the thresholds in Section 3.1. This is the primary result and the core of the CUPUM chapter.
4. Produce figures F1, F2, F3, F5.

The Phase A scope is deliberately sized so that the September 4 long abstract and the October 23 chapter draft report only Phase A results. This resolves a contradiction in the previous plan, where the chapter draft was due before the work it described was scheduled to be built.

### 8.3 Phase B: close one loop (October 2026 to January 2027)

Close the retrofit-to-heat-to-routing loop named in Section 5, for one scenario pair, at L2. Produce figure F6. This is chapter outlook material and the substance of the February 2027 conference paper.

### 8.4 Phase C: L3 tier and fidelity evaluation (January to April 2027)

Build the L3 tier on whichever platform access materializes, port one decision, and complete the decision-by-tier matrix. The agentic and LLM scenario layer, if built, sits here as an interface convenience and is explicitly not the headline (Section 13 explains why).

---

## 9. What exists today

| Asset | File or location | Honest status |
|---|---|---|
| Energy twin, Cesium | `outputs/energy_cesium_view.html` | Working. 22 buildings in real WGS84 position on a flat ellipsoid base (`EllipsoidTerrainProvider`) with a designed streetscape and georeferenced PLATEAU LOD2 context; Bing imagery and Google photoreal tiles are opt-in. Metric and demand and supply toggles, hourly occupancy scrub |
| Energy twin, offline | `outputs/energy_view.html` | Working. three.js (module imports from the unpkg CDN); no map-tile, terrain, or Ion-token dependency; used for headless QA |
| High-fidelity city twin | `outputs/cesium_view.html`, `outputs/twin_view.html` | Working. `cesium_view.html` streams the official PLATEAU LOD2 Cesium 3D Tileset; `twin_view.html` defaults to the georeferenced LOD2 build. See the georeferencing note below |
| Scene builder | `scripts/export_energy_scene.py` | Working. Reads WWR and R-value only. Does **not** read EUI. Uses an ad hoc local frame |
| Per-building records | `data/energy/energy_dataset.json` | **Compromised.** Pro-rata split (Section 6.1). No generator script exists |
| Retrofit parameters | `data/energy/Index_energy.xlsx` (baseline, s1, s2) | Available and joinable. EUI column unused |
| Supply optimization | `TS_ND_1_..._results.json` | Real REopt output: 417 kW PV, 100 kW / 783 kWh storage, 39.8 % onsite renewable fraction. Optimized against a combined building-plus-vehicle, winter-peaking load |
| Per-building hourly workbooks | `data/energy/Nihonbashi_District/` (22 building workbooks, plus `Index_baseline.xlsx`) | Available. Sum to 655,461.23 kWh/yr |
| Vehicle charging series | `annual_total_car_bus_energy_8760h.csv` | Available. 608,551.86 kWh/yr, 8760 hours |
| Mobility pings | `pings_in_area_6677.geojson` | Available. 25,254 pings, 812 devices, EPSG:6677, single day 2018-08-08 |
| Occupancy profiles | `bldg_hourly_total_imputed 1.csv` | Partially usable. 31 buildings have no usable magnitude (Section 6.6) |
| Heat-cost field | `scripts/build_heat_cost_field.py`, `outputs/` | Working. Precomputed, not coupled to building loads |
| Robot ABM testbed | `sim/`, `scripts/run_testbed.py` | Working, Stage 1. Heat-aware routing, A/B scenarios. Not coupled to the energy layer |
| USD export | Not yet written | Planned for Day 2. `usd-core` 26.8 verified working in this environment |
| L3 GPU environment | None | Not secured. No PACE allocation requested |

**Georeferencing, stated honestly.** The 22-building energy scene is correctly georeferenced: real WGS84 footprints, stored as local metres in `energy_scene.json` and re-projected by the viewer with the same anchor and constants, so the round trip is exact to the stored 0.01 m rounding. (The base is a flat ellipsoid, not a terrain product; the buildings are positioned correctly in plan but sit on height 0, not on a DEM.) The high-fidelity PLATEAU city twin is georeferenced on both of its default paths, by two different mechanisms.

`outputs/cesium_view.html` streams the official PLATEAU LOD2 Cesium 3D Tileset published by MLIT directly from the PLATEAU asset host, so it carries the publisher's own geodetic frame and is georeferenced by definition. Nothing in this project positions those tiles by hand.

`outputs/twin_view.html` defaults to the LOD2 build: `const useLod2 = (params.get("lod2") ?? "1") !== "0";`, and when that flag is set the mesh is placed with `root.position.set(cityDX, 0, cityDZ)` and `root.rotation.y = 0`, that is, with no rotation correction. The reason it needs none is in `scripts/fetch_plateau_lod2.py`, which decodes each source tile through CESIUM_RTC to ECEF and then to geodetic and then to the same local-metre frame and anchor as the OSM street network, so every vertex is placed by its true earth-centred position and the buildings share the street frame by construction rather than by fitting.

The unregistered placement is the legacy fallback only. Requesting `?lod2=0` loads the older welded `nihonbashi_city.glb`, which is centered on the agent grid and rotated by a hand-tuned angle because that source package carried no usable georeference. That path is reachable only by explicit query parameter and no figure in this document uses it. `scripts/register_city.py` exists for that legacy case and performs FFT footprint cross-correlation between PLATEAU and OSM footprints to recover a rotation and translation.

What is not yet claimed is accuracy. The ECEF construction guarantees the correct frame, not a measured residual, and the visual confirmation of the LOD2 buildings against the OSM road centerlines has not yet been captured; it will be included with the July 31 package. No sub-metre alignment claim is made anywhere in this document.

---

## 10. Units and normalization conventions

These are locked here so that every figure, table, and abstract in the project uses the same basis. Any deviation must be labeled in the figure itself.

| Quantity | Convention |
|---|---|
| Energy | **Site** electricity, kWh. Source energy is not used. If a source conversion is ever needed, it is stated with its factor |
| Energy intensity | kWh/m²/yr, **site**, denominator = gross floor area |
| Gross floor area | Footprint polygon area × `nfloor`, from `tokyo_bldg_smaller_block.geojson`. Buildings failing the floor-height check (Section 11) are excluded from intensity figures and listed |
| Temporal basis | **Annual** totals for sizing and ranking. **Peak-day** (24 h) profiles for schedule and dispatch figures. Never mixed on one axis |
| Building vs vehicle load | Always reported separately. The combined figure is labeled "building + vehicle charging" and never called "building energy" |
| Scenario deltas | Percent change from baseline, **GFA-weighted** at block level, unweighted per building. Both are shown |
| Currency | JPY, millions (¥M), as in the source workbooks. Where USD is shown, the rate and its date are stated inline |
| Carbon | tonnes CO2 per year, from the REopt `ElectricUtility` output, attributed per building in proportion to corrected load |
| Coordinates | WGS84 (EPSG:4326) for all display. EPSG:6677 for ping source data, transformed via `pyproj`. Scene-local metres for USD, with the anchor recorded in metadata |
| Occupancy | Fraction of daily maximum, 0 to 1, 24 values. Buildings with imputed-empty magnitude are marked shape-only |

**Unresolved:** the 11.5 times discrepancy between `Index_energy` EUIs (185.1 to 994.9 kWh/m²/yr) and workbook-derived intensities (approximately 65 kWh/m²/yr for building 2070). Until the studio team confirms the EUI definition, absolute EUI values are labeled "unverified scale" wherever they appear, and conclusions rest on relative comparison.

---

## 11. Verification checks that must pass before any figure ships

These are implemented as assertions in the scene builder and in a QA script. A failing assertion blocks the figure.

| # | Check | Pass condition |
|---|---|---|
| V1 | Distinct intensities | `len(set(round(eui,1))) >= 15` across 22 buildings. Catches any recurrence of the pro-rata bug |
| V2 | Plausible intensity range | All per-building intensities in a stated, documented range. Any value outside it is listed, not silently clipped |
| V3 | ID set equality | Building ID sets from `tokyo_bldg_smaller_block.geojson`, `energy_dataset.json`, `Index_energy.xlsx`, and `Nihonbashi_District/*.xlsx` are identical. Currently **verified for all four**: the same 22 IDs in every source |
| V4 | Floor height sanity | 2.5 m ≤ height/nfloor ≤ 6.0 m for every building. Currently **fails** for 2563 (15.0) and 3067 (12.3); 2070 (5.94) is flagged |
| V5 | Sheet-total reconciliation | Sum of per-building annual kWh reconstructed from EUI × GFA agrees with the sum of the 22 hourly workbooks to within 0.5 %, or the discrepancy is reported with its cause |
| V6 | Load decomposition | building_kWh + vehicle_kWh equals the REopt `annual_calculated_kwh` to within 1 kWh. Currently exact |
| V7 | Scenario consistency | `annual_reduction_kwh` equals `annual_reduction_pct` × baseline total, to within 0.5 %, for s1 and s2 |
| V8 | Occupancy coverage | Every building's occupancy record is tagged `magnitude_ok`, `shape_only`, or `archetype_fallback`. No untagged records |
| V9 | USD structure | `usdchecker` passes with no errors on the exported stage |
| V10 | USD units | `metersPerUnit == 1.0` and `upAxis` is explicitly set on the stage |
| V11 | USD content | Exactly 22 building meshes, each with a non-degenerate triangulated cap and outward normals |
| V12 | CRS round-trip | A ping transformed EPSG:6677 to WGS84 to scene-local metres and back lands within 0.5 m of its origin |

---

## 12. Collaboration and attribution boundary

**This is an unresolved risk, stated plainly.** Data rights with the studio teammates are currently unclear. Two datasets are at risk:

| Dataset | Producer | Status | Contingency if unavailable |
|---|---|---|---|
| REopt run (`TS_ND_1_..._results.json`) | Studio teammate | **At risk.** No written agreement | Re-run REopt independently from the NREL public API using the corrected load; report the teammate run as a comparison point only if permitted |
| `Index_energy.xlsx` retrofit sheets (baseline, s1, s2, including EUI) | Studio teammate | **At risk.** No written agreement | Fall back to published Japanese office archetype EUIs and reconstruct scenarios parametrically. The method survives; the absolute numbers become archetype-based |
| Per-building hourly workbooks (`Nihonbashi_District/`) | Studio teammate | **At risk** | Same fallback as above |
| PLATEAU LOD2 geometry | MLIT open data | Clear. Open license | None needed |
| OSM road network | OpenStreetMap | Clear. ODbL, attribution required | None needed |
| Mobility ping data | Studio-provided, third-party origin | **Unclear provenance.** Licensing for publication not confirmed | Publish derived aggregate schedules only, never raw pings; confirm before any figure using ping data ships |
| Integration pipeline, twin, calibration method, fidelity evaluation, USD exporter, ABM | **This author** | Clear. Independently authored in this repository | None needed |

**The core contribution is deliberately placed on the author-owned side of this boundary.** The integration pipeline, the reconciliation and calibration method, the twin itself, and the fidelity evaluation framework are all independently owned and would survive intact if every teammate dataset had to be replaced with public archetype data. The absolute numbers would change; the method and the findings about method would not.

> **ACTION ITEM, before the September 4 abstract: obtain written agreement from the studio teammates on use and attribution.** Specifically: (a) permission to use the REopt run, `Index_energy.xlsx`, and the district hourly workbooks in publications; (b) the agreed citation or co-authorship arrangement for each; (c) confirmation of the ping data's licensing for derived publication. Target date: **August 15, 2026**, to leave time for the archetype fallback if agreement is not reached. Dr. Yang's guidance on the appropriate channel for this request is requested.

---

## 13. Positioning against the 2025 to 2026 literature

The July 2026 scan produced a clear signal about where not to compete.

| Thread | Representative work | Implication for this project |
|---|---|---|
| Agentic and LLM-driven urban twins | "Agentic Urban Digital Twins", *Urban Informatics* 2025; "Towards fully automated city operations", *CEUS* 2026 | **Commoditized.** Two papers already do LLM agents over urban twins. An agentic layer here is a convenience feature, not a contribution, and must not be the headline |
| District-scale energy twins | Review, *Frontiers in Sustainable Cities* 2026 | Confirms the domain is active. The review's own critique, that most work treats demand or supply but rarely both on the same buildings, is where the integration sits, but integration alone is not enough |
| Urban heat twins | *Discover Cities* 2025 | Establishes heat as a twin-worthy variable. None of this work couples the heat field back to building retrofit decisions, which is the loop named in Section 5 |
| Pedestrian agents in twins | SenseWalk, LLM-driven pedestrian agents, 2026 | Pedestrian agents exist but are not coupled to energy or heat. The D-3 decision is genuinely open |
| Industry reference stack | NVIDIA Smart City Blueprint, 2025 to 2026 | Establishes SimReady city twins plus synthetic data plus AI agents as an industry architecture. Academic evaluation of what that tier actually adds over a web twin remains scarce, which is exactly the secondary question |

**Defensible edge:** the dataset coupling and its audit, the occupancy calibration with characterized failure modes, and the fidelity evaluation. Not the agent layer.

---

## 14. Figure plan

Each figure has a chart type, explicit axes and units, a stated comparison, a color encoding, and the sentence with blanks that it exists to fill. If a figure cannot fill its sentence, the figure is wrong or the analysis is not done.

| ID | Chart | Axes and units | Comparison | Color | Sentence it must fill |
|---|---|---|---|---|---|
| **F1** | Horizontal dot plot, 22 rows sorted by corrected EUI | y = building ID and use; x = energy intensity, kWh/m²/yr | Two marks per row: current pro-rata constant (49.93, grey) vs corrected per-building EUI (colored) | Sequential single hue by corrected EUI; grey for the pro-rata mark | "Replacing the pro-rata split with per-building intensity widens the block's intensity range from a single value to ___ to ___ kWh/m²/yr, and changes the rank order of ___ of 22 buildings (Spearman ρ = ___)." |
| **F2** | Grouped horizontal bars, 22 rows, two bars each | y = building ID; x = percent reduction from baseline, negative to the left | s1 and s2 sheet-derived reduction per building, with vertical dashed reference lines at -5 % and -15 % (the flat viewer assumption) | Two-hue categorical for s1 and s2; dashed grey for the flat reference | "The flat -5 % and -15 % scenario assumptions overstate the GFA-weighted block reduction by ___ and ___ percentage points, and conceal that ___ of 22 buildings achieve under 1 % reduction under s2." |
| **F3** | Stacked column, 12 months | x = month; y = electricity, MWh | Building load vs EV and bus charging, stacked | Two-hue categorical, building load in the primary hue | "48.1 % of the load the supply optimization was sized against is vehicle charging, and the combined load peaks in January at 150.8 MWh against 86.0 MWh in July, so the existing 417 kW PV and 783 kWh storage were sized against a winter-peaking load." |
| **F4** | Layered schematic, 4 columns, rendered by `scripts/build_figures.py` | none (schematic); boxes annotated with source magnitudes | Six source families reconciled into one per-building record, behind the V1 to V8 assertion gate | Grey sources, blue processes, dark hub, vermillion outputs and gate | "The pipeline reconciles 6 source families into one per-building record behind an 8-check assertion gate; building load (655,461 kWh/yr) and vehicle charging (608,552 kWh/yr) are carried as separate block-level layers and never summed into a per-building attribution." |
| **F5** | Grouped column, 3 load constructions × 2 metrics, dual panel | x = load construction (pro-rata flat, EUI-corrected, EUI-corrected + ping occupancy); y = PV kW (left panel), storage kWh (right panel) | The primary-question result | Sequential ramp across the three constructions | "Correcting per-building intensity and occupancy changes cost-optimal PV from 417 kW to ___ kW (___ %) and storage from 783 kWh to ___ kWh (___ %), which does / does not cross the 10 % materiality threshold." |
| **F6** | Paired map panels with a difference inset | Plan view of the block; color = street-level heat cost, dimensionless index; inset = difference in index | Baseline vs s2 retrofit, at the peak-day hour | Diverging ramp centered at zero for the difference inset only | *Outlook.* "Closing the retrofit-to-heat-rejection-to-street loop shifts the peak-hour street heat index by ___ over ___ m of the block's pedestrian network." |
| **F7** | Layered schematic, 4 columns plus one feedback loop, rendered by `scripts/build_figures.py` | none (schematic) | What runs today against what is scheduled: sources, processes, the `energy_scene.json` contract, the L1/L2/L3 viewers, the agent and traffic layers, and the REopt re-run loop | Same palette as F4; solid = executed in the repository, dashed grey = planned, vermillion = assertion gate | "The system is four source families reconciled into one scene contract that three viewer tiers read without recomputing anything, and the loop from the corrected load back to the supply optimization is the one arrow in the figure that is still dashed." |
| **F8** | Small-multiple line chart, 24 h, 3 panels | x = hour of day, 0 to 23; y = fraction of daily maximum, 0 to 1 | Ping-derived schedule vs archetype schedule, for one normal building, one inverted building (2070), and the 167-building aggregate | One hue for ping-derived, grey for archetype | "Ping-derived occupancy is usable as a shape prior for ___ of 136 buildings; ___ show a night-over-day inversion consistent with overnight dwell bias, and ___ buildings have no usable magnitude at all." |

F1, F2, F3, and F5 are the core set for the CUPUM chapter. F4 is the methods figure and F7 is the system architecture figure. F6 is outlook. The July 31 field study package contains F1, F2, F3, F4, and F7: the three result figures that Phase 0 can already fill, plus the two schematics, which are inexpensive because they draw only on repository structure already in place. F5 waits on the supply re-run in Phase A, F6 waits on Phase B, and F8 waits on the occupancy extraction reaching figure quality.

Figure numbering note: F4 is the methods and data-pipeline schematic, which is what `scripts/build_figures.py` renders and has rendered since it was written. The occupancy small-multiple that an earlier draft of this table numbered F4 is now F8; nothing about that figure changed except its number.

---

## 15. Curated views specification

Four screenshots with fixed, reproducible camera poses. They are labeled C1 to C4 to keep them distinct from the V1 to V12 verification checks in Section 11. The poses are to be committed to the repository as `outputs/qa/camera_poses.json` (written on Day 1; the file does not exist yet, and `scripts/qa_cesium_views.mjs` currently hard-codes a single oblique pose and does not read a pose file, so the harness needs a small extension) so that any run reproduces the identical frame. Fields: `lon`, `lat`, `height_m` (ellipsoid), `heading_deg`, `pitch_deg`, plus the UI state.

| ID | Camera (lon, lat, height m, heading°, pitch°) | UI state | Story in one sentence | Draft caption |
|---|---|---|---|---|
| **C1 Block overview** | 139.77910, 35.68700, 700, 0, -55 | Energy view; metric = corrected intensity; demand = baseline; hour = 12 | This is the study block, 22 buildings, and every building now has a different intensity. | "The Nihonbashi study block, 22 buildings, colored by corrected per-building energy use intensity. Under the previous pro-rata construction every building carried the identical value of 49.93 kWh/m²/yr." |
| **C2 Retrofit contrast** | 139.77890, 35.68790, 320, 45, -35 | Energy view; metric = intensity; demand toggled baseline then s2, same frame, side by side | Scenario s2 does not help every building equally. | "The same view under baseline (left) and retrofit scenario s2 (right). Sheet-derived reductions range from 0.00 % to 14.76 % per building, against the flat 15 % previously applied to all." |
| **C3 Occupancy scrub** | 139.77930, 35.68840, 260, 200, -30 | Energy view; metric = occupancy; hour = 03 and hour = 14, same frame | Some buildings are apparently busiest at 3 a.m., and that is a data artifact worth naming. | "Ping-derived occupancy at 03:00 (left) and 14:00 (right). Approximately 24 of 136 buildings show this night-over-day inversion, on the test that mean occupancy over hours 22:00 to 05:00 exceeds the mean over hours 09:00 to 17:00, and it is attributable to overnight dwell bias rather than an extraction error." |
| **C4 Street-level context** | 139.77950, 35.68760, 40, 300, -8 | High-fidelity city view; heat field on; streetscape on | This is the fidelity tier the street-level heat and routing question needs. | "Pedestrian-eye view in the high-fidelity PLATEAU twin with the heat-cost field active. The LOD2 buildings are placed by their true ECEF positions into the same local frame as the OSM streets, so they are georeferenced by construction; the quantified alignment residual against the road centerlines has not yet been measured, so building-to-road alignment is described as approximate rather than to a stated tolerance." |

Capture procedure: run the existing headless QA harness (`scripts/qa_cesium_views.mjs`) with the pose file. Note the known constraint recorded in project memory: this codespace has no GPU and software rendering is too slow to screenshot the legacy welded city mesh (`outputs/twin/plateau/nihonbashi_city.glb`, 18 MB, 4.7 M triangles) reliably. The current default mesh is the lighter LOD2 build (`nihonbashi_lod2_opt.glb`, 1.7 MB, 0.66 M triangles), so this constraint should be re-tested before assuming C4 cannot be captured headlessly. If it still holds, C4 must be captured on a machine with hardware acceleration, or captured manually with the pose applied from the pose file.

---

## 16. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **GPU access for L3 never materializes.** No PACE allocation exists or has been requested for Omniverse or Isaac Sim | High | High for Phase C only | The ladder is a framework, not a dependency. The PLATEAU Unity or Unreal path runs on consumer hardware. If neither materializes, L3 is reported as an unexecuted tier with a stated argument about what it would add, and the study still delivers L1 and L2 results. Request PACE allocation by September 2026 regardless |
| **Data agreement not reached with teammates** | Medium | High for absolute numbers, low for method | Section 12 fallback: reconstruct from public archetype EUIs and an independent REopt run. Action item dated August 15, 2026 |
| **Units discrepancy (11.5×) unresolved** | Medium | Blocks absolute-value claims | Figures use relative comparison and label absolute scale as unverified. Escalate to the studio team immediately. This is the single most schedule-critical open question |
| **Further data integrity defects surface** | Medium | Medium | The assertion suite in Section 11 runs on every build. New defects become documented findings rather than silent errors |
| **n = 22 is too small for statistical claims** | Certain | Medium | The study makes no distributional claims. Findings are reported as per-building deltas and as a block-level total, with the sample size stated in every caption. The block is treated as a case, not a sample |
| **Scope creep into the agentic layer** | Medium | Medium | Section 13 establishes that the agentic layer is commoditized. It is scoped to Phase C outlook and is explicitly not in the September or October deliverables |
| **Advisor feedback arrives too late to act on** | Was high, now mitigated | High | The restructured design is sent to Dr. Yang at the end of Day 3 (July 30) so that Day 4 can absorb one round before the July 31 due date |

---

## 17. Limitations

Stated up front so they are not read as omissions.

1. **Archetype-based, not metered.** No building in the study has metered kWh ground truth. All energy values trace to simulation workbooks built on archetype assumptions. The study calibrates between representations; it does not validate against reality.
2. **n = 22.** One block, 22 buildings. Findings are a case study. No claim generalizes statistically to Tokyo or to other districts.
3. **Single-day mobility data from 2018.** The ping layer covers one day, 2018-08-08, with 812 devices. It carries no seasonal, weekday-versus-weekend, or post-pandemic variation, and it predates the study period by eight years. Occupancy derived from it is a shape prior, not a measurement.
4. **No usable occupancy magnitude for 31 buildings**, including three study buildings (2563, 3067, 4560).
5. **Geometry defects in the source data** affect at least two study buildings (Section 6.7) and are not correctable without better source geometry.
6. **The high-fidelity city twin is georeferenced but its alignment residual is unmeasured** (Section 9). The default LOD2 path places every vertex by its true ECEF position into the street frame, and the Cesium path streams the official PLATEAU tileset, so both are georeferenced by construction. What has not been done is a quantified check of the residual against the OSM road centerlines, so street-level spatial claims are stated as approximate until that confirmation ships with the July 31 package. The unregistered agent-grid placement survives only on the legacy `?lod2=0` fallback, which no figure uses.
7. **The heating-dominated load profile is implausible for Tokyo offices** and is inherited from the source workbooks. Until it is explained, all supply-sizing results carry that inherited assumption.
8. **The system is co-located, not yet coupled.** No information currently flows from the energy layer to the heat layer to the mobility layer. Closing one loop is the remaining research work, not completed work.
9. **The L3 tier does not exist yet.** All statements about what it would add are hypotheses to be tested, not results.

---

## 18. Deliverables and timeline

| Date | Deliverable | Scope |
|---|---|---|
| **July 31, 2026** | **Field study package** (this document) | Restructured project design, corrected magnitude layer, figures F1 to F4, curated views C1 to C4, USD format-feasibility artifact, live demo links, executive summary |
| August 15, 2026 | Written data agreement with studio teammates | Action item, Section 12 |
| September 2026 | PACE or GPU access request submitted | For Phase C, regardless of outcome |
| **September 4, 2026** | **CUPUM 2027 long abstract, 500 words** | **Phase A results only.** The data reconciliation finding and the primary-question result. No agentic layer, no L3 claims |
| **October 23, 2026** | **CUPUM 2027 book chapter draft, 4,000 to 6,000 words** | **Phase A results plus the fidelity evaluation framework.** Phase B and C as outlook |
| **January 29, 2027** | **CUPUM 2027 revised book chapter** | Editor and reviewer revisions to the October draft, incorporating Phase B progress |
| **February 12, 2027** | **CUPUM 2027 conference paper or poster** | Phase B: the closed retrofit-to-heat-to-routing loop |
| Spring 2027 | L3 tier pilot and fidelity evaluation matrix | Phase C |
| **July 5 to 10, 2027** | **CUPUM 2027, Sydney** | Presentation |

The January 29, 2027 revised chapter falls inside Phase B (October 2026 to January 2027), at the very end of it, so the revision window and the close-one-loop work compete for the same weeks. Phase B is planned with that in mind: the revision draws on Phase A results, which are already complete by then, and any Phase B result that has landed by late January is added as strengthened outlook rather than as required content.

**ISMT (multimodal transportation, NUS), 8th edition:** the call for papers is not yet posted. Treated as **watch only**. No hard deliverable is planned against it. If the CFP appears with a compatible deadline, the Phase B robot and pedestrian routing work is the natural submission.

---

## 19. Execution plan: the audit is done, July 28 to 31, 2026

### Day 0.5, July 27: magnitude reconciliation — **complete**

Not a sanity pass. This was the half-day that made every subsequent number defensible, and it is the work reported as the data integrity audit in Section 6. Every finding in Section 6 was computed from repository files during this pass, so the items below are recorded as done rather than planned. The remaining three and a half days run July 28 to July 31.

1. Extend `scripts/export_energy_scene.py` to read the `EUI` column (zero-based index 10) from the `baseline`, `s1`, and `s2` sheets of `Index_energy.xlsx`, alongside the WWR and R-value it already reads.
2. **Decide the magnitude layer.** Given the unresolved 11.5× discrepancy, adopt this rule and record it in the scene metadata: EUI values drive *relative* per-building intensity and *relative* scenario deltas; absolute annual kWh per building is reconstructed by rescaling the EUI-weighted distribution so that the block total matches the sum of the 22 hourly workbooks (655,461.23 kWh). This preserves both the real per-building variation and a defensible block total, and it is reversible once the studio team answers the units question.
3. **Separate EV and vehicle load from building load.** Add `vehicle_annual_kwh` as a block-level scene field (608,551.86 kWh) and remove vehicle energy from every per-building attribution. Relabel every UI element that currently says "building energy" for the combined figure.
4. **Repair the nfloor anomalies.** For 2563 and 3067, either derive nfloor from height at 3.5 m per floor and flag the correction in the record, or exclude them from intensity figures. Either way, record the decision per building in a `geometry_flag` field.
5. **Rebuild the scenario reductions** from EUI sheets: per-building percentages, plus GFA-weighted block totals (-3.64 % for s1, -8.17 % for s2), replacing the flat multipliers in both `energy_view.html` and `energy_cesium_view.html`.
6. **Add the assertion suite** V1 to V8 from Section 11 to the scene builder, failing the build on violation.
7. Send the units question (Section 6.10) to the studio team today, so that an answer can arrive within the week.

### Day 1, July 28: figures

Produce F1, F2, F3, and F4 to the specification in Section 14, with each figure's sentence filled in. All four ship in the July 31 package; F4 is the methods figure and is produced from the occupancy data already extracted, so it costs little beyond the three result figures. Capture views C1, C2, and C3 using the committed camera poses. Write `outputs/qa/camera_poses.json`. F5 requires the supply re-run and is Phase A, not Day 1; the F5 slot is reserved in the document with its sentence stated and blanks visible.

### Day 2, July 29: USD exporter

Write a full USD exporter for the 22-building scene, honestly scoped. **This produces a format-feasibility artifact, not a SimReady asset.** The distinction is stated in the document and in the code header: SimReady requires physically based materials, semantic labeling, and physics properties that this export does not provide. What it does demonstrate is that the scene's geometry and per-building attributes survive the round trip into the interchange format that both L3 platform paths consume.

Traps to handle explicitly, all verified relevant in this environment (`usd-core` 26.8 installed and working):

- Set `metersPerUnit = 1.0` on the stage. The default is 0.01 and would silently shrink the block by 100×.
- Set the stage up axis explicitly rather than relying on a default.
- The scene frame is "+x east, +z north, Y up", which is **left-handed**. three.js is right-handed with north at -z. Converting requires flipping an axis.
- Flipping an axis reverses ring winding and inverts normals. Reverse the winding when flipping.
- Concave footprints need triangulated caps, not naive fans.
- Transform ping positions from EPSG:6677 via `pyproj`, not via the ad hoc equirectangular approximation.

Run V9 to V12 from Section 11. Report `usdchecker` output verbatim in the deliverable.

### Day 3, July 30: document restructure and advisor send

Finalize this document with Day 1 and Day 2 results filled in. Insert Figure 0 and the four curated views C1 to C4. **Send to Dr. Yang by end of day**, with a short cover note flagging the three items where his judgment is specifically requested: (a) whether the repositioned research question is the right one, (b) the appropriate channel for the teammate data agreement, and (c) whether the fidelity-evaluation framing is defensible for the CUPUM audience.

### Day 4, July 31: absorb feedback and ship

Incorporate one round of advisor feedback. Write the one-page executive summary. Verify every demo link resolves from a clean browser session, including the deployed URL. Upload the package to the Project Design folder.

---

## 20. References scanned, July 2026

These are the works consulted for positioning. No claim in this document rests on a source not listed here.

- "Agentic Urban Digital Twins", *Urban Informatics*, 2025.
- "Towards fully automated city operations" (agentic AI and urban digital twins), *Computers, Environment and Urban Systems*, 2026.
- District-scale energy digital twins, review article, *Frontiers in Sustainable Cities*, 2026.
- Urban heat resilience digital twin, *Discover Cities*, 2025.
- NVIDIA Smart City Blueprint (Omniverse, Metropolis, Isaac Sim), 2025 to 2026.
- SenseWalk: LLM-driven pedestrian agents, 2026.
- PLATEAU LOD2 building data and SDK documentation, MLIT (Japan), open data.
- REopt, National Renewable Energy Laboratory.
