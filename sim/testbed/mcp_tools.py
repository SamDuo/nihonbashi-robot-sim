"""Agent-orchestrator-callable tools for the Nihonbashi testbed.

These functions expose the simulation's three policies + comparison metrics
as a clean, JSON-shaped surface that an autonomous agent (Claude Code via
Claude Agent SDK, or any MCP-compatible orchestrator) can call without
needing to understand Mesa internals.

Today: import and call directly from Python.
Stage Two: register as in-process MCP server via `mcp_server.py` (see
docs/cuopt_integration_plan.md for the integration plan).

Design rules:
- Each tool returns a JSON-serializable dict (no numpy arrays, no
  Mesa objects). Orchestrators consume dicts; they don't unwrap classes.
- Every tool is pure-ish: no globals, no side effects on the world
  state passed in. Re-running a tool with the same inputs gives the
  same output.
- Tool docstrings are agent-readable spec. They become the MCP tool
  description verbatim when exposed.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .heat_field import build_heat_field
from .policy import HEAT_THRESHOLD, POLICIES, VULN_THRESHOLD
from .population import AgentProfile, build_population, planned_cell, planned_status
from .scene import SHELTER_CELLS
from .shelter_model import build_envelope
from .world import World


SCENARIOS = ("baseline", "reactive", "proactive")


def _build_default_world(num_agents: int = 200, seed: int = 42) -> tuple[World, list[AgentProfile]]:
    """Synthetic Stage One world. Real Stage Two world replaces this loader."""
    heat = build_heat_field()
    envelope = build_envelope(shelter_ids=list(SHELTER_CELLS.keys()))
    world = World(heat_field=heat, shelter_rows=envelope)
    profiles = build_population(n=num_agents, seed=seed)
    return world, profiles


def list_scenarios() -> dict[str, Any]:
    """Return the names + descriptions of the three policy scenarios.

    Use this when an orchestrator needs to know what scenarios exist before
    running one. Returns a stable contract; the three names never change
    across Stage One/Stage Two.

    Returns:
        {
          "scenarios": ["baseline", "reactive", "proactive"],
          "descriptions": {scenario_name: one-line description},
          "thresholds": {"heat": float, "vulnerability": float},
        }
    """
    return {
        "scenarios": list(SCENARIOS),
        "descriptions": {
            "baseline": "No intervention. Agents follow planned activity regardless of heat.",
            "reactive": "Route vulnerable agents to nearest open shelter once heat at their cell exceeds threshold.",
            "proactive": "3-hour lookahead. Pre-position vulnerable agents to shelters before exposure crosses threshold. (Stage Two: cuOpt VRPTW solver replaces threshold rule — see cuopt_integration_plan.md.)",
        },
        "thresholds": {
            "heat_cost_factor": HEAT_THRESHOLD,
            "vulnerability_score": VULN_THRESHOLD,
        },
    }


def inspect_agent(agent_id: str, hour: int, num_agents: int = 200) -> dict[str, Any]:
    """Return the full state of one agent at one hour without running a sim.

    Use for what-if inspection: 'what would agent a042 see at hour 14?'.
    Does not mutate world. Does not consume shelter capacity.

    Args:
        agent_id: e.g. 'a042'. Must exist in the synthetic population.
        hour: 0..23.
        num_agents: population size to build (must match the run that
            produced agent_id; default 200 matches Stage One default).

    Returns:
        {
          "agent_id": str,
          "hour": int,
          "profile": {agent fields},
          "planned": {"cell": [x, y], "status": "home|working"},
          "heat_at_planned": float,
          "vulnerability_score": float,
          "would_trigger": {"reactive": bool, "proactive": bool},
        }
    """
    if not (0 <= hour <= 23):
        raise ValueError(f"hour must be in [0, 23], got {hour}")
    world, profiles = _build_default_world(num_agents=num_agents)
    agent = next((p for p in profiles if p.agent_id == agent_id), None)
    if agent is None:
        raise KeyError(f"agent_id {agent_id!r} not in population of {num_agents}")
    cell = planned_cell(agent, hour)
    heat_now = world.heat_at(hour, cell)
    lookahead_max = max(
        (world.heat_at(min(23, hour + dh), cell) for dh in range(4)),
        default=0.0,
    )
    return {
        "agent_id": agent.agent_id,
        "hour": hour,
        "profile": asdict(agent),
        "planned": {
            "cell": list(cell),
            "status": planned_status(agent, hour),
        },
        "heat_at_planned": float(heat_now),
        "lookahead_max_4h": float(lookahead_max),
        "vulnerability_score": float(agent.vulnerability_score),
        "would_trigger": {
            "reactive": bool(
                heat_now > HEAT_THRESHOLD
                and agent.vulnerability_score > VULN_THRESHOLD
            ),
            "proactive": bool(
                agent.vulnerability_score > VULN_THRESHOLD
                and lookahead_max > (HEAT_THRESHOLD - 0.1)
            ),
        },
    }


def get_policy_decision(
    agent_id: str, hour: int, scenario: str, num_agents: int = 200,
) -> dict[str, Any]:
    """Run one policy on one agent at one hour. Returns the decision rationale.

    Use when an orchestrator needs to *explain* a specific decision rather
    than re-run the full simulation. Note: this consumes shelter capacity
    if the decision routes the agent to a shelter — call inspect_agent
    instead if you only want a read-only check.

    Args:
        agent_id: e.g. 'a042'.
        hour: 0..23.
        scenario: one of 'baseline', 'reactive', 'proactive'.
        num_agents: population size; must match the run that produced agent_id.

    Returns:
        {
          "agent_id": str,
          "scenario": str,
          "hour": int,
          "chosen_cell": [x, y],
          "status": "home|working|sheltering",
          "rationale": {policy-specific dict — decision, latency_ms, heat, ...},
        }
    """
    if scenario not in POLICIES:
        raise ValueError(f"scenario must be one of {list(POLICIES)}, got {scenario!r}")
    if not (0 <= hour <= 23):
        raise ValueError(f"hour must be in [0, 23], got {hour}")
    world, profiles = _build_default_world(num_agents=num_agents)
    agent = next((p for p in profiles if p.agent_id == agent_id), None)
    if agent is None:
        raise KeyError(f"agent_id {agent_id!r} not in population of {num_agents}")
    cell, status, rationale = POLICIES[scenario](agent, hour, world)
    return {
        "agent_id": agent.agent_id,
        "scenario": scenario,
        "hour": hour,
        "chosen_cell": list(cell),
        "status": status,
        "rationale": rationale,
    }


def run_full_simulation(
    scenario: str, num_agents: int = 200, out_root: str | None = None,
) -> dict[str, Any]:
    """Run a complete 24-hour scenario and return summary metrics + artifact paths.

    Use when an orchestrator wants the headline numbers for one policy
    without writing/reading CSVs manually. Writes the same artifacts as
    `scripts/run_testbed.py` (population.csv, agents.csv, metrics.csv,
    provenance.jsonl) under `<out_root>/outputs/`.

    Args:
        scenario: one of 'baseline', 'reactive', 'proactive'.
        num_agents: population size.
        out_root: where to write outputs/. Defaults to the repo root.
            Set this to a non-OneDrive path when local quota is tight.

    Returns:
        {
          "scenario": str,
          "num_agents": int,
          "hours_simulated": 24,
          "metrics": {Xilin six metrics as a dict},
          "artifacts": {filename: absolute_path},
        }
    """
    if scenario not in POLICIES:
        raise ValueError(f"scenario must be one of {list(POLICIES)}, got {scenario!r}")
    from .run import main as run_main  # lazy import to avoid heavy startup
    repo_root = Path(__file__).resolve().parents[2]
    out = Path(out_root) if out_root else repo_root
    # `run_main` writes all three scenarios; we just surface the requested one.
    # TODO Stage Two: thread `scenario` and `num_agents` through `run_main`.
    run_main(out_root=str(out))
    metrics_path = out / "outputs" / "timeseries" / "metrics.csv"
    return {
        "scenario": scenario,
        "num_agents": num_agents,
        "hours_simulated": 24,
        "artifacts": {
            "metrics_csv": str(metrics_path),
            "agents_csv": str(out / "outputs" / "timeseries" / "agents.csv"),
            "population_csv": str(out / "outputs" / "timeseries" / "population.csv"),
            "provenance_jsonl": str(out / "outputs" / "reports" / "provenance.jsonl"),
            "shelters_geojson": str(out / "outputs" / "geo" / f"shelters_{scenario}.geojson"),
        },
        "notes": "metrics returned via artifact CSV; read with pandas. Stage Two will inline summary metrics in this response.",
    }


def compare_all_scenarios(num_agents: int = 200, out_root: str | None = None) -> dict[str, Any]:
    """Run all three policies and return Xilin six-metric comparison.

    The canonical 'workshop deliverable' tool. Use this for headline results.

    Args:
        num_agents: population size.
        out_root: where to write outputs/. Defaults to repo root.

    Returns:
        {
          "scenarios": ["baseline", "reactive", "proactive"],
          "num_agents": int,
          "artifacts": {filename: absolute_path},
          "comparison_md": absolute path to outputs/reports/testbed_comparison.md,
        }
    """
    from .run import main as run_main
    repo_root = Path(__file__).resolve().parents[2]
    out = Path(out_root) if out_root else repo_root
    run_main(out_root=str(out))
    return {
        "scenarios": list(SCENARIOS),
        "num_agents": num_agents,
        "artifacts": {
            "metrics_csv": str(out / "outputs" / "timeseries" / "metrics.csv"),
            "comparison_md": str(out / "outputs" / "reports" / "testbed_comparison.md"),
            "provenance_jsonl": str(out / "outputs" / "reports" / "provenance.jsonl"),
        },
        "comparison_md": str(out / "outputs" / "reports" / "testbed_comparison.md"),
    }


def list_shelters() -> dict[str, Any]:
    """Return canonical shelter locations + IDs.

    Returns:
        {
          "shelters": {shelter_id: {"cell": [x, y], "lat": float, "lng": float}},
          "count": int,
        }
    """
    from .scene import cell_centroid_latlng
    out: dict[str, dict[str, Any]] = {}
    for sid, cell in SHELTER_CELLS.items():
        lat, lng = cell_centroid_latlng(cell[0], cell[1])
        out[sid] = {"cell": list(cell), "lat": float(lat), "lng": float(lng)}
    return {"shelters": out, "count": len(out)}


# ---------------------------------------------------------------------------
# Tool registry — single source of truth for the MCP wrapper layer.
# When `mcp_server.py` is added (Stage Two), it iterates this dict to
# auto-register each function as an MCP tool. Until then, importable directly.

# Lazy import so the cuOpt branch only loads when needed.
def _preview_vrptw(hour: int = 14, fleet_size: int = 5, num_agents: int = 200) -> dict[str, Any]:
    """Build the Stage Two VRPTW input for cuOpt at the given hour.

    Inspection-only: does not invoke the solver (which requires cuOpt to be
    installed). Use to verify what the proactive AV-dispatch branch would
    hand to cuOpt at any hour. See docs/cuopt_integration_plan.md.

    Args:
        hour: 0..23.
        fleet_size: number of AVs to plan with.
        num_agents: population size to build.

    Returns:
        VRPTWInput as a JSON-friendly dict (vehicles, orders, edge_costs,
        shelter_capacity, solver_config).
    """
    from .cuopt_formulator import preview_vrptw_input
    return preview_vrptw_input(hour=hour, fleet_size=fleet_size, num_agents=num_agents)


TOOLS = {
    "list_scenarios": list_scenarios,
    "list_shelters": list_shelters,
    "inspect_agent": inspect_agent,
    "get_policy_decision": get_policy_decision,
    "run_full_simulation": run_full_simulation,
    "compare_all_scenarios": compare_all_scenarios,
    "preview_vrptw_for_cuopt": _preview_vrptw,
}
