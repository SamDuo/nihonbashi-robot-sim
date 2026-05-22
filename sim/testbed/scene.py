"""Nihonbashi 200m scene: WGS84-anchored 20x10 grid + shelter footprints.

User explicitly approved C:\\Users\\Public\\Documents\\nihon-stage1 as the build path
via AskUserQuestion after C:\\Users\\qduong7\\ proved unwritable (OneDrive intercepting profile).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from shapely.geometry import Polygon


LAT_MIN, LAT_MAX = 35.6840, 35.6852
LON_MIN, LON_MAX = 139.7735, 139.7747

GRID_X, GRID_Y = 20, 10


@dataclass(frozen=True)
class Shelter:
    building_id: str
    cell: Tuple[int, int]
    footprint: Polygon
    centroid_lat: float
    centroid_lon: float


def cell_to_latlon(ix: int, iy: int) -> Tuple[float, float]:
    lon = LON_MIN + (ix + 0.5) * (LON_MAX - LON_MIN) / GRID_X
    lat = LAT_MIN + (iy + 0.5) * (LAT_MAX - LAT_MIN) / GRID_Y
    return lat, lon


def cell_polygon(ix: int, iy: int) -> Polygon:
    lon0 = LON_MIN + ix * (LON_MAX - LON_MIN) / GRID_X
    lon1 = LON_MIN + (ix + 1) * (LON_MAX - LON_MIN) / GRID_X
    lat0 = LAT_MIN + iy * (LAT_MAX - LAT_MIN) / GRID_Y
    lat1 = LAT_MIN + (iy + 1) * (LAT_MAX - LAT_MIN) / GRID_Y
    return Polygon([(lon0, lat0), (lon1, lat0), (lon1, lat1), (lon0, lat1)])


def build_shelters() -> List[Shelter]:
    layout = [
        ("SH_MITSUKOSHI",   (2, 7)),
        ("SH_COREDO",       (6, 2)),
        ("SH_BANK_HALL",    (10, 7)),
        ("SH_SUBWAY_EXIT",  (13, 3)),
        ("SH_BRIDGE_PLAZA", (17, 6)),
    ]
    shelters: List[Shelter] = []
    for bid, (ix, iy) in layout:
        poly = cell_polygon(ix, iy)
        cx, cy = poly.centroid.x, poly.centroid.y
        shrunk = Polygon([
            (cx + 0.4 * (p[0] - cx), cy + 0.4 * (p[1] - cy))
            for p in list(poly.exterior.coords)[:-1]
        ])
        lat, lon = cell_to_latlon(ix, iy)
        shelters.append(Shelter(bid, (ix, iy), shrunk, lat, lon))
    return shelters


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
