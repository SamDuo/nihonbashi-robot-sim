"""Unit tests for sim/testbed/cuopt_formulator.py — the Stage Two VRPTW builder.

These tests cover the deterministic Python portions of the formulator that
don't require cuOpt itself: at-risk filtering, edge-cost calculation, the
build_vrptw bundle, and JSON serialization. The solve() function is tested
only for its expected NotImplementedError when cuOpt is missing.
"""
import pytest

from sim.testbed.cuopt_formulator import (
    DEFAULT_DEPOT_CELL,
    DEFAULT_FLEET_SIZE,
    DEFAULT_VEHICLE_CAPACITY,
    HEAT_TRIGGER,
    LATENESS_PENALTY_PER_MIN,
    LOOKAHEAD_HOURS,
    VRPTWInput,
    VULN_TRIGGER,
    VULN_WEIGHT_MULTIPLIER,
    Vehicle,
    Order,
    _edge_cost,
    _manhattan_cells,
    _nearest_feasible_shelter,
    _shelter_capacity_snapshot,
    build_vrptw,
    find_at_risk_agents,
    solve,
    vrptw_to_dict,
)
from sim.testbed.scene import SHELTER_CELLS


pytestmark = pytest.mark.unit


class TestManhattan:
    def test_zero_distance_same_cell(self):
        assert _manhattan_cells((3, 4), (3, 4)) == 0

    def test_horizontal_distance(self):
        assert _manhattan_cells((0, 5), (4, 5)) == 4

    def test_vertical_distance(self):
        assert _manhattan_cells((5, 0), (5, 7)) == 7

    def test_diagonal_distance(self):
        assert _manhattan_cells((0, 0), (3, 4)) == 7


class TestEdgeCost:
    def test_zero_distance_returns_zero(self, hot_world):
        assert _edge_cost(hot_world, 14, (5, 5), (5, 5)) == 0.0

    def test_hot_cells_cost_more_than_cold(self, hot_world, cold_world):
        hot = _edge_cost(hot_world, 14, (0, 0), (5, 0))
        cold = _edge_cost(cold_world, 14, (0, 0), (5, 0))
        assert hot > cold > 0.0

    def test_cost_scales_with_distance(self, hot_world):
        short = _edge_cost(hot_world, 14, (0, 0), (1, 0))
        long = _edge_cost(hot_world, 14, (0, 0), (10, 0))
        assert long > short > 0.0


class TestShelterSnapshot:
    def test_open_world_reports_full_capacity(self, hot_world):
        snap = _shelter_capacity_snapshot(hot_world, 14)
        assert set(snap.keys()) == set(SHELTER_CELLS.keys())
        assert all(cap == 10 for cap in snap.values())

    def test_full_world_reports_zero_capacity(self, hot_world_no_capacity):
        snap = _shelter_capacity_snapshot(hot_world_no_capacity, 14)
        assert all(cap == 0 for cap in snap.values())


class TestNearestFeasibleShelter:
    def test_picks_nearest_when_open(self, hot_world):
        # Cell (3,7) is shelter_north; pickup near it should resolve to it.
        match = _nearest_feasible_shelter(hot_world, 14, (3, 6))
        assert match is not None
        sid, cell = match
        assert sid == "shelter_north"
        assert cell == SHELTER_CELLS["shelter_north"]

    def test_returns_none_when_all_full(self, hot_world_no_capacity):
        match = _nearest_feasible_shelter(hot_world_no_capacity, 14, (5, 5))
        assert match is None


class TestFindAtRiskAgents:
    def test_rejects_invalid_hour(self, hot_world, vulnerable_agent):
        with pytest.raises(ValueError):
            find_at_risk_agents(hot_world, [vulnerable_agent], hour=24)
        with pytest.raises(ValueError):
            find_at_risk_agents(hot_world, [vulnerable_agent], hour=-1)

    def test_vulnerable_agent_in_hot_world_flagged(self, hot_world, vulnerable_agent):
        at_risk = find_at_risk_agents(hot_world, [vulnerable_agent], hour=14)
        assert vulnerable_agent in at_risk

    def test_robust_agent_never_flagged(self, hot_world, robust_agent):
        at_risk = find_at_risk_agents(hot_world, [robust_agent], hour=14)
        assert robust_agent not in at_risk

    def test_cold_world_yields_no_at_risk_agents(self, cold_world, vulnerable_agent):
        at_risk = find_at_risk_agents(cold_world, [vulnerable_agent], hour=14)
        assert at_risk == []

    def test_empty_population_returns_empty(self, hot_world):
        assert find_at_risk_agents(hot_world, [], hour=10) == []


class TestBuildVRPTW:
    def test_returns_vrptw_input_dataclass(self, hot_world, vulnerable_agent):
        out = build_vrptw(hot_world, [vulnerable_agent], hour=14)
        assert isinstance(out, VRPTWInput)
        assert out.hour == 14

    def test_default_fleet_has_expected_size(self, hot_world, vulnerable_agent):
        out = build_vrptw(hot_world, [vulnerable_agent], hour=14)
        assert len(out.vehicles) == DEFAULT_FLEET_SIZE
        assert all(isinstance(v, Vehicle) for v in out.vehicles)
        assert all(v.capacity == DEFAULT_VEHICLE_CAPACITY for v in out.vehicles)

    def test_default_depot_used_when_none_provided(self, hot_world, vulnerable_agent):
        out = build_vrptw(hot_world, [vulnerable_agent], hour=14)
        assert all(v.depot_cell == DEFAULT_DEPOT_CELL for v in out.vehicles)

    def test_custom_fleet_size_respected(self, hot_world, vulnerable_agent):
        out = build_vrptw(hot_world, [vulnerable_agent], hour=14, fleet_size=10)
        assert len(out.vehicles) == 10

    def test_multi_depot_pads_when_fewer_depots_than_vehicles(self, hot_world, vulnerable_agent):
        out = build_vrptw(
            hot_world, [vulnerable_agent], hour=14,
            fleet_size=5, depot_cells=[(1, 1), (2, 2)],
        )
        # First two get distinct depots, remaining three replicate the last.
        assert out.vehicles[0].depot_cell == (1, 1)
        assert out.vehicles[1].depot_cell == (2, 2)
        assert all(v.depot_cell == (2, 2) for v in out.vehicles[2:])

    def test_orders_generated_for_at_risk_agents(self, hot_world, vulnerable_agent):
        out = build_vrptw(hot_world, [vulnerable_agent], hour=14)
        assert len(out.orders) == 1
        order = out.orders[0]
        assert isinstance(order, Order)
        assert order.agent_id == vulnerable_agent.agent_id
        assert order.dropoff_shelter_id in SHELTER_CELLS
        assert order.priority_weight == pytest.approx(
            vulnerable_agent.vulnerability_score * VULN_WEIGHT_MULTIPLIER
        )

    def test_orders_skip_when_no_shelter_capacity(self, hot_world_no_capacity, vulnerable_agent):
        out = build_vrptw(hot_world_no_capacity, [vulnerable_agent], hour=14)
        assert out.orders == []

    def test_no_orders_for_robust_agents(self, hot_world, robust_agent):
        out = build_vrptw(hot_world, [robust_agent], hour=14)
        assert out.orders == []

    def test_edge_costs_include_depots_pickups_and_dropoffs(self, hot_world, vulnerable_agent):
        out = build_vrptw(hot_world, [vulnerable_agent], hour=14)
        # Edge cost map is keyed by "x1,y1->x2,y2".
        relevant = {DEFAULT_DEPOT_CELL, vulnerable_agent.activity_cell}
        for o in out.orders:
            relevant.add(o.dropoff_cell)
        # n cells × (n-1) directed edges.
        expected = len(relevant) * (len(relevant) - 1)
        assert len(out.edge_costs) == expected

    def test_solver_config_carries_expected_keys(self, hot_world, vulnerable_agent):
        out = build_vrptw(hot_world, [vulnerable_agent], hour=14)
        cfg = out.solver_config
        assert cfg["lateness_penalty_per_minute"] == LATENESS_PENALTY_PER_MIN
        assert cfg["vulnerability_weight_multiplier"] == VULN_WEIGHT_MULTIPLIER
        assert cfg["lookahead_hours"] == LOOKAHEAD_HOURS
        assert "objective" in cfg
        assert "time_limit_seconds" in cfg

    def test_shelter_capacity_snapshot_attached(self, hot_world, vulnerable_agent):
        out = build_vrptw(hot_world, [vulnerable_agent], hour=14)
        assert set(out.shelter_capacity.keys()) == set(SHELTER_CELLS.keys())


class TestVrptwToDict:
    def test_round_trip_flattens_tuples_to_lists(self, hot_world, vulnerable_agent):
        bundle = build_vrptw(hot_world, [vulnerable_agent], hour=14)
        d = vrptw_to_dict(bundle)
        assert all(isinstance(v["depot_cell"], list) for v in d["vehicles"])
        for o in d["orders"]:
            assert isinstance(o["pickup_cell"], list)
            assert isinstance(o["dropoff_cell"], list)

    def test_dict_is_json_serializable(self, hot_world, vulnerable_agent):
        import json
        bundle = build_vrptw(hot_world, [vulnerable_agent], hour=14)
        d = vrptw_to_dict(bundle)
        # Will raise TypeError if not JSON-clean.
        json.dumps(d)


class TestSolveNotImplemented:
    def test_solve_raises_when_cuopt_missing(self, hot_world, vulnerable_agent):
        # cuOpt isn't installed in the test environment; solve() must raise
        # NotImplementedError with a clear pointer to the install path.
        bundle = build_vrptw(hot_world, [vulnerable_agent], hour=14)
        with pytest.raises(NotImplementedError, match="cuOpt"):
            solve(bundle)


class TestConstants:
    def test_vuln_trigger_in_valid_range(self):
        assert 0.0 < VULN_TRIGGER < 1.0

    def test_heat_trigger_is_a_float(self):
        assert isinstance(HEAT_TRIGGER, float)

    def test_lookahead_is_positive(self):
        assert LOOKAHEAD_HOURS > 0

    def test_default_fleet_is_positive(self):
        assert DEFAULT_FLEET_SIZE > 0
