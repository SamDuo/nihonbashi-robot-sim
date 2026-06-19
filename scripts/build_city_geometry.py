"""Build real Nihonbashi geometry for the WebGL twin from OpenStreetMap.

Replaces the procedural-placeholder geometry (V1) with the V2 real-geometry
step from docs/high_fidelity_twin_architecture.md:

1. Fetch the official administrative boundaries (admin_level=9 machi) whose
   name starts with 日本橋, select the ones our Stage One study area (the
   hand-drawn Cesium polygon) was approximating, and union them into the
   exact district boundary.
2. Fetch building footprints inside that district (+margin) with heights
   from OSM tags (height / building:levels), estimating only when untagged.
3. Fetch the street network (classified) and water polygons (Nihonbashi
   River) for ground rendering.
4. Project everything into the local-meter frame shared with the simulator
   (anchor = sim/testbed/scene.py ANCHOR_LAT/LNG) and write a single cached
   artifact: data/network/nihonbashi_geometry.json

The exporter (scripts/export_twin_frames.py) consumes the cache when present
and falls back to procedural geometry when absent, so the renderer contract
never changes. Data (c) OpenStreetMap contributors, ODbL — see data/README.md.

Usage:
    python scripts/build_city_geometry.py            # fetch + write cache
    python scripts/build_city_geometry.py --offline  # re-process raw cache only
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import linemerge, polygonize, unary_union

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sim.testbed.scene import ANCHOR_LAT, ANCHOR_LNG, DLAT_PER_M, DLNG_PER_M  # noqa: E402

OUT_PATH = ROOT / "data" / "network" / "nihonbashi_geometry.json"
RAW_PATH = ROOT / "data" / "network" / "raw_overpass_cache.json"  # gitignored dir-level? kept small
OVERPASS = "https://overpass-api.de/api/interpreter"

# Stage One hand-drawn study area (outputs/cesium_view.html NIHONBASHI_BOUNDARY).
# Used only to SELECT which official machi belong to the study district.
HAND_DRAWN = Polygon([
    (139.7720, 35.6800), (139.7780, 35.6788), (139.7835, 35.6810),
    (139.7840, 35.6855), (139.7800, 35.6890), (139.7745, 35.6895),
    (139.7710, 35.6860),
])

FETCH_BBOX = (35.6745, 139.7655, 35.6935, 139.7895)  # generous: covers district + margin

ROAD_CLASSES = {
    "motorway": 18.0, "trunk": 16.0, "primary": 15.0, "secondary": 12.0,
    "tertiary": 9.0, "unclassified": 7.0, "residential": 6.5, "service": 4.5,
    "pedestrian": 6.0, "footway": 2.6, "cycleway": 2.4, "living_street": 5.5,
}
LEVEL_M = 3.1          # meters per building level when only levels are tagged
DEFAULT_LEVELS = {     # crude fallback by footprint area, deterministic
    150.0: 3, 400.0: 5, 1200.0: 8, 1e12: 11,
}


def overpass(query: str, attempts: int = 5) -> dict:
    req = urllib.request.Request(
        OVERPASS,
        data=urllib.parse.urlencode({"data": query}).encode(),
        headers={"User-Agent": "nihonbashi-robot-sim (GT 2026 Tokyo Studio; research)"},
    )
    delay = 12.0
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as err:
            if err.code in (429, 504) and attempt < attempts - 1:
                print(f"    HTTP {err.code}, retrying in {delay:.0f}s …")
                time.sleep(delay)
                delay *= 1.8
                continue
            raise
    raise RuntimeError("unreachable")


def to_m(lng: float, lat: float) -> tuple[float, float]:
    """lat/lng -> local meters in the simulator frame (anchor = grid SW corner)."""
    return ((lng - ANCHOR_LNG) / DLNG_PER_M, (lat - ANCHOR_LAT) / DLAT_PER_M)


def ring_to_m(ring) -> list[list[float]]:
    return [[round(x, 1) for x in to_m(lng, lat)] for lng, lat in ring]


def fetch_raw() -> dict:
    s, w, n, e = FETCH_BBOX
    bbox = f"({s},{w},{n},{e})"
    queries = {
        "machi": f"""
[out:json][timeout:90];
relation["boundary"="administrative"]["admin_level"="9"]["name"~"^日本橋"]{bbox};
out geom;""",
        "buildings": f"""
[out:json][timeout:120];
(
  way["building"]{bbox};
  relation["building"]["type"="multipolygon"]{bbox};
);
out geom;""",
        "ground": f"""
[out:json][timeout:90];
(
  way["highway"]{bbox};
  way["natural"="water"]{bbox};
  relation["natural"="water"]["type"="multipolygon"]{bbox};
  way["waterway"="riverbank"]{bbox};
);
out geom;""",
    }
    raw = {}
    if RAW_PATH.exists():  # resume partial fetches
        raw = json.loads(RAW_PATH.read_text())
    for name, q in queries.items():
        if name in raw:
            print(f"  overpass: {name} cached ({len(raw[name]['elements'])} elements)")
            continue
        print(f"  overpass: fetching {name} …")
        raw[name] = overpass(q)
        print(f"    {len(raw[name]['elements'])} elements")
        RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
        RAW_PATH.write_text(json.dumps(raw))
        time.sleep(8)  # be polite; public API
    return raw


def relation_polygons(rel: dict) -> list[Polygon]:
    """Assemble outer-member ways of a relation into polygons."""
    lines = []
    for m in rel.get("members", []):
        if m.get("type") == "way" and m.get("role") in ("outer", "") and "geometry" in m:
            pts = [(g["lon"], g["lat"]) for g in m["geometry"]]
            if len(pts) >= 2:
                lines.append(LineString(pts))
    if not lines:
        return []
    merged = linemerge(lines)
    return [p for p in polygonize(merged) if p.is_valid and p.area > 0]


def build_district(raw_machi: dict) -> tuple[Polygon, list[dict]]:
    """Union the official machi that the hand-drawn study area approximated."""
    selected, polys = [], []
    for rel in raw_machi["elements"]:
        name = rel.get("tags", {}).get("name", "?")
        parts = relation_polygons(rel)
        if not parts:
            continue
        machi = unary_union(parts)
        overlap = machi.intersection(HAND_DRAWN).area / machi.area
        if overlap >= 0.30:  # the machi is substantially inside the study area
            selected.append({"name": name, "osm_rel": rel["id"],
                             "overlap": round(overlap, 2)})
            polys.append(machi)
    if not polys:
        raise RuntimeError("no machi selected — Overpass result unexpected")
    district = unary_union(polys)
    if isinstance(district, MultiPolygon):  # keep the main contiguous block
        district = max(district.geoms, key=lambda p: p.area)
    district = Polygon(district.exterior).simplify(0.000004)  # ~0.4 m
    return district, selected


def parse_height(tags: dict, area_m2: float) -> tuple[float, str]:
    for key in ("height", "building:height"):
        v = tags.get(key, "").replace("m", "").strip()
        try:
            h = float(v)
            if 2.0 < h < 350.0:
                return round(h, 1), "osm_height"
        except ValueError:
            pass
    for key in ("building:levels", "levels"):
        try:
            lv = float(tags.get(key, ""))
            if 0 < lv < 80:
                return round(lv * LEVEL_M + 1.5, 1), "osm_levels"
        except ValueError:
            pass
    for limit, lv in sorted(DEFAULT_LEVELS.items()):
        if area_m2 <= limit:
            return round(lv * LEVEL_M, 1), "estimated"
    return 12.0, "estimated"


def way_polygon(el: dict) -> Polygon | None:
    if "geometry" not in el:
        return None
    pts = [(g["lon"], g["lat"]) for g in el["geometry"]]
    if len(pts) < 4:
        return None
    poly = Polygon(pts)
    return poly if poly.is_valid and poly.area > 0 else None


def process(raw: dict) -> dict:
    district, machi = build_district(raw["machi"])
    print(f"  district = {len(machi)} machi united "
          f"({', '.join(m['name'] for m in machi)})")
    fetch_area = district.buffer(0.0008)  # ~80 m context margin around boundary

    buildings, h_src_count = [], {"osm_height": 0, "osm_levels": 0, "estimated": 0}
    for el in raw["buildings"]["elements"]:
        if el["type"] == "way":
            poly = way_polygon(el)
            polys = [poly] if poly else []
        else:
            polys = relation_polygons(el)
        for poly in polys:
            c = poly.representative_point()
            if not fetch_area.contains(c):
                continue
            # rough m² (equirect at this latitude)
            area_m2 = poly.area / (DLNG_PER_M * DLAT_PER_M)
            if area_m2 < 12:
                continue
            h, src = parse_height(el.get("tags", {}), area_m2)
            h_src_count[src] += 1
            ext = poly.exterior.simplify(0.0000035)
            ring = ring_to_m(list(ext.coords)[:-1])
            if len(ring) < 3:
                continue
            buildings.append({
                "poly": ring, "h": h, "src": src,
                "in": 1 if district.contains(c) else 0,
                "kind": "tower" if h > 55 else ("midrise" if h > 22 else "lowrise"),
            })
    print(f"  buildings: {len(buildings)} "
          f"(height tags {h_src_count['osm_height']}, levels {h_src_count['osm_levels']}, "
          f"estimated {h_src_count['estimated']})")

    roads, water = [], []
    for el in raw["ground"]["elements"]:
        tags = el.get("tags", {})
        hw = tags.get("highway")
        if hw and el["type"] == "way" and "geometry" in el:
            base = hw.split("_link")[0]
            if base not in ROAD_CLASSES:
                continue
            pts = [(g["lon"], g["lat"]) for g in el["geometry"]]
            line = LineString(pts)
            if not line.intersects(fetch_area):
                continue
            roads.append({
                "pts": ring_to_m(pts), "w": ROAD_CLASSES[base], "cls": base,
                "name": tags.get("name:en") or tags.get("name") or "",
                "bridge": 1 if tags.get("bridge") else 0,
            })
        elif tags.get("natural") == "water" or tags.get("waterway") == "riverbank":
            polys = [way_polygon(el)] if el["type"] == "way" else relation_polygons(el)
            for poly in polys:
                if poly and poly.intersects(fetch_area):
                    water.append({"poly": ring_to_m(list(poly.exterior.coords)[:-1]),
                                  "name": tags.get("name", "")})
    print(f"  roads: {len(roads)}, water polys: {len(water)}")

    bnd_ring = ring_to_m(list(district.exterior.coords)[:-1])
    xs = [p[0] for p in bnd_ring]; zs = [p[1] for p in bnd_ring]
    return {
        "meta": {
            "source": "OpenStreetMap (ODbL) via Overpass API",
            "fetched": time.strftime("%Y-%m-%d"),
            "anchor_lat": ANCHOR_LAT, "anchor_lng": ANCHOR_LNG,
            "frame": "local meters, x east, z north, origin = sim grid SW anchor",
            "machi": machi, "height_sources": h_src_count,
        },
        "boundary": {"poly": bnd_ring,
                     "bbox": [round(min(xs), 1), round(min(zs), 1),
                              round(max(xs), 1), round(max(zs), 1)]},
        "buildings": buildings,
        "roads": roads,
        "water": water,
    }


def main() -> None:
    offline = "--offline" in sys.argv
    if offline and RAW_PATH.exists():
        raw = json.loads(RAW_PATH.read_text())
    else:
        raw = fetch_raw()
        RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
        RAW_PATH.write_text(json.dumps(raw))
        print(f"  raw cache -> {RAW_PATH.relative_to(ROOT)}")
    geom = process(raw)
    OUT_PATH.write_text(json.dumps(geom, separators=(",", ":"), ensure_ascii=False))
    kb = OUT_PATH.stat().st_size // 1024
    print(f"  wrote {OUT_PATH.relative_to(ROOT)} ({kb} KB)")


if __name__ == "__main__":
    main()
