# Data

Canonical layer registry. Each subfolder has its own README with source URLs, CRS, date, and license.

| Folder | Purpose | Owner | Storage |
|---|---|---|---|
| `heat_risk/` | Heat-scenario classifier output, joined to sidewalk segments | Sam, Qinghao | Small CSV / GeoJSON in repo; raw rasters in OneDrive |
| `pedestrian/` | GPS, OD, density samples for the 200 m scene | Yi Tai | CSV in repo for samples; raw GPS in OneDrive |
| `network/` | OSM sidewalk graph + SUMO `.net.xml` build | Yi Tai | Repo |
| `robot_params/` | Variable matrix, baseline + proposal CSVs | All — see `CODEOWNERS` once added | Repo |

## Conventions

- All spatial layers in **EPSG:4326** (WGS84) for portability; reproject to JGD2000 / EPSG:2451 only when feeding ArcGIS Pro for stakeholder maps.
- Time fields in **ISO 8601** UTC (`YYYY-MM-DDTHH:mm:ssZ`).
- Each layer carries a `metadata.json` with `source`, `source_url`, `retrieved_date`, `crs`, `license`.
- Anything > 50 MB goes to the shared OneDrive folder. Link from the relevant README.

## Cross-repo data

Heat-risk classifier outputs are produced upstream in [`GT-Summer-Tokyo-Studio/2026-Summer-Tokyo-Studio`](https://github.com/GT-Summer-Tokyo-Studio/2026-Summer-Tokyo-Studio). This repo pulls the output via `scripts/sync_heat_risk.py` (to be added).
