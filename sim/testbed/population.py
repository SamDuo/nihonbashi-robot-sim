"""Synthetic G1 population: one row per agent per hour. Schema in section 4a."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd

from .scene import GRID_X, GRID_Y


AGE_BUCKETS = ("child", "adult", "elderly")
OCCUPATIONS = ("worker", "commuter", "visitor", "resident", "student")
MOBILITIES = ("mobile", "assisted", "restricted")


@dataclass
class AgentSpec:
    agent_id: int
    age_bucket: str
    occupation_class: str
    mobility_class: str
    vulnerability_score: float
    home_cell: Tuple[int, int]
    hourly_activity_cell: List[Tuple[int, int]]


def _vulnerability(age: str, mob: str, rng: np.random.Generator) -> float:
    base = {"child": 0.55, "adult": 0.25, "elderly": 0.75}[age]
    mod = {"mobile": 0.0, "assisted": 0.10, "restricted": 0.20}[mob]
    return float(np.clip(base + mod + rng.normal(0.0, 0.04), 0.0, 1.0))


def _activity_schedule(home: Tuple[int, int], rng: np.random.Generator) -> List[Tuple[int, int]]:
    schedule: List[Tuple[int, int]] = []
    work = (int(rng.integers(0, GRID_X)), int(rng.integers(0, GRID_Y)))
    for h in range(24):
        if h < 7 or h >= 22:
            schedule.append(home)
        elif 9 <= h < 17:
            schedule.append(work)
        else:
            cx = int(np.clip(work[0] + rng.integers(-2, 3), 0, GRID_X - 1))
            cy = int(np.clip(work[1] + rng.integers(-2, 3), 0, GRID_Y - 1))
            schedule.append((cx, cy))
    return schedule


def generate_synthetic(n_agents: int = 240, seed: int = 11) -> Tuple[List[AgentSpec], pd.DataFrame]:
    rng = np.random.default_rng(seed)
    agents: List[AgentSpec] = []
    rows = []
    for aid in range(n_agents):
        age = AGE_BUCKETS[rng.choice(3, p=[0.18, 0.62, 0.20])]
        occ = OCCUPATIONS[rng.choice(5, p=[0.40, 0.25, 0.15, 0.12, 0.08])]
        if age == "child":
            occ = "student" if rng.random() < 0.7 else "visitor"
        if age == "elderly":
            occ = "resident" if rng.random() < 0.6 else "visitor"
        mob_p = {
            "child":   [0.85, 0.10, 0.05],
            "adult":   [0.95, 0.04, 0.01],
            "elderly": [0.55, 0.30, 0.15],
        }[age]
        mob = MOBILITIES[rng.choice(3, p=mob_p)]
        vuln = _vulnerability(age, mob, rng)
        home = (int(rng.integers(0, GRID_X)), int(rng.integers(0, GRID_Y)))
        schedule = _activity_schedule(home, rng)
        agents.append(AgentSpec(aid, age, occ, mob, vuln, home, schedule))
        for h, (cx, cy) in enumerate(schedule):
            rows.append({
                "agent_id": aid,
                "age_bucket": age,
                "occupation_class": occ,
                "mobility_class": mob,
                "vulnerability_score": vuln,
                "home_grid_cell": f"{home[0]},{home[1]}",
                "hour": h,
                "activity_grid_cell": f"{cx},{cy}",
            })
    return agents, pd.DataFrame(rows)
