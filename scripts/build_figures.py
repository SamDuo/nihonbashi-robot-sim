"""Regenerate every publication figure for the Nihonbashi field-study package.

Single entry point, no notebook state. Everything is read from
outputs/energy/energy_scene.json (built by scripts/export_energy_scene.py) so
the figures cannot drift from the twin.

    python scripts/build_figures.py

Writes 300 dpi PNGs to outputs/figures/ and prints a provenance line and the
"sentence it must fill" (project_design.md Section 14) for each figure.

Figures
  F1  Per-building energy use intensity, baseline / s1 / s2 (kWh/m2/yr)
  F2  Retrofit priority: absolute annual savings under s2 (kWh/yr)
  F3  Load composition and seasonality: building load vs EV+bus charging
  F4  Methods: the data pipeline
  F7  System architecture: sources to viewers, with the loops that are not closed yet

Conventions (project_design.md Section 10)
  * Energy is SITE electricity, kWh. Intensity is kWh/m2/yr, denominator = GFA.
  * Building load and vehicle charging are never summed into "building energy".
  * Index_energy EUI absolute scale is UNVERIFIED (Section 6.10); every figure
    that shows an absolute EUI or an EUI-derived kWh says so.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCENE_PATH = ROOT / "outputs" / "energy" / "energy_scene.json"
FIGDIR = ROOT / "outputs" / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

DPI = 300
TODAY = date.today().isoformat()

# --------------------------------------------------------------------------
# Single source of truth for colour. Okabe-Ito, colourblind-safe.
# Baseline is a neutral grey; s1 and s2 are the two accents. Reused everywhere.
# --------------------------------------------------------------------------
SCENARIO_COLORS = {
    "baseline": "#585858",   # neutral grey  — current / do-nothing
    "s1":       "#0072B2",   # blue          — S1, WWR -20 %
    "s2":       "#D55E00",   # vermillion    — S2, WWR -20 % + R +40 %
}
SCENARIO_LABELS = {
    "baseline": "Baseline",
    "s1": "S1 · WWR −20 %",
    "s2": "S2 · WWR −20 % + R +40 %",
}
# Load layers (F3). Distinct from the scenario accents on purpose.
LAYER_COLORS = {
    "building": "#0072B2",   # blue        — building load (22 hourly workbooks)
    "vehicle":  "#E69F00",   # orange      — EV + bus charging (8760 h series)
}
MUTED = "#8A8A8A"
RULE = "#B4B4B4"
INK = "#1A1A1A"

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": DPI,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.labelsize": 9.5,
    "axes.edgecolor": "#444444",
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": INK,
    "ytick.color": INK,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.frameon": False,
    "legend.fontsize": 8.5,
    "grid.color": "#DDDDDD",
    "grid.linewidth": 0.6,
})

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

PROVENANCE: list[str] = []


def provenance(fig_id: str, path: Path, magnitude: str, sources: str, note: str = ""):
    px = ""
    try:
        from PIL import Image
        with Image.open(path) as im:
            px = f", {im.size[0]}x{im.size[1]} px"
    except Exception:
        pass
    size_kb = path.stat().st_size / 1024
    line = (f"{fig_id}  {path.relative_to(ROOT)}  [{size_kb:.0f} kB{px}, {DPI} dpi]\n"
            f"      source : {sources}\n"
            f"      layer  : {magnitude}\n"
            f"      built  : {TODAY}" + (f"\n      note   : {note}" if note else ""))
    PROVENANCE.append(line)
    print(line)


def spearman(a, b):
    def rank(v):
        order = np.argsort(np.argsort(np.asarray(v, dtype=float)))
        return order.astype(float)
    ra, rb = rank(a), rank(b)
    ra -= ra.mean()
    rb -= rb.mean()
    return float((ra @ rb) / np.sqrt((ra @ ra) * (rb @ rb)))


# --------------------------------------------------------------------------
# load the scene
# --------------------------------------------------------------------------
scene = json.load(open(SCENE_PATH))
B = scene["buildings"]
DEM = scene["demand_scenarios"]
TOT = scene["totals"]
N = len(B)

PRORATA = scene["meta"]["legacy_prorata_intensity_kwh_m2"]
BUILD_WB = TOT["building_annual_energy_kwh_workbook"]
EVBUS = TOT["ev_bus_load_kwh"]
SITE = TOT["reopt_site_load_kwh"]

SRC_SCENE = "outputs/energy/energy_scene.json"
SRC_CHAIN = ("Index_energy.xlsx {baseline,s1,s2}.EUI × GFA(tokyo_bldg_smaller_block.geojson) "
             "→ " + SRC_SCENE)
UNVERIFIED = ("Index_energy EUI, site kWh/m²/yr — ABSOLUTE SCALE UNVERIFIED "
              "(project_design.md §6.10); relative comparison only")


# ==========================================================================
# F1 — per-building energy use intensity under baseline, s1, s2
# ==========================================================================
def fig_f1() -> Path:
    rows = sorted(B, key=lambda b: b["scn"]["baseline"]["eui"])
    y = np.arange(len(rows))
    base = np.array([r["scn"]["baseline"]["eui"] for r in rows])
    s1 = np.array([r["scn"]["s1"]["eui"] for r in rows])
    s2 = np.array([r["scn"]["s2"]["eui"] for r in rows])

    fig, ax = plt.subplots(figsize=(7.6, 7.4))
    ax.grid(axis="x", zorder=0)
    ax.set_axisbelow(True)

    # connector: the retrofit travel distance for each building
    for i in y:
        ax.plot([min(s2[i], base[i]), base[i]], [i, i],
                color=RULE, lw=1.2, zorder=1, solid_capstyle="round")

    ax.scatter(base, y, s=42, color=SCENARIO_COLORS["baseline"], zorder=3,
               label=SCENARIO_LABELS["baseline"])
    ax.scatter(s1, y, s=30, color=SCENARIO_COLORS["s1"], zorder=4, marker="o",
               label=SCENARIO_LABELS["s1"])
    ax.scatter(s2, y, s=44, color=SCENARIO_COLORS["s2"], zorder=5, marker="D",
               label=SCENARIO_LABELS["s2"])

    ax.axvline(PRORATA, color=MUTED, ls="--", lw=1.1, zorder=2)
    ax.text(PRORATA + 12, len(rows) - 0.4,
            f"previous pro-rata constant\n{PRORATA:.2f} kWh/m²/yr (all 22 buildings)",
            color=MUTED, fontsize=8, va="top", ha="left")

    labels = [f"{r['id']}  ·  {r['use'][:22]}" for r in rows]
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_ylim(-0.8, len(rows) - 0.2)
    ax.set_xlim(0, max(base) * 1.08)
    ax.set_xlabel("Energy use intensity (kWh/m²/yr, site; denominator = gross floor area)")
    ax.set_ylabel("Building ID and primary use")
    ax.set_title("F1 · Per-building energy use intensity replaces a single pro-rata constant\n"
                 f"Nihonbashi study block, n = {N} buildings, sorted by baseline intensity",
                 loc="left")
    ax.legend(loc="lower right", ncol=1)
    fig.text(0.005, -0.012,
             "Absolute EUI scale is unverified (project_design.md §6.10): Σ(EUI × GFA) is 12.1× the "
             "hourly-workbook building load.\nRanking and relative scenario deltas are the "
             "defensible reading. Source: Index_energy.xlsx, sheets baseline / s1 / s2.",
             fontsize=7.4, color="#555555", ha="left", va="top")

    p = FIGDIR / "F1_building_energy_intensity.png"
    fig.savefig(p)
    plt.close(fig)

    # sentence values
    gfa = np.array([b["gfa_m2"] for b in B])
    eui = np.array([b["scn"]["baseline"]["eui"] for b in B])
    prorata_energy = gfa * PRORATA                       # rank == GFA rank
    corrected_energy = eui * gfa
    rho = spearman(prorata_energy, corrected_energy)
    r_old = np.argsort(np.argsort(-prorata_energy))
    r_new = np.argsort(np.argsort(-corrected_energy))
    n_moved = int(np.sum(r_old != r_new))
    F1_FACTS.update(dict(lo=float(eui.min()), hi=float(eui.max()),
                         rho=rho, n_moved=n_moved))
    return p


# ==========================================================================
# F2 — retrofit priority: absolute annual savings under s2
# ==========================================================================
def fig_f2() -> Path:
    sav = [(b["scn"]["baseline"]["annual_energy_kwh"] - b["scn"]["s2"]["annual_energy_kwh"], b)
           for b in B]
    sav.sort(key=lambda t: -t[0])
    vals = np.array([v for v, _ in sav])
    ids = [b["id"] for _, b in sav]
    pct = [b["scn"]["s2"]["reduction_pct"] for _, b in sav]
    top5 = set(ids[:5])

    fig, ax = plt.subplots(figsize=(7.6, 7.0))
    ax.grid(axis="x", zorder=0)
    ax.set_axisbelow(True)
    y = np.arange(len(vals))
    colors = [SCENARIO_COLORS["s2"] if i in top5 else "#C9C9C9" for i in ids]
    ax.barh(y, vals / 1000.0, color=colors, height=0.72, zorder=3)

    for i, (v, p_) in enumerate(zip(vals, pct)):
        ax.text(v / 1000.0 + max(vals) / 1000.0 * 0.012, i,
                f"{p_:.1f} %", va="center", ha="left", fontsize=7.6,
                color=INK if ids[i] in top5 else "#767676")

    ax.set_yticks(y)
    ax.set_yticklabels([f"{i}" for i in ids])
    ax.invert_yaxis()
    ax.set_xlim(0, max(vals) / 1000.0 * 1.16)
    ax.set_xlabel("Absolute annual saving under S2 vs baseline (MWh/yr, EUI scale)")
    ax.set_ylabel("Building ID")
    ax.set_title("F2 · Retrofit priority (decision D-1): absolute annual saving under S2\n"
                 f"n = {N} buildings, sorted descending; top 5 highlighted; "
                 "label = per-building % reduction",
                 loc="left")

    handles = [plt.Line2D([], [], marker="s", ls="", ms=8,
                          color=SCENARIO_COLORS["s2"], label="Top 5 retrofit candidates"),
               plt.Line2D([], [], marker="s", ls="", ms=8,
                          color="#C9C9C9", label="Remaining buildings")]
    ax.legend(handles=handles, loc="lower right")

    zero = [i for i, p_ in zip(ids, pct) if p_ < 1.0]
    fig.text(0.005, -0.012,
             f"Absolute saving = (EUI_baseline − EUI_s2) × GFA. Percent reduction is per building, "
             f"unweighted; the GFA-weighted block reduction is "
             f"{DEM['s2']['annual_reduction_pct']:.2f} %, not the flat 15 % previously applied.\n"
             f"{len(zero)} of {N} buildings ({', '.join(str(i) for i in zero)}) gain under 1 % from "
             f"the S2 package. Absolute EUI scale unverified (§6.10). Source: Index_energy.xlsx.",
             fontsize=7.4, color="#555555", ha="left", va="top")

    p = FIGDIR / "F2_retrofit_priority_s2.png"
    fig.savefig(p)
    plt.close(fig)
    F2_FACTS.update(dict(top5=[(i, float(v), float(q))
                               for i, v, q in zip(ids[:5], vals[:5], pct[:5])],
                         n_under_1pct=len(zero), zero_ids=zero))
    return p


# ==========================================================================
# F3 — load composition and the seasonality correction
# ==========================================================================
def fig_f3() -> Path:
    mb = np.array(scene["monthly_building_load_kwh"], dtype=float) / 1000.0   # MWh
    mv = np.array(scene["monthly_ev_bus_load_kwh"], dtype=float) / 1000.0
    reopt = np.array(scene["monthly_load_kwh"], dtype=float) / 1000.0

    fig = plt.figure(figsize=(10.6, 4.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 2.9], wspace=0.34)

    # -- left: annual decomposition -------------------------------------
    axl = fig.add_subplot(gs[0, 0])
    b_mwh, v_mwh = BUILD_WB / 1000.0, EVBUS / 1000.0
    axl.bar([0], [b_mwh], width=0.7, color=LAYER_COLORS["building"], zorder=3)
    axl.bar([0], [v_mwh], bottom=[b_mwh], width=0.7, color=LAYER_COLORS["vehicle"], zorder=3)
    axl.text(0, b_mwh / 2, f"{100*b_mwh/(b_mwh+v_mwh):.1f} %",
             ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
    axl.text(0, b_mwh + v_mwh / 2, f"{100*v_mwh/(b_mwh+v_mwh):.1f} %",
             ha="center", va="center", color="#3A2A00", fontsize=9.5, fontweight="bold")
    axl.text(0.42, b_mwh / 2, f"Building load\n{BUILD_WB:,.0f} kWh/yr",
             ha="left", va="center", fontsize=7.8, color=INK)
    axl.text(0.42, b_mwh + v_mwh / 2, f"EV + bus\n{EVBUS:,.0f} kWh/yr",
             ha="left", va="center", fontsize=7.8, color=INK)
    axl.annotate(f"REopt site load\n{SITE:,.2f} kWh/yr",
                 xy=(0.36, b_mwh + v_mwh), xytext=(0.42, (b_mwh + v_mwh) * 1.02),
                 fontsize=7.8, color=INK, ha="left", va="center",
                 arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.9))
    axl.set_xlim(-0.95, 2.15)
    axl.set_ylim(0, (b_mwh + v_mwh) * 1.16)
    axl.set_xticks([])
    axl.set_ylabel("Annual electricity (MWh)")
    axl.grid(axis="y", zorder=0)
    axl.set_axisbelow(True)
    axl.set_title("a · Annual composition", loc="left", fontsize=9.5, pad=9)

    # -- right: monthly stack -------------------------------------------
    axr = fig.add_subplot(gs[0, 1])
    x = np.arange(12)
    axr.bar(x, mb, width=0.68, color=LAYER_COLORS["building"], zorder=3)
    axr.bar(x, mv, bottom=mb, width=0.68, color=LAYER_COLORS["vehicle"], zorder=3)
    axr.plot(x, reopt, ls="none", marker="_", ms=16, mew=1.8, color=INK, zorder=5)
    axr.grid(axis="y", zorder=0)
    axr.set_axisbelow(True)
    axr.set_xticks(x)
    axr.set_xticklabels(MONTHS)
    axr.set_xlabel("Month")
    axr.set_ylabel("Electricity (MWh)")
    axr.set_ylim(0, reopt.max() * 1.30)
    axr.set_title("b · Monthly load shape — winter-peaking, driven by the building component",
                  loc="left", fontsize=9.5, pad=9)

    jan, jul = int(np.argmax(reopt)), 6
    axr.annotate(f"Jan {reopt[jan]:.1f} MWh", xy=(jan, reopt[jan]),
                 xytext=(jan + 0.55, reopt[jan] * 1.10), fontsize=8,
                 arrowprops=dict(arrowstyle="->", color=INK, lw=0.9))
    axr.annotate(f"Jul {reopt[jul]:.1f} MWh", xy=(jul, reopt[jul]),
                 xytext=(jul - 1.2, reopt.max() * 1.06), fontsize=8,
                 arrowprops=dict(arrowstyle="->", color=INK, lw=0.9))
    axr.text(0.015, 0.965,
             f"peak / trough = {reopt.max()/reopt.min():.2f}×   "
             f"(min {MONTHS[int(np.argmin(reopt))]} {reopt.min():.1f} MWh)",
             transform=axr.transAxes, fontsize=7.8, color="#555555", va="top")

    handles = [plt.Rectangle((0, 0), 1, 1, color=LAYER_COLORS["building"]),
               plt.Rectangle((0, 0), 1, 1, color=LAYER_COLORS["vehicle"]),
               plt.Line2D([], [], ls="none", marker="_", ms=14, mew=1.8, color=INK)]
    labels = ["Building load — 22 hourly workbooks",
              "EV + bus charging — 8760 h series",
              "REopt monthly site load (the stack reproduces it exactly)"]
    fig.legend(handles, labels, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.09))
    fig.suptitle("F3 · The district total is building load plus vehicle charging, and it peaks in winter",
                 x=0.005, ha="left", fontsize=11, fontweight="bold", y=1.02)
    fig.text(0.005, -0.145,
             f"Decomposition is exact: {BUILD_WB:,.2f} + {EVBUS:,.2f} = {SITE:,.2f} kWh/yr "
             f"(check V6, residual 0.00 kWh). The twin previously attributed the whole site load to "
             f"buildings pro rata,\nso {100*v_mwh/(b_mwh+v_mwh):.1f} % of every building's \"energy\" "
             f"was transport charging. Sources: Nihonbashi_District/*.xlsx (22 workbooks), "
             f"annual_total_car_bus_energy_8760h.csv, TS_ND_1_…_results.json (ElectricLoad).",
             fontsize=7.4, color="#555555", ha="left", va="top")

    p = FIGDIR / "F3_load_composition_seasonality.png"
    fig.savefig(p)
    plt.close(fig)
    F3_FACTS.update(dict(veh_share=100 * v_mwh / (b_mwh + v_mwh),
                         jan=float(reopt[jan]), jul=float(reopt[jul]),
                         ratio=float(reopt.max() / reopt.min())))
    return p


# ==========================================================================
# F4 — methods / pipeline schematic
# ==========================================================================
def fig_f4() -> Path:
    fig, ax = plt.subplots(figsize=(11.0, 6.2))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 62)
    ax.axis("off")

    C_SRC = "#F2F2F2"
    C_SRC_EDGE = "#9A9A9A"
    C_PROC = "#0072B2"
    C_HUB = "#585858"
    C_OUT = "#D55E00"

    def box(x, y, w, h, text, fc, ec, tc="#1A1A1A", fs=8.2, weight="normal", r=1.4):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle=f"round,pad=0,rounding_size={r}",
                                    linewidth=1.1, facecolor=fc, edgecolor=ec, zorder=3))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=tc, zorder=4, linespacing=1.35, fontweight=weight)
        return (x, y, w, h)

    def arrow(a, b, side="h", color="#7A7A7A", lw=1.2, style="-|>"):
        if side == "h":
            p0 = (a[0] + a[2], a[1] + a[3] / 2)
            p1 = (b[0], b[1] + b[3] / 2)
        else:
            p0 = (a[0] + a[2] / 2, a[1])
            p1 = (b[0] + b[2] / 2, b[1] + b[3])
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=11,
                                     color=color, lw=lw, zorder=2,
                                     connectionstyle="arc3,rad=0.0",
                                     shrinkA=1.5, shrinkB=1.5))

    # ---- column headings ----
    for cx, t in [(2.5, "1 · SOURCES  (studio + open data)"),
                  (36.5, "2 · EXTRACTION & REPAIR"),
                  (60.0, "3 · RECONCILED\n     RECORD"),
                  (80.0, "4 · DELIVERABLES")]:
        ax.text(cx, 58.4, t, fontsize=8.6, fontweight="bold", color="#3A3A3A",
                ha="left", va="top", linespacing=1.3)
    for x in (34.5, 58.5, 78.5):
        ax.plot([x, x], [3, 57], color="#E2E2E2", lw=1.0, zorder=1)

    # ---- sources ----
    src = [
        ("Index_energy.xlsx\nbaseline · s1 · s2\nEUI, WWR, R-value", 49.0),
        ("Nihonbashi_District/\n22 hourly workbooks\n655,461 kWh/yr", 41.0),
        ("TS_ND_1_…_results.json\nREopt PV + BESS\n417 kW / 783 kWh", 33.0),
        ("annual_total_car_bus\n_energy_8760h.csv\n608,552 kWh/yr", 25.0),
        ("pings_in_area_6677\n.geojson · EPSG:6677\n25,254 pings, 812 devices", 17.0),
        ("PLATEAU LOD2 +\ntokyo_bldg_smaller_block\n.geojson · WGS84", 9.0),
    ]
    sboxes = []
    for t, y in src:
        sboxes.append(box(2.5, y, 30, 6.6, t, C_SRC, C_SRC_EDGE, fs=7.6))

    # ---- extraction / repair ----
    proc = [
        ("EUI join on building ID\n(22 = 22 = 22)", 47.5),
        ("nfloor repair from height\n@ 3.5 m/storey, flagged", 39.5),
        ("Load decomposition\nbuilding ≠ vehicle", 31.5),
        ("Monthly aggregation\n8760 h → 12 months", 23.5),
        ("Occupancy shape prior\n+ dwell-bias test", 15.5),
        ("WGS84 → local metres\nanchored at block centroid", 7.5),
    ]
    pboxes = []
    for t, y in proc:
        pboxes.append(box(36.5, y, 20.5, 6.2, t, "white", C_PROC, tc="#0B3B57", fs=7.6))

    for s, p_ in zip(sboxes, pboxes):
        arrow(s, p_)

    # ---- assertion gate ----
    gate = box(36.5, 1.0, 20.5, 5.0,
               "ASSERTION SUITE  V1–V8\nfails the build, writes nothing",
               "#FBEEE4", C_OUT, tc="#7A3600", fs=7.6, weight="bold")

    # ---- hub ----
    hub = box(60.0, 22.0, 17.0, 17.0,
              "energy_scene.json\n\n22 buildings\nEUI · GFA · scenarios\nblock loads kept\nseparate\n\n"
              "+ magnitude-layer\nprovenance",
              C_HUB, C_HUB, tc="white", fs=8.0, weight="bold")
    for p_ in pboxes:
        arrow(p_, hub)
    arrow(gate, hub, color=C_OUT, lw=1.3)

    # ---- outputs ----
    outs = [
        ("Cesium energy view\nenergy_cesium_view.html", 45.0),
        ("three.js offline view\nenergy_view.html", 36.5),
        ("Figures F1–F4\nbuild_figures.py", 28.0),
        ("USD export (Day 2)\nformat-feasibility artifact", 19.5),
    ]
    for t, y in outs:
        b_ = box(80.0, y, 18.0, 6.8, t, "white", C_OUT, tc="#7A3600", fs=7.6)
        arrow(hub, b_)

    # ---- unresolved blocker callout ----
    ax.add_patch(FancyBboxPatch((60.0, 6.0), 38.0, 12.0,
                                boxstyle="round,pad=0,rounding_size=1.4",
                                linewidth=1.1, facecolor="#FFF8E6",
                                edgecolor="#E69F00", zorder=3))
    ax.text(79.0, 12.0,
            "UNRESOLVED (project_design.md §6.10)\n"
            "Σ(EUI × GFA) = 7,923,977 kWh/yr is 12.1× the\n"
            "hourly-workbook building load of 655,461 kWh/yr.\n"
            "EUI drives relative intensity and scenario deltas;\n"
            "absolute magnitude is labelled unverified everywhere.",
            ha="center", va="center", fontsize=7.6, color="#6B4E00",
            zorder=4, linespacing=1.45)

    ax.text(0.0, 61.4,
            "F4 · Data pipeline: heterogeneous studio artefacts reconciled into one per-building record",
            fontsize=11, fontweight="bold", color=INK, ha="left")
    ax.text(0.0, -0.6,
            "Every arrow is executed code in this repository. scripts/export_energy_scene.py performs "
            "columns 1–3 and runs the assertion gate; scripts/build_figures.py performs column 4. "
            "Vehicle charging never enters a per-building record.",
            fontsize=7.4, color="#555555", ha="left", va="top")

    p = FIGDIR / "F4_pipeline_methods.png"
    fig.savefig(p)
    plt.close(fig)
    return p


# ==========================================================================
# F7 — system architecture
# ==========================================================================
# F4 answers "how was the number produced". F7 answers "what is the system":
# which artefacts exist, which process writes which, which viewer reads which,
# and which loops are open. Same palette and box/arrow grammar as F4 on purpose:
# a reader who has parsed F4 can parse F7 without relearning the notation.
def fig_f7() -> Path:
    fig, ax = plt.subplots(figsize=(12.4, 6.6))
    # use the full canvas: the box text is sized against these axes units, not the figure
    fig.subplots_adjust(left=0.012, right=0.988, top=0.985, bottom=0.015)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 64)
    ax.axis("off")

    C_SRC = "#F2F2F2"
    C_SRC_EDGE = "#9A9A9A"
    C_PROC = "#0072B2"
    C_HUB = "#585858"
    C_OUT = "#D55E00"
    C_PLAN = "#8A8A8A"          # planned / not executed yet — dashed everywhere

    def box(x, y, w, h, text, fc, ec, tc=INK, fs=7.6, weight="normal", r=1.4, ls="solid"):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle=f"round,pad=0,rounding_size={r}",
                                    linewidth=1.1, facecolor=fc, edgecolor=ec,
                                    linestyle=ls, zorder=3))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=tc, zorder=4, linespacing=1.35, fontweight=weight)
        return (x, y, w, h)

    def arrow(a, b, side="h", color="#7A7A7A", lw=1.2, ls="solid", rad=0.0,
              style="-|>", label=None, lx=0, ly=0, lcolor=None):
        if side == "h":
            p0 = (a[0] + a[2], a[1] + a[3] / 2)
            p1 = (b[0], b[1] + b[3] / 2)
        elif side == "v":                      # a above b
            p0 = (a[0] + a[2] / 2, a[1])
            p1 = (b[0] + b[2] / 2, b[1] + b[3])
        else:                                  # "u": a below b
            p0 = (a[0] + a[2] / 2, a[1] + a[3])
            p1 = (b[0] + b[2] / 2, b[1])
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=11,
                                     color=color, lw=lw, linestyle=ls, zorder=2,
                                     connectionstyle=f"arc3,rad={rad}",
                                     shrinkA=1.5, shrinkB=1.5))
        if label:
            ax.text((p0[0] + p1[0]) / 2 + lx, (p0[1] + p1[1]) / 2 + ly, label,
                    fontsize=6.8, color=lcolor or color, ha="center", va="center", zorder=5)

    # ---- column headings ----
    for cx, t in [(1.5, "1 · SOURCES"),
                  (26.5, "2 · PROCESSES  (executed code)"),
                  (52.0, "3 · SCENE CONTRACT"),
                  (73.5, "4 · VIEWERS · FIDELITY LADDER")]:
        ax.text(cx, 60.6, t, fontsize=8.6, fontweight="bold", color="#3A3A3A",
                ha="left", va="top", linespacing=1.3)
    for x in (24.5, 50.0, 71.5):
        ax.plot([x, x], [2.5, 59.2], color="#E2E2E2", lw=1.0, zorder=1)

    # ---- 1 · sources ----
    s_studio = box(1.5, 48.0, 22.0, 8.2,
                   "STUDIO ARTEFACTS\nIndex_energy.xlsx (baseline · s1 · s2)\n"
                   "22 hourly workbooks · REopt results.json", C_SRC, C_SRC_EDGE)
    s_open = box(1.5, 37.5, 22.0, 8.2,
                 "OPEN GEODATA\nPLATEAU LOD2 · OSM roads and water\n"
                 "Google Photorealistic 3D Tiles (Ion)", C_SRC, C_SRC_EDGE)
    s_mob = box(1.5, 27.0, 22.0, 8.2,
                "MOBILITY AND DEMAND\npings_in_area_6677.geojson (812 devices)\n"
                "annual_total_car_bus_energy_8760h.csv", C_SRC, C_SRC_EDGE)
    s_abm = box(1.5, 16.5, 22.0, 8.2,
                "PHASE 1 ABM TESTBED\nsim/testbed · 100 agents, 24 h\n"
                "walk network (OSM)", C_SRC, C_SRC_EDGE)

    # ---- 2 · processes ----
    p_scene = box(26.5, 47.0, 21.5, 9.2,
                  "export_energy_scene.py\nEUI join · load decomposition\n"
                  "nfloor repair · WGS84 → local m", "white", C_PROC, tc="#0B3B57")
    p_gate = box(26.5, 39.0, 21.5, 5.6,
                 "ASSERTION SUITE  V1–V8\nfails the build, writes nothing",
                 "#FBEEE4", C_OUT, tc="#7A3600", weight="bold")
    p_street = box(26.5, 30.0, 21.5, 6.4,
                   "export_streetscape.py\nOSM roads · water · kerb trees", "white", C_PROC, tc="#0B3B57")
    p_abm = box(26.5, 21.0, 21.5, 6.4,
                "run_testbed.py\nABM → time-dynamic CZML", "white", C_PROC, tc="#0B3B57")
    p_traffic = box(26.5, 12.0, 21.5, 6.4,
                    "build_traffic_czml.py\nsynthetic vehicles on OSM drive loops",
                    "white", C_PLAN, tc="#5A5A5A", ls="dashed")

    arrow(s_studio, p_scene)
    arrow(s_open, p_scene)
    arrow(s_open, p_street)
    arrow(s_mob, p_scene)
    arrow(s_mob, p_traffic, ls="dashed", color=C_PLAN)
    arrow(s_abm, p_abm)
    arrow(p_gate, p_scene, side="u", color=C_OUT, lw=1.3)

    # ---- 3 · scene contract ----
    hub = box(52.0, 40.0, 17.5, 16.2,
              "energy_scene.json\n\n22 buildings\nEUI · GFA · scenarios\n"
              "block loads kept separate\n+ magnitude provenance",
              C_HUB, C_HUB, tc="white", fs=7.8, weight="bold")
    a_street = box(52.0, 30.0, 17.5, 6.4, "streetscape.json\nroads · water · trees",
                   "white", C_HUB, tc="#2F2F2F")
    a_agents = box(52.0, 21.0, 17.5, 6.4,
                   "agents_<scenario>.czml\n100 ABM pedestrians · 24 h", "white", C_HUB, tc="#2F2F2F")
    a_traffic = box(52.0, 12.0, 17.5, 6.4, "traffic.czml\nillustrative, not simulated",
                    "white", C_PLAN, tc="#5A5A5A", ls="dashed")

    arrow(p_scene, hub)
    arrow(p_street, a_street)
    arrow(p_abm, a_agents)
    arrow(p_traffic, a_traffic, ls="dashed", color=C_PLAN)

    # ---- 4 · viewers ----
    v_l1 = box(73.5, 48.0, 24.5, 7.4,
               "L1 · offline three.js\nenergy_view.html — block massing, no stream",
               "white", C_OUT, tc="#7A3600")
    v_l2 = box(73.5, 33.5, 24.5, 12.4,
               "L2 · browser twin (Cesium)\nenergy_cesium_view.html\n"
               "photoreal base · study block clipped in\n"
               "agents · traffic · day–night · split\ncesium_view.html — heat field",
               "white", C_OUT, tc="#7A3600")
    v_fig = box(73.5, 24.0, 24.5, 7.4,
                "FIGURES AND CAPTURES\nbuild_figures.py · qa_cesium_views.mjs",
                "white", C_OUT, tc="#7A3600")
    v_l3 = box(73.5, 12.0, 24.5, 9.0,
               "L3 · USD export → Omniverse\nformat-feasibility artifact\n"
               "(scheduled, not executed)", "white", C_PLAN, tc="#5A5A5A", ls="dashed")

    arrow(hub, v_l1)
    arrow(hub, v_l2)
    arrow(hub, v_fig)
    arrow(hub, v_l3, ls="dashed", color=C_PLAN)
    arrow(a_street, v_l2)
    arrow(a_agents, v_l2)
    arrow(a_traffic, v_l2, ls="dashed", color=C_PLAN)

    # ---- the loop that is not closed yet: corrected load → REopt re-run → hub ----
    loop = box(26.5, 3.0, 43.0, 6.2,
               "REopt RE-RUN  ·  Phase A, not executed yet\n"
               "corrected per-building load + ping occupancy → new PV kW / storage kWh → F5",
               "#EAF3FA", C_PROC, tc="#0B3B57", ls="dashed")
    # routed through the column gutters so the loop never crosses a box:
    # hub -> down the right gutter -> into the re-run box; re-run -> up the left gutter -> process
    ax.plot([69.5, 70.6, 70.6], [42.0, 42.0, 6.1], color=C_PROC, lw=1.2, ls="dashed", zorder=2)
    ax.add_patch(FancyArrowPatch((70.6, 6.1), (69.5, 6.1), arrowstyle="-|>", mutation_scale=11,
                                 color=C_PROC, lw=1.2, linestyle="dashed", zorder=2, shrinkA=0, shrinkB=1))
    ax.plot([26.5, 25.4, 25.4, 31.0], [6.1, 6.1, 45.9, 45.9], color=C_PROC, lw=1.2, ls="dashed", zorder=2)
    ax.add_patch(FancyArrowPatch((31.0, 45.9), (31.0, 47.0), arrowstyle="-|>", mutation_scale=11,
                                 color=C_PROC, lw=1.2, linestyle="dashed", zorder=2, shrinkA=0, shrinkB=1))
    ax.text(50.0, 1.1, "the open loop: the supply optimisation still answers to the "
                       "uncorrected load", fontsize=7.2, color=C_PROC, ha="center", va="center")

    # ---- legend ----
    ax.add_patch(FancyBboxPatch((73.5, 3.0), 24.5, 6.2,
                                boxstyle="round,pad=0,rounding_size=1.4",
                                linewidth=1.0, facecolor="white", edgecolor="#D6D6D6", zorder=3))
    ax.plot([75.2, 78.2], [7.6, 7.6], color="#7A7A7A", lw=1.3, zorder=4)
    ax.text(79.0, 7.6, "executed in this repository", fontsize=7.0, va="center", color=INK, zorder=4)
    ax.plot([75.2, 78.2], [5.9, 5.9], color=C_PLAN, lw=1.3, ls="dashed", zorder=4)
    ax.text(79.0, 5.9, "planned / not executed yet", fontsize=7.0, va="center", color="#5A5A5A", zorder=4)
    ax.plot([75.2, 78.2], [4.2, 4.2], color=C_OUT, lw=1.3, zorder=4)
    ax.text(79.0, 4.2, "assertion gate — blocks the write", fontsize=7.0, va="center", color="#7A3600", zorder=4)

    ax.text(0.0, 63.4,
            "F7 · System architecture: four source families, one scene contract, three viewer tiers, "
            "one loop still open",
            fontsize=11, fontweight="bold", color=INK, ha="left")
    ax.text(0.0, -0.9,
            "Solid boxes and arrows are code that runs today; dashed elements are scheduled and "
            "explicitly not claimed as results. Every viewer reads the same energy_scene.json, which "
            "is the contract:\nno viewer recomputes energy, and no per-building record ever contains "
            "vehicle charging. Context traffic, when enabled, is illustrative; densities scaled from "
            "the measured EV and bus\ncharging series; pedestrian trajectories are Phase 1 ABM output.",
            fontsize=7.4, color="#555555", ha="left", va="top")

    p = FIGDIR / "F7_system_architecture.png"
    fig.savefig(p)
    plt.close(fig)
    return p


# --------------------------------------------------------------------------
F1_FACTS: dict = {}
F2_FACTS: dict = {}
F3_FACTS: dict = {}


def main():
    print(f"Nihonbashi figure build · {TODAY}")
    print(f"scene: {SCENE_PATH.relative_to(ROOT)}  ({N} buildings)\n")

    p1 = fig_f1()
    provenance("F1", p1, UNVERIFIED, SRC_CHAIN)
    p2 = fig_f2()
    provenance("F2", p2, UNVERIFIED,
               "Index_energy.xlsx {baseline,s2}.EUI × GFA → " + SRC_SCENE)
    p3 = fig_f3()
    provenance("F3", p3,
               "site kWh, VERIFIED — decomposition exact to 0.00 kWh (check V6)",
               "Nihonbashi_District/*.xlsx (22), annual_total_car_bus_energy_8760h.csv, "
               "TS_ND_1_nihonbashi_building_EV_PV_BESS_results.json → " + SRC_SCENE)
    p4 = fig_f4()
    provenance("F4", p4, "schematic, no magnitude layer",
               "repository structure: scripts/export_energy_scene.py, scripts/build_figures.py")
    p7 = fig_f7()
    provenance("F7", p7, "schematic, no magnitude layer",
               "repository structure: scripts/{export_energy_scene,export_streetscape,run_testbed}.py, "
               "outputs/energy_cesium_view.html, outputs/energy_view.html, outputs/cesium_view.html",
               note="dashed elements (traffic CZML, USD export, REopt re-run) are scheduled, "
                    "not executed; the figure says so on its face")

    print("\n" + "=" * 78)
    print("SENTENCES THE FIGURES FILL (project_design.md §14)")
    print("=" * 78)
    print(
        f"F1  Replacing the pro-rata split with per-building intensity widens the block's\n"
        f"    intensity range from a single value of {PRORATA:.2f} to "
        f"{F1_FACTS['lo']:.1f}–{F1_FACTS['hi']:.1f} kWh/m2/yr,\n"
        f"    and changes the rank order of {F1_FACTS['n_moved']} of {N} buildings "
        f"(Spearman rho = {F1_FACTS['rho']:.3f} against\n"
        f"    the pro-rata ordering, which is the GFA ordering)."
    )
    print(
        f"\nF2  The flat -5 % and -15 % scenario assumptions overstate the GFA-weighted block\n"
        f"    reduction by {5.0 - DEM['s1']['annual_reduction_pct']:.2f} and "
        f"{15.0 - DEM['s2']['annual_reduction_pct']:.2f} percentage points "
        f"(real: -{DEM['s1']['annual_reduction_pct']:.2f} % and "
        f"-{DEM['s2']['annual_reduction_pct']:.2f} %),\n"
        f"    and conceal that {F2_FACTS['n_under_1pct']} of {N} buildings "
        f"({', '.join(str(i) for i in F2_FACTS['zero_ids'])}) achieve under 1 % reduction under s2.\n"
        f"    Top 5 retrofit candidates by absolute annual saving: "
        + ", ".join(f"{i} ({v/1000:.1f} MWh/yr, {q:.1f} %)" for i, v, q in F2_FACTS["top5"])
    )
    print(
        f"\nF3  {F3_FACTS['veh_share']:.1f} % of the load the supply optimisation was sized against is\n"
        f"    vehicle charging, and the combined load peaks in January at {F3_FACTS['jan']:.1f} MWh\n"
        f"    against {F3_FACTS['jul']:.1f} MWh in July (peak/trough {F3_FACTS['ratio']:.2f}x), so the "
        f"existing 417 kW PV and\n    783 kWh storage were sized against a winter-peaking load."
    )
    print(
        f"\nF4  The pipeline reconciles 6 source families into one per-building record behind an\n"
        f"    8-check assertion gate; building load ({BUILD_WB:,.2f} kWh/yr) and vehicle charging\n"
        f"    ({EVBUS:,.2f} kWh/yr) are carried as separate block-level layers and never summed\n"
        f"    into a per-building attribution."
    )
    print(
        f"\nF7  The system is four source families reconciled into one scene contract "
        f"(energy_scene.json)\n    that three viewer tiers read without recomputing anything, and the "
        f"loop from the corrected\n    load back to the supply optimisation is the one arrow in the "
        f"figure that is still dashed."
    )
    print("\n" + "=" * 78)
    print(f"{len(PROVENANCE)} figures written to {FIGDIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
