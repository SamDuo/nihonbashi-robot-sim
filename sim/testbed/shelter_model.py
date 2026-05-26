"""Synthetic shelter cooling envelope matching the G2 contract.

Each shelter has hourly max_occupants, cooling_kwh, and emissions_intensity.
Placeholder for Group 2's N-UBEM + ReOpt output; schema matches
docs/system_architecture.md section 7b.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class ShelterRow:
    building_id: str
    hour: int
    max_occupants: int
    cooling_kwh: float
    emissions_intensity: float


def build_envelope(shelter_ids: list[str], seed: int = 11) -> list[ShelterRow]:
    rng = np.random.default_rng(seed)
    rows: list[ShelterRow] = []
    for sid in shelter_ids:
        nominal_cap = int(rng.integers(70, 140))
        nominal_kwh = float(rng.uniform(8.0, 18.0))
        for h in range(24):
            avail = 0.3 + 0.7 * max(0.0, np.sin(np.pi * (h - 5) / 16.0))
            cap = int(nominal_cap * avail)
            kwh = nominal_kwh * avail
            ei = 0.35 + 0.1 * (1.0 - avail)
            rows.append(ShelterRow(sid, h, cap, kwh, ei))
    return rows
