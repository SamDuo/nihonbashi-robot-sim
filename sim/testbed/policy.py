"""Three policies for the agentic decision loop.

Each policy takes (agent_profile, hour, world) and returns:
  (chosen_cell, status, rationale_dict)

status in {'home', 'working', 'sheltering'}.
rationale_dict has: policy, decision, latency_ms, plus contextual fields.
"""
import math
import time
from .population import AgentProfile, planned_cell, planned_status
from .scene import SHELTER_CELLS


HEAT_THRESHOLD = 1.10
VULN_THRESHOLD = 0.50


def _nearest_feasible_shelter(world, hour: int, prefer: tuple[int, int]):
    best, best_d2 = None, math.inf
    for sid, cell in SHELTER_CELLS.items():
        if world.shelter_remaining(sid, hour) <= 0:
            continue
        d2 = (cell[0] - prefer[0]) ** 2 + (cell[1] - prefer[1]) ** 2
        if d2 < best_d2:
            best_d2, best = d2, (sid, cell)
    return best


def baseline(agent: AgentProfile, hour: int, world) -> tuple[tuple[int, int], str, dict]:
    t0 = time.perf_counter()
    cell = planned_cell(agent, hour)
    r = {"policy": "baseline", "decision": "no_intervention",
         "heat": world.heat_at(hour, cell),
         "vulnerability": agent.vulnerability_score}
    r["latency_ms"] = (time.perf_counter() - t0) * 1000.0
    return cell, planned_status(agent, hour), r


def reactive(agent: AgentProfile, hour: int, world) -> tuple[tuple[int, int], str, dict]:
    t0 = time.perf_counter()
    cell = planned_cell(agent, hour)
    heat = world.heat_at(hour, cell)
    r = {"policy": "reactive", "heat": heat, "vulnerability": agent.vulnerability_score}
    if heat > HEAT_THRESHOLD and agent.vulnerability_score > VULN_THRESHOLD:
        match = _nearest_feasible_shelter(world, hour, cell)
        if match is not None:
            sid, scell = match
            world.consume_shelter(sid, hour)
            r["decision"] = "route_to_shelter"
            r["shelter"] = sid
            r["latency_ms"] = (time.perf_counter() - t0) * 1000.0
            return scell, "sheltering", r
        r["decision"] = "stay_no_capacity"
    else:
        r["decision"] = "stay_below_threshold"
    r["latency_ms"] = (time.perf_counter() - t0) * 1000.0
    return cell, planned_status(agent, hour), r


def proactive(agent: AgentProfile, hour: int, world) -> tuple[tuple[int, int], str, dict]:
    t0 = time.perf_counter()
    cell = planned_cell(agent, hour)
    lookahead_max = max(
        (world.heat_at(min(23, hour + dh), cell) for dh in range(4)),
        default=0.0,
    )
    r = {"policy": "proactive",
         "lookahead_max": lookahead_max,
         "heat": world.heat_at(hour, cell),
         "vulnerability": agent.vulnerability_score}
    if agent.vulnerability_score > VULN_THRESHOLD and lookahead_max > (HEAT_THRESHOLD - 0.1):
        match = _nearest_feasible_shelter(world, hour, cell)
        if match is not None:
            sid, scell = match
            world.consume_shelter(sid, hour)
            r["decision"] = "preposition_to_shelter"
            r["shelter"] = sid
            r["latency_ms"] = (time.perf_counter() - t0) * 1000.0
            return scell, "sheltering", r
        r["decision"] = "stay_no_capacity"
    else:
        r["decision"] = "stay_below_lookahead_threshold"
    r["latency_ms"] = (time.perf_counter() - t0) * 1000.0
    return cell, planned_status(agent, hour), r


POLICIES = {"baseline": baseline, "reactive": reactive, "proactive": proactive}
