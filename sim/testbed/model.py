"""Mesa Model + Agent for the testbed.

The decision flow is policy-driven; Mesa provides the scheduling envelope
and an extensible agent base for Stage Two (Mesa <-> traci/SUMO co-sim).
"""
import mesa
from .population import AgentProfile
from .policy import POLICIES


class HeatAgent(mesa.Agent):
    def __init__(self, model: "HeatModel", profile: AgentProfile):
        super().__init__(model)
        self.profile = profile
        self.current_cell = profile.home_cell
        self.status = "home"
        self.cumulative_exposure = 0.0
        self.last_rationale: dict = {}
        self.last_displacement: int = 0

    def step(self) -> None:
        model: "HeatModel" = self.model  # type: ignore[assignment]
        hour = model.current_hour
        policy = POLICIES[model.scenario_name]
        cell, status, rationale = policy(self.profile, hour, model.world)
        # Displacement from the policy-free intended cell:
        from .population import planned_cell
        intended = planned_cell(self.profile, hour)
        self.last_displacement = abs(cell[0] - intended[0]) + abs(cell[1] - intended[1])
        self.current_cell = cell
        self.status = status
        self.last_rationale = rationale
        # Sheltering reduces effective heat exposure to a cooled value.
        heat = 0.1 if status == "sheltering" else model.world.heat_at(hour, cell)
        self.cumulative_exposure += heat


class HeatModel(mesa.Model):
    def __init__(
        self,
        world,
        profiles: list[AgentProfile],
        scenario_name: str,
        rng: int | None = 42,
    ):
        super().__init__(rng=rng)
        self.world = world
        self.scenario_name = scenario_name
        self.current_hour = 0
        for prof in profiles:
            HeatAgent(self, prof)

    def step(self) -> None:
        self.agents.shuffle_do("step")
