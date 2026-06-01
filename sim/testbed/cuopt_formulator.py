"""VRPTW formulation for the Stage Two proactive AV-dispatch policy.

Translates World state + at-risk agents into a Vehicle-Routing-Problem-with-
Time-Windows input dict that NVIDIA cuOpt can solve. See
docs/cuopt_integration_plan.md for the design rationale.

Architecture (Stage Two):

    World + AgentProfiles
            |
            v
    find_at_risk_agents()   <-- 3-hour lookahead, vulnerability + heat filter
            |
            v
    build_vrptw()           <-- this module: produces cuOpt-shaped input
            |
            v
    solve()                 <-- this module: thin wrapper around cuOpt
            |
            v
    DispatchPlan            <-- consumed by sim/testbed/policy.py:proactive

Today: cuOpt not installed. solve() raises a clear error pointing at
cuopt-install. find_at_risk_agents() and build_vrptw() work standalone
and emit JSON-shaped output that can be inspected or fed to a mocked
solver during development.

Schemas align with the locked Group 1 / Group 2 contracts in
docs/system_architecture.md section 7.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from .population import AgentProfile, planned_cell
from .scene import GRID_W, GRID_H, SHELTER_CELLS, cell_centroid_latlng
from .world import World


# Tunables for the lookahead trigger. Match policy.py constants so the
# Stage Two cuOpt branch and the Stage One threshold branch agree on
# what 'at risk' means.
LOOKAHEAD_HOURS = 4
HEAT_TRIGGER = 1.00       # cuOpt branch fires slightly earlier than reactive
VULN_TRIGGER = 0.55       # same as policy.py VULN_THRESHOLD + safety margin

# Fleet defaults. Stage Two starts with a small fleet; scale via the
# fleet_size parameter when running scenarios.
DEFAULT_FLEET_SIZE = 5
DEFAULT_VEHICLE_CAPACITY = 4    # passengers per AV
DEFAULT_DEPOT_CELL = (0, 0)     # SW corner; revisit when Yi Tai's SHP lands

# Penalty scaling. The solver objective is total travel cost plus
# vulnerability-weighted lateness; these knobs balance the two.
LATENESS_PENALTY_PER_MIN = 1.0
VULN_WEIGHT_MULTIPLIER = 3.0    # multiply lateness penalty by score


# ---------------------------------------------------------------------------
# Data classes (Stage Two-ready, JSON-serializable)

@dataclass(frozen=True)
class Vehicle:
    """One AV in the dispatch fleet."""
    vehicle_id: str
    depot_cell: tuple[int, int]
    capacity: int


@dataclass(frozen=True)
class Order:
    """One pickup-and-dropoff job: pick up an at-risk agent, deliver to shelter."""
    order_id: str
    agent_id: str
    pickup_cell: tuple[int, int]
    dropoff_shelter_id: str
    dropoff_cell: tuple[int, int]
    earliest_pickup_minute: int       # minutes from sim start
    latest_dropoff_minute: int        # before exposure exceeds safe threshold
    priority_weight: float            # vulnerability_score * VULN_WEIGHT_MULTIPLIER


@dataclass
class VRPTWInput:
    """The full cuOpt input bundle. Serialize via asdict()."""
    hour: int
    vehicles: list[Vehicle] = field(default_factory=list)
    orders: list[Order] = field(default_factory=list)
    edge_costs: dict[str, float] = field(default_factory=dict)   # "x1,y1->x2,y2" -> cost
    shelter_capacity: dict[str, int] = field(default_factory=dict)
    solver_config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DispatchAssignment:
    """One vehicle's planned route, returned by solve()."""
    vehicle_id: str
    order_ids: list[str]              # in pickup order
    total_minutes: float
    total_exposure_units: float


# ---------------------------------------------------------------------------
# Trigger: who needs an AV?

def find_at_risk_agents(
    world: World,
    profiles: list[AgentProfile],
    hour: int,
    lookahead_h: int = LOOKAHEAD_HOURS,
) -> list[AgentProfile]:
    """Return profiles whose vulnerability + projected heat clear the cuOpt trigger.

    Args:
        world: current world state (heat field + shelter capacity).
        profiles: full agent population.
        hour: current sim hour, 0..23.
        lookahead_h: how many hours forward to scan for heat.

    Returns:
        Subset of profiles flagged for AV dispatch at this hour.
    """
    if not (0 <= hour <= 23):
        raise ValueError(f"hour must be in [0, 23], got {hour}")
    at_risk: list[AgentProfile] = []
    for prof in profiles:
        if prof.vulnerability_score <= VULN_TRIGGER:
            continue
        cell = planned_cell(prof, hour)
        peak = max(
            world.heat_at(min(23, hour + dh), cell)
            for dh in range(lookahead_h)
        )
        if peak >= HEAT_TRIGGER:
            at_risk.append(prof)
    return at_risk


# ---------------------------------------------------------------------------
# Cost model

def _manhattan_cells(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Grid-cell Manhattan distance. Stage Two: replace with SUMO net distance."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _edge_cost(
    world: World, hour: int, a: tuple[int, int], b: tuple[int, int],
) -> float:
    """Travel-time + heat-cost integration along a path between two cells.

    Stage One placeholder: Manhattan distance times average heat-cost over
    the two endpoints. Stage Two replaces this with SUMO travel time on the
    real network and a line-integral of the heat raster.
    """
    dist = _manhattan_cells(a, b)
    if dist == 0:
        return 0.0
    avg_heat = 0.5 * (world.heat_at(hour, a) + world.heat_at(hour, b))
    travel_min = dist * 2.0    # crude: 50 m cell at ~25 m/min = 2 min/cell
    return travel_min * avg_heat


def _shelter_capacity_snapshot(world: World, hour: int) -> dict[str, int]:
    """Remaining capacity for each shelter at this hour."""
    return {sid: world.shelter_remaining(sid, hour) for sid in SHELTER_CELLS}


def _nearest_feasible_shelter(
    world: World, hour: int, agent_cell: tuple[int, int],
) -> tuple[str, tuple[int, int]] | None:
    """Pick the closest shelter with remaining capacity. Mirrors policy.py."""
    best: tuple[str, tuple[int, int]] | None = None
    best_d = float("inf")
    for sid, scell in SHELTER_CELLS.items():
        if world.shelter_remaining(sid, hour) <= 0:
            continue
        d = _manhattan_cells(agent_cell, scell)
        if d < best_d:
            best_d, best = d, (sid, scell)
    return best


# ---------------------------------------------------------------------------
# Formulator

def build_vrptw(
    world: World,
    profiles: list[AgentProfile],
    hour: int,
    fleet_size: int = DEFAULT_FLEET_SIZE,
    depot_cells: list[tuple[int, int]] | None = None,
    vehicle_capacity: int = DEFAULT_VEHICLE_CAPACITY,
) -> VRPTWInput:
    """Build the VRPTW input dict from current world state + at-risk agents.

    The output is a JSON-serializable bundle (via asdict) that cuOpt's
    routing API accepts. Producing it here means the same bundle can be
    inspected, mocked, or replayed without invoking the solver.

    Args:
        world: current world state.
        profiles: full agent population.
        hour: current sim hour.
        fleet_size: number of AVs to plan with.
        depot_cells: where each AV starts. Defaults to [DEFAULT_DEPOT_CELL]
            replicated to fleet_size; pass a list of distinct cells for
            multi-depot scenarios.
        vehicle_capacity: passengers per AV.

    Returns:
        VRPTWInput ready for solve() or for asdict() serialization.
    """
    if depot_cells is None:
        depot_cells = [DEFAULT_DEPOT_CELL] * fleet_size
    if len(depot_cells) < fleet_size:
        depot_cells = depot_cells + [depot_cells[-1]] * (fleet_size - len(depot_cells))

    at_risk = find_at_risk_agents(world, profiles, hour)

    vehicles = [
        Vehicle(vehicle_id=f"av{i:02d}", depot_cell=depot_cells[i], capacity=vehicle_capacity)
        for i in range(fleet_size)
    ]

    orders: list[Order] = []
    for prof in at_risk:
        pickup = planned_cell(prof, hour)
        match = _nearest_feasible_shelter(world, hour, pickup)
        if match is None:
            continue   # no feasible shelter for this agent right now
        sid, scell = match
        # Latest dropoff = the hour at which projected exposure would
        # cross HEAT_TRIGGER, in minutes from sim start.
        worst_h = hour
        for dh in range(LOOKAHEAD_HOURS):
            h2 = min(23, hour + dh)
            if world.heat_at(h2, pickup) >= HEAT_TRIGGER:
                worst_h = h2
                break
        orders.append(Order(
            order_id=f"o_{prof.agent_id}_{hour:02d}",
            agent_id=prof.agent_id,
            pickup_cell=pickup,
            dropoff_shelter_id=sid,
            dropoff_cell=scell,
            earliest_pickup_minute=hour * 60,
            latest_dropoff_minute=worst_h * 60,
            priority_weight=prof.vulnerability_score * VULN_WEIGHT_MULTIPLIER,
        ))

    # Edge cost matrix: only the cells we actually need (depots, pickups, dropoffs).
    relevant_cells: set[tuple[int, int]] = set()
    for v in vehicles:
        relevant_cells.add(v.depot_cell)
    for o in orders:
        relevant_cells.add(o.pickup_cell)
        relevant_cells.add(o.dropoff_cell)
    edge_costs: dict[str, float] = {}
    for a in relevant_cells:
        for b in relevant_cells:
            if a == b:
                continue
            key = f"{a[0]},{a[1]}->{b[0]},{b[1]}"
            edge_costs[key] = _edge_cost(world, hour, a, b)

    return VRPTWInput(
        hour=hour,
        vehicles=vehicles,
        orders=orders,
        edge_costs=edge_costs,
        shelter_capacity=_shelter_capacity_snapshot(world, hour),
        solver_config={
            "lateness_penalty_per_minute": LATENESS_PENALTY_PER_MIN,
            "vulnerability_weight_multiplier": VULN_WEIGHT_MULTIPLIER,
            "objective": "minimize_total_cost_plus_weighted_lateness",
            "time_limit_seconds": 10,
            "lookahead_hours": LOOKAHEAD_HOURS,
        },
    )


def vrptw_to_dict(vrptw: VRPTWInput) -> dict[str, Any]:
    """asdict() that flattens tuples to lists (JSON-friendly)."""
    d = asdict(vrptw)
    for v in d["vehicles"]:
        v["depot_cell"] = list(v["depot_cell"])
    for o in d["orders"]:
        o["pickup_cell"] = list(o["pickup_cell"])
        o["dropoff_cell"] = list(o["dropoff_cell"])
    return d


# ---------------------------------------------------------------------------
# Solver (Stage Two — requires cuOpt)

def solve(vrptw: VRPTWInput) -> list[DispatchAssignment]:
    """Submit the VRPTW to NVIDIA cuOpt and return one DispatchAssignment per vehicle.

    Stage Two only: requires `nvidia-cuopt` (or the cuopt-server-api endpoint).
    Install via the cuopt-install skill from nvidia/skills.

    Stage One: raises NotImplementedError with a clear pointer. Callers
    should fall back to the threshold-rule policy until cuOpt lands.
    """
    try:
        import cuopt  # type: ignore   # noqa: F401
    except ImportError as exc:
        raise NotImplementedError(
            "cuOpt is not installed. Install via the nvidia/skills "
            "`cuopt-install` skill, then `pip install nvidia-cuopt`. "
            "Until then, sim/testbed/policy.py:proactive falls back to "
            "the threshold rule. See docs/cuopt_integration_plan.md."
        ) from exc

    # TODO Stage Two W2-W3 (per docs/cuopt_integration_plan.md):
    #   1. Convert VRPTWInput to cuopt.routing data model
    #   2. Apply cuopt-user-rules for mobility_class constraints
    #   3. Invoke solver, time-limited per solver_config["time_limit_seconds"]
    #   4. Parse routes, map back to DispatchAssignment per vehicle
    raise NotImplementedError("cuOpt routing solver not wired yet (see Stage Two W2-W3).")


# ---------------------------------------------------------------------------
# Tool-callable surface (mirrors mcp_tools.py contract)

def preview_vrptw_input(
    hour: int, fleet_size: int = DEFAULT_FLEET_SIZE, num_agents: int = 200,
) -> dict[str, Any]:
    """Build a VRPTW input from the synthetic world and return it as a dict.

    Lets an orchestrator inspect what cuOpt would receive at any given
    hour without needing cuOpt installed. Useful for sanity checks, demos,
    and Stage One review material.

    Returns:
        dict with vehicles, orders, edge_costs, shelter_capacity, solver_config.
    """
    from .mcp_tools import _build_default_world
    world, profiles = _build_default_world(num_agents=num_agents)
    vrptw = build_vrptw(world, profiles, hour=hour, fleet_size=fleet_size)
    return vrptw_to_dict(vrptw)


if __name__ == "__main__":
    import json
    sample = preview_vrptw_input(hour=14, fleet_size=3, num_agents=100)
    print(json.dumps({
        "hour": sample["hour"],
        "num_vehicles": len(sample["vehicles"]),
        "num_orders": len(sample["orders"]),
        "num_edges": len(sample["edge_costs"]),
        "shelter_capacity": sample["shelter_capacity"],
        "solver_config": sample["solver_config"],
        "first_order": sample["orders"][0] if sample["orders"] else None,
    }, indent=2))
