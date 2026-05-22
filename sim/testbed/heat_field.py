"""Synthetic G1 heat field: shape (24, GRID_X, GRID_Y), values in [0, 2].

Schema: docs/system_architecture.md section 4a. Real loader replaces generate_synthetic()
at Stage Two without touching downstream code.
"""

from __future__ import annotations

import numpy as np

from .scene import GRID_X, GRID_Y


HEAT_FIELD_SHAPE = (24, GRID_X, GRID_Y)


def generate_synthetic(seed: int = 7) -> np.ndarray:
    """Diurnal heat with a sun-baked south-side ridge and a shaded north canopy strip."""
    rng = np.random.default_rng(seed)
    field = np.zeros(HEAT_FIELD_SHAPE, dtype=np.float32)

    diurnal = np.array([
        0.20, 0.18, 0.15, 0.12, 0.10, 0.10, 0.15, 0.30,
        0.55, 0.80, 1.05, 1.25, 1.45, 1.65, 1.78, 1.80,
        1.70, 1.55, 1.30, 1.00, 0.75, 0.55, 0.40, 0.30,
    ], dtype=np.float32)

    for h in range(24):
        base = diurnal[h]
        for ix in range(GRID_X):
            for iy in range(GRID_Y):
                sun_side = 0.30 if iy < 3 else 0.0
                shade = -0.20 if iy >= 7 else 0.0
                pocket = 0.25 if (8 <= ix <= 12 and 3 <= iy <= 5) else 0.0
                noise = rng.normal(0.0, 0.05)
                field[h, ix, iy] = float(np.clip(base + sun_side + shade + pocket + noise, 0.0, 2.0))
    return field


def load_or_generate(path: str | None, seed: int = 7) -> np.ndarray:
    if path:
        arr = np.load(path)
        if arr.shape != HEAT_FIELD_SHAPE:
            raise ValueError(f"heat_field shape {arr.shape} != expected {HEAT_FIELD_SHAPE}")
        if arr.min() < 0 or arr.max() > 2:
            raise ValueError(f"heat_field values must lie in [0,2]; got [{arr.min()}, {arr.max()}]")
        return arr.astype(np.float32)
    return generate_synthetic(seed)
