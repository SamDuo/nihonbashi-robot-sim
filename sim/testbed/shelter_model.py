"""Synthetic G2 shelter envelope per building_id and hour. Schema in section 4b."""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .scene import Shelter


def generate_envelope(shelters: List[Shelter], seed: int = 23) -> Tuple[pd.DataFrame, Dict[Tuple[str, int], dict]]:
    rng = np.random.default_rng(seed)
    rows = []
    table: Dict[Tuple[str, int], dict] = {}
    for sh in shelters:
        cap_base = int(rng.integers(28, 46))
        cooling_kw_peak = float(rng.uniform(45.0, 70.0))
        for h in range(24):
            staffed = 7 <= h <= 21
            cap_h = cap_base if staffed else max(6, int(cap_base * 0.25))
            cooling_kwh = cooling_kw_peak * (0.25 + 0.75 * max(0.0, np.sin((h - 6) / 12 * np.pi)))
            emissions = float(rng.uniform(0.42, 0.55))
            rec = {
                "building_id": sh.building_id,
                "hour": h,
                "max_occupants": cap_h,
                "cooling_kwh": round(cooling_kwh, 3),
                "emissions_intensity": round(emissions, 4),
            }
            rows.append(rec)
            table[(sh.building_id, h)] = rec
    return pd.DataFrame(rows), table
