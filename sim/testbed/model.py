"""Mesa-based Nihonbashi twin loop. One mesa.Agent per pedestrian."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import mesa

from .population import AgentSpec
from .policy import POLICY_REGISTRY, Decision
from .provenance import ProvenanceWriter
from .scene import GRID_X, GRID_Y, Shelter, manhattan


class PedestrianAgent(mesa.Agent):
    def __init__(self, model: "NihonbashiModel", spec: AgentSpec):
        super().__init__(model)
        self.spec = spec
        self.current_cell: Tuple[int, int] = spec.hourly_activity_cell[0]
        self.in_shelter_building: str | None = None
        self.last_decision: Decision | None = None

    def planned_activity_cell(self, hour: int) -> Tuple[int, int]:
        return self.spec.hourly_activity_cell[hour]

    def vulnerability(self) -> float:
        return self.spec.vulnerability_score


class NihonbashiModel(mesa.Model):
    def __init__(
        self,
        agents: List[AgentSpec],
        shelters: List[Shelter],
        envelope_table: Dict[Tuple[str, int], dict],
        heat_field: np.ndarray,
        policy_name: str,
        provenance_path: str,
        seed: int = 42,
    ):
        super().__init__(seed=seed)
        if policy_name not in POLICY_REGISTRY:
            raise ValueError(f"unknown policy {policy_name}")
        self.policy_name = policy_name
        self.policy_fn = POLICY_REGISTRY[policy_name]
        self.shelters = shelters
        self.envelope_table = envelope_table
        self.heat_field = heat_field
        self.hour = 0
        self.exposure_rows: List[dict] = []
        self.shelter_rows: List[dict] = []
        self.decision_rows: List[dict] = []
        self.latencies_ms: List[float] = []
        self.prov = ProvenanceWriter(provenance_path)

        for spec in agents:
            PedestrianAgent(self, spec)

        self.capacity_table: Dict[Tuple[str, int], int] = {
            k: v["max_occupants"] for k, v in envelope_table.items()
        }

    def _shelter_capacity_at(self, hour: int) -> Dict[str, int]:
        return {sh.building_id: self.capacity_table.get((sh.building_id, hour), 0)
                for sh in self.shelters}

    def step(self) -> None:
        h = self.hour
        occupied: Dict[str, int] = defaultdict(int)
        for pa in self.agents:
            if pa.in_shelter_building is not None:
                occupied[pa.in_shelter_building] += 1

        for pa in self.agents:
            planned = pa.planned_activity_cell(h)
            heat_here = float(self.heat_field[h, planned[0], planned[1]])

            t0 = time.perf_counter()
            decision = self.policy_fn(
                agent_id=pa.spec.agent_id,
                hour=h,
                cell=planned,
                exposure_now=heat_here,
                vulnerability=pa.vulnerability(),
                heat_field=self.heat_field,
                shelters=self.shelters,
                occupied=occupied,
                capacity=self.capacity_table,
            )
            t1 = time.perf_counter()
            self.latencies_ms.append((t1 - t0) * 1000.0)

            wanted = (heat_here > 1.0) or (
                pa.vulnerability() >= 0.55
                and h + 1 < self.heat_field.shape[0]
                and self.heat_field[h + 1, planned[0], planned[1]] >= 0.8
            )

            in_shelter = decision.chosen_shelter is not None
            if in_shelter:
                pa.in_shelter_building = decision.chosen_shelter
                pa.current_cell = decision.target_cell or planned
                occupied[decision.chosen_shelter] += 1
                effective_exposure = 0.0
            else:
                pa.in_shelter_building = None
                pa.current_cell = planned
                effective_exposure = heat_here

            pa.last_decision = decision

            self.exposure_rows.append({
                "scenario": self.policy_name,
                "agent_id": pa.spec.agent_id,
                "hour": h,
                "vulnerability_score": pa.vulnerability(),
                "age_bucket": pa.spec.age_bucket,
                "cell_x": pa.current_cell[0],
                "cell_y": pa.current_cell[1],
                "raw_heat": round(heat_here, 4),
                "effective_exposure": round(effective_exposure, 4),
                "in_shelter": int(in_shelter),
                "shelter_building_id": pa.in_shelter_building or "",
            })
            self.shelter_rows.append({
                "scenario": self.policy_name,
                "agent_id": pa.spec.agent_id,
                "hour": h,
                "in_shelter": int(in_shelter),
                "shelter_building_id": pa.in_shelter_building or "",
            })
            self.decision_rows.append({
                "scenario": self.policy_name,
                "agent_id": pa.spec.agent_id,
                "hour": h,
                "rule": decision.rule,
                "wanted_shelter": int(wanted),
                "chosen_shelter": decision.chosen_shelter,
                "target_cell_x": decision.target_cell[0] if decision.target_cell else None,
                "target_cell_y": decision.target_cell[1] if decision.target_cell else None,
                "reason": decision.reason,
            })
            self.prov.write({
                "scenario": self.policy_name,
                "hour": h,
                "agent_id": pa.spec.agent_id,
                "rule": decision.rule,
                "cell": list(planned),
                "raw_heat": round(heat_here, 4),
                "vulnerability": round(pa.vulnerability(), 4),
                "wanted_shelter": int(wanted),
                "chosen_shelter": decision.chosen_shelter,
                "reason": decision.reason,
                "decision_latency_ms": round((t1 - t0) * 1000.0, 4),
            })

        self.hour += 1

    def run_24h(self) -> None:
        for _ in range(24):
            self.step()
        self.prov.close()

    def exposure_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.exposure_rows)

    def shelter_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.shelter_rows)

    def decisions_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.decision_rows)
