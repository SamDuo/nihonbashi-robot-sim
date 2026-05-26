# Stage Two Data and Layer Requirements for Visualization

| | |
|---|---|
| **Owner** | Urban Digital Twins (Sam Duong, Yi Tai, Xilin Tang, Murugesan Devesh) |
| **Status** | Draft v0.1, 2026-05-25 |
| **Companion** | [system_architecture.md](system_architecture.md), [visualization_plan.md](visualization_plan.md) |
| **Purpose** | One single place that catalogs every layer feeding the digital twin viewer, what we have today, what we need next, and who owns each input. |

---

## A. 3D geometry layers

| Layer | Stage One (today) | Stage Two needed | Source / Provider | Format | Status |
|---|---|---|---|---|---|
| Buildings, Chuo-ku Nihonbashi | PLATEAU LOD2 no texture, clipped polygon | PLATEAU LOD2 textured plus selective LOD3 around Nihonbashi Bridge | MLIT PLATEAU (`13102`) | 3D Tiles | have |
| Buildings, Chiyoda-ku adjacent | none | PLATEAU LOD2 Chiyoda-ku, same clipping | MLIT PLATEAU (`13101`) | 3D Tiles | needed |
| Buildings, Sumida-ku east bank | none | PLATEAU LOD2 across the river | MLIT PLATEAU (`13107`) | 3D Tiles | optional |
| Road network | OSM raster basemap | SHP to SUMO `.net.xml` plus vector overlay | Yi Tai via ArcGIS Pro | `.shp`, `.net.xml`, GeoJSON | in progress |
| Terrain / DEM | Cesium ellipsoid (flat) | PLATEAU 1 m DEM quantized mesh | MLIT PLATEAU `dem` | quantized mesh | needed |
| Tree canopy / vegetation | none | PLATEAU vegetation LOD1 plus NDVI from Sentinel 2 | MLIT plus ESA | 3D Tiles plus GeoTIFF | needed |
| Land use / zoning | none | PLATEAU `lu` plus Tokyo MPP zoning | MLIT plus Tokyo Metropolitan Gov | GeoJSON | optional |
| Underground infrastructure | none | PLATEAU `unf` water gas telecom | MLIT | 3D Tiles | Stage Three |

## B. Urban Risk inputs (Urban Risk team owns)

| Layer | Stage One | Stage Two needed | Source | Format | Status |
|---|---|---|---|---|---|
| Synthetic population | numpy random uniform on 20 by 10 grid | Urban Risk synthetic population engine with cho level home assignment | Urban Risk | `population.csv` | placeholder |
| Hourly heat exposure raster | numpy synthetic diurnal | UTCI raster at 5 m resolution, 24 hour cycle | Urban Risk model or sensor based | NetCDF or GeoTIFF tiles | needed |
| Vulnerability score | derived from age and mobility | Urban Risk vulnerability index incorporating health, income, housing | Urban Risk | column on `population.csv` | placeholder |
| Occupancy schedule | uniform commute pattern | Tokyo Open Data pedestrian counts plus building occupancy | Tokyo Metro Gov plus Urban Risk | `occupancy.csv` | needed |
| Air temperature observations | none | JMA AMeDAS station network within Chuo-ku and Chiyoda-ku | Japan Meteorological Agency | CSV time series | needed |
| Surface temperature | none | Landsat 8, Landsat 9 thermal band | USGS, JAXA | GeoTIFF | optional |
| Heat island intensity layer | none | Observed minus rural baseline | Urban Risk derived | GeoTIFF | optional |

## C. Urban Regeneration inputs (Urban Regeneration team owns)

| Layer | Stage One | Stage Two needed | Source | Format | Status |
|---|---|---|---|---|---|
| Shelter cooling envelope | synthetic piecewise constant | N-UBEM hourly cooling demand per shelter building | Urban Regeneration | `shelter_envelope.csv` | placeholder |
| Building cooling capacity | synthetic nominal | ReOpt sized cooling capacity per building | Urban Regeneration | `cooling_capacity.csv` | placeholder |
| Energy supply mix | none | ReOpt PV plus storage plus grid time series | Urban Regeneration | `energy_supply.csv` | needed |
| Emissions intensity | synthetic per hour | Grid carbon intensity hourly from TEPCO data | Urban Regeneration plus TEPCO | `emissions_intensity.csv` | placeholder |
| Building footprints with cooling status | none | GeoJSON of all candidate shelters with N-UBEM outputs | Urban Regeneration | GeoJSON | needed |
| Renewable potential layer | none | Rooftop PV potential per building | Urban Regeneration plus PLATEAU surface | GeoJSON | optional |

## D. Urban Digital Twins outputs feeding the viz

| Output | Stage One | Stage Two needed | Format | Consumed by |
|---|---|---|---|---|
| Agent trajectories | snapshot per hour in `agents.csv` | time animated CZML | CZML or GeoJSON-T | Cesium, Re:Earth, Omniverse |
| Shelter polygons plus occupancy | static GeoJSON per scenario with hour properties | time aware CZML with live occupancy | CZML | Cesium, Re:Earth |
| Decision provenance | JSONL one line per decision | unchanged | JSONL | Streamlit, audit |
| Cooling gap residuals | CSV per agent and hour | unchanged | CSV | Streamlit, Urban Regeneration feedback |
| Six methodology metrics | CSV scalar plus hourly | add 50 replicate confidence intervals | CSV | Streamlit, proposal |
| Robot trajectories | none | from Mesa SUMO co simulation, fed to Isaac Sim playback | USD plus CZML | Omniverse, Isaac Sim |
| Heat exposure aggregated per cho | none | derived during run | GeoJSON | dashboard, Urban Risk feedback |

## E. Reference and supplementary layers

| Layer | Stage One | Stage Two needed | Source | Format | Status |
|---|---|---|---|---|---|
| Basemap | OSM tile (CartoDB Positron, OSM) | Carto Voyager, Mapbox Streets, or Tokyo Open Data tiles | various | XYZ tiles | swappable |
| Imagery (satellite, optional) | none | Sentinel 2 cloud free composite or PLATEAU ortho | ESA or MLIT | XYZ tiles | optional |
| Service nodes (charging, supply) | none | OSM POI plus Phase 4 designed nodes | OSM plus design team | GeoJSON | needed when Phase 4 lands |
| Pedestrian volume baseline | none | Tokyo Open Data pedestrian count | Tokyo Metro Gov | CSV time series | needed |
| Boundary polygons (chome) | hand drawn hexagon | Tokyo Statistical Bureau chome polygons | Tokyo Metro Gov | GeoJSON | needed |
| Sky and atmosphere | Cesium default | Omniverse volumetric atmosphere | NVIDIA | USD | Stage Two only |

## F. Visualization capabilities to add in Stage Two

| Capability | Why | Where it lives |
|---|---|---|
| Time animated playback of agents and shelters | Stakeholders want to see the day evolve | Cesium CZML, Re:Earth Story, Omniverse timeline |
| Side by side scenario comparison panes | Quick A versus B reading | Cesium split view, dashboard small multiples |
| Click through to building level details | Inspect cooling demand, occupants, emissions per building | Cesium info box, dashboard linked panel |
| Real time data refresh | When live sensors come online | TerriaJS or Cesium with refreshable feed |
| High fidelity rendering with path traced lighting | Proposal calls for photo real twin | NVIDIA Omniverse Kit on GT CURA HPC |
| Robot sensor level validation | Phase 6 of the methodology | NVIDIA Isaac Sim with PhysX |
| Stakeholder published link with story mode | Self paced walkthrough for Perry Yang, Subhro, Sei | Re:Earth Story or TerriaJS hosted catalog |

## G. Priority order for the next four weeks

1. Chiyoda-ku PLATEAU tileset, dual ward rendering. Fills the western buildings now missing in the Cesium view.
2. Yi Tai SHP to SUMO net, vector overlay on the twin. First real Nihonbashi network.
3. Time animated CZML for agents. Replaces hour slider with playback.
4. Urban Risk heat raster sample (any single hour at 5 m resolution). Replaces synthetic heat field.
5. Urban Regeneration N-UBEM sample for one shelter. Replaces synthetic envelope.
6. Tokyo chome boundary GeoJSON. Replaces hand drawn polygon.
7. PLATEAU DEM for Chuo-ku. Adds correct ground elevation.

Items 1, 2, and 3 unblock visual realism. Items 4 and 5 unblock the real data path. Item 6 makes the boundary correct. Item 7 adds polish.
