"""Shared pytest fixtures for the nihonbashi-robot-sim test suite.

Fixtures here are deliberately tiny — a 24h heat field on the project grid,
a handful of agents, and a stub shelter envelope. Real data still flows
through scripts/run_testbed.py; the fixtures exist so unit tests can run
without disk I/O or osmnx/SUMO imports.
"""
import numpy as np
import pytest

from sim.testbed.population import AgentProfile
from sim.testbed.scene import GRID_W, GRID_H, SHELTER_CELLS
from sim.testbed.shelter_model import ShelterRow
from sim.testbed.world import World


@pytest.fixture
def hot_heat_field() -> np.ndarray:
    """24h heat field that is uniformly HOT (1.3) — exceeds HEAT_THRESHOLD."""
    return np.full((24, GRID_W, GRID_H), 1.3, dtype=np.float32)


@pytest.fixture
def cold_heat_field() -> np.ndarray:
    """24h heat field that is uniformly COLD (0.5) — well below threshold."""
    return np.full((24, GRID_W, GRID_H), 0.5, dtype=np.float32)


@pytest.fixture
def open_shelter_rows() -> list[ShelterRow]:
    """All three project shelters open with capacity=10/hour, no congestion."""
    rows = []
    for sid in SHELTER_CELLS.keys():
        for hour in range(24):
            rows.append(ShelterRow(sid, hour, max_occupants=10,
                                   cooling_kwh=12.0, emissions_intensity=0.4))
    return rows


@pytest.fixture
def full_shelter_rows() -> list[ShelterRow]:
    """All three shelters at capacity=0 — no shelter is feasible."""
    rows = []
    for sid in SHELTER_CELLS.keys():
        for hour in range(24):
            rows.append(ShelterRow(sid, hour, max_occupants=0,
                                   cooling_kwh=0.0, emissions_intensity=0.4))
    return rows


@pytest.fixture
def hot_world(hot_heat_field, open_shelter_rows) -> World:
    return World(hot_heat_field, open_shelter_rows)


@pytest.fixture
def cold_world(cold_heat_field, open_shelter_rows) -> World:
    return World(cold_heat_field, open_shelter_rows)


@pytest.fixture
def hot_world_no_capacity(hot_heat_field, full_shelter_rows) -> World:
    return World(hot_heat_field, full_shelter_rows)


@pytest.fixture
def vulnerable_agent() -> AgentProfile:
    """Elderly + restricted mobility → vulnerability > VULN_THRESHOLD (0.50)."""
    return AgentProfile(
        agent_id="a_vuln",
        age_bucket="elderly",
        occupation_class="resident",
        mobility_class="restricted",
        vulnerability_score=0.95,
        home_cell=(5, 5),
        activity_cell=(15, 5),
        work_start=9,
        work_end=17,
    )


@pytest.fixture
def robust_agent() -> AgentProfile:
    """Adult + mobile → low vulnerability, below VULN_THRESHOLD."""
    return AgentProfile(
        agent_id="a_rob",
        age_bucket="adult",
        occupation_class="worker",
        mobility_class="mobile",
        vulnerability_score=0.15,
        home_cell=(2, 2),
        activity_cell=(18, 2),
        work_start=9,
        work_end=17,
    )
