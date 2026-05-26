"""Synthetic 20x10 grid scene anchored at Nihonbashi.

Each cell is 50m x 50m; total extent 1000m x 500m, centered roughly on the
Nihonbashi Bridge and fully inside the Nihonbashi clipping polygon used by
the Cesium twin. The scene exposes lat/lng conversion so outputs can be
consumed by Re:Earth, Folium, TerriaJS, or the local Cesium view without
further transformation. Yi Tai's SHP -> SUMO network will drop in here in
Stage Two.
"""
from dataclasses import dataclass
import math
from shapely.geometry import Polygon

GRID_W = 20
GRID_H = 10
CELL_M = 50.0

# Nihonbashi SW anchor. With CELL_M=50 the scene spans 1000m east-west by
# 500m north-south. Anchor is set east of Sotobori dori (the Chuo ku /
# Chiyoda ku ward boundary), so every cell sits inside Chuo ku and is
# covered by the Chuo ku PLATEAU 3D Tiles dataset.
ANCHOR_LAT = 35.6810
ANCHOR_LNG = 139.7720

DLAT_PER_M = 1.0 / 111_000.0
DLNG_PER_M = 1.0 / (111_320.0 * math.cos(math.radians(ANCHOR_LAT)))


def cell_centroid_latlng(cx: int, cy: int) -> tuple[float, float]:
    lat = ANCHOR_LAT + (cy + 0.5) * CELL_M * DLAT_PER_M
    lng = ANCHOR_LNG + (cx + 0.5) * CELL_M * DLNG_PER_M
    return lat, lng


def cell_polygon(cx: int, cy: int) -> Polygon:
    lat0 = ANCHOR_LAT + cy * CELL_M * DLAT_PER_M
    lat1 = ANCHOR_LAT + (cy + 1) * CELL_M * DLAT_PER_M
    lng0 = ANCHOR_LNG + cx * CELL_M * DLNG_PER_M
    lng1 = ANCHOR_LNG + (cx + 1) * CELL_M * DLNG_PER_M
    return Polygon([(lng0, lat0), (lng1, lat0), (lng1, lat1), (lng0, lat1), (lng0, lat0)])


SHELTER_CELLS: dict[str, tuple[int, int]] = {
    "shelter_north": (3, 7),
    "shelter_mid":   (10, 7),
    "shelter_south": (17, 7),
}


@dataclass(frozen=True)
class Scene:
    width: int = GRID_W
    height: int = GRID_H

    @classmethod
    def default(cls) -> "Scene":
        return cls()

    def cells(self):
        for x in range(self.width):
            for y in range(self.height):
                yield (x, y)

    def shelter_cells(self) -> dict[str, tuple[int, int]]:
        return dict(SHELTER_CELLS)
