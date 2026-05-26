"""Mutable world state: immutable heat field + per-scenario shelter usage."""
from collections import defaultdict
import numpy as np
from .shelter_model import ShelterRow


class World:
    def __init__(self, heat_field: np.ndarray, shelter_rows: list[ShelterRow]):
        self.heat_field = heat_field
        self.shelter_rows = shelter_rows
        self._max: dict[tuple[str, int], int] = {
            (r.building_id, r.hour): r.max_occupants for r in shelter_rows
        }
        self._kwh: dict[tuple[str, int], float] = {
            (r.building_id, r.hour): r.cooling_kwh for r in shelter_rows
        }
        self._ei: dict[tuple[str, int], float] = {
            (r.building_id, r.hour): r.emissions_intensity for r in shelter_rows
        }
        self._used: dict[tuple[str, int], int] = defaultdict(int)
        self.shelter_ids = sorted({r.building_id for r in shelter_rows})

    def reset_shelter_usage(self) -> None:
        self._used = defaultdict(int)

    def heat_at(self, hour: int, cell: tuple[int, int]) -> float:
        return float(self.heat_field[hour, cell[0], cell[1]])

    def shelter_max(self, sid: str, hour: int) -> int:
        return self._max[(sid, hour)]

    def shelter_remaining(self, sid: str, hour: int) -> int:
        return self._max[(sid, hour)] - self._used[(sid, hour)]

    def consume_shelter(self, sid: str, hour: int) -> int:
        self._used[(sid, hour)] += 1
        return self._used[(sid, hour)]

    def shelter_occupants_by_hour(self) -> dict[str, dict[int, int]]:
        out = {sid: {h: 0 for h in range(24)} for sid in self.shelter_ids}
        for (sid, h), v in self._used.items():
            out[sid][h] = v
        return out

    def shelter_cooling_kwh(self, sid: str, hour: int) -> float:
        return float(self._kwh[(sid, hour)])

    def shelter_emissions_intensity(self, sid: str, hour: int) -> float:
        return float(self._ei[(sid, hour)])
