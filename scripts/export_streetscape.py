"""Project the OSM streetscape (roads, water, kerb trees) from the WebGL twin's
scene.json into WGS84 for the Cesium energy view, so we can drape a *designed*
street network instead of the flat Bing basemap.

scene.json stores geometry in a local-metre frame (x=east, z=north) anchored at
grid.anchor_lat/lng. We re-project to lng/lat and keep only what's within RADIUS
of the energy study block, then synthesise street trees along the major roads.

Run:  python scripts/export_streetscape.py
"""
from __future__ import annotations
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "outputs" / "twin" / "scene.json"
OUT = ROOT / "outputs" / "energy" / "streetscape.json"

# energy study-block centre (WGS84) and how far around it to keep streetscape
BLK_LNG, BLK_LAT = 139.7791, 35.6882
RADIUS_M = 430.0   # match the energy view's ~330 m photoreal clip (a little wider for context)

s = json.load(open(SCENE))
g = s["grid"]
ALAT, ALNG = g["anchor_lat"], g["anchor_lng"]
MLAT = 111320.0
MLNG = 111320.0 * math.cos(ALAT * math.pi / 180)

def to_ll(x, z):
    return [round(ALNG + x / MLNG, 7), round(ALAT + z / MLAT, 7)]

# block centre back in the scene's local metres (for the radius filter)
BCX = (BLK_LNG - ALNG) * MLNG
BCZ = (BLK_LAT - ALAT) * MLAT

def near(pts, r=RADIUS_M):
    return any((x - BCX) ** 2 + (z - BCZ) ** 2 < r * r for x, z in pts)

# road tier (controls width + colour in the view)
def tier(cls):
    if cls in ("motorway", "trunk", "primary"): return "major"
    if cls in ("secondary", "tertiary"):        return "mid"
    if cls in ("footway", "pedestrian"):        return "path"
    return "minor"

roads, trees = [], []
# Trees + lights cluster tightly around the STUDY BLOCK only (keeps focus there, no trees
# trailing off down far highways). Roads/water still cover the wider RADIUS_M for context.
TREE_RADIUS = 200.0
TREE_OK = {"primary", "secondary", "tertiary", "residential", "unclassified"}  # local streets, no highways
for r in s["roads"]:
    pts = r["pts"]
    if len(pts) < 2 or not near(pts):
        continue
    t = tier(r["cls"])
    ll = []
    for x, z in pts:
        ll.extend(to_ll(x, z))
    roads.append({"ll": ll, "w": round(float(r["w"]), 1), "tier": t,
                  "name": r.get("name") or ""})
    # street trees: only on local streets near the study block (not highways, not far out)
    if r["cls"] in TREE_OK and near(pts, TREE_RADIUS):
        half = float(r["w"]) / 2 + 2.5
        acc = 0.0
        for i in range(len(pts) - 1):
            x0, z0 = pts[i]; x1, z1 = pts[i + 1]
            dx, dz = x1 - x0, z1 - z0
            seg = math.hypot(dx, dz)
            if seg < 1e-3: continue
            nx, nz = -dz / seg, dx / seg          # left normal
            d = acc
            while d < seg:
                px, pz = x0 + dx * d / seg, z0 + dz * d / seg
                for side in (+1, -1):
                    trees.append(to_ll(px + nx * half * side, pz + nz * half * side))
                d += 24.0
            acc = d - seg

water = []
for w in s.get("water", []):
    poly = w["poly"]
    if len(poly) < 3 or not near(poly):
        continue
    ll = []
    for x, z in poly:
        ll.extend(to_ll(x, z))
    water.append({"ll": ll, "name": w.get("name") or ""})

OUT.parent.mkdir(parents=True, exist_ok=True)
out = {"anchor": [ALNG, ALAT], "center": [BLK_LNG, BLK_LAT],
       "roads": roads, "water": water, "trees": trees}
json.dump(out, open(OUT, "w"), separators=(",", ":"))
print(f"wrote {OUT}")
print(f"  roads={len(roads)}  water={len(water)}  trees={len(trees)}")
by_t = {}
for r in roads: by_t[r["tier"]] = by_t.get(r["tier"], 0) + 1
print(f"  road tiers: {by_t}")
