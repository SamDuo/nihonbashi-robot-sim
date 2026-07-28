"""Build outputs/energy/energy_scene.json for the energy digital-twin viewer.

Joins the 22 study-building footprints (tokyo_bldg_smaller_block.geojson, WGS84)
with the extracted energy/cost dataset (energy_dataset.json), the per-building
retrofit sheets (Index_energy.xlsx: baseline/s1/s2, including the EUI column),
the per-building hourly workbooks (Nihonbashi_District/*.xlsx), the 8760-hour
vehicle charging series and the REopt PV+BESS supply optimisation
(TS_ND_1_..._results.json), projecting footprints to a local-metre frame
anchored at the block centroid.

Magnitude layer (project_design.md Sections 6.10, 10, 19):
  * Per-building `intensity` is the REAL baseline EUI from Index_energy.xlsx.
    Its ABSOLUTE SCALE IS UNVERIFIED: Sigma(EUI x GFA) over the 22 buildings is
    ~12x the sum of the 22 hourly workbooks (655,461.23 kWh/yr). Until the
    studio team confirms the EUI definition (source vs site, per-floor vs
    per-footprint denominator, MJ vs kWh), EUI drives RELATIVE per-building
    intensity and RELATIVE scenario deltas only.
  * `annual_energy_kwh` = EUI x GFA (EUI scale, unverified absolute magnitude).
  * `annual_energy_kwh_reconciled` = the same EUI-weighted distribution
    rescaled so the block total matches the hourly-workbook sum. This is the
    defensible absolute magnitude layer and is reversible once the units
    question is answered.
  * Vehicle charging (EV + bus, 608,551.86 kWh/yr) is NEVER attributed to
    buildings. It is carried as a block-level field only. The REopt site load
    (1,264,013.09 kWh/yr) is building + vehicle and is labelled as such.

Fails loudly: Index_energy.xlsx is a hard dependency, and assertions V1-V8
(project_design.md Section 11) run before anything is written.

Run:  python scripts/export_energy_scene.py
"""
from __future__ import annotations
import csv, json, math, os, sys, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ED = ROOT / "data" / "energy"
OUT = ROOT / "outputs" / "energy"
OUT.mkdir(parents=True, exist_ok=True)

SCENARIOS = ("baseline", "s1", "s2")
# Storey height used to repair implausible nfloor values (Section 19, item 4).
REPAIR_STOREY_M = 3.5
FLOOR_H_MIN, FLOOR_H_MAX = 2.5, 6.0        # V4
EUI_MIN, EUI_MAX = 50.0, 1200.0            # V2, stated range
WORKBOOK_BUILDING_KWH = None               # computed below from the 22 workbooks


class BuildFailure(RuntimeError):
    pass


def fail(msg: str):
    raise BuildFailure(msg)


# --------------------------------------------------------------------------
# sources
# --------------------------------------------------------------------------
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

# ---- Index_energy.xlsx: real per-scenario WWR, R-value AND EUI ---------------
# FATAL on failure. A silent fallback here is what produced the pro-rata bug.
scn_by_id: dict[int, dict] = {}
try:
    import openpyxl
except Exception as e:                                   # pragma: no cover
    fail(f"openpyxl is required to read Index_energy.xlsx ({e})")

try:
    wbx = openpyxl.load_workbook(ED / "Index_energy.xlsx", read_only=True, data_only=True)
except Exception as e:
    fail(f"FATAL: cannot open Index_energy.xlsx ({e}). "
         "Per-building EUI is not optional; the build stops here.")

for sh in SCENARIOS:
    if sh not in wbx.sheetnames:
        fail(f"FATAL: Index_energy.xlsx is missing required sheet '{sh}' "
             f"(has {wbx.sheetnames})")
    ws = wbx[sh]
    hdr = [str(c).strip().lower() if c else "" for c in
           next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
    ci = {h: i for i, h in enumerate(hdr)}
    for col in ("window ratio", "r-value", "eui"):
        if col not in ci:
            fail(f"FATAL: sheet '{sh}' of Index_energy.xlsx has no '{col}' column "
                 f"(header={hdr})")
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or row[0] is None:
            continue
        eui = row[ci["eui"]]
        if eui is None:
            fail(f"FATAL: sheet '{sh}' row id={row[0]} has an empty EUI cell")
        rec = scn_by_id.setdefault(int(row[0]), {})
        rec[sh] = {"wwr": round(float(row[ci["window ratio"]]), 3),
                   "r": round(float(row[ci["r-value"]]), 2),
                   "eui": round(float(eui), 3)}
print(f"  Index_energy: {len(scn_by_id)} buildings x {len(SCENARIOS)} scenarios (WWR, R-value, EUI)")

# ---- EV / bus charging (8760 h) — block level ONLY, never per building ------
ev_annual_kwh = None
ev_monthly_kwh = None
try:
    DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_of_hour = []
    for m, d in enumerate(DAYS):
        month_of_hour += [m] * d * 24
    mo = [0.0] * 12
    tot = 0.0
    with open(ED / "annual_total_car_bus_energy_8760h.csv") as f:
        for i, row in enumerate(csv.DictReader(f)):
            v = float(row["energy_consumed_kwh"])
            tot += v
            if i < len(month_of_hour):
                mo[month_of_hour[i]] += v
    ev_annual_kwh = round(tot, 2)
    ev_monthly_kwh = [round(v, 2) for v in mo]
except Exception as e:
    fail(f"FATAL: cannot read annual_total_car_bus_energy_8760h.csv ({e})")

# ---- per-building hourly workbooks: the defensible building-load magnitude --
wb_annual: dict[int, float] = {}
wb_monthly = [0.0] * 12
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
month_of_hour = []
for m, d in enumerate(DAYS):
    month_of_hour += [m] * d * 24
wb_files = sorted(glob.glob(str(ED / "Nihonbashi_District" / "[0-9]*.xlsx")))
if not wb_files:
    fail("FATAL: no per-building hourly workbooks found in Nihonbashi_District/")
for fp in wb_files:
    bid = int(Path(fp).stem)
    wbb = openpyxl.load_workbook(fp, data_only=True, read_only=True)
    ws = wbb[wbb.sheetnames[0]]
    s = 0.0
    h = 0
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[0] is None and r[1] is None:
            continue
        v = sum(float(x or 0) for x in r[:3])
        s += v
        if h < len(month_of_hour):
            wb_monthly[month_of_hour[h]] += v
        h += 1
    wb_annual[bid] = s
    wbb.close()
wb_monthly = [round(v, 2) for v in wb_monthly]
WORKBOOK_BUILDING_KWH = round(sum(wb_annual.values()), 2)
print(f"  hourly workbooks: {len(wb_annual)} buildings, {WORKBOOK_BUILDING_KWH:,.2f} kWh/yr building load")
print(f"  vehicle charging: {ev_annual_kwh:,.2f} kWh/yr (EV + bus, block level, NOT per building)")

by_id = {b["id"]: b for b in ds["buildings"]}

# --------------------------------------------------------------------------
# anchor at footprint centroid; project WGS84 -> local metres
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# per-building records
# --------------------------------------------------------------------------
buildings = []
repairs = []
for f in geo["features"]:
    p = f["properties"]
    bid = p["id"]
    d = by_id.get(bid, {})
    u = be.get(str(bid), {})        # UBEM detail (enduse, WWR, material, profile)
    scn_raw = scn_by_id.get(bid)
    if not scn_raw:
        fail(f"FATAL: building {bid} has no row in Index_energy.xlsx")

    height = round(float(p.get("height") or 12), 1)
    nfloor_src = int(p.get("nfloor") or 1)
    footprint = float(p.get("shape_area") or 0.0)

    # --- V4 repair: implausible storey height => rebuild nfloor from height ---
    nfloor = nfloor_src
    geometry_flag = "ok"
    if nfloor_src <= 0 or not (FLOOR_H_MIN <= height / nfloor_src <= FLOOR_H_MAX):
        nfloor = max(1, int(round(height / REPAIR_STOREY_M)))
        geometry_flag = "nfloor_repaired_from_height"
        repairs.append((bid, height, nfloor_src, round(height / nfloor_src, 2),
                        nfloor, round(height / nfloor, 2)))
    elif height / nfloor_src > 5.5:
        geometry_flag = "flagged_tall_storey"      # 2070 at 5.94 m/floor: flagged, not corrected

    gfa = round(footprint * nfloor, 1)

    scn = {}
    base_eui = float(scn_raw["baseline"]["eui"])
    for s in SCENARIOS:
        if s not in scn_raw:
            fail(f"FATAL: building {bid} missing scenario sheet '{s}' in Index_energy.xlsx")
        eui = float(scn_raw[s]["eui"])
        scn[s] = {
            "wwr": scn_raw[s]["wwr"],
            "r": scn_raw[s]["r"],
            "eui": round(eui, 3),
            "annual_energy_kwh": round(eui * gfa, 1),
            # positive = reduction from baseline, same sign convention as
            # demand_scenarios[*].annual_reduction_pct and both viewers
            "reduction_pct": round(100.0 * (base_eui - eui) / base_eui, 3),
        }

    buildings.append({
        "id": bid,
        "poly": outer_ring(f["geometry"]),
        "height": height,
        "nfloor": nfloor,
        "nfloor_source": nfloor_src,
        "geometry_flag": geometry_flag,
        "floor_height_m": round(height / nfloor, 2),
        "use": d.get("usename") or p.get("usename") or "Unknown",
        "tier": d.get("tier") or "Unknown",
        "footprint_m2": round(footprint, 1),
        "gfa_m2": gfa,
        # --- corrected magnitude layer -----------------------------------
        "intensity": round(base_eui, 1),                 # real baseline EUI, kWh/m2/yr (unverified scale)
        "annual_energy_kwh": round(base_eui * gfa, 0),   # EUI x GFA, EUI scale
        "intensity_prorata_legacy": round(d.get("energy_intensity_kwh_m2") or 0, 2),
        "workbook_annual_kwh": round(wb_annual.get(bid, 0.0), 1),
        # ------------------------------------------------------------------
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
        "scn": scn,                            # per-scenario WWR + R + EUI + kWh + reduction_pct
    })

if repairs:
    print("  nfloor repairs (geometry_flag=nfloor_repaired_from_height):")
    for bid, h, nsrc, hsrc, nnew, hnew in repairs:
        print(f"    {bid}: height {h} m, nfloor {nsrc} ({hsrc} m/floor) -> "
              f"nfloor {nnew} ({hnew} m/floor)")

# ---- block totals on the EUI scale ------------------------------------------
total_gfa = round(sum(b["gfa_m2"] for b in buildings), 2)
block_eui_scale = {s: round(sum(b["scn"][s]["annual_energy_kwh"] for b in buildings), 1)
                   for s in SCENARIOS}
base_total = block_eui_scale["baseline"]

# EUI-weighted rescale to the defensible workbook magnitude (Section 19, item 2)
recon_k = WORKBOOK_BUILDING_KWH / base_total
for b in buildings:
    b["annual_energy_kwh_reconciled"] = round(b["annual_energy_kwh"] * recon_k, 1)

# --------------------------------------------------------------------------
# demand scenarios rebuilt from the sheets (GFA-weighted, internally consistent)
# --------------------------------------------------------------------------
LABELS = {"baseline": "Current demand",
          "s1": "S1 · WWR -20% (sheet EUI)",
          "s2": "S2 · WWR -20% + R +40% (sheet EUI)"}
demand = {}
for s in SCENARIOS:
    tot = block_eui_scale[s]
    red_kwh = round(base_total - tot, 1)
    red_pct = round(100.0 * red_kwh / base_total, 4)
    per = [b["scn"][s]["reduction_pct"] for b in buildings]
    demand[s] = {
        "label": LABELS[s],
        "annual_reduction_pct": red_pct,                 # GFA-weighted block reduction
        "annual_reduction_kwh": red_kwh,                 # EUI scale, consistent with pct
        "annual_reduction_kwh_reconciled": round(red_kwh * recon_k, 1),
        "block_annual_kwh": tot,
        "per_building_reduction_pct": {
            "min": round(min(per), 3), "max": round(max(per), 3),
            "mean_unweighted": round(sum(per) / len(per), 3),
            "n_under_1pct": sum(1 for v in per if abs(v) < 1.0),
        },
        "legacy_flat_pct": {"baseline": 0.0, "s1": 5.0, "s2": 15.0}[s],
        "sign_convention": "positive = reduction from baseline",
        "source": "Index_energy.xlsx EUI column, GFA-weighted over 22 buildings",
    }

# --------------------------------------------------------------------------
# supply scenarios (enrich PV+BESS with real REopt numbers)
# --------------------------------------------------------------------------
supply = json.loads(json.dumps(ds["supply_scenarios"]))   # deep copy
reopt_site_load_kwh = None
monthly_load = None
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
        "sized_against": "building + vehicle charging (REopt site load), winter-peaking",
    })
    monthly_load = load.get("monthly_calculated_kwh")
    reopt_site_load_kwh = load.get("annual_calculated_kwh")

# ---- self-supply fractions per supply case (for per-building CO2 split) ------
supply["baseline"].setdefault("self_supply_frac", 0.0)
supply["pv_bess"].setdefault("self_supply_frac", supply["pv_bess"].get("onsite_renewable_frac", 0.4))
supply["pv_bess_chp"].setdefault("self_supply_frac", 0.55)

# --------------------------------------------------------------------------
# metric ranges for colour normalisation
# --------------------------------------------------------------------------
def rng(key):
    vals = [b[key] for b in buildings if isinstance(b.get(key), (int, float))]
    return [min(vals), max(vals)] if vals else [0, 1]


metric_ranges = {k: rng(k) for k in
                 ["annual_energy_kwh", "intensity", "revit_cost_yenM", "est_value_yenM",
                  "height", "nfloor", "wwr"]}

totals = json.loads(json.dumps(ds["totals"]))
totals.update({
    "total_gfa_m2": total_gfa,
    "total_gfa_m2_source_nfloor": round(ds["totals"]["total_gfa_m2"], 4),
    # viewer-facing block total: BUILDING load only, EUI scale, consistent with
    # the sum of per-building annual_energy_kwh
    "total_annual_energy_kwh": base_total,
    "building_annual_energy_kwh_eui_scale": base_total,
    "building_annual_energy_kwh_workbook": WORKBOOK_BUILDING_KWH,
    "ev_bus_load_kwh": ev_annual_kwh,
    "reopt_site_load_kwh": reopt_site_load_kwh,
    "eui_to_workbook_scale_factor": round(recon_k, 6),
    "legacy_prorata_total_annual_energy_kwh": round(ds["totals"]["total_annual_energy_kwh"]),
})

scene = {
    "meta": {
        "title": "Nihonbashi Energy Twin — carbon-neutrality pathways",
        "anchor_lat": ALAT, "anchor_lng": ALNG,
        "frame": "local metres, +x east, +z north, origin = block centroid",
        "n_buildings": len(buildings),
        "generated_by": "scripts/export_energy_scene.py",
        # --- magnitude layer, stated explicitly (Sections 6.10 / 10 / 19) ---
        "magnitude_layer": {
            "intensity_source": "Index_energy.xlsx per-sheet EUI column (baseline/s1/s2)",
            "intensity_units": "kWh/m2/yr, site, denominator = GFA (footprint x nfloor)",
            "absolute_scale": "UNVERIFIED — sum(EUI x GFA) is ~12x the hourly-workbook "
                              "building load; use EUI for relative comparison and ranking only",
            "reconciled_field": "annual_energy_kwh_reconciled rescales the EUI distribution "
                                "so the block total equals the hourly-workbook sum",
            "vehicle_load": "EV + bus charging is block level only and is never attributed "
                            "to buildings",
        },
        # block-level loads, never conflated
        "building_load_kwh_eui_scale": base_total,
        "building_load_kwh_workbook": WORKBOOK_BUILDING_KWH,
        "ev_bus_load_kwh": ev_annual_kwh,
        "reopt_site_load_kwh": reopt_site_load_kwh,
        "reopt_site_load_note": "building + vehicle charging; NOT building energy",
        # legacy / deprecated
        "total_annual_energy_kwh": base_total,
        "ev_annual_kwh": ev_annual_kwh,
        "legacy_prorata_intensity_kwh_m2": 49.92954090210394,
    },
    "buildings": buildings,
    "supply_scenarios": supply,
    "demand_scenarios": demand,
    "monthly_load_kwh": monthly_load,                     # REopt: building + vehicle
    "monthly_building_load_kwh": wb_monthly,              # 22 hourly workbooks
    "monthly_ev_bus_load_kwh": ev_monthly_kwh,            # 8760 h car+bus series
    "occupancy_hourly": {str(b["id"]): ds["occupancy_hourly"].get(str(b["id"]))
                         for b in buildings if str(b["id"]) in ds["occupancy_hourly"]},
    "metric_ranges": metric_ranges,
    "totals": totals,
}

# --------------------------------------------------------------------------
# assertion suite (project_design.md Section 11, V1-V8). Fails the build.
# --------------------------------------------------------------------------
def run_assertions(scene):
    bs = scene["buildings"]
    failures, notes = [], []

    # V1 — distinct intensities (catches recurrence of the pro-rata bug)
    n_distinct = len({round(b["intensity"], 1) for b in bs})
    if n_distinct < 15:
        failures.append(f"V1 distinct intensities: {n_distinct} < 15 "
                        "(pro-rata bug may have recurred)")
    notes.append(f"V1 distinct intensities: {n_distinct}/22")

    # V2 — plausible intensity range
    bad = [(b["id"], b["intensity"]) for b in bs
           if not (EUI_MIN <= b["intensity"] <= EUI_MAX)]
    if bad:
        failures.append(f"V2 intensity outside [{EUI_MIN},{EUI_MAX}] kWh/m2/yr: {bad}")
    notes.append(f"V2 intensity range: {min(b['intensity'] for b in bs)} to "
                 f"{max(b['intensity'] for b in bs)} kWh/m2/yr")

    # V3 — ID-set equality across geojson, dataset, all three Index sheets, workbooks
    ids_scene = {b["id"] for b in bs}
    ids_geo = {f["properties"]["id"] for f in geo["features"]}
    ids_ds = {b["id"] for b in ds["buildings"]}
    ids_wb = set(wb_annual)
    sheet_sets = {}
    for s in SCENARIOS:
        sheet_sets[s] = {i for i, r in scn_by_id.items() if s in r}
    for name, s in [("geojson", ids_geo), ("energy_dataset.json", ids_ds),
                    ("workbooks", ids_wb)] + [(f"Index[{k}]", v) for k, v in sheet_sets.items()]:
        if s != ids_scene:
            failures.append(f"V3 ID-set mismatch vs {name}: "
                            f"only_scene={sorted(ids_scene - s)} only_{name}={sorted(s - ids_scene)}")
    notes.append(f"V3 ID sets: {len(ids_scene)} identical across geojson, dataset, "
                 f"3 Index sheets, 22 workbooks")

    # V4 — floor height sanity AFTER repair
    bad = [(b["id"], b["floor_height_m"]) for b in bs
           if not (FLOOR_H_MIN <= b["floor_height_m"] <= FLOOR_H_MAX)]
    if bad:
        failures.append(f"V4 floor height outside [{FLOOR_H_MIN},{FLOOR_H_MAX}] m: {bad}")
    rep = [b["id"] for b in bs if b["geometry_flag"] == "nfloor_repaired_from_height"]
    flg = [b["id"] for b in bs if b["geometry_flag"] == "flagged_tall_storey"]
    notes.append(f"V4 floor height ok; repaired={rep} flagged={flg}")

    # V5a — every building's EUI x GFA reconciles with the sheet recomputation
    for s in SCENARIOS:
        want = sum(scn_by_id[b["id"]][s]["eui"] * b["gfa_m2"] for b in bs)
        got = sum(b["scn"][s]["annual_energy_kwh"] for b in bs)
        if want == 0 or abs(got - want) / want > 0.005:
            failures.append(f"V5 sheet reconciliation [{s}]: stored {got:.1f} vs "
                            f"sheet {want:.1f} kWh ({100*(got-want)/want:+.3f}%)")
    notes.append("V5 sheet reconciliation: stored Sum(EUI x GFA) matches Index sheets "
                 "for all 3 scenarios within 0.5%")

    # V5b — workbook reconciliation is REPORTED, not asserted (Section 6.10 blocker)
    ratio = base_total / WORKBOOK_BUILDING_KWH
    notes.append(f"V5b workbook reconciliation: Sum(EUI x GFA)={base_total:,.0f} kWh vs "
                 f"workbooks={WORKBOOK_BUILDING_KWH:,.0f} kWh — ratio {ratio:.2f}x. "
                 "UNRESOLVED units discrepancy (Section 6.10); reported, not clipped.")

    # V6 — load decomposition
    if reopt_site_load_kwh is not None:
        resid = abs((WORKBOOK_BUILDING_KWH + ev_annual_kwh) - reopt_site_load_kwh)
        if resid > 1.0:
            failures.append(f"V6 load decomposition: building+vehicle differs from "
                            f"REopt site load by {resid:.2f} kWh")
        notes.append(f"V6 load decomposition: {WORKBOOK_BUILDING_KWH:,.2f} + "
                     f"{ev_annual_kwh:,.2f} = {reopt_site_load_kwh:,.2f} kWh "
                     f"(residual {resid:.2f} kWh)")

    # V7 — scenario consistency: reduction_kwh == pct x baseline total
    for s in SCENARIOS:
        d = scene["demand_scenarios"][s]
        want = d["annual_reduction_pct"] / 100.0 * base_total
        if abs(d["annual_reduction_kwh"] - want) > max(1.0, 0.005 * abs(want)):
            failures.append(f"V7 scenario consistency [{s}]: kwh={d['annual_reduction_kwh']} "
                            f"vs pct-implied {want:.1f}")
    notes.append("V7 scenario consistency: annual_reduction_kwh matches "
                 "annual_reduction_pct x baseline for s1 and s2")

    # V8 — every building has all three scenarios with a usable EUI
    for b in bs:
        for s in SCENARIOS:
            v = (b.get("scn") or {}).get(s, {}).get("eui")
            if v is None or v <= 0:
                failures.append(f"V8 building {b['id']} missing/invalid EUI for '{s}'")
    notes.append("V8 scenario coverage: all 22 buildings have baseline, s1, s2 EUI")

    for n in notes:
        print(f"  [ok] {n}")
    if failures:
        print("\nASSERTION FAILURES:")
        for f_ in failures:
            print(f"  [FAIL] {f_}")
        fail(f"{len(failures)} assertion(s) failed; nothing written.")


try:
    run_assertions(scene)
except BuildFailure as e:
    print(f"\nBUILD FAILED: {e}", file=sys.stderr)
    sys.exit(1)

out = OUT / "energy_scene.json"
json.dump(scene, open(out, "w"), separators=(",", ":"), ensure_ascii=False)
print(f"\nwrote {out}")
print(f"  buildings: {len(buildings)}  anchor=({ALAT:.5f},{ALNG:.5f})")
sx = [x for b in buildings for x, z in b["poly"]]
sz = [z for b in buildings for x, z in b["poly"]]
print(f"  scene span: x[{min(sx):.0f},{max(sx):.0f}] z[{min(sz):.0f},{max(sz):.0f}] m")
print(f"  intensity range (real EUI): {metric_ranges['intensity']} kWh/m2/yr")
print(f"  building load  : {base_total:,.0f} kWh/yr (EUI scale) / "
      f"{WORKBOOK_BUILDING_KWH:,.0f} kWh/yr (workbooks)")
print(f"  EV+bus charging: {ev_annual_kwh:,.0f} kWh/yr (block level, separate)")
print(f"  REopt site load: {reopt_site_load_kwh:,.2f} kWh/yr (building + vehicle)")
print(f"  demand s1: {demand['s1']['annual_reduction_pct']:+.4f} % "
      f"(was flat -5.00 %)   s2: {demand['s2']['annual_reduction_pct']:+.4f} % (was flat -15.00 %)")
print(f"  supply pv_bess: {supply['pv_bess'].get('pv_kw')}kW PV, "
      f"{supply['pv_bess'].get('bess_kwh')}kWh BESS, {supply['pv_bess']['annual_co2_tonnes']}t CO2")
