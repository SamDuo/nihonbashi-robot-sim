"""Regenerate every publication figure for the Nihonbashi field-study package.

Single entry point, no notebook state. Everything is read from
outputs/energy/energy_scene.json (built by scripts/export_energy_scene.py) so
the figures cannot drift from the twin.

    python scripts/build_figures.py

Writes 300 dpi PNGs to outputs/figures/, prints a provenance block per figure,
and writes outputs/figures/captions.md.

Division of labour between the image and the document
  * The image carries marks: data, axes, terse noun-phrase titles, and data
    callouts of at most four words plus a number.
  * The document carries prose: figure number, caption, source chain, the
    unverified-magnitude caveat, build date. None of that is rendered inside
    a PNG. captions.md holds a ready-to-paste caption for each figure.

Figures
  F1  Building energy use intensity by scenario
  F2  Annual saving under S2 by building
  F3  District electricity: composition and seasonality
  F4  Data pipeline
  F7  System architecture

Conventions (project_design.md Section 10)
  * Energy is SITE electricity, kWh. Intensity is kWh/m2/yr, denominator = GFA.
  * Building load and vehicle charging are never summed into "building energy".
  * Index_energy EUI absolute scale is UNVERIFIED (Section 6.10). That caveat
    lives in the caption, not in the image.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
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
    "s1": "S1",
    "s2": "S2",
}
# Load layers (F3). Distinct from the scenario accents on purpose.
LAYER_COLORS = {
    "building": "#0072B2",   # blue        — building load (22 hourly workbooks)
    "vehicle":  "#E69F00",   # orange      — EV + bus charging (8760 h series)
}
MUTED = "#8A8A8A"
RULE = "#B4B4B4"
INK = "#1A1A1A"

# Schematic grammar (F4, F7): grey for everything, one accent for the hub,
# dashed stroke for designed-not-built. Nothing else.
SCHEMA_EDGE = "#6E6E6E"
SCHEMA_ARROW = "#9A9A9A"
SCHEMA_PLAN = "#A8A8A8"
SCHEMA_ACCENT = SCENARIO_COLORS["s2"]

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": DPI,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.titlesize": 10.5,
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
EUI_TOTAL = float(sum(b["scn"]["baseline"]["annual_energy_kwh"] for b in B))
EUI_RATIO = EUI_TOTAL / BUILD_WB

SRC_SCENE = "outputs/energy/energy_scene.json"
SRC_CHAIN = ("Index_energy.xlsx {baseline, s1, s2}.EUI x GFA "
             "(tokyo_bldg_smaller_block.geojson) -> " + SRC_SCENE)
UNVERIFIED = ("Index_energy EUI, site kWh/m2/yr — ABSOLUTE SCALE UNVERIFIED "
              "(project_design.md 6.10); relative comparison only")

# fig_id -> record, filled as each figure is written
RECORDS: list[dict] = []


def record(fig_id: str, path: Path, title: str, caption: str,
           sources: str, layer: str, note: str = ""):
    """Print provenance to stdout and stash it for captions.md."""
    px = ""
    try:
        from PIL import Image
        with Image.open(path) as im:
            px = f"{im.size[0]}x{im.size[1]} px"
    except Exception:
        px = "unknown size"
    size_kb = path.stat().st_size / 1024
    rec = dict(fig_id=fig_id, path=path, title=title, caption=caption,
               sources=sources, layer=layer, note=note,
               px=px, size_kb=size_kb)
    RECORDS.append(rec)
    print(f"{fig_id}  {path.relative_to(ROOT)}  [{size_kb:.0f} kB, {px}, {DPI} dpi]")
    print(f"      title  : {title}")
    print(f"      source : {sources}")
    print(f"      layer  : {layer}")
    print(f"      built  : {TODAY}")
    if note:
        print(f"      note   : {note}")


def write_captions():
    out = [
        "# Figure captions",
        "",
        f"Generated by `scripts/build_figures.py` on {TODAY}. The PNGs carry marks only:",
        "figure numbers, provenance, build dates and the unverified-magnitude caveat live",
        "here and belong in the document, not inside the image.",
        "",
    ]
    for r in RECORDS:
        out += [
            f"## {r['fig_id']} — {r['title']}",
            "",
            f"`{r['path'].relative_to(ROOT)}` · {DPI} dpi · {r['px']} · {r['size_kb']:.0f} kB",
            "",
            f"**Caption.** {r['caption']}",
            "",
            f"- Source: {r['sources']}",
            f"- Magnitude layer: {r['layer']}",
            f"- Built: {TODAY}",
        ]
        if r["note"]:
            out.append(f"- Note: {r['note']}")
        out.append("")
    p = FIGDIR / "captions.md"
    p.write_text("\n".join(out))
    return p


def spearman(a, b):
    def rank(v):
        order = np.argsort(np.argsort(np.asarray(v, dtype=float)))
        return order.astype(float)
    ra, rb = rank(a), rank(b)
    ra -= ra.mean()
    rb -= rb.mean()
    return float((ra @ rb) / np.sqrt((ra @ ra) * (rb @ rb)))


# ==========================================================================
# schematic primitives — shared by F4 and F7
# ==========================================================================
def node(ax, x, y, w, h, label, accent=False, planned=False, fs=8.0):
    """A plain rectangle with a short label. No fill, no rounding, no shadow."""
    ec = SCHEMA_ACCENT if accent else (SCHEMA_PLAN if planned else SCHEMA_EDGE)
    tc = SCHEMA_ACCENT if accent else (SCHEMA_PLAN if planned else INK)
    ax.add_patch(Rectangle((x, y), w, h, facecolor="white", edgecolor=ec,
                           linewidth=1.5 if accent else 0.9,
                           linestyle="dashed" if planned else "solid", zorder=3))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=fs, color=tc, zorder=4, linespacing=1.3,
            fontweight="bold" if accent else "normal")
    return (x, y, w, h)


def anchor(box, side, frac=0.5):
    x, y, w, h = box
    if side == "r":
        return (x + w, y + h * frac)
    if side == "l":
        return (x, y + h * frac)
    if side == "t":
        return (x + w * frac, y + h)
    return (x + w * frac, y)


def link(ax, p0, p1, planned=False, label=None, ldx=0.0, ldy=0.9, lha="center"):
    c = SCHEMA_PLAN if planned else SCHEMA_ARROW
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=9,
                                 color=c, lw=0.9,
                                 linestyle="dashed" if planned else "solid",
                                 zorder=2, shrinkA=1.0, shrinkB=1.5))
    if label:
        ax.text((p0[0] + p1[0]) / 2 + ldx, (p0[1] + p1[1]) / 2 + ldy, label,
                fontsize=7.0, color=c, ha=lha, va="center", zorder=5)


def elbow(ax, pts, planned=False):
    """Polyline with an arrowhead on the final segment."""
    c = SCHEMA_PLAN if planned else SCHEMA_ARROW
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.plot(xs[:-1], ys[:-1], color=c, lw=0.9,
            ls="dashed" if planned else "solid", zorder=2,
            solid_capstyle="round")
    ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle="-|>",
                                 mutation_scale=9, color=c, lw=0.9,
                                 linestyle="dashed" if planned else "solid",
                                 zorder=2, shrinkA=0, shrinkB=1.5))


def style_key(ax, x, y):
    """Two-entry line-style key. Built vs designed. No box, no other legend."""
    ax.plot([x, x + 3.2], [y, y], color=SCHEMA_ARROW, lw=1.1, zorder=4)
    ax.text(x + 3.9, y, "built", fontsize=7.4, va="center", color=INK, zorder=4)
    ax.plot([x, x + 3.2], [y - 2.6, y - 2.6], color=SCHEMA_PLAN, lw=1.1,
            ls="dashed", zorder=4)
    ax.text(x + 3.9, y - 2.6, "designed", fontsize=7.4, va="center",
            color=SCHEMA_PLAN, zorder=4)


def column_heads(ax, heads, y):
    for x, t in heads:
        ax.text(x, y, t, fontsize=8.0, color="#6E6E6E", ha="left", va="bottom")


# ==========================================================================
# F1 — building energy use intensity by scenario
# ==========================================================================
def fig_f1() -> Path:
    rows = sorted(B, key=lambda b: b["scn"]["baseline"]["eui"])
    y = np.arange(len(rows))
    base = np.array([r["scn"]["baseline"]["eui"] for r in rows])
    s1 = np.array([r["scn"]["s1"]["eui"] for r in rows])
    s2 = np.array([r["scn"]["s2"]["eui"] for r in rows])

    fig, ax = plt.subplots(figsize=(7.2, 6.8))
    ax.grid(axis="x", zorder=0)
    ax.set_axisbelow(True)

    for i in y:
        ax.plot([min(s2[i], base[i]), base[i]], [i, i],
                color=RULE, lw=1.2, zorder=1, solid_capstyle="round")

    ax.scatter(base, y, s=40, color=SCENARIO_COLORS["baseline"], zorder=3,
               label=SCENARIO_LABELS["baseline"])
    ax.scatter(s1, y, s=28, color=SCENARIO_COLORS["s1"], zorder=4, marker="o",
               label=SCENARIO_LABELS["s1"])
    ax.scatter(s2, y, s=40, color=SCENARIO_COLORS["s2"], zorder=5, marker="D",
               label=SCENARIO_LABELS["s2"])

    ax.axvline(PRORATA, color=MUTED, ls="--", lw=1.0, zorder=2)
    ax.text(PRORATA + 14, len(rows) - 0.55, f"pro-rata {PRORATA:.1f}",
            color=MUTED, fontsize=8, va="center", ha="left")

    labels = [f"{r['id']}  {r['use'][:22]}" for r in rows]
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_ylim(-0.8, len(rows) - 0.2)
    ax.set_xlim(0, max(base) * 1.06)
    ax.set_xlabel("Energy use intensity (kWh/m²/yr)")
    ax.set_ylabel("Building")
    ax.set_title("Building energy use intensity by scenario", loc="left", pad=10)
    ax.legend(loc="lower right", ncol=1, handletextpad=0.4)

    p = FIGDIR / "F1_building_energy_intensity.png"
    fig.savefig(p)
    plt.close(fig)

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
# F2 — annual saving under S2 by building
# ==========================================================================
def fig_f2() -> Path:
    sav = [(b["scn"]["baseline"]["annual_energy_kwh"] - b["scn"]["s2"]["annual_energy_kwh"], b)
           for b in B]
    sav.sort(key=lambda t: -t[0])
    vals = np.array([v for v, _ in sav])
    ids = [b["id"] for _, b in sav]
    pct = [b["scn"]["s2"]["reduction_pct"] for _, b in sav]
    top5 = set(ids[:5])

    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    ax.grid(axis="x", zorder=0)
    ax.set_axisbelow(True)
    y = np.arange(len(vals))
    colors = [SCENARIO_COLORS["s2"] if i in top5 else "#C9C9C9" for i in ids]
    ax.barh(y, vals / 1000.0, color=colors, height=0.72, zorder=3)

    span = max(vals) / 1000.0
    for i, (v, p_) in enumerate(zip(vals, pct)):
        ax.text(v / 1000.0 + span * 0.012, i, f"{p_:.1f} %",
                va="center", ha="left", fontsize=7.4,
                color=INK if ids[i] in top5 else "#8A8A8A")

    ax.set_yticks(y)
    ax.set_yticklabels([f"{i}" for i in ids])
    ax.invert_yaxis()
    ax.set_xlim(0, span * 1.34)
    ax.set_xlabel("Annual saving under S2 (MWh/yr)")
    ax.set_ylabel("Building")
    ax.set_title("Annual saving under S2 by building", loc="left", pad=10)

    # the only in-plot annotation: one data callout on the highlighted group
    ax.annotate("", xy=(span * 1.20, -0.2), xytext=(span * 1.20, 4.2),
                arrowprops=dict(arrowstyle="-", color=SCENARIO_COLORS["s2"], lw=1.1))
    ax.text(span * 1.23, 2.0, "top 5", color=SCENARIO_COLORS["s2"],
            fontsize=8.5, fontweight="bold", ha="left", va="center")

    p = FIGDIR / "F2_retrofit_priority_s2.png"
    fig.savefig(p)
    plt.close(fig)
    zero = [i for i, p_ in zip(ids, pct) if p_ < 1.0]
    F2_FACTS.update(dict(top5=[(i, float(v), float(q))
                               for i, v, q in zip(ids[:5], vals[:5], pct[:5])],
                         n_under_1pct=len(zero), zero_ids=zero))
    return p


# ==========================================================================
# F3 — composition and seasonality
# ==========================================================================
def fig_f3() -> Path:
    mb = np.array(scene["monthly_building_load_kwh"], dtype=float) / 1000.0   # MWh
    mv = np.array(scene["monthly_ev_bus_load_kwh"], dtype=float) / 1000.0
    reopt = np.array(scene["monthly_load_kwh"], dtype=float) / 1000.0

    fig = plt.figure(figsize=(9.6, 4.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 3.4], wspace=0.26)

    # -- left: annual composition ----------------------------------------
    axl = fig.add_subplot(gs[0, 0])
    b_mwh, v_mwh = BUILD_WB / 1000.0, EVBUS / 1000.0
    axl.bar([0], [b_mwh], width=0.62, color=LAYER_COLORS["building"], zorder=3)
    axl.bar([0], [v_mwh], bottom=[b_mwh], width=0.62,
            color=LAYER_COLORS["vehicle"], zorder=3)
    axl.text(0, b_mwh / 2, f"{100*b_mwh/(b_mwh+v_mwh):.1f} %",
             ha="center", va="center", color="white", fontsize=9, fontweight="bold")
    axl.text(0, b_mwh + v_mwh / 2, f"{100*v_mwh/(b_mwh+v_mwh):.1f} %",
             ha="center", va="center", color="#3A2A00", fontsize=9, fontweight="bold")
    axl.set_xlim(-0.55, 0.55)
    axl.set_ylim(0, (b_mwh + v_mwh) * 1.10)
    axl.set_xticks([])
    axl.set_ylabel("Annual electricity (MWh)")
    axl.grid(axis="y", zorder=0)
    axl.set_axisbelow(True)
    axl.set_title("a  Annual", loc="left", fontsize=9.5, pad=8)

    # -- right: monthly stack --------------------------------------------
    axr = fig.add_subplot(gs[0, 1])
    x = np.arange(12)
    axr.bar(x, mb, width=0.68, color=LAYER_COLORS["building"], zorder=3,
            label="Building load")
    axr.bar(x, mv, bottom=mb, width=0.68, color=LAYER_COLORS["vehicle"], zorder=3,
            label="EV + bus charging")
    axr.plot(x, reopt, ls="none", marker="_", ms=14, mew=1.7, color=INK, zorder=5,
             label="Optimizer site load")
    axr.grid(axis="y", zorder=0)
    axr.set_axisbelow(True)
    axr.set_xticks(x)
    axr.set_xticklabels(MONTHS)
    axr.set_xlabel("Month")
    axr.set_ylabel("Electricity (MWh)")
    axr.set_ylim(0, reopt.max() * 1.34)
    axr.set_title("b  Monthly", loc="left", fontsize=9.5, pad=8)

    jan, jul = int(np.argmax(reopt)), 6
    for i, tag in ((jan, "Jan"), (jul, "Jul")):
        axr.text(i, reopt[i] + reopt.max() * 0.035, f"{tag} {reopt[i]:.0f}",
                 ha="center", va="bottom", fontsize=7.8, color=INK)
    axr.text(0.015, 0.98, f"peak/trough {reopt.max()/reopt.min():.2f}×",
             transform=axr.transAxes, fontsize=7.8, color="#666666", va="top")
    h, l = axr.get_legend_handles_labels()
    order = [l.index("Building load"), l.index("EV + bus charging"),
             l.index("Optimizer site load")]
    axr.legend([h[i] for i in order], [l[i] for i in order],
               loc="upper right", ncol=1, handletextpad=0.5, borderaxespad=0.2)

    p = FIGDIR / "F3_load_composition_seasonality.png"
    fig.savefig(p)
    plt.close(fig)
    F3_FACTS.update(dict(veh_share=100 * v_mwh / (b_mwh + v_mwh),
                         jan=float(reopt[jan]), jul=float(reopt[jul]),
                         ratio=float(reopt.max() / reopt.min())))
    return p


# ==========================================================================
# F4 — data pipeline
# ==========================================================================
# Six sources, one repair step each, one assertion gate, one record, three
# consumers. Node labels are <= 3 words; magnitudes live in the caption.
def fig_f4() -> Path:
    fig, ax = plt.subplots(figsize=(10.0, 5.4))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.axis("off")

    C1, C2, C3, C4 = 1.0, 29.0, 58.0, 80.0
    W1, W2, W3, W4 = 22.0, 20.0, 15.0, 19.0
    ROWS = [48.0, 40.5, 33.0, 25.5, 18.0, 10.5]
    H = 5.6

    column_heads(ax, [(C1, "Sources"), (C2, "Repair"),
                      (C3, "Record"), (C4, "Consumers")], 55.6)

    srcs = ["Retrofit parameters", "Simulated building loads", "Supply optimization",
            "Vehicle charging demand", "Mobility traces", "City geometry"]
    procs = ["Intensity join", "Floor-count repair", "Load decomposition",
             "Monthly aggregation", "Occupancy prior", "Coordinate transform"]
    sboxes = [node(ax, C1, y, W1, H, t) for t, y in zip(srcs, ROWS)]
    pboxes = [node(ax, C2, y, W2, H, t) for t, y in zip(procs, ROWS)]
    for s, q in zip(sboxes, pboxes):
        link(ax, anchor(s, "r"), anchor(q, "l"))

    hub = node(ax, C3, 29.0, W3, 9.0, "Unified building\nenergy record",
               accent=True, fs=8.4)
    gate = node(ax, C3, 17.5, W3, 5.6, "Verification gate")
    for q, frac in zip(pboxes, (0.90, 0.78, 0.66, 0.54, 0.42, 0.30)):
        link(ax, anchor(q, "r"), anchor(hub, "l", frac))
    link(ax, anchor(gate, "t"), anchor(hub, "b"), label="8 checks",
         ldx=0.9, ldy=0.0, lha="left")

    outs = [("Tables and figures", 41.0, False),
            ("Web twin", 32.0, False),
            ("Simulation tier", 23.0, True)]
    for t, y, planned in outs:
        b_ = node(ax, C4, y, W4, H, t, planned=planned)
        link(ax, anchor(hub, "r"), anchor(b_, "l"), planned=planned)

    style_key(ax, C1, 8.0)
    ax.text(0.0, 58.0, "Data pipeline", fontsize=11, fontweight="bold",
            color=INK, ha="left", va="bottom")

    p = FIGDIR / "F4_pipeline_methods.png"
    fig.savefig(p)
    plt.close(fig)
    return p


# ==========================================================================
# F7 — system architecture
# ==========================================================================
# Same grammar as F4 so a reader who has parsed F4 can parse F7 without
# relearning the notation. 13 nodes, left-to-right, one accent on the hub,
# dashed = designed and not built.
def fig_f7() -> Path:
    fig, ax = plt.subplots(figsize=(10.4, 5.2))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 56)
    ax.axis("off")

    C1, C2, C3, C4 = 1.0, 26.0, 51.0, 76.0
    W1, W2, W3, W4 = 18.0, 18.0, 18.0, 21.0
    H = 5.0

    column_heads(ax, [(C1, "Sources"), (C2, "Processes"),
                      (C3, "Shared record"), (C4, "Fidelity tiers")], 51.5)

    # 1 sources
    n_param = node(ax, C1, 42.0, W1, H, "Retrofit parameters")
    n_load = node(ax, C1, 35.0, W1, H, "Simulated building loads")
    n_veh = node(ax, C1, 28.0, W1, H, "Vehicle charging demand")
    n_geo = node(ax, C1, 21.0, W1, H, "City geometry")

    # 2 processes
    n_recon = node(ax, C2, 32.0, W2, 6.0, "Reconciliation")
    n_ped = node(ax, C2, 21.0, W2, H, "Pedestrian model")

    # 3 shared record
    n_hub = node(ax, C3, 31.0, W3, 8.0, "Unified building\nenergy record",
                 accent=True, fs=8.4)
    n_traj = node(ax, C3, 21.0, W3, H, "Pedestrian trajectories")
    n_traffic = node(ax, C3, 12.0, W3, H, "Vehicle traffic layer", planned=True)

    # 4 fidelity tiers: L1 dashboard, L2 web twin (built), L3 simulation twin
    # (designed), bridged by the simulation-ready export. MCP drives the twin.
    n_l1 = node(ax, C4, 44.0, W4, H, "Dashboard (L1)")
    n_mcp = node(ax, C4 + 3.0, 37.0, 15.0, 4.5, "MCP channel", planned=True, fs=7.6)
    n_l2 = node(ax, C4, 22.0, W4, 13.0, "Web digital twin (L2)")
    n_export = node(ax, C4 + 3.0, 15.0, 15.0, 4.5, "Simulation-ready\nexport",
                    planned=True, fs=7.6)
    n_l3 = node(ax, C4, 7.0, W4, H, "Simulation twin (L3)", planned=True)

    # 5 designed feedback
    n_supply = node(ax, C2, 3.0, W2, H, "Supply re-run", planned=True)

    # edges — built
    link(ax, anchor(n_param, "r"), anchor(n_recon, "l", 0.85))
    link(ax, anchor(n_load, "r"), anchor(n_recon, "l", 0.60))
    link(ax, anchor(n_veh, "r"), anchor(n_recon, "l", 0.35))
    link(ax, anchor(n_geo, "r"), anchor(n_recon, "l", 0.10))
    link(ax, anchor(n_geo, "r"), anchor(n_ped, "l"))
    link(ax, anchor(n_recon, "r"), anchor(n_hub, "l", 0.5), label="8 checks", ldy=1.1)
    link(ax, anchor(n_ped, "r"), anchor(n_traj, "l"))
    link(ax, anchor(n_hub, "r", 0.85), anchor(n_l1, "l"))
    link(ax, anchor(n_hub, "r", 0.25), anchor(n_l2, "l", 0.72))
    link(ax, anchor(n_traj, "r"), anchor(n_l2, "l", 0.30))

    # edges — designed
    link(ax, anchor(n_traffic, "r"), anchor(n_l2, "l", 0.11), planned=True)
    link(ax, anchor(n_mcp, "b", 0.5), anchor(n_l2, "t", 0.5), planned=True)
    link(ax, anchor(n_l2, "b", 0.5), anchor(n_export, "t", 0.5), planned=True)
    link(ax, anchor(n_export, "b", 0.5), anchor(n_l3, "t", 0.5), planned=True)
    # the loop that is not closed: corrected load -> supply re-run -> new record
    elbow(ax, [anchor(n_hub, "l", 0.25), (46.0, 33.0), (46.0, 7.0),
               anchor(n_supply, "r", 0.8)], planned=True)
    elbow(ax, [anchor(n_supply, "r", 0.3), (48.5, 4.5), (48.5, 29.0),
               (42.0, 29.0), (42.0, 32.0)], planned=True)

    style_key(ax, C1, 8.0)
    ax.text(0.0, 53.6, "System architecture", fontsize=11, fontweight="bold",
            color=INK, ha="left", va="bottom")

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
    record(
        "F1", p1, "Building energy use intensity by scenario",
        f"Site energy use intensity of the {N} buildings in the Nihonbashi study block, "
        f"sorted by baseline intensity. Grey = baseline, blue = S1 (window-to-wall ratio "
        f"−20 %), vermillion = S2 (WWR −20 % and R-value +40 %); the connector spans the "
        f"baseline-to-S2 travel. The dashed line at {PRORATA:.2f} kWh/m²/yr is the single "
        f"pro-rata constant the twin previously assigned to every building. Denominator is "
        f"gross floor area. The absolute EUI scale is unverified (project_design.md §6.10): "
        f"Σ(EUI × GFA) = {EUI_TOTAL:,.0f} kWh/yr is {EUI_RATIO:.1f}× the hourly-workbook "
        f"building load of {BUILD_WB:,.0f} kWh/yr, so the ranking and the relative scenario "
        f"deltas are the defensible reading, not the level.",
        SRC_CHAIN, UNVERIFIED)

    p2 = fig_f2()
    record(
        "F2", p2, "Annual saving under S2 by building",
        f"Absolute annual electricity saving under retrofit scenario S2 against baseline, "
        f"per building, sorted descending; the five largest are highlighted and support "
        f"decision D-1 (where to retrofit first). Saving = (EUI_baseline − EUI_S2) × GFA. "
        f"The label on each bar is that building's own percentage reduction, unweighted; the "
        f"GFA-weighted block reduction is {DEM['s2']['annual_reduction_pct']:.2f} %, not the "
        f"flat 15 % the viewer previously applied. "
        f"{F2_FACTS['n_under_1pct']} of {N} buildings "
        f"({', '.join(str(i) for i in F2_FACTS['zero_ids'])}) gains under 1 % from the S2 "
        f"package. Absolute EUI scale unverified (§6.10).",
        "Index_energy.xlsx {baseline, s2}.EUI x GFA -> " + SRC_SCENE, UNVERIFIED)

    p3 = fig_f3()
    record(
        "F3", p3, "District electricity: composition and seasonality",
        f"(a) Annual site electricity for the block, split into building load "
        f"({BUILD_WB:,.0f} kWh/yr, from 22 hourly workbooks) and EV plus bus charging "
        f"({EVBUS:,.0f} kWh/yr, from the 8760-hour series). (b) The same two layers by "
        f"month; the black ticks are the monthly site load the REopt supply optimisation was "
        f"sized against. The decomposition is exact: "
        f"{BUILD_WB:,.2f} + {EVBUS:,.2f} = {SITE:,.2f} kWh/yr, residual 0.00 kWh "
        f"(check V6). The twin previously attributed the whole site load to buildings pro "
        f"rata, so {F3_FACTS['veh_share']:.1f} % of every building's reported energy was in "
        f"fact transport charging. Building load and vehicle charging are never summed into "
        f"a per-building figure.",
        "Nihonbashi_District/*.xlsx (22 workbooks), annual_total_car_bus_energy_8760h.csv, "
        "TS_ND_1_nihonbashi_building_EV_PV_BESS_results.json (ElectricLoad) -> " + SRC_SCENE,
        "site kWh, VERIFIED — decomposition exact to 0.00 kWh (check V6)")

    p4 = fig_f4()
    record(
        "F4", p4, "Data pipeline",
        "Six source families, one extraction or repair step each, reconciled into a single "
        "per-building record behind the eight verification checks V1–V8, which fail the "
        "build and write nothing when a check does not pass. Nodes are named for what they "
        "are; the underlying artefacts are: retrofit parameters = Index_energy.xlsx (sheets "
        f"baseline, s1, s2); simulated building loads = Nihonbashi_District/*.xlsx, 22 hourly "
        f"workbooks, {BUILD_WB:,.0f} kWh/yr; supply optimisation = "
        "TS_ND_1_nihonbashi_building_EV_PV_BESS_results.json, 417 kW PV and 783 kWh storage; "
        f"vehicle charging demand = annual_total_car_bus_energy_8760h.csv, {EVBUS:,.0f} "
        "kWh/yr; mobility traces = pings_in_area_6677.geojson, 25,254 pings from 812 "
        "devices; city geometry = PLATEAU LOD2 and tokyo_bldg_smaller_block.geojson. The "
        "unified building energy record is outputs/energy/energy_scene.json. Columns 1–3 are "
        "performed by scripts/export_energy_scene.py and column 4 by "
        "scripts/build_figures.py. Vehicle charging never enters a per-building record. "
        "Solid = built, dashed = designed and not yet executed.",
        "repository structure: scripts/export_energy_scene.py, scripts/build_figures.py",
        "schematic, no magnitude layer")

    p7 = fig_f7()
    record(
        "F7", p7, "System architecture",
        "Sources, processes, the shared record, and the fidelity tiers that read it. The "
        "unified building energy record (accent) is the single contract: every tier reads "
        "it and none recomputes energy. Reconciliation writes it only after the eight "
        "verification checks V1–V8 pass. Nodes are named for what they are; the underlying "
        "artefacts are: retrofit parameters = Index_energy.xlsx; simulated building loads = "
        "22 hourly workbooks in Nihonbashi_District/ plus the REopt site load in "
        "TS_ND_1_nihonbashi_building_EV_PV_BESS_results.json; vehicle charging demand = "
        "annual_total_car_bus_energy_8760h.csv and pings_in_area_6677.geojson; city "
        "geometry = PLATEAU LOD2, tokyo_bldg_smaller_block.geojson and the OSM road, water "
        "and walk networks, which also feed scripts/export_streetscape.py. Reconciliation "
        "is scripts/export_energy_scene.py, the pedestrian model is scripts/run_testbed.py, "
        "the unified record is outputs/energy/energy_scene.json, pedestrian trajectories "
        "are agents_<scenario>.czml, and the web digital twin is "
        "outputs/energy_cesium_view.html with outputs/cesium_view.html for the heat field. "
        "Fidelity tiers: L1 the analytical dashboard and basic views, L2 the photoreal web "
        "digital twin running today, L3 the game-engine or Omniverse simulation twin, "
        "reached through a simulation-ready USD export that is in progress. Solid = built "
        "and running in this repository; dashed = designed and explicitly not claimed as a "
        "result, namely the vehicle traffic layer, the simulation-ready export and the L3 "
        "simulation twin, the supply re-run on the corrected load, and the MCP channel "
        "into the twin.",
        "repository structure: scripts/{export_energy_scene,export_streetscape,run_testbed}.py, "
        "outputs/energy_cesium_view.html, outputs/energy_view.html, outputs/cesium_view.html",
        "schematic, no magnitude layer",
        note="dashed elements (vehicle traffic layer, simulation-ready export, L3 "
             "simulation twin, supply re-run, MCP channel) are designed, not executed")

    cap = write_captions()

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
    print(f"{len(RECORDS)} figures written to {FIGDIR.relative_to(ROOT)}/")
    print(f"captions -> {cap.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
