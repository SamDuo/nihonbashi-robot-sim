# Project Design — Agentic Urban Energy–Heat Digital Twin of Nihonbashi

**Student:** Sam Duong  |  **Advisor:** Dr. Perry Yang
**Independent post-workshop research, Tokyo Studio 2026 → publication track**
**Prepared:** July 2026

---

## 1. Working title

*From Georeferenced Digital Twin to Omniverse: An AI-Assisted Energy–Heat–Mobility Twin for Block-Scale Urban Regeneration in Nihonbashi, Tokyo*

## 2. Research question

Can a block-scale urban digital twin that couples building energy demand (UBEM),
distributed supply optimization (PV + BESS + EV), and heat-aware mobility support
**AI-assisted scenario exploration** for urban regeneration decisions — and what does
migrating such a twin to a SimReady Omniverse environment add beyond web-based
(CesiumJS) visualization?

## 3. Gap and positioning (from July 2026 literature scan)

Current research frontier (2025–2026):

- **Agentic AI + urban digital twins** is the emerging paradigm — LLM-driven agents
  that query, run, and interpret twin scenarios ("Agentic Urban Digital Twins,"
  *Urban Informatics* 2025; "Towards fully automated city operations," *CEUS* 2026).
- **Heat-resilience digital twins** integrating sensor + geospatial + socio-economic
  data are an active thread (*Discover Cities* 2025; hazard-responsive equity-aware
  twins, arXiv 2025).
- **District-scale energy digital twins** are reviewed as a key enabler of
  decentralized energy coordination (*Frontiers in Sustainable Cities* 2026) — but
  most work treats demand OR supply, rarely both on the same georeferenced buildings.
- **Pedestrian/robot agents inside twins** remain rare; recent work uses LLM-driven
  crowd agents (SenseWalk 2026) but not coupled to energy or heat.
- **NVIDIA Omniverse Smart City Blueprint** (2025–26) established SimReady city
  twins + synthetic data + AI agents as an industry reference stack; academic
  evaluations of what Omniverse adds over web twins are still scarce.

**Our position:** no published block-scale twin couples (a) archetype UBEM with
per-building envelope-retrofit scenarios, (b) REopt PV/BESS/EV supply optimization,
(c) a heat-cost field driving pedestrian/robot mobility, and (d) mobility-data-driven
occupancy schedules — in one georeferenced PLATEAU-based scene. That coupling is the
contribution; the Omniverse migration is the forward-looking method extension.

## 4. What already exists (Tokyo Studio, July 2026)

| Asset | Status |
|---|---|
| Georeferenced Cesium twin (PLATEAU LOD2, Nihonbashi block) with live scenario controls | Working |
| UBEM: 22 buildings, material/R-value/WWR/use/HVAC, end-use split, 24 h + monthly profiles | Working |
| Envelope-retrofit scenarios (baseline / s1 / s2) with real per-building parameters | Working |
| REopt PV + BESS + EV supply optimization results joined to buildings | Working |
| Heat-cost field + pedestrian activity data (mobility pings, hourly, per building) | Working |
| Mesa ABM testbed (heat-aware robot routing, A/B scenarios) | Working (Stage 1) |
| Omniverse / Isaac Sim deployment plan (Phase 4–6, NVIDIA Smart City Blueprint mapping) | Planned |

## 5. Proposed development (Aug 2026 → Jul 2027)

**Phase A — Consolidate the coupled twin (Aug–Sep 2026)**
1. Validate/calibrate UBEM occupancy schedules against the hourly per-building
   activity data (mobility-driven occupancy — a novelty in itself).
2. Produce the core result: how cost-optimal PV/BESS sizing shifts under envelope
   retrofit scenarios s1/s2 vs baseline; sensitivity sweep on WWR/R-value.
3. Heat–energy coupling result: cooling end-use vs heat-field exposure on extreme
   days; grid-stress buffering by PV + BESS.

**Phase B — AI-assisted scenario layer (Oct–Dec 2026)**
4. Add an LLM/agentic interface over the twin: natural-language scenario queries
   ("retrofit all pre-1990 offices, size PV to cover 60% of the block") compiled to
   scenario runs + narrated results. This is the CUPUM "Era of AI" hook.

**Phase C — Omniverse migration pilot (Jan–Apr 2027)**
5. Export the block (PLATEAU geometry + scenario data) to USD; pilot the NVIDIA
   Smart City Blueprint path (Omniverse + Metropolis); evaluate concretely what it
   adds over the Cesium twin (physics, synthetic data, robot sim via Isaac).
6. Reconnect the Stage-1 heat-aware robot ABM inside the Omniverse scene
   (multimodal/robot angle for ISMT).

## 6. Publication targets and deadlines

| Venue | Angle | Deadline |
|---|---|---|
| **CUPUM 2027** (Sydney, "Future Cities in the Era of AI") — book chapter | Coupled energy–heat twin + agentic scenario layer | **Long abstract Sep 4, 2026**; chapter draft Oct 23, 2026 |
| CUPUM 2027 — conference paper (fallback/second) | Omniverse migration evaluation | Feb 12, 2027 |
| **ISMT 2026/8th** (NUS, multimodal transportation) | Heat-aware robot/pedestrian routing + EV energy coupling in the twin | CFP to be confirmed (7th was Nov 2025) |

## 7. Data, tools, and attribution

PLATEAU LOD2 (MLIT open data), OSM, CesiumJS; Mesa ABM; REopt (NREL); studio-team
energy datasets (Index_energy, building_energy, REopt run — used with attribution /
co-authorship as agreed with the studio team); Omniverse/Isaac via planned
PACE/LaunchPad access. Collaboration boundary: this independent project leads on the
twin integration, coupling analysis, AI scenario layer, and Omniverse migration;
teammates' demand/supply modeling is cited or co-authored per agreement.

## 8. Deliverables

1. Project design (this document) — July 2026.
2. CUPUM long abstract (500 w) — by Sep 4, 2026.
3. Coupled-scenario results notebook + three publication figures — Oct 2026.
4. CUPUM book chapter draft (4,000–6,000 w) — Oct 23, 2026.
5. Omniverse pilot + ISMT paper draft — spring 2027.
