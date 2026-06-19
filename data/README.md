# Data

Canonical layer registry. Each subfolder has its own README with source URLs, CRS, date, and license.

| Folder | Purpose | Owner | Storage |
|---|---|---|---|
| `heat_risk/` | Heat-scenario classifier output, joined to sidewalk segments | Sam, Qinghao | Small CSV / GeoJSON in repo; raw rasters in OneDrive |
| `pedestrian/` | GPS, OD, density samples for the 200 m scene | Yi Tai | CSV in repo for samples; raw GPS in OneDrive |
| `network/` | OSM sidewalk graph + SUMO `.net.xml` build | Yi Tai | Repo |
| `network/nihonbashi_geometry.json` | WebGL-twin district geometry: official 日本橋* machi boundary union (10 admin_level=9 relations), 4,160 building footprints w/ heights (`src`: osm_height/osm_levels/estimated), classified roads, Nihonbashi River polygons. Local-meter frame anchored at `sim/testbed/scene.py` ANCHOR. Source: OpenStreetMap via Overpass, retrieved 2026-06-12, EPSG:4326 → local meters, **ODbL** (© OpenStreetMap contributors). Rebuild: `scripts/build_city_geometry.py` | Sam | Repo (raw Overpass cache gitignored) |
| `robot_params/` | Variable matrix, baseline + proposal CSVs | All — see `CODEOWNERS` once added | Repo |

## Conventions

- All spatial layers in **EPSG:4326** (WGS84) for portability; reproject to JGD2000 / EPSG:2451 only when feeding ArcGIS Pro for stakeholder maps.
- Time fields in **ISO 8601** UTC (`YYYY-MM-DDTHH:mm:ssZ`).
- Each layer carries a `metadata.json` with `source`, `source_url`, `retrieved_date`, `crs`, `license`.
- Anything > 50 MB goes to the shared OneDrive folder. Link from the relevant README.

## Cross-repo data

Heat-risk classifier outputs are produced upstream in [`GT-Summer-Tokyo-Studio/2026-Summer-Tokyo-Studio`](https://github.com/GT-Summer-Tokyo-Studio/2026-Summer-Tokyo-Studio). This repo pulls the output via `scripts/sync_heat_risk.py` (to be added).
