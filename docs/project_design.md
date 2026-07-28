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

This study asks whether per-building energy use intensity and mobility-derived occupancy change the cost-optimal sizing of distributed solar and battery storage for a block in Nihonbashi, Tokyo. The comparison is against the flat archetype and pro-rata assumptions the twin previously carried, at building scale and at block scale. The study is built on a browser-deployable digital twin of 22 buildings that co-locates building geometry, retrofit parameters, a district supply optimization, a heat-cost field, and pedestrian mobility ping data in one georeferenced scene. Diagnostic work for this document produced a preliminary result that reframes the project. The per-building energy values in the twin are not a model output: they are a single district total divided pro rata by floor area. Of that district total, 48.1% is electric vehicle and bus charging rather than building load. Real per-building intensities exist in the studio workbooks and were unused. Correcting this is the first phase of the work.

The second phase reframes the fidelity ladder, which runs from an analytical dashboard through a web-based digital twin to a game-engine or Omniverse simulation tier, as an evaluation framework rather than a migration roadmap. The study reports, for each of three urban design decisions, the lowest fidelity tier at which the decision stops changing. One of those decisions (D-3) requires the L3 simulation tier, whose GPU access is not yet secured, so that tier may be reported as unexecuted, with an argument for what it would have added. The contribution the author independently owns is the integration pipeline, the reconciliation and calibration method, the twin, and the fidelity evaluation framework. Teammate-produced datasets are used with an attribution boundary that is not yet resolved (Section 12).

---

## 2. Hero figure

![Figure 0. The same study block, one month apart.](../outputs/figures/photoreal/C0_evolution_before_after.png)

**Figure 0. The same study block, one month apart.** (a) The 22 study buildings on the designed streetscape base, June 2026. (b) The same block, the same metric and the same demand state, on photoreal urban context, July 2026. Both panels color the block by energy use intensity under baseline demand at the same scale, so the change between them is context, not data. Basemap in (b): Google Photorealistic 3D Tiles, © Google. The block is georeferenced in both panels: the Cesium view places every study building by its real WGS84 footprint, and the PLATEAU LOD2 context path places every vertex by its true earth-centered position. Visual confirmation against the OSM road centerlines is pending (Section 9).

Live views in this repository, all browser-runnable with no build step:

| View | File | What it shows |
|---|---|---|
| Energy twin (Cesium, primary) | `outputs/energy_cesium_view.html` | The 22 study buildings in real WGS84 position on photoreal urban context |
| Energy twin (three.js, offline) | `outputs/energy_view.html` | The same scene with no map-tile, terrain, or Ion-token dependency |
| High-fidelity city twin | `outputs/cesium_view.html`, `outputs/twin_view.html` | PLATEAU LOD2 city mesh, streetscape, heat field, robot agent testbed |
| Landing redirect | `outputs/index.html` | Redirects to the energy view; deployed to a static host (Vercel) |

The repository contains no `vercel.json` or `.vercel` directory, so the hosting project name is not recorded in the code. The deployment URL and project name must be confirmed against the hosting dashboard and added to this table before the July 31 upload.

---

## 3. Research questions and success criteria

### 3.1 Primary question (falsifiable, measurable)

> **Does per-building energy use intensity from the studio's simulation workbooks, combined with ping-derived occupancy schedules, materially change the cost-optimal PV and battery sizing for a Nihonbashi block? The reference case is the flat pro-rata and flat-schedule assumptions previously embedded in the twin.**

"Materially" is defined in advance so the question can fail:

| Criterion | Threshold for "yes, it matters" |
|---|---|
| Block-scale PV sizing | Cost-optimal PV capacity changes by more than 10% from the current 417 kW |
| Block-scale storage sizing | Cost-optimal storage energy changes by more than 10% from the current 783 kWh |
| Building-scale ranking | The rank order of the 22 buildings by energy intensity changes for more than 5 buildings, or the Spearman rank correlation against the GFA ordering (which the pro-rata construction reproduces exactly) falls below 0.9 |
| Retrofit priority | The top 5 retrofit candidates by absolute annual savings change by at least 2 members |

If none of these thresholds is crossed, the answer is "no", and the negative result is publishable: at block scale, a pro-rata split would be a defensible approximation for supply sizing.

### 3.2 Secondary question (methods)

> **At which fidelity tier does the answer to a given urban energy decision stop changing?**

For each of the three design decisions in Section 4, the study reports the lowest tier in the L1 to L3 ladder (Section 7) at which the recommended action is stable. The tiers are the analytical dashboard and basic views (L1), the web-based digital twin (L2), and the game-engine or Omniverse simulation tier (L3). The deliverable is a decision-by-tier matrix, not a claim that higher fidelity is better.

### 3.3 What this study does not claim

This study does not claim a validated building energy model. There is no metered kWh ground truth for these buildings. It does not claim that agentic or LLM-driven scenario exploration is novel; two 2026 papers already do that (Section 13). It does not claim a real-time or operational twin.

---

## 4. Design decisions this twin is meant to answer

The test of an urban twin is whether a designer or a district manager would act differently after looking at it. Three decisions are in scope, each mapped to a planned figure.

| # | Decision question | Who asks it | Figure |
|---|---|---|---|
| D-1 | Given a fixed retrofit budget, which of the 22 buildings should be renovated first? | Block owner, district regeneration council | F1, F2 |
| D-2 | How much solar and battery should the block procure collectively, and does the answer depend on modeling who is inside the buildings? | District energy operator | F3, F5 |
| D-3 | Does the retrofit and electrification program make the street warmer or cooler for pedestrians and delivery robots, once rejected heat is accounted for? | Urban designer, public-space planner | F6 (outlook) |

D-1 and D-2 are answerable with the Phase A work described in Section 8. D-3 requires the closed loop described in Section 5 and is scoped as outlook for the CUPUM chapter.

---

## 5. Contribution

The earlier framing of this project claimed novelty by conjunction: first to combine archetype building energy modeling, supply optimization, a heat field, and mobility-derived occupancy in one georeferenced scene. That framing does not survive review. Combining four existing things is integration work rather than a research contribution.

What is defensible:

1. **A reproducible dataset-coupling and reconciliation method.** The diagnostic in Section 6 is the evidence. The substantive work is reconciling six heterogeneous studio artifacts into a single per-building record with stated units, one that passes consistency assertions. The sources are spreadsheet retrofit sheets, per-building hourly workbooks, a REopt results JSON, an 8760-hour vehicle charging series, a mobility ping layer in a projected CRS, and PLATEAU geometry. Most district twin papers assert this step; almost none audit it.

2. **A calibration of occupancy from mobility pings, with its failure mode characterized.** The ping-derived schedules are usable for shape, not magnitude. Approximately 24 of the 136 buildings with data show a night-over-day inversion attributable to overnight dwell bias; Section 6.5 states the test and its sensitivity. Documenting when this data source fails is more useful than claiming it works.

3. **A fidelity evaluation framework.** Section 7 reframes the L1 to L3 ladder as an experiment: for a given decision, does the answer change when a tier is added? This is the part that generalizes beyond Nihonbashi.

**One closed loop, named.** The current system is mostly co-location: several layers share a coordinate frame and a view, but information does not flow between them. The research work is to close one loop end to end:

> retrofit scenario (WWR and R-value change) → building cooling load change → anthropogenic heat rejected to the street canyon → street-level heat cost field → pedestrian and delivery-robot route choice and exposure

Today, steps 1 and 2 exist as spreadsheet columns, step 4 exists as a precomputed field, and step 5 exists as a Mesa agent testbed. Steps 2 to 3 and 3 to 4 are not connected. Closing them is what remains to be built. Until it is closed, the twin is a coordinated set of views, not a coupled model.

---

## 6. Preliminary result: the data integrity audit

All numbers below were computed from repository files during preparation of this document and are reproducible. The audit examined the state of the data layer before the July 27 correction pass; Section 19 records which findings have since been acted on.

### 6.1 Per-building energy in the twin was a pro-rata split, not a model output

Every one of the 22 buildings in `data/energy/energy_dataset.json` satisfies

```
annual_energy_kwh = gfa_m2 × 49.92954090210394
```

exactly. The relative spread of that ratio across the 22 buildings is 1.4 × 10⁻¹⁴, which is floating-point noise. The constant is not arbitrary:

```
1,264,013 kWh ÷ 25,315.9347585096 m² = 49.92954090210394 kWh/m²
```

The numerator is `ElectricLoad.annual_calculated_kwh` from `data/energy/TS_ND_1_nihonbashi_building_EV_PV_BESS_results.json` (line 96692), which is 1,264,013.09 kWh, rounded to the whole kWh before the division; `energy_scene.json` recorded `meta.total_annual_energy_kwh = 1264013`. Dividing the unrounded 1,264,013.09 instead gives 49.9295444572, so the rounding step is part of the reconstruction. The denominator is the block's total gross floor area. One district total was divided by total floor area and multiplied back out per building. Every building therefore carried an identical energy intensity, and the twin's "energy intensity" metric layer carried no information.

### 6.2 Half of the "building energy" is vehicle charging

The REopt total decomposes with no residual:

| Component | Annual kWh | Share |
|---|---|---|
| District building load (sum of the 22 `Nihonbashi_District` hourly workbooks) | 655,461.23 | 51.9% |
| EV and bus charging (`annual_total_car_bus_energy_8760h.csv`) | 608,551.86 | 48.1% |
| **Total (= REopt `annual_calculated_kwh`)** | **1,264,013.09** | 100% |

The sum is exact. So 48.1% of what the twin attributed to building energy is transport charging. Any per-building energy figure or CO2 attribution derived from this total is inflated by approximately a factor of two. The split was also uniform across buildings, regardless of whether a building has any charging infrastructure.

### 6.3 Real per-building intensities exist and were unused

`data/energy/Index_energy.xlsx` has three sheets, `baseline`, `s1`, and `s2`, each with an `EUI` column at zero-based index 10. Building 2070, for example:

| Sheet | WWR | R-value | EUI (kWh/m²/yr) |
|---|---|---|---|
| baseline | 0.15 | 0.90 | 409.831 |
| s1 | 0.12 | 0.90 | 396.158 |
| s2 | 0.12 | 1.26 | 349.354 |

Before the correction pass, `scripts/export_energy_scene.py` read only the `window ratio` and `r-value` columns from these sheets, and a repository-wide search found zero code references to that EUI column. (The string "EUI" appears once, at `energy_cesium_view.html:413`, but only as the display label for the intensity field, that is, for the pro-rata constant.) The building ID sets in `Index_energy.xlsx` and `energy_dataset.json` are identical (22 IDs in each, no difference in either direction), so the join is available directly.

### 6.4 The scenario reductions in the view contradicted the sheets

The twin applied flat global multipliers: `energy_view.html` line 206 and `energy_cesium_view.html` line 385 both scaled every building by `1 - annual_reduction_pct/100`, with s1 at -5% and s2 at -15%.

The EUI sheets imply something different:

| Scenario | Previous flat multiplier | GFA-weighted reduction from EUI sheets | Per-building range |
|---|---|---|---|
| s1 | -5.00% | -3.53% | -0.65% to -5.26% |
| s2 | -15.00% | -7.91% | 0.00% to -14.76% |

The GFA-weighted figures are computed on the repaired floor areas of Section 6.7. The flat assumption nearly doubles the s2 block reduction. It also erases two facts: building 2563 gains nothing from the s2 package, and the best case is -14.76%, still below the flat -15%. The companion `annual_reduction_kwh` fields in `energy_scene.json` (16,076 and 49,544 kWh) were also inconsistent with the percentage fields against the stated total, so both representations were rebuilt from the sheets.

### 6.5 Occupancy inversion is inherited from the source, not an extraction bug

Building 2070's `occupancy_hourly` array peaks at 100.0 at midnight and dips to 40.476 at 13:00 and 14:00. This is a faithful copy of `pct_of_daily_max` in the source CSV rather than a parsing error. It is also not universal: approximately 24 of the 136 buildings with data are night-over-day inverted, using the test that the mean of hours 22:00 to 05:00 exceeds the mean of hours 09:00 to 17:00. That count is sensitive to the definition and ranges from 15 to 27 depending on which window pair and which margin are chosen, so the test above is the one carried through the figures. The 167-building aggregate has a normal daytime peak at hour 15.

The underlying ping data is sound: 25,254 pings from 812 devices on a single day, 2018-08-08, with 76.3% of pings between 08:00 and 17:00 and a peak hour of 12. The most likely cause of the inverted subset is overnight dwell bias in the raw per-building ping counts, where a device parked near a building all night produces more pings than transient daytime visitors. The correct treatment is to use ping schedules as shape priors for buildings that pass a daytime-dominance test, to fall back to archetype schedules elsewhere, and to report how many buildings fall in each bucket.

### 6.6 Imputation gaps

In `data/energy/bldg_hourly_total_imputed 1.csv`, the 744 rows flagged `imputed=True` have empty count cells. For 31 buildings, including study buildings 2563, 3067, and 4560, all 24 hours are empty. Only the profile shape survives for those buildings; the magnitude is unusable. This must be surfaced per building in any figure that uses occupancy.

### 6.7 Geometry defects propagate into energy

| Building | Height (m) | nfloor as published | m per floor as published | GFA as published (m²) |
|---|---|---|---|---|
| 2563 | 30.0 | 2 | 15.0 | 82 |
| 3067 | 24.6 | 2 | 12.3 | 51 |
| 2070 | 29.7 | 5 | 5.94 | 411 |

Because GFA is computed as footprint area times nfloor, buildings 2563 and 3067 received implausibly small floor areas, and under the pro-rata scheme that error passed straight into their energy values. This is a defect in `data/energy/tokyo_bldg_smaller_block.geojson`, not in the extraction code. The scene builder now rebuilds nfloor from height at 3.5 m per floor for those two buildings and records the correction in a `geometry_flag` field: 2563 becomes 9 floors at 3.33 m and 3067 becomes 7 floors at 3.51 m. Building 2070 at 5.94 m per floor is borderline and is flagged rather than corrected.

### 6.8 Coordinate frame issues

The mobility pings are stored in EPSG:6677 (JGD2011 / Japan Plane Rectangular CS IX). The energy scene uses a local equirectangular frame anchored at the block centroid (`scripts/export_energy_scene.py` lines 70 to 76, anchor 35.68818 N, 139.77910 E), with meters per degree approximated by constants. A `pyproj` transform is needed to place pings correctly in the scene and in any USD export. `pyproj` 3.7.2 is installed and available.

### 6.9 Heating dominance is real but implausible

Heating-dominated end use appears in 19 of the 22 source workbooks, under the criterion that annual heating exceeds annual cooling plus lighting combined. Under the weaker criterion that heating exceeds cooling alone, all 22 workbooks are heating dominated, so the count depends on which test is used and the stricter one is reported here. The REopt monthly load is winter-peaked: January 150.8 MWh against July 86.0 MWh, with a December value of 141.6 MWh and an annual minimum of 75.8 MWh in June. This is not a parsing artifact. It is nonetheless implausible for Tokyo offices, where cooling normally dominates. The consequence is direct: the existing sizing (417 kW PV, 100 kW / 783 kWh storage) was optimized against a winter-peaking load, close to the worst case for solar self-consumption. This is a question for the studio team about how the workbook models were configured, and it must be resolved before any REopt re-run.

### 6.10 Root cause and the unresolved units question

`data/energy/energy_dataset.json` has no generator script in the repository. It appeared fully formed in commit `2f70684`. The pro-rata construction therefore could not be fixed by re-running anything that existed in `scripts/`; a new generator had to be written.

One discrepancy remains unresolved and is treated as a blocker. The `Index_energy` baseline EUIs range from 185.1 to 994.9 kWh/m²/yr. The workbook-derived intensity for building 2070 is approximately 65 kWh/m²/yr, and the legacy pro-rata constant is 49.93 kWh/m²/yr. At block level the discrepancy is a factor of 12.1: Σ(EUI × GFA) over the 22 buildings is 7,923,977 kWh against 655,461 kWh from the hourly workbooks. On the published floor areas, before the Section 6.7 repair, the same ratio was 11.5×. Per building the ratio is not uniform, ranging from 2.8× (building 3552) to 47.1× (building 4050), which argues against a single unit conversion as the explanation. Plausible explanations are:

- a source-versus-site energy definition;
- a per-floor-area versus per-footprint-area denominator;
- a different unit, since MJ/m² would account for a factor near 3.6;
- a conditioned-area convention that excludes unconditioned floor area.

**This must be resolved with the studio team before any figure ships or any REopt re-run is performed.** Until it is resolved, figures use the EUI values for relative comparison and ranking only, with the absolute scale labeled unverified.

---

## 7. The fidelity ladder as an evaluation framework

The ladder below is not a migration plan. It is the independent variable of the secondary research question. Each tier is a level of representational fidelity, and the experiment asks, for each decision in Section 4, whether moving up a tier changes the recommended action.

| Tier | Representation | Physics and behavior | Cost to build | Decisions it can plausibly settle |
|---|---|---|---|---|
| **L1** | Analytical dashboard and basic views. Per-building records, charts, the Streamlit dashboard in `analysis/dashboard.py`, and the basic Cesium and three.js views. | None. Annual and monthly aggregates. | Days. Built. | D-1 retrofit priority; block-total supply sizing |
| **L2** | Web-based digital twin. CesiumJS on real terrain and photoreal tiles, the 22 study buildings, hourly scrubbing, scenario toggles, agent overlay. Running today. | Precomputed fields. No solver in the loop. | Weeks. Already paid. | D-2 with spatial context; communication and stakeholder review; shading and adjacency screening |
| **L3** | Simulation tier. Game engine or Omniverse. Physically based rendering, ray-traced or simulated solar and thermal exchange, agent physics, sensor simulation. | Simulation in the loop. Robot policies, pedestrian agents, radiative exchange. | Months. Requires GPU access not yet secured. | D-3 street-level heat exposure; robot and pedestrian routing under physical constraints |

The simulation-ready USD export is not a tier of this ladder. It is the bridge artifact on the L2 to L3 path: the interchange format in which the L2 scene is handed to whichever L3 runtime access materializes. Section 8 and Section 19 schedule it as such.

**L2+, photoreal context.** The web twin now streams Google Photorealistic 3D Tiles as its full base, overlaying the 22 study buildings on a photogrammetric mesh of the surrounding city. This raises the appearance fidelity of the web tier to the level usually associated with game-engine captures, at zero simulation cost. It also clarifies what appearance fidelity is not. The Google mesh is baked at capture time, with a fixed sun position, frozen vehicles and vegetation, no per-building identity outside the study block, and no physics. The photoreal base therefore sharpens the evaluation question of the higher tier. What a game-engine or Omniverse tier must justify is not visual realism, which the web tier already demonstrates in a browser, but simulation fidelity: semantic structure, controllable lighting and weather, collision and sensor physics for agent simulation, and synthetic data generation.

The hypothesis, to be tested rather than assumed, is that D-1 settles at L1 or L2, D-2 settles at L2, and only D-3 requires L3. If that is what the study finds, the finding is "most district energy decisions do not require a game engine", which is more useful to the field than a migration success story.

### 7.1 L3 platform comparison, platform-agnostic

Two credible paths exist to the L3 tier. The project commits to whichever access materializes first and reports the choice as a constraint rather than a preference.

| | NVIDIA Omniverse / Isaac Sim | Official PLATEAU Unity and Unreal SDKs |
|---|---|---|
| Reference stack | NVIDIA Smart City Blueprint (2025 to 2026): SimReady assets, synthetic data generation, AI agents | MLIT PLATEAU SDK, purpose-built for Japanese city GML |
| Georeferencing | Must be solved by the author. USD has no built-in geodetic frame | Solved. The SDK ingests CityGML with its coordinate reference system intact |
| Hardware | RTX-class GPU required. A PACE allocation for this does **not** exist and has not been requested | Consumer hardware. Runs on the existing laptop. No PACE dependency |
| Robot simulation | Isaac Sim gives physically simulated robot policies, sensor models, and domain randomization | Unity ML-Agents or an external planner. Weaker physical realism for robots |
| Risk | Access risk is the single largest schedule risk in this project | Low. Licensing and tooling are public |
| Strategic value | Aligns with an industry reference architecture; strong for the "Era of AI" framing | Aligns with the PLATEAU ecosystem and Japanese municipal practice; strong for local relevance |

At the simulation tier, Omniverse Kit provides the USD-native runtime and composition layer, with Isaac Sim supplying robot physics. NVIDIA's demonstrated Model Context Protocol (MCP) integration for Omniverse Kit is noted as a candidate control channel. The natural-language scenario interface planned for Phase B could drive an Omniverse scene through the same protocol, which would make that layer view-agnostic rather than tied to either tier. This is recorded as a design direction, not a committed dependency; it activates only if the GPU access described in Section 16 materializes.

The USD exporter work (Section 8, Day 2) is platform-agnostic: USD is the interchange format for the Omniverse path and imports, with effort, into Unity and Unreal.

---

## 8. Method and phases, with corrected dates

### 8.1 Phase 0: magnitude reconciliation (July 27 to 31, 2026)

This phase is the execution plan in Section 19. Its purpose is to make the twin's numbers defensible before anything is shown to an advisor or an editor. The reconciliation half-day is complete and is reported as the data integrity audit in Section 6; the remainder runs July 28 to 31.

### 8.2 Phase A: calibration and the primary result (August to September 2026)

1. Rebuild the per-building energy record from `Index_energy` EUIs, with the units discrepancy resolved with the studio team, and with the EV and bus load separated from building load as a distinct scene layer.
2. Build occupancy schedules from the ping data for the subset of buildings that pass a daytime-dominance test; fall back to archetype schedules elsewhere; report the split.
3. Re-run or re-scale the supply optimization under three load constructions: pro-rata flat, EUI-corrected, and EUI-corrected plus ping occupancy. Report the change in cost-optimal PV and storage against the thresholds in Section 3.1. This is the primary result and the core of the CUPUM chapter.
4. Produce figures F1, F2, F3, F5.

Phase A is sized so that the September 4 long abstract and the October 23 chapter draft report only Phase A results. This resolves a contradiction in the previous plan, where the chapter draft was due before the work it described was scheduled to be built.

### 8.3 Phase B: close one loop (October 2026 to January 2027)

Close the retrofit-to-heat-to-routing loop named in Section 5, for one scenario pair, at L2. Produce figure F6. This is chapter outlook material and the substance of the February 2027 conference paper.

### 8.4 Phase C: L3 simulation tier and fidelity evaluation (January to April 2027)

Carry the simulation-ready USD export across the L2 to L3 bridge, build the L3 tier on whichever platform access materializes, port one decision, and complete the decision-by-tier matrix. The agentic and LLM scenario layer, if built, sits here as an interface convenience and is not the headline (Section 13).

---

## 9. What exists today

| Asset | File or location | Status |
|---|---|---|
| Energy twin, Cesium (L2) | `outputs/energy_cesium_view.html` | Working. The 22 buildings in real WGS84 position, defaulting to Google Photorealistic 3D Tiles with a designed streetscape and georeferenced PLATEAU LOD2 context as alternate bases. Metric, demand, and supply toggles; hourly occupancy scrub |
| Energy twin, offline | `outputs/energy_view.html` | Working. three.js (module imports from the unpkg CDN); no map-tile, terrain, or Ion-token dependency; used for headless QA |
| Analytical dashboard (L1) | `analysis/dashboard.py` | Working. Streamlit, four tabs: twin, metrics, architecture, handoff |
| High-fidelity city twin | `outputs/cesium_view.html`, `outputs/twin_view.html` | Working. `cesium_view.html` streams the official PLATEAU LOD2 Cesium 3D Tileset; `twin_view.html` defaults to the georeferenced LOD2 build. See the georeferencing note below |
| Scene builder | `scripts/export_energy_scene.py` | Working. Reads WWR, R-value, and the per-sheet EUI column. Runs the V1 to V8 assertions and fails the build on violation |
| Per-building records, legacy | `data/energy/energy_dataset.json` | **Compromised.** Pro-rata split (Section 6.1). No generator script exists. No longer the twin's energy source |
| Per-building records, current | `outputs/energy/energy_scene.json` | Working. Rebuilt from `Index_energy` EUIs, 22 distinct intensities, vehicle load held as a block-level field |
| Retrofit parameters | `data/energy/Index_energy.xlsx` (baseline, s1, s2) | Available and joinable. EUI column now read |
| Supply optimization | `TS_ND_1_..._results.json` | Real REopt output: 417 kW PV, 100 kW / 783 kWh storage, 39.8% onsite renewable fraction. Optimized against a combined building-plus-vehicle, winter-peaking load |
| Per-building hourly workbooks | `data/energy/Nihonbashi_District/` (22 building workbooks, plus `Index_baseline.xlsx`) | Available. Sum to 655,461.23 kWh/yr |
| Vehicle charging series | `annual_total_car_bus_energy_8760h.csv` | Available. 608,551.86 kWh/yr, 8760 hours |
| Mobility pings | `pings_in_area_6677.geojson` | Available. 25,254 pings, 812 devices, EPSG:6677, single day 2018-08-08 |
| Occupancy profiles | `bldg_hourly_total_imputed 1.csv` | Partially usable. 31 buildings have no usable magnitude (Section 6.6) |
| Heat-cost field | `scripts/build_heat_cost_field.py`, `outputs/` | Working. Precomputed, not coupled to building loads |
| Robot ABM testbed | `sim/`, `scripts/run_testbed.py` | Working, Stage 1. Heat-aware routing, A/B scenarios. Not coupled to the energy layer |
| Curated view poses | `outputs/qa/camera_poses.json` | Written. Read by `scripts/qa_cesium_views.mjs --poses` |
| Simulation-ready USD export | Not yet written | Planned for Day 2 as the L2 to L3 bridge artifact. `usd-core` 26.8 verified working in this environment |
| L3 GPU environment | None | Not secured. No PACE allocation requested |

**Interface.** The twin presents one surface system: a single bottom dock carries the metric, demand, supply, layer, and clock controls with the color legend integrated as its right-most group, so no panel overlaps another. The clock is labeled SIM TIME, because it drives agent positions, the occupancy metric, and the Cesium sun, and does not relight the photoreal base mesh, whose daylight is baked into the tiles.

**Georeferencing.** The 22-building energy scene is correctly georeferenced: real WGS84 footprints, stored as local meters in `energy_scene.json` and re-projected by the view with the same anchor and constants, so the round trip is exact to the stored 0.01 m rounding. The high-fidelity PLATEAU city twin is georeferenced on both default paths, by different mechanisms.

`outputs/cesium_view.html` streams the official PLATEAU LOD2 Cesium 3D Tileset published by MLIT directly from the PLATEAU asset host, so it carries the publisher's own geodetic frame and is georeferenced by definition. Nothing in this project positions those tiles by hand.

`outputs/twin_view.html` defaults to the LOD2 build: `const useLod2 = (params.get("lod2") ?? "1") !== "0";`, and when that flag is set the mesh is placed with `root.position.set(cityDX, 0, cityDZ)` and `root.rotation.y = 0`, that is, with no rotation correction. It needs none because `scripts/fetch_plateau_lod2.py` decodes each source tile through CESIUM_RTC to ECEF, then to geodetic, then into the same local-meter frame and anchor as the OSM street network. Every vertex is therefore placed by its true earth-centered position, and the buildings share the street frame by construction rather than by fitting.

The unregistered placement is the legacy fallback only. Requesting `?lod2=0` loads the older welded `nihonbashi_city.glb`, which is centered on the agent grid and rotated by a hand-tuned angle because that source package carried no usable georeference. That path is reachable only by query parameter, and no figure in this document uses it. `scripts/register_city.py` exists for that legacy case and performs FFT footprint cross-correlation between PLATEAU and OSM footprints to recover a rotation and translation.

Accuracy is not claimed. The ECEF construction guarantees the correct frame, not a measured residual, and the visual confirmation of the LOD2 buildings against the OSM road centerlines has not yet been captured; it will be included with the July 31 package. No sub-meter alignment claim is made in this document.

---

## 10. Units and normalization conventions

These are locked here so that every figure, table, and abstract in the project uses the same basis. Any deviation must be labeled in the figure.

| Quantity | Convention |
|---|---|
| Energy | **Site** electricity, kWh. Source energy is not used. If a source conversion is ever needed, it is stated with its factor |
| Energy intensity | kWh/m²/yr, **site**, denominator = gross floor area. Abbreviated EUI throughout |
| Gross floor area | Footprint polygon area × `nfloor`, from `tokyo_bldg_smaller_block.geojson`, with the floor-height repair of Section 6.7 applied and recorded per building |
| Temporal basis | **Annual** totals for sizing and ranking. **Peak-day** (24 h) profiles for schedule and dispatch figures. Never mixed on one axis |
| Building vs vehicle load | Always reported separately. The combined figure is labeled "building + vehicle charging" and never called "building energy" |
| Scenario deltas | Percent change from baseline, **GFA-weighted** at block level, unweighted per building. Both are shown |
| Currency | JPY, millions (¥M), as in the source workbooks. Where USD is shown, the rate and its date are stated inline |
| Carbon | tonnes CO2 per year, from the REopt `ElectricUtility` output, attributed per building in proportion to corrected load |
| Coordinates | WGS84 (EPSG:4326) for all display. EPSG:6677 for ping source data, transformed via `pyproj`. Scene-local meters for USD, with the anchor recorded in metadata |
| Occupancy | Fraction of daily maximum, 0 to 1, 24 values. Buildings with imputed-empty magnitude are marked shape-only |

**Unresolved:** the 12.1× discrepancy between `Index_energy` EUIs (185.1 to 994.9 kWh/m²/yr) and workbook-derived intensities (approximately 65 kWh/m²/yr for building 2070). Until the studio team confirms the EUI definition, absolute EUI values are labeled "unverified scale" wherever they appear, and conclusions rest on relative comparison.

---

## 11. Verification checks that must pass before any figure ships

V1 to V8 are implemented as assertions in the scene builder, `scripts/export_energy_scene.py`, which writes nothing when a check fails. V9 to V12 run in the USD QA script, added with the exporter (Section 19, Day 2). V13 is added with the Phase A occupancy extraction. A failing assertion blocks the figure.

| # | Check | Pass condition | State |
|---|---|---|---|
| V1 | Distinct intensities | `len(set(round(eui,1))) >= 15` across 22 buildings. Catches any recurrence of the pro-rata construction | Passing at 22 of 22 |
| V2 | Plausible intensity range | All per-building intensities within 50 to 1,200 kWh/m²/yr. Any value outside it is listed, not silently clipped | Passing at 185.1 to 994.9 |
| V3 | ID set equality | Building ID sets from `tokyo_bldg_smaller_block.geojson`, `energy_dataset.json`, the three `Index_energy.xlsx` sheets, and `Nihonbashi_District/*.xlsx` are identical | Passing. The same 22 IDs in every source |
| V4 | Floor height sanity | 2.5 m ≤ height/nfloor ≤ 6.0 m for every building, after the Section 6.7 repair | Passing. 2563 and 3067 repaired, 2070 flagged |
| V5 | Sheet-total reconciliation | Stored Σ(EUI × GFA) agrees with a recomputation from the Index sheets to within 0.5%, for all three scenarios | Passing |
| V5b | Workbook reconciliation | Reported, not asserted: Σ(EUI × GFA) against the sum of the 22 hourly workbooks, with the ratio printed | Reported at 12.1×, the Section 6.10 blocker |
| V6 | Load decomposition | building_kWh + vehicle_kWh equals the REopt `annual_calculated_kwh` to within 1 kWh | Passing. Residual 0.00 kWh |
| V7 | Scenario consistency | `annual_reduction_kwh` equals `annual_reduction_pct` × baseline total, to within 0.5%, for s1 and s2 | Passing |
| V8 | Scenario coverage | Every building carries a usable EUI for baseline, s1, and s2 | Passing for all 22 |
| V9 | USD structure | `usdchecker` passes with no errors on the exported stage | With the exporter, Day 2 |
| V10 | USD units | `metersPerUnit == 1.0` and `upAxis` is set on the stage | With the exporter, Day 2 |
| V11 | USD content | Exactly 22 building meshes, each with a non-degenerate triangulated cap and outward normals | With the exporter, Day 2 |
| V12 | CRS round-trip | A ping transformed EPSG:6677 to WGS84 to scene-local meters and back lands within 0.5 m of its origin | With the exporter, Day 2 |
| V13 | Occupancy coverage | Every building's occupancy record is tagged `magnitude_ok`, `shape_only`, or `archetype_fallback`. No untagged records | With Phase A occupancy extraction |

---

## 12. Collaboration and attribution boundary

**Unresolved risk.** Data rights with the studio teammates are unclear. Three teammate datasets are at risk, and the ping data's provenance is unresolved:

| Dataset | Producer | Status | Contingency if unavailable |
|---|---|---|---|
| REopt run (`TS_ND_1_..._results.json`) | Studio teammate | **At risk.** No written agreement | Re-run REopt independently from the NREL public API using the corrected load; report the teammate run as a comparison point only if permitted |
| `Index_energy.xlsx` retrofit sheets (baseline, s1, s2, including EUI) | Studio teammate | **At risk.** No written agreement | Fall back to published Japanese office archetype EUIs and reconstruct scenarios parametrically. The method survives; the absolute numbers become archetype-based |
| Per-building hourly workbooks (`Nihonbashi_District/`) | Studio teammate | **At risk** | Same fallback as above |
| PLATEAU LOD2 geometry | MLIT open data | Clear. Open license | None needed |
| OSM road network | OpenStreetMap | Clear. ODbL, attribution required | None needed |
| Google Photorealistic 3D Tiles | Google, via Cesium ion | Clear for research display. On-screen attribution required in every capture | Fall back to Bing imagery or the designed streetscape base |
| Mobility ping data | Studio-provided, third-party origin | **Unclear provenance.** Licensing for publication not confirmed | Publish derived aggregate schedules only, never raw pings; confirm before any figure using ping data ships |
| Integration pipeline, twin, calibration method, fidelity evaluation, USD exporter, ABM | **The author** | Clear. Independently authored in this repository | None needed |

**The core contribution sits on the author-owned side of this boundary.** The integration pipeline, the reconciliation and calibration method, the twin, and the fidelity evaluation framework would survive intact if every teammate dataset had to be replaced with public archetype data. The absolute numbers would change; the method and the findings about the method would not.

> **ACTION ITEM, before the September 4 abstract: obtain written agreement from the studio teammates on use and attribution.** The items are: (a) permission to use the REopt run, `Index_energy.xlsx`, and the district hourly workbooks in publications; (b) the agreed citation or co-authorship arrangement for each; (c) confirmation of the ping data's licensing for derived publication. Target date: **August 15, 2026**, to leave time for the archetype fallback if agreement is not reached. Dr. Yang's guidance on the appropriate channel would be valuable here.

---

## 13. Positioning against the 2025–2026 literature

The July 2026 literature scan shows where not to compete.

| Thread | Representative work | Implication for this project |
|---|---|---|
| Agentic and LLM-driven urban twins | Ye et al. (2026), *Urban Informatics*; Xu et al. (2026), *Computers, Environment and Urban Systems* | **Commoditized.** Two papers already do LLM agents over urban twins. An agentic layer here is a convenience feature, not a contribution, and must not be the headline |
| District-scale energy twins | Paule et al. (2026), review, *Frontiers in Sustainable Cities* | Confirms the domain is active. The review's own critique, that most work treats demand or supply but rarely both on the same buildings, is where this integration sits; integration alone is not enough |
| Urban heat twins | Hossain et al. (2026), *Discover Cities* | Establishes heat as a twin-worthy variable. None of this work couples the heat field back to building retrofit decisions, which is the loop named in Section 5 |
| Pedestrian agents in twins | Lin and Wang (2026), SenseWalk | Pedestrian agents exist but are not coupled to energy or heat. The D-3 decision is open |
| Industry reference stack | NVIDIA (2025), Omniverse Blueprint for smart city AI | Establishes SimReady city twins plus synthetic data plus AI agents as an industry architecture. Academic evaluation of what that tier adds over a web twin is scarce, which is the secondary question here |

**Defensible edge:** the dataset coupling and its audit, the occupancy calibration with characterized failure modes, and the fidelity evaluation. Not the agent layer.

---

## 14. Figure plan

Each figure has a chart type, stated axes and units, a stated comparison, a color encoding, and the sentence with blanks that it exists to fill. If a figure cannot fill its sentence, the figure is wrong or the analysis is not done. Figure titles, provenance lines, and the unverified-magnitude caveat live in `outputs/figures/captions.md` and in this document, not inside the images.

| ID | Chart | Axes and units | Comparison | Color | Sentence it must fill |
|---|---|---|---|---|---|
| **F1** | Horizontal dot plot, 22 rows sorted by baseline EUI, three marks and a connector per row | y = building ID and use; x = energy use intensity, kWh/m²/yr | Baseline, S1, and S2 EUI per building, against a dashed reference at the 49.93 pro-rata constant | Grey baseline, blue S1, vermillion S2; grey dashed for the pro-rata reference | "Replacing the pro-rata split with per-building intensity widens the block's intensity range from the single value 49.93 to 185.1 to 994.9 kWh/m²/yr, and changes the rank position of 22 of 22 buildings; the Spearman rank correlation against the GFA ordering that the pro-rata construction reproduces is −0.62, below the 0.9 threshold." |
| **F2** | Horizontal bars, 22 rows, one bar each, sorted descending, top 5 highlighted | y = building ID; x = absolute annual saving under S2, kWh/yr | Saving = (EUI_baseline − EUI_S2) × GFA; each bar labeled with that building's own unweighted percent reduction | Single hue, highlight hue for the five largest | "The five buildings returning the largest absolute annual saving under S2 are 4050, 3042, 3554, 3562, and 4571; the GFA-weighted block reduction is 7.91%, not the flat 15% the twin previously applied, and 1 of 22 buildings gains under 1%." |
| **F3** | Two panels: (a) annual split, (b) stacked columns by month with monthly REopt ticks | x = month; y = electricity, MWh | Building load against EV and bus charging, stacked, with the REopt site load overlaid | Two-hue categorical, building load in the primary hue | "48.1% of the load the supply optimization was sized against is vehicle charging, and the combined load peaks in January at 150.8 MWh against 86.0 MWh in July, so the existing 417 kW PV and 783 kWh storage were sized against a winter-peaking load." |
| **F4** | Layered schematic, 4 columns, rendered by `scripts/build_figures.py` | none (schematic); boxes annotated with source magnitudes | Six source families reconciled into one per-building record, behind the V1 to V8 assertion gate | Grey sources, blue processes, dark hub, vermillion outputs and gate | "The pipeline reconciles 6 source families into one per-building record behind an 8-check assertion gate; building load (655,461 kWh/yr) and vehicle charging (608,552 kWh/yr) are carried as separate block-level layers and never summed into a per-building attribution." |
| **F5** | Grouped column, 3 load constructions × 2 metrics, dual panel | x = load construction (pro-rata flat, EUI-corrected, EUI-corrected + ping occupancy); y = PV kW (left panel), storage kWh (right panel) | The primary-question result | Sequential ramp across the three constructions | "Correcting per-building intensity and occupancy changes cost-optimal PV from 417 kW to ___ kW (___%) and storage from 783 kWh to ___ kWh (___%), which does / does not cross the 10% materiality threshold." |
| **F6** | Paired map panels with a difference inset | Plan view of the block; color = street-level heat cost, dimensionless index; inset = difference in index | Baseline against s2 retrofit, at the peak-day hour | Diverging ramp centered at zero for the difference inset only | *Outlook.* "Closing the retrofit-to-heat-rejection-to-street loop shifts the peak-hour street heat index by ___ over ___ m of the block's pedestrian network." |
| **F7** | Layered schematic, 4 columns plus one feedback loop, rendered by `scripts/build_figures.py` | none (schematic) | What runs today against what is scheduled: sources, processes, the `energy_scene.json` contract, the L1, L2, and L3 tiers, the agent and traffic layers, and the REopt re-run loop | Same palette as F4; solid = executed in the repository, dashed grey = planned, vermillion = assertion gate | "The system is four source families reconciled into one scene contract that three fidelity tiers read without recomputing anything, and the loop from the corrected load back to the supply optimization is the one arrow in the figure that is still dashed." |
| **F8** | Small-multiple line chart, 24 h, 3 panels | x = hour of day, 0 to 23; y = fraction of daily maximum, 0 to 1 | Ping-derived schedule against archetype schedule, for one normal building, one inverted building (2070), and the 167-building aggregate | One hue for ping-derived, grey for archetype | "Ping-derived occupancy is usable as a shape prior for ___ of 136 buildings; ___ show a night-over-day inversion consistent with overnight dwell bias, and ___ buildings have no usable magnitude." |

F1, F2, F3, and F5 are the core set for the CUPUM chapter. F4 is the methods figure and F7 is the system architecture figure. F6 is outlook. The July 31 field study package contains F1, F2, F3, F4, and F7. F5 waits on the supply re-run in Phase A, F6 waits on Phase B, and F8 waits on the occupancy extraction reaching figure quality.

Figure numbering note: F4 is the methods and data-pipeline schematic rendered by `scripts/build_figures.py`. The occupancy small-multiple numbered F4 in an earlier draft is now F8.

### 14.1 The July 31 figures

![Figure F1. Building energy use intensity by scenario.](../outputs/figures/F1_building_energy_intensity.png)

**F1. Building energy use intensity by scenario.** Site energy use intensity of the 22 buildings in the Nihonbashi study block, sorted by baseline intensity. Grey = baseline, blue = S1 (window-to-wall ratio −20%), vermillion = S2 (WWR −20% and R-value +40%); the connector spans the baseline-to-S2 travel. The dashed line at 49.93 kWh/m²/yr is the single pro-rata constant the twin previously assigned to every building. Denominator is gross floor area. The absolute EUI scale is unverified (Section 6.10): Σ(EUI × GFA) = 7,923,977 kWh/yr is 12.1× the hourly-workbook building load of 655,461 kWh/yr, so the ranking and the relative scenario deltas are the defensible reading, not the level. n = 22.

![Figure F2. Annual saving under S2 by building.](../outputs/figures/F2_retrofit_priority_s2.png)

**F2. Annual saving under S2 by building.** Absolute annual electricity saving under retrofit scenario S2 against baseline, per building, sorted descending; the five largest are highlighted and support decision D-1. Saving = (EUI_baseline − EUI_S2) × GFA. The label on each bar is that building's own percentage reduction, unweighted; the GFA-weighted block reduction is 7.91%, not the flat 15% the view previously applied. 1 of 22 buildings (2563) gains under 1% from the S2 package. Absolute EUI scale unverified (Section 6.10). n = 22.

![Figure F3. District electricity: composition and seasonality.](../outputs/figures/F3_load_composition_seasonality.png)

**F3. District electricity: composition and seasonality.** (a) Annual site electricity for the block, split into building load (655,461 kWh/yr, from 22 hourly workbooks) and EV plus bus charging (608,552 kWh/yr, from the 8760-hour series). (b) The same two layers by month; the black ticks are the monthly site load the REopt supply optimization was sized against. The decomposition is exact: 655,461.23 + 608,551.86 = 1,264,013.09 kWh/yr, residual 0.00 kWh (check V6). The twin previously attributed the whole site load to buildings pro rata, so 48.1% of every building's reported energy was transport charging. Building load and vehicle charging are never summed into a per-building figure.

![Figure F4. Data pipeline.](../outputs/figures/F4_pipeline_methods.png)

**F4. Data pipeline.** Six source families, one extraction or repair step each, reconciled into a single per-building record behind the eight verification checks V1 to V8. A failing check fails the build and writes nothing. The underlying artifacts are: retrofit parameters = `Index_energy.xlsx` (sheets baseline, s1, s2); simulated building loads = `Nihonbashi_District/*.xlsx`, 22 hourly workbooks, 655,461 kWh/yr; supply optimization = `TS_ND_1_nihonbashi_building_EV_PV_BESS_results.json`, 417 kW PV and 783 kWh storage; vehicle charging demand = `annual_total_car_bus_energy_8760h.csv`, 608,552 kWh/yr; mobility traces = `pings_in_area_6677.geojson`, 25,254 pings from 812 devices; city geometry = PLATEAU LOD2 and `tokyo_bldg_smaller_block.geojson`. The unified record is `outputs/energy/energy_scene.json`. Columns 1 to 3 are performed by `scripts/export_energy_scene.py` and column 4 by `scripts/build_figures.py`. Vehicle charging never enters a per-building record. Solid = built, dashed = designed and not yet executed.

![Figure F7. System architecture.](../outputs/figures/F7_system_architecture.png)

**F7. System architecture.** Sources, processes, the shared record, and the fidelity tiers that read it. The unified building energy record is the single contract: every tier reads it and none recomputes energy. Reconciliation writes it only after the eight verification checks V1 to V8 pass. Reconciliation is `scripts/export_energy_scene.py`, the pedestrian model is `scripts/run_testbed.py`, the unified record is `outputs/energy/energy_scene.json`, pedestrian trajectories are `agents_<scenario>.czml`, and the web digital twin is `outputs/energy_cesium_view.html` with `outputs/cesium_view.html` for the heat field. Fidelity tiers: L1 the analytical dashboard and basic views, L2 the photoreal web digital twin running today, L3 the game-engine or Omniverse simulation tier, reached through a simulation-ready USD export that is in progress. Solid = built and running in this repository; dashed = designed and not claimed as a result, namely the vehicle traffic layer, the simulation-ready export and the L3 tier, the supply re-run on the corrected load, and the MCP channel into the twin.

---

## 15. Curated views

Eight captures are committed in `outputs/figures/photoreal/`, together with the two-panel evolution composite used as Figure 0. They are labeled C0 to C7 to keep them distinct from the V-numbered verification checks in Section 11. C1 through C6 were captured interactively on GPU hardware on July 28, 2026, at 1920 × 1200. C0 and C7 sit on the designed streetscape base, C0 from the headless pose harness in this codespace. The camera poses are committed as `outputs/qa/camera_poses.json`, which `scripts/qa_cesium_views.mjs --poses` reads, so any re-capture reproduces the identical frame; the pose file records the harness path, the render settings, and the local server the views must be served from. Fields per pose: `lon`, `lat`, `height_m` (ellipsoidal), `heading_deg`, `pitch_deg`, `roll_deg`, plus the UI state.

Every capture that shows the photoreal base carries the on-screen Google and Cesium ion attribution, and that attribution must remain intact and legible in any reproduction. This applies to C1 through C6 and to panel (b) of Figure 0.

| ID | File | UI state | What it shows |
|---|---|---|---|
| **C0** | `C0_first_model_block_only.png` | Energy view, designed streetscape base, metric = intensity | The first working model: the study block alone, no photoreal context. Panel (a) of Figure 0 |
| **C1** | `C1_hero_energy_day.png` | Energy view, photoreal base, metric = energy, demand = baseline, supply = PV+BESS+CHP, day | Hero day oblique. The block reads as a data object against the real city |
| **C2** | `C2_energy_night_baked_lighting.png` | Same as C1, sim clock at night | Night sim time over a daylit mesh, which is the baked-lighting caveat made visible |
| **C3** | `C3_inspector_b4050_s1_energy.png` | Energy view, demand = S1, building 4050 selected | Building inspector: per-building energy, intensity, and the per-scenario WWR and R-value record |
| **C4** | `C4_eui_s1_inspector_b3042.png` | Metric = EUI, demand = S1, building 3042 selected | The intensity metric that the pro-rata construction previously flattened to one value |
| **C5** | `C5_wwr_s1_inspector_b3042.png` | Metric = WWR, demand = S1, building 3042 selected | The retrofit parameter layer, which drives the EUI deltas |
| **C6** | `C6_occupancy_agents_inspector_b3037.png` | Metric = occupancy, agents layer on, building 3037 selected | Ping-derived occupancy with the pedestrian agents visible, the D-3 precursor |
| **C7** | `C7_current_topdown_energy_base.png` | Energy view, designed base, top-down | Plan-view reference frame for the block, used to check footprint placement |

![Figure C1. Hero day oblique.](../outputs/figures/photoreal/C1_hero_energy_day.png)

**C1. The study block on photoreal urban context.** The 22 study buildings colored by annual building energy, on Google Photorealistic 3D Tiles, at a day sim time. The KPI card reports building load only: EV and bus charging are excluded, and the absolute scale comes from the unverified `Index_energy` EUI column (Section 6.10). The dock reads the same metric token as the legend. Basemap: Google Photorealistic 3D Tiles, © Google; rendered with CesiumJS.

![Figure C3. Building inspector, 4050.](../outputs/figures/photoreal/C3_inspector_b4050_s1_energy.png)

**C3. Per-building record, building 4050 under S1.** Selecting a building exposes the record the twin is built on: use, program, annual energy, intensity, and the WWR and R-value triple for baseline, S1, and S2. Under the previous pro-rata construction, the intensity field carried 49.93 kWh/m²/yr for every one of the 22 buildings. Building 4050 is also the largest absolute saver under S2 (F2) and the building with the widest EUI-to-workbook ratio, 47.1× (Section 6.10). Basemap: Google Photorealistic 3D Tiles, © Google.

![Figure C6. Occupancy with pedestrian agents.](../outputs/figures/photoreal/C6_occupancy_agents_inspector_b3037.png)

**C6. Ping-derived occupancy with the agent layer on.** The block colored by occupancy as a fraction of each building's own daily maximum, with the Mesa pedestrian agents drawn on the street network. This is the precursor to decision D-3: the agents route on the heat-cost field, which is not yet driven by the building loads shown here (Section 5). Approximately 24 of the 136 buildings with data show the night-over-day inversion described in Section 6.5. Basemap: Google Photorealistic 3D Tiles, © Google.

Capture procedure for re-capture: serve `outputs/` over HTTP with `python scripts/serve_outputs.py`, then run `node scripts/qa_cesium_views.mjs --poses`. One known constraint: this codespace has no GPU, and software rendering is too slow to screenshot the legacy welded city mesh (`outputs/twin/plateau/nihonbashi_city.glb`, 18 MB, 4.7 M triangles) reliably. The current default mesh is the lighter LOD2 build (`nihonbashi_lod2_opt.glb`, 1.7 MB, 0.66 M triangles). Photoreal captures stream Google tiles, which also exceed what software rendering completes in a reasonable time, so the committed set was captured on hardware-accelerated machines with the poses applied from the pose file.

---

## 16. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **GPU access for the L3 simulation tier never materializes.** No PACE allocation exists or has been requested for Omniverse or Isaac Sim | High | High for Phase C only | The ladder is a framework, not a dependency. The PLATEAU Unity or Unreal path runs on consumer hardware. If neither materializes, L3 is reported as an unexecuted tier with an argument for what it would add, and the study still delivers L1 and L2 results. Request PACE allocation by September 2026 regardless |
| **Data agreement not reached with teammates** | Medium | High for absolute numbers, low for method | Section 12 fallback: reconstruct from public archetype EUIs and an independent REopt run. Action item dated August 15, 2026 |
| **Units discrepancy (12.1×) unresolved** | Medium | Blocks absolute-value claims | Figures use relative comparison and label absolute scale as unverified. Escalate to the studio team immediately. This is the most schedule-critical open question |
| **Further data integrity defects surface** | Medium | Medium | The assertion suite in Section 11 runs on every build. New defects become documented findings rather than silent errors |
| **n = 22 is too small for statistical claims** | Certain | Medium | The study makes no distributional claims. Findings are reported as per-building deltas and as a block-level total, with the sample size stated in every caption. The block is treated as a case, not a sample |
| **Scope creep into the agentic layer** | Medium | Medium | Section 13 establishes that the agentic layer is commoditized. It is scoped to Phase C outlook and is not in the September or October deliverables |
| **Advisor feedback arrives too late to act on** | Low (mitigated) | High | The restructured design is sent to Dr. Yang at the end of Day 3 (July 30) so that Day 4 can absorb one round before the July 31 due date |

---

## 17. Limitations

1. **Archetype-based, not metered.** No building in the study has metered kWh ground truth. All energy values trace to simulation workbooks built on archetype assumptions. The study calibrates between representations; it does not validate against reality.
2. **n = 22.** One block, 22 buildings. Findings are a case study. No claim generalizes statistically to Tokyo or to other districts.
3. **Single-day mobility data from 2018.** The ping layer covers one day, 2018-08-08, with 812 devices. It carries no seasonal, weekday-versus-weekend, or post-pandemic variation, and it predates the study period by eight years. Occupancy derived from it is a shape prior, not a measurement.
4. **No usable occupancy magnitude for 31 buildings**, including three study buildings (2563, 3067, 4560).
5. **Geometry defects in the source data** affect at least two study buildings (Section 6.7). The floor counts are repaired from height and flagged, but the underlying footprint geometry is not correctable without better source data.
6. **The high-fidelity city twin is georeferenced but its alignment residual is unmeasured.** Both default paths are georeferenced by construction (Section 9). The residual against the OSM road centerlines has not been quantified, so street-level spatial claims are stated as approximate until that check ships with the July 31 package.
7. **The heating-dominated load profile is implausible for Tokyo offices** and is inherited from the source workbooks. Until it is explained, all supply-sizing results carry that inherited assumption.
8. **The absolute EUI scale is unverified.** The 12.1× discrepancy of Section 6.10 is open, so every absolute intensity in this document is a relative quantity with a provisional scale.
9. **The system is co-located, not yet coupled.** No information flows from the energy layer to the heat layer to the mobility layer. Closing one loop is the remaining research work, not completed work.
10. **The L3 simulation tier does not exist yet.** All statements about what it would add are hypotheses to be tested, not results.

---

## 18. Deliverables and timeline

| Date | Deliverable | Scope |
|---|---|---|
| **July 31, 2026** | **Field study package** (this document) | Restructured project design, corrected magnitude layer, figures F1 to F4 and F7, curated views C0 to C7, USD format-feasibility artifact, live demo links, executive summary |
| August 15, 2026 | Written data agreement with studio teammates | Action item, Section 12 |
| September 2026 | PACE or GPU access request submitted | For Phase C, regardless of outcome |
| **September 4, 2026** | **CUPUM 2027 long abstract, 500 words** | **Phase A results only.** The data reconciliation finding and the primary-question result. No agentic layer, no L3 claims |
| **October 23, 2026** | **CUPUM 2027 book chapter draft, 4,000 to 6,000 words** | **Phase A results plus the fidelity evaluation framework.** Phase B and C as outlook |
| **January 29, 2027** | **CUPUM 2027 revised book chapter** | Editor and reviewer revisions to the October draft, incorporating Phase B progress |
| **February 12, 2027** | **CUPUM 2027 conference paper or poster** | Phase B: the closed retrofit-to-heat-to-routing loop |
| Spring 2027 | L3 tier pilot and fidelity evaluation matrix | Phase C |
| **July 5 to 10, 2027** | **CUPUM 2027, Sydney** | Presentation |

The January 29, 2027 revised chapter falls at the end of Phase B (October 2026 to January 2027), so the revision window and the close-one-loop work compete for the same weeks. Phase B is planned accordingly: the revision draws on Phase A results, complete by then, and any Phase B result landing by late January is added as outlook, not as required content.

**ISMT (multimodal transportation, NUS), 8th edition:** the call for papers is not yet posted. Treated as **watch only**. No hard deliverable is planned against it. If the CFP appears with a compatible deadline, the Phase B robot and pedestrian routing work is the natural submission.

---

## 19. Execution plan, July 28 to 31, 2026

### Day 0.5, July 27: magnitude reconciliation (complete)

This half-day produced the data integrity audit reported in Section 6. The items below are the corrections that audit determined. The remaining three and a half days run July 28 to July 31.

1. `scripts/export_energy_scene.py` now reads the `EUI` column (zero-based index 10) from the `baseline`, `s1`, and `s2` sheets of `Index_energy.xlsx`, alongside the WWR and R-value it already read.
2. **The magnitude layer is decided.** Given the unresolved 12.1× discrepancy, this rule is recorded in the scene metadata: EUI values drive *relative* per-building intensity and *relative* scenario deltas; absolute annual kWh per building is reconstructed by rescaling the EUI-weighted distribution so that the block total matches the sum of the 22 hourly workbooks (655,461.23 kWh), and is carried in `annual_energy_kwh_reconciled`. This preserves both the real per-building variation and a defensible block total, and it is reversible once the studio team answers the units question.
3. **EV and vehicle load is separated from building load.** `ev_bus_load_kwh` is a block-level scene field (608,551.86 kWh) and vehicle energy is removed from every per-building attribution. The UI headline reads "building load only".
4. **The nfloor anomalies are repaired.** For 2563 and 3067, nfloor is derived from height at 3.5 m per floor and the correction is recorded per building in a `geometry_flag` field; 2070 is flagged rather than corrected.
5. **The scenario reductions are rebuilt** from the EUI sheets: per-building percentages, plus GFA-weighted block totals (-3.53% for s1, -7.91% for s2), replacing the flat multipliers in both `energy_view.html` and `energy_cesium_view.html`.
6. **The assertion suite V1 to V8 from Section 11 is in the scene builder**, and the build writes nothing on violation.
7. Send the units question (Section 6.10) to the studio team on July 28, so that an answer can arrive within the week.

### Day 1, July 28: figures

Produce F1, F2, F3, F4, and F7 to the specification in Section 14, with each figure's sentence filled in. All five ship in the July 31 package. F4 and F7 are schematics drawn from repository structure already in place, so they cost little beyond the three result figures. Capture the curated views using the committed camera poses in `outputs/qa/camera_poses.json`. F5 requires the supply re-run and is Phase A, not Day 1; the F5 slot is reserved in the document with its sentence stated and blanks visible.

### Day 2, July 29: USD exporter

Write a USD exporter for the 22-building scene. **This produces a format-feasibility artifact, not a SimReady asset.** The distinction is stated in the document and in the code header: SimReady requires physically based materials, semantic labeling, and physics properties that this export does not provide. It demonstrates that the scene's geometry and per-building attributes survive the round trip into the interchange format both L3 paths consume.

Traps to handle, all verified relevant in this environment (`usd-core` 26.8 installed and working):

- Set `metersPerUnit = 1.0` on the stage. The default is 0.01 and would silently shrink the block by 100×.
- Set the stage up axis rather than relying on a default.
- The scene frame is +X east, +Z north, +Y up, which is **left-handed**. three.js is right-handed with north at -Z. Converting requires flipping an axis.
- Flipping an axis reverses ring winding and inverts normals. Reverse the winding when flipping.
- Concave footprints need triangulated caps, not naive fans.
- Transform ping positions from EPSG:6677 via `pyproj`, not via the local equirectangular approximation.

Run V9 to V12 from Section 11. Report `usdchecker` output verbatim in the deliverable.

### Day 3, July 30: document restructure and advisor send

Finalize this document with Day 1 and Day 2 results filled in. Insert Figure 0 and the curated views. **Send to Dr. Yang by end of day**, with a short cover note flagging the three items where his judgment would help most: (a) whether the repositioned research question is the right one, (b) the appropriate channel for the teammate data agreement, and (c) whether the fidelity-evaluation framing is defensible for the CUPUM audience.

### Day 4, July 31: absorb feedback and ship

Incorporate one round of advisor feedback. Write the one-page executive summary. Verify every demo link resolves from a clean browser session, including the deployed URL. Upload the package to the Project Design folder.

---

## 20. References

Anderson, K., et al. (2017). *REopt: A platform for energy system integration and optimization* (NREL/TP-7A40-70022). National Renewable Energy Laboratory. https://doi.org/10.2172/1395453

Hossain, M. I., Hossan, M. R., Shaon, Z. H., & Ferdous, M. N. (2026). Linking digital twin paradigm for urban heat monitoring and policy integration to building smart city climate resilience. *Discover Cities*, 3, 1. https://doi.org/10.1007/s44327-025-00179-8

Lin, Z., & Wang, K. (2026). *SenseWalk: Agent-based semantic trajectory simulation powered by large language models in zoned environments*. arXiv:2607.00989. https://arxiv.org/abs/2607.00989

Ministry of Land, Infrastructure, Transport and Tourism (Japan). *PLATEAU: 3D city model open data*. https://www.mlit.go.jp/plateau/ (accessed July 28, 2026)

NVIDIA. (2025). *NVIDIA Omniverse Blueprint for smart city AI*. https://blogs.nvidia.com/blog/smart-city-ai-blueprint-europe/ (accessed July 28, 2026)

Paule, D., Pubule, J., Gabranova, U., Blumberga, A., & Blumberga, D. (2026). Digital twins for sustainable urban energy systems: a systematic review of market mechanisms, flexibility, and coordination at the district scale. *Frontiers in Sustainable Cities*, 8, 1837026. https://doi.org/10.3389/frsc.2026.1837026

Xu, H., Zlatanova, S., Li, X., Wachowicz, M., & Batty, M. (2026). Towards fully automated city operations: Integrating agentic AI with urban digital twins. *Computers, Environment and Urban Systems*, 128, 102449. https://doi.org/10.1016/j.compenvurbsys.2026.102449

Ye, X., Gong, W., Yang, Y., Zou, L., Tu, Z., Huang, X., Li, Z., Ning, H., & Wu, L. (2026). Towards Agentic Urban Digital Twins (AUDiTs): advancing new urban science through Human–AI co-learning agents. *Urban Informatics*, 5, 9. https://doi.org/10.1007/s44212-025-00099-3

No claim in this document rests on a source not listed here.
