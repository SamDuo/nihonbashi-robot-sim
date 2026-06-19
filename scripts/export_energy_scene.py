"""Build outputs/energy/energy_scene.json for the energy digital-twin viewer.

Joins the 22 study-building footprints (tokyo_bldg_smaller_block.geojson, WGS84)
with the extracted energy/cost dataset (energy_dataset.json) and the REopt
PV+BESS supply optimisation (TS_ND_1_..._results.json), projecting footprints to
a local-metre frame anchored at the block centroid.

Run:  python scripts/export_energy_scene.py
"""
from __future__ import annotations
import json, math, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ED = ROOT / "data" / "energy"
OUT = ROOT / "outputs" / "energy"
OUT.mkdir(parents=True, exist_ok=True)

geo = json.load(open(ED / "tokyo_bldg_smaller_block.geojson"))
ds = json.load(open(ED / "energy_dataset.json"))
try:
    reopt = json.load(open(ED / "TS_ND_1_nihonbashi_building_EV_PV_BESS_results.json"))
except Exception:
    reopt = None
try:
    be = json.load(open(ED / "building_energy.json"))   # UBEM: enduse split, WWR, material, profile
except Exception:
    be = {}

# Per-building retrofit parameters per scenario (Index_energy.xlsx: baseline/s1/s2
# sheets give each building's real WWR + R-value under each demand scenario).
scn_by_id = {}
try:
    import openpyxl
    wbx = openpyxl.load_workbook(ED / "Index_energy.xlsx", read_only=True, data_only=True)
    for sh in ("baseline", "s1", "s2"):
        if sh not in wbx.sheetnames:
            continue
        ws = wbx[sh]
        hdr = [str(c).strip().lower() if c else "" for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
        ci = {h: i for i, h in enumerate(hdr)}
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or row[0] is None:
                continue
            rec = scn_by_id.setdefault(int(row[0]), {})
            rec[sh] = {"wwr": round(float(row[ci["window ratio"]]), 3),
                       "r": round(float(row[ci["r-value"]]), 2)}
    print(f"  Index_energy: {len(scn_by_id)} buildings × {len(['baseline','s1','s2'])} scenarios")
except Exception as e:
    print(f"  Index_energy not read ({e}); scenarios stay uniform")
# EV / transport sector (8760h car+bus) — annual total only for the integrated KPI
ev_annual_kwh = None
try:
    import csv
    with open(ED / "annual_total_car_bus_energy_8760h.csv") as f:
        r = csv.DictReader(f)
        ev_annual_kwh = round(sum(float(row["energy_consumed_kwh"]) for row in r))
except Exception:
    pass

by_id = {b["id"]: b for b in ds["buildings"]}

# ---- anchor at footprint centroid; project WGS84 -> local metres -------------
pts = []
for f in geo["features"]:
    g = f["geometry"]
    rings = g["coordinates"] if g["type"] == "Polygon" else g["coordinates"][0]
    for lng, lat in rings[0]:
        pts.append((lng, lat))
ALNG = sum(p[0] for p in pts) / len(pts)
ALAT = sum(p[1] for p in pts) / len(pts)
M_PER_LAT = 111320.0
M_PER_LNG = 111320.0 * math.cos(math.radians(ALAT))

def to_m(lng, lat):
    return [round((lng - ALNG) * M_PER_LNG, 2), round((lat - ALAT) * M_PER_LAT, 2)]

def outer_ring(geom):
    coords = geom["coordinates"]
    ring = coords[0] if geom["type"] == "Polygon" else coords[0][0]
    r = [to_m(x, y) for x, y in ring]
    if r and r[0] == r[-1]:
        r = r[:-1]                       # drop closing duplicate
    return r

# ---- per-building records ---------------------------------------------------
buildings = []
for f in geo["features"]:
    p = f["properties"]
    bid = p["id"]
    d = by_id.get(bid, {})
    u = be.get(str(bid), {})        # UBEM detail (enduse, WWR, material, profile)
    buildings.append({
        "id": bid,
        "poly": outer_ring(f["geometry"]),
        "height": round(float(p.get("height") or 12), 1),
        "nfloor": int(p.get("nfloor") or 1),
        "use": d.get("usename") or p.get("usename") or "Unknown",
        "tier": d.get("tier") or "Unknown",
        "gfa_m2": round(d.get("gfa_m2") or p.get("shape_area", 0), 1),
        "annual_energy_kwh": round(d.get("annual_energy_kwh") or 0, 0),
        "intensity": round(d.get("energy_intensity_kwh_m2") or 0, 1),
        "revit_cost_yenM": round(d.get("revitalization_cost_yenM") or 0, 1),
        "est_value_yenM": round(d.get("est_value_yenM") or 0, 1),
        "built_year": d.get("built_year"),
        # --- UBEM detail (real, varies per building) ---
        "wwr": u.get("wwr"),
        "material": u.get("material"),
        "r_value": u.get("r_value"),
        "program": u.get("program"),
        "enduse": u.get("enduse_frac"),       # {cooling,heating,lighting} fractions
        "profile24": u.get("profile24"),       # 0..1 hourly load shape
        "scn": scn_by_id.get(bid),             # real per-scenario WWR + R (baseline/s1/s2)
    })

# ---- supply scenarios (enrich PV+BESS with real REopt numbers) ---------------
supply = json.loads(json.dumps(ds["supply_scenarios"]))   # deep copy
if reopt:
    pv = reopt.get("PV", {})
    bess = reopt.get("ElectricStorage", {})
    site = reopt.get("Site", {})
    util = reopt.get("ElectricUtility", {})
    load = reopt.get("ElectricLoad", {})
    supply["pv_bess"].update({
        "pv_kw": round(pv.get("size_kw", 0)),
        "pv_annual_kwh": round(pv.get("annual_energy_produced_kwh", 0)),
        "bess_kw": round(bess.get("size_kw", 0)),
        "bess_kwh": round(bess.get("size_kwh", 0)),
        "onsite_renewable_frac": round(site.get("onsite_renewable_energy_fraction_of_total_load", 0), 3),
        "total_renewable_frac": round(site.get("onsite_and_grid_renewable_energy_fraction_of_total_load", 0), 3),
        "annual_co2_tonnes": round(util.get("annual_emissions_tonnes_CO2", supply["pv_bess"]["annual_co2_tonnes"]), 1),
        "reopt": True,
    })
    monthly_load = load.get("monthly_calculated_kwh")
else:
    monthly_load = None

demand = ds["demand_scenarios"]
total_energy = ds["totals"]["total_annual_energy_kwh"]

# ---- self-supply fractions per supply case (for per-building CO2 split) ------
supply["baseline"].setdefault("self_supply_frac", 0.0)
supply["pv_bess"].setdefault("self_supply_frac", supply["pv_bess"].get("onsite_renewable_frac", 0.4))
supply["pv_bess_chp"].setdefault("self_supply_frac", 0.55)

# ---- metric ranges for color normalisation ----------------------------------
def rng(key):
    vals = [b[key] for b in buildings if isinstance(b.get(key), (int, float))]
    return [min(vals), max(vals)] if vals else [0, 1]
metric_ranges = {k: rng(k) for k in
                 ["annual_energy_kwh", "intensity", "revit_cost_yenM", "est_value_yenM", "height", "nfloor", "wwr"]}

scene = {
    "meta": {
        "title": "Nihonbashi Energy Twin — carbon-neutrality pathways",
        "anchor_lat": ALAT, "anchor_lng": ALNG,
        "frame": "local metres, +x east, +z north, origin = block centroid",
        "n_buildings": len(buildings),
        "total_annual_energy_kwh": round(total_energy),
        "ev_annual_kwh": ev_annual_kwh,
    },
    "buildings": buildings,
    "supply_scenarios": supply,
    "demand_scenarios": demand,
    "monthly_load_kwh": monthly_load,
    "occupancy_hourly": {str(b["id"]): ds["occupancy_hourly"].get(str(b["id"]))
                         for b in buildings if str(b["id"]) in ds["occupancy_hourly"]},
    "metric_ranges": metric_ranges,
    "totals": ds["totals"],
}
out = OUT / "energy_scene.json"
json.dump(scene, open(out, "w"), separators=(",", ":"), ensure_ascii=False)
print(f"wrote {out}")
print(f"  buildings: {len(buildings)}  anchor=({ALAT:.5f},{ALNG:.5f})")
sx = [x for b in buildings for x, z in b["poly"]]
sz = [z for b in buildings for x, z in b["poly"]]
print(f"  scene span: x[{min(sx):.0f},{max(sx):.0f}] z[{min(sz):.0f},{max(sz):.0f}] m")
print(f"  energy range: {metric_ranges['annual_energy_kwh']} kWh")
print(f"  supply pv_bess: {supply['pv_bess'].get('pv_kw')}kW PV, "
      f"{supply['pv_bess'].get('bess_kwh')}kWh BESS, {supply['pv_bess']['annual_co2_tonnes']}t CO2")
