"""Unit tests for sim/testbed/mcp_tools.py — the 7-tool orchestrator surface.

Tests the 5 fast tools end-to-end against the synthetic Stage One world:
  list_scenarios, list_shelters, inspect_agent, get_policy_decision,
  preview_vrptw_for_cuopt.

The two slow tools (run_full_simulation, compare_all_scenarios) are tested
only at the contract level: TOOLS registry shape and input validation.
Their happy-path integration is covered by scripts/nightly_smoke.ps1.
"""
import pytest

from sim.testbed.mcp_tools import (
    SCENARIOS,
    TOOLS,
    get_policy_decision,
    inspect_agent,
    list_scenarios,
    list_shelters,
    run_full_simulation,
)
from sim.testbed.scene import SHELTER_CELLS


# Small population for speed; we still hit build_heat_field once per process.
SMALL_N = 50


pytestmark = pytest.mark.unit


class TestRegistry:
    def test_seven_tools_registered(self):
        assert len(TOOLS) == 7

    def test_expected_tool_names(self):
        assert set(TOOLS.keys()) == {
            "list_scenarios",
            "list_shelters",
            "inspect_agent",
            "get_policy_decision",
            "run_full_simulation",
            "compare_all_scenarios",
            "preview_vrptw_for_cuopt",
        }

    def test_all_tools_callable(self):
        for name, fn in TOOLS.items():
            assert callable(fn), f"{name} is not callable"

    def test_all_tools_have_docstrings(self):
        # Docstrings become the MCP tool description — they're contract.
        for name, fn in TOOLS.items():
            assert fn.__doc__ is not None and len(fn.__doc__.strip()) > 20, (
                f"{name} needs a real docstring (it becomes the agent-visible spec)"
            )


class TestListScenarios:
    def test_returns_three_scenarios_in_canonical_order(self):
        r = list_scenarios()
        assert r["scenarios"] == list(SCENARIOS)

    def test_descriptions_cover_all_scenarios(self):
        r = list_scenarios()
        for name in SCENARIOS:
            assert name in r["descriptions"]
            assert isinstance(r["descriptions"][name], str)
            assert len(r["descriptions"][name]) > 10

    def test_thresholds_present(self):
        r = list_scenarios()
        assert "heat_cost_factor" in r["thresholds"]
        assert "vulnerability_score" in r["thresholds"]
        assert r["thresholds"]["heat_cost_factor"] > 1.0
        assert 0.0 < r["thresholds"]["vulnerability_score"] < 1.0


class TestListShelters:
    def test_returns_all_shelters(self):
        r = list_shelters()
        assert r["count"] == len(SHELTER_CELLS)
        assert set(r["shelters"].keys()) == set(SHELTER_CELLS.keys())

    def test_each_shelter_has_cell_and_latlng(self):
        r = list_shelters()
        for sid, info in r["shelters"].items():
            assert "cell" in info and len(info["cell"]) == 2
            assert "lat" in info and isinstance(info["lat"], float)
            assert "lng" in info and isinstance(info["lng"], float)


class TestInspectAgent:
    def test_returns_full_state_for_valid_agent(self):
        r = inspect_agent("a002", hour=14, num_agents=SMALL_N)
        assert r["agent_id"] == "a002"
        assert r["hour"] == 14
        assert "profile" in r
        assert "planned" in r and "cell" in r["planned"] and "status" in r["planned"]
        assert isinstance(r["heat_at_planned"], float)
        assert isinstance(r["lookahead_max_4h"], float)
        assert isinstance(r["vulnerability_score"], float)
        assert "would_trigger" in r
        assert set(r["would_trigger"].keys()) == {"reactive", "proactive"}

    def test_would_trigger_values_are_booleans(self):
        r = inspect_agent("a002", hour=14, num_agents=SMALL_N)
        assert isinstance(r["would_trigger"]["reactive"], bool)
        assert isinstance(r["would_trigger"]["proactive"], bool)

    def test_invalid_hour_raises(self):
        with pytest.raises(ValueError):
            inspect_agent("a000", hour=24, num_agents=SMALL_N)
        with pytest.raises(ValueError):
            inspect_agent("a000", hour=-1, num_agents=SMALL_N)

    def test_missing_agent_raises(self):
        with pytest.raises(KeyError):
            inspect_agent("a999999", hour=14, num_agents=SMALL_N)


class TestGetPolicyDecision:
    @pytest.mark.parametrize("scenario", ["baseline", "reactive", "proactive"])
    def test_returns_decision_for_each_scenario(self, scenario):
        r = get_policy_decision("a002", hour=14, scenario=scenario, num_agents=SMALL_N)
        assert r["scenario"] == scenario
        assert r["agent_id"] == "a002"
        assert r["hour"] == 14
        assert "chosen_cell" in r and len(r["chosen_cell"]) == 2
        assert r["status"] in {"home", "working", "sheltering"}
        assert "rationale" in r
        assert r["rationale"]["policy"] == scenario
        assert "decision" in r["rationale"]
        assert "latency_ms" in r["rationale"]

    def test_invalid_scenario_raises(self):
        with pytest.raises(ValueError, match="scenario"):
            get_policy_decision("a000", hour=14, scenario="bogus", num_agents=SMALL_N)

    def test_invalid_hour_raises(self):
        with pytest.raises(ValueError, match="hour"):
            get_policy_decision("a000", hour=99, scenario="reactive", num_agents=SMALL_N)

    def test_missing_agent_raises(self):
        with pytest.raises(KeyError):
            get_policy_decision("a999", hour=10, scenario="baseline", num_agents=SMALL_N)


class TestPreviewVrptwForCuopt:
    def test_preview_returns_vrptw_shape(self):
        r = TOOLS["preview_vrptw_for_cuopt"](hour=14, fleet_size=3, num_agents=SMALL_N)
        assert r["hour"] == 14
        assert "vehicles" in r and len(r["vehicles"]) == 3
        assert "orders" in r
        assert "edge_costs" in r
        assert "shelter_capacity" in r
        assert "solver_config" in r

    def test_preview_orders_are_json_clean(self):
        import json
        r = TOOLS["preview_vrptw_for_cuopt"](hour=14, fleet_size=3, num_agents=SMALL_N)
        json.dumps(r)


class TestSlowToolContracts:
    """run_full_simulation + compare_all_scenarios are smoke-tested for input
    validation only; their full run is covered by scripts/nightly_smoke.ps1."""

    def test_run_full_simulation_rejects_unknown_scenario(self):
        with pytest.raises(ValueError, match="scenario"):
            run_full_simulation(scenario="not_a_scenario", num_agents=SMALL_N)
