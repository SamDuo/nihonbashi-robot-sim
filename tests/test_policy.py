"""Unit tests for sim/testbed/policy.py — the Stage One decision functions.

These tests are the regression net before Stage Two (cuOpt) work resumes.
Each policy is exercised across the four interesting world states:
    hot+vulnerable+open, hot+vulnerable+full, hot+robust, cold+vulnerable.
"""
import pytest

from sim.testbed.policy import (
    HEAT_THRESHOLD,
    POLICIES,
    VULN_THRESHOLD,
    baseline,
    proactive,
    reactive,
)
from sim.testbed.scene import SHELTER_CELLS


pytestmark = pytest.mark.unit


class TestPolicyRegistry:
    def test_three_policies_registered(self):
        assert set(POLICIES.keys()) == {"baseline", "reactive", "proactive"}

    def test_policies_map_to_callables(self):
        for name, fn in POLICIES.items():
            assert callable(fn), f"{name} is not callable"

    def test_thresholds_are_sane(self):
        assert 0.0 < VULN_THRESHOLD < 1.0
        assert HEAT_THRESHOLD > 1.0


class TestBaseline:
    """Baseline never intervenes — same cell as planned, status as planned."""

    def test_baseline_returns_planned_cell_when_hot(self, vulnerable_agent, hot_world):
        cell, status, r = baseline(vulnerable_agent, hour=14, world=hot_world)
        assert cell == vulnerable_agent.activity_cell
        assert status == "working"
        assert r["policy"] == "baseline"
        assert r["decision"] == "no_intervention"

    def test_baseline_returns_planned_cell_when_cold(self, vulnerable_agent, cold_world):
        cell, status, r = baseline(vulnerable_agent, hour=14, world=cold_world)
        assert cell == vulnerable_agent.activity_cell
        assert r["decision"] == "no_intervention"

    def test_baseline_respects_home_hours(self, vulnerable_agent, hot_world):
        cell, status, _ = baseline(vulnerable_agent, hour=3, world=hot_world)
        assert cell == vulnerable_agent.home_cell
        assert status == "home"

    def test_baseline_records_latency(self, vulnerable_agent, cold_world):
        _, _, r = baseline(vulnerable_agent, hour=10, world=cold_world)
        assert "latency_ms" in r
        assert r["latency_ms"] >= 0.0


class TestReactive:
    """Reactive triggers only when current heat exceeds threshold AND agent is vulnerable."""

    def test_routes_vulnerable_agent_to_shelter_when_hot_and_open(self, vulnerable_agent, hot_world):
        cell, status, r = reactive(vulnerable_agent, hour=14, world=hot_world)
        assert status == "sheltering"
        assert r["decision"] == "route_to_shelter"
        assert r["shelter"] in SHELTER_CELLS
        assert cell == SHELTER_CELLS[r["shelter"]]

    def test_consumes_shelter_capacity(self, vulnerable_agent, hot_world):
        sid_first = None
        for _ in range(10):
            _, _, r = reactive(vulnerable_agent, hour=14, world=hot_world)
            if r["decision"] == "route_to_shelter":
                sid_first = sid_first or r["shelter"]
        # After 10 routes (capacity=10), at least one shelter is at zero remaining.
        assert any(hot_world.shelter_remaining(sid, 14) == 0 for sid in SHELTER_CELLS)

    def test_stays_when_hot_but_robust(self, robust_agent, hot_world):
        cell, status, r = reactive(robust_agent, hour=14, world=hot_world)
        assert r["decision"] == "stay_below_threshold"
        assert status != "sheltering"
        assert cell == robust_agent.activity_cell

    def test_stays_when_cold_and_vulnerable(self, vulnerable_agent, cold_world):
        _, status, r = reactive(vulnerable_agent, hour=14, world=cold_world)
        assert r["decision"] == "stay_below_threshold"
        assert status != "sheltering"

    def test_stays_when_no_shelter_capacity(self, vulnerable_agent, hot_world_no_capacity):
        cell, status, r = reactive(vulnerable_agent, hour=14, world=hot_world_no_capacity)
        assert r["decision"] == "stay_no_capacity"
        assert status != "sheltering"
        assert cell == vulnerable_agent.activity_cell


class TestProactive:
    """Proactive triggers on 4h lookahead max — fires earlier than reactive."""

    def test_routes_when_lookahead_hot(self, vulnerable_agent, hot_world):
        _, status, r = proactive(vulnerable_agent, hour=14, world=hot_world)
        assert status == "sheltering"
        assert r["decision"] == "preposition_to_shelter"
        assert r["lookahead_max"] >= HEAT_THRESHOLD - 0.1

    def test_lookahead_field_present(self, vulnerable_agent, hot_world):
        _, _, r = proactive(vulnerable_agent, hour=14, world=hot_world)
        assert "lookahead_max" in r
        assert isinstance(r["lookahead_max"], float)

    def test_stays_when_lookahead_cold(self, vulnerable_agent, cold_world):
        _, status, r = proactive(vulnerable_agent, hour=14, world=cold_world)
        assert r["decision"] == "stay_below_lookahead_threshold"
        assert status != "sheltering"

    def test_stays_when_robust_even_if_hot(self, robust_agent, hot_world):
        _, status, r = proactive(robust_agent, hour=14, world=hot_world)
        assert r["decision"] == "stay_below_lookahead_threshold"
        assert status != "sheltering"

    def test_lookahead_window_does_not_run_off_end(self, vulnerable_agent, hot_world):
        # Hour 23 is the last hour — lookahead must clamp at 23 without IndexError.
        _, _, r = proactive(vulnerable_agent, hour=23, world=hot_world)
        assert "lookahead_max" in r

    def test_proactive_records_latency(self, vulnerable_agent, hot_world):
        _, _, r = proactive(vulnerable_agent, hour=14, world=hot_world)
        assert r["latency_ms"] >= 0.0


class TestPolicyDifferentiation:
    """Sanity check: all three policies disagree on a hot, vulnerable scenario."""

    def test_baseline_does_not_shelter_when_others_do(self, vulnerable_agent, hot_world):
        # Fresh worlds per call so shelter consumption doesn't bleed across.
        from sim.testbed.world import World

        def fresh():
            return World(hot_world.heat_field, hot_world.shelter_rows)

        _, base_status, _ = baseline(vulnerable_agent, 14, fresh())
        _, react_status, _ = reactive(vulnerable_agent, 14, fresh())
        _, proact_status, _ = proactive(vulnerable_agent, 14, fresh())

        assert base_status != "sheltering"
        assert react_status == "sheltering"
        assert proact_status == "sheltering"
