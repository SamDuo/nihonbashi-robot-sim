"""Three policies: baseline (no-op), reactive (route on exposure), proactive (pre-position vulnerable)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from .scene import Shelter, manhattan


REACTIVE_EXPOSURE_TRIGGER = 1.0
PROACTIVE_VULN_THRESHOLD = 0.55
PROACTIVE_FORECAST_THRESHOLD = 0.8


@dataclass
class Decision:
    agent_id: int
    hour: int
    rule: str
    chosen_shelter: Optional[str]
    target_cell: Optional[Tuple[int, int]]
    reason: str


def _forecast_next_hour(heat: np.ndarray, hour: int, ix: int, iy: int) -> float:
    if hour + 1 >= heat.shape[0]:
        return float(heat[hour, ix, iy])
    return float(heat[hour + 1, ix, iy])


def _nearest_feasible_shelter(
    cell: Tuple[int, int],
    shelters: List[Shelter],
    occupied: Dict[str, int],
    capacity: Dict[Tuple[str, int], int],
    hour: int,
) -> Optional[Shelter]:
    ranked = sorted(shelters, key=lambda s: manhattan(cell, s.cell))
    for sh in ranked:
        cap = capacity.get((sh.building_id, hour), 0)
        if occupied.get(sh.building_id, 0) < cap:
            return sh
    return None


def baseline_decision(
    agent_id: int,
    hour: int,
    cell: Tuple[int, int],
    exposure_now: float,
    vulnerability: float,
    heat_field: np.ndarray,
    shelters: List[Shelter],
    occupied: Dict[str, int],
    capacity: Dict[Tuple[str, int], int],
) -> Decision:
    return Decision(agent_id, hour, "baseline", None, None,
                    reason="no policy intervention")


def reactive_decision(
    agent_id: int,
    hour: int,
    cell: Tuple[int, int],
    exposure_now: float,
    vulnerability: float,
    heat_field: np.ndarray,
    shelters: List[Shelter],
    occupied: Dict[str, int],
    capacity: Dict[Tuple[str, int], int],
) -> Decision:
    if exposure_now <= REACTIVE_EXPOSURE_TRIGGER:
        return Decision(agent_id, hour, "reactive", None, None,
                        reason=f"exposure {exposure_now:.2f} <= trigger {REACTIVE_EXPOSURE_TRIGGER}")
    sh = _nearest_feasible_shelter(cell, shelters, occupied, capacity, hour)
    if sh is None:
        return Decision(agent_id, hour, "reactive", None, None,
                        reason="no feasible shelter (capacity exhausted)")
    return Decision(agent_id, hour, "reactive", sh.building_id, sh.cell,
                    reason=f"exposure {exposure_now:.2f} > trigger {REACTIVE_EXPOSURE_TRIGGER}; routed to {sh.building_id}")


def proactive_decision(
    agent_id: int,
    hour: int,
    cell: Tuple[int, int],
    exposure_now: float,
    vulnerability: float,
    heat_field: np.ndarray,
    shelters: List[Shelter],
    occupied: Dict[str, int],
    capacity: Dict[Tuple[str, int], int],
) -> Decision:
    forecast = _forecast_next_hour(heat_field, hour, cell[0], cell[1])
    if vulnerability >= PROACTIVE_VULN_THRESHOLD and forecast >= PROACTIVE_FORECAST_THRESHOLD:
        sh = _nearest_feasible_shelter(cell, shelters, occupied, capacity, hour)
        if sh is not None:
            return Decision(agent_id, hour, "proactive", sh.building_id, sh.cell,
                            reason=(f"vuln {vulnerability:.2f} >= {PROACTIVE_VULN_THRESHOLD} and "
                                    f"forecast {forecast:.2f} >= {PROACTIVE_FORECAST_THRESHOLD}; "
                                    f"pre-positioned to {sh.building_id}"))
    if exposure_now > REACTIVE_EXPOSURE_TRIGGER:
        sh = _nearest_feasible_shelter(cell, shelters, occupied, capacity, hour)
        if sh is not None:
            return Decision(agent_id, hour, "proactive", sh.building_id, sh.cell,
                            reason=(f"proactive fallback: exposure {exposure_now:.2f} > "
                                    f"{REACTIVE_EXPOSURE_TRIGGER}; routed to {sh.building_id}"))
    return Decision(agent_id, hour, "proactive", None, None,
                    reason=(f"no action: vuln {vulnerability:.2f}, forecast {forecast:.2f}, "
                            f"exposure {exposure_now:.2f}"))


POLICY_REGISTRY = {
    "baseline": baseline_decision,
    "reactive": reactive_decision,
    "proactive": proactive_decision,
}
