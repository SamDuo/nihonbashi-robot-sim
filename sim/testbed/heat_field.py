"""Synthetic hourly heat-cost field.

Shape: (24, GRID_W, GRID_H), value = heat-cost factor in [0, ~2].
Diurnal pattern peaks at 14:00; central pedestrian row (y=5) is hottest.
This is a placeholder for Group 1's hourly raster -- same shape, same
ranges, so the simulator code path does not change when real data lands.
"""
import numpy as np
from .scene import GRID_W, GRID_H


def build_heat_field(seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    field = np.zeros((24, GRID_W, GRID_H), dtype=float)
    for h in range(24):
        diurnal = max(0.0, np.sin(np.pi * (h - 6) / 14.0)) * 1.5 + 0.1
        for y in range(GRID_H):
            y_factor = float(np.exp(-((y - 5) ** 2) / 6.0))
            for x in range(GRID_W):
                noise = float(rng.normal(0.0, 0.05))
                field[h, x, y] = max(0.0, diurnal * (0.4 + 0.9 * y_factor) + noise)
    return field


def cell_heat(field: np.ndarray, hour: int, cell: tuple[int, int]) -> float:
    return float(field[hour, cell[0], cell[1]])
