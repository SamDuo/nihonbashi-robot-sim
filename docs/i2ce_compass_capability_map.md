# Portfolio → "360 Real Estate Compass" — Capability Map

**Prepared for:** Prof. Ingeborg Rocker, I2CE Lab (GT College of Design)
**From:** Sam Duong — urban-AI / digital-twin stack (GT)
**One line:** We already run working prototypes of the Compass's *core engine* and three of its hardest data layers. The funded work is **integration + validation on a real Atlanta site (The Stitch)** — not building from zero.

---

## How the existing repos map onto the Compass

| 360 Compass layer | Existing asset (repo) | Maturity | What the funded team adds |
|---|---|---|---|
| **Estimate value / optimal location** (the core) | **polyscape** — XGBoost + SHAP/GeoShapley site-suitability prediction, multi-scale viz | Working prototype | Retarget the model from a composite *suitability* index to **assessed/transaction value** (add real sales data) |
| GIS / geospatial mapping | polyscape, nihonbashi twin, polymetron | Working | Unify on one basemap/coordinate frame |
| Demographic & economic trends | polyscape (Census ACS + LODES jobs) | Working | Add rental / market-demand feeds |
| Urban growth / neighborhood evolution | polyscape (predictive hex surfaces) | Working | Time-series / trend layer |
| Infrastructure & mobility access | nihonbashi networks, polyscape (OSMnx/Overture), heatwave_route | Working | Transit/access scoring |
| **Environmental & climate factors** | **nihonbashi-robot-sim** — heat digital twin + scenario A/B + living visualization | Working (synthetic + OSM geometry) | Plug in real Atlanta heat / land-surface-temp data |
| **Zoning, land-use & building code** | **smart-codes-cura** — multi-agent RAG + knowledge graph over codes across 9 US cities (GT CURA) | Demo | Atlanta zoning/entitlement focus |
| Existing-conditions / site survey | polymetron / polymetron-ar — on-device CV + VLM scene assessment | Working demo | Structured condition reports |
| Generative AI → development variations / adaptive reuse | agentic + optimization scaffolding (cuOpt, MCP) + code-RAG + perception | Foundation | The generative dev-scenario engine |
| Construction / development costs | — | **gap** | Source cost data / partner |
| Comparable sales / investment performance | polyscape (comparative framework) | Partial | Real comps feed |

**Coverage:** working prototypes touch ~8 of 11 Compass layers; genuine gaps are construction cost, deep market comps, and a **unified integration layer**.

---

## The three pillars to demo

1. **polyscape** — *the Compass engine.* Predicts where to develop and *explains why* (SHAP), at city → district → street zoom. This is Rocker's "estimate value / identify optimal locations" goal, already running.
2. **nihonbashi-robot-sim** — *the climate + living-twin module.* Interactive, time-of-day, heat-aware district model — beats a static render or wood model for usability questions.
3. **smart-codes-cura** — *the code/zoning brain.* Answers cross-jurisdiction zoning & building-code questions via RAG. Already GT CURA-branded → inside the GT ecosystem she's recruiting into.

Supporting: **polymetron** (perception / existing-conditions), **heatwave_route** (mobility + climate), **Food_Circular_Network** (circular-economy thread — aligns with I2CE's literal name).

---

## Proposed pilot: The Stitch (division of labor)

| Our stack delivers | I2CE / architecture studio delivers |
|---|---|
| Location-intelligence + value/suitability scoring (polyscape) | Urban-design, massing, density/height scenarios |
| Climate/usability analysis of the new deck-park public realm (nihonbashi twin) | Vision report, entitlement framework |
| Zoning/code screening (smart-codes) | Physical wood massing model, exhibition materials |
| Interactive **district-scale digital model** for stakeholder & fundraising | Comprehensive redevelopment vision |

The Stitch is an ideal pilot for us: it caps a highway with new public space, so the key question — *"will people use this ground in an Atlanta summer?"* — is exactly our climate-twin strength.

---

## What the I2CE sponsorship funds

These are **separate prototypes today**, not one platform. A small funded team across summer/fall would **integrate them into a single "Compass" pilot and validate it on The Stitch** — matching Rocker's timeline (robust pilot by end of summer, real-site test in fall).

---

## Maturity & honesty ledger (don't overstate in the room)

| Asset | Honest status |
|---|---|
| polyscape | Working prototype. Predicts a **composite suitability index** (POI mix, walk score, etc.), **not** validated property value yet — retargetable with real sales data. |
| smart-codes-cura | RAG **prototype** for cross-jurisdiction code Q&A; not a certified compliance tool. |
| nihonbashi twin | Infrastructure complete; runs on **synthetic + OSM** data. Photoreal 3D mesh is Tokyo/PLATEAU-only — Atlanta would use OSM/USGS. Research *result* pending real heat data. |
| polymetron / -ar | Working on-device CV/VLM **demo** — scene description/flagging, not a calibrated inspection instrument. |
| heatwave_route | Working heat-routing tool (Tokyo studio). |
| Integration layer | **Does not exist yet** — this is the proposed funded deliverable. |
</content>
