"""Synthetic agent population matching the G1 contract.

100 agents with age, occupation, mobility, vulnerability_score, home cell,
activity cell, and a simple home -> activity -> home routine over 24 hours.
Schema matches docs/system_architecture.md section 7a.
"""
from dataclasses import dataclass
import numpy as np
from .scene import GRID_W, GRID_H


AGE_BUCKETS = ["child", "adult", "elderly"]
OCCUPATIONS = ["worker", "commuter", "visitor", "resident", "student"]
MOBILITY = ["mobile", "assisted", "restricted"]


@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    age_bucket: str
    occupation_class: str
    mobility_class: str
    vulnerability_score: float
    home_cell: tuple[int, int]
    activity_cell: tuple[int, int]
    work_start: int
    work_end: int


def _vulnerability(age: str, mobility: str, rng) -> float:
    base = {"child": 0.55, "adult": 0.25, "elderly": 0.78}[age]
    mob = {"mobile": 0.0, "assisted": 0.15, "restricted": 0.30}[mobility]
    return float(min(1.0, max(0.0, base + mob + rng.normal(0, 0.05))))


def build_population(n: int = 100, seed: int = 17) -> list[AgentProfile]:
    rng = np.random.default_rng(seed)
    out: list[AgentProfile] = []
    for i in range(n):
        age = str(rng.choice(AGE_BUCKETS, p=[0.15, 0.65, 0.20]))
        occ = str(rng.choice(OCCUPATIONS, p=[0.25, 0.25, 0.20, 0.20, 0.10]))
        mob = str(rng.choice(MOBILITY, p=[0.80, 0.15, 0.05]))
        vuln = _vulnerability(age, mob, rng)
        home = (int(rng.integers(0, GRID_W)), int(rng.integers(0, GRID_H)))
        activity = (int(rng.integers(0, GRID_W)), int(rng.integers(0, GRID_H)))
        ws = int(rng.integers(6, 10))
        we = int(rng.integers(16, 20))
        out.append(AgentProfile(
            agent_id=f"a{i:03d}",
            age_bucket=age,
            occupation_class=occ,
            mobility_class=mob,
            vulnerability_score=vuln,
            home_cell=home,
            activity_cell=activity,
            work_start=ws,
            work_end=we,
        ))
    return out


def planned_cell(p: AgentProfile, hour: int) -> tuple[int, int]:
    if p.work_start <= hour < p.work_end:
        return p.activity_cell
    return p.home_cell


def planned_status(p: AgentProfile, hour: int) -> str:
    if p.work_start <= hour < p.work_end:
        return "working"
    return "home"
