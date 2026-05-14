# Simulation

| Folder | Purpose |
|---|---|
| `sumo/` | SUMO network + config files for the 200 m Nihonbashi scene |
| `abm/` | Mesa-based agent definitions (pedestrians, robots, service nodes) |
| `runs/` | Output of simulation runs (most contents gitignored — see `.gitignore`) |

## Setup

Install SUMO from https://sumo.dlr.de/docs/Downloads.php and ensure `sumolib` + `traci` are importable.

```powershell
pip install sumolib traci mesa
```

## Run convention

Every run produces a folder:

```
sim/runs/<phase>_<batch>/<side>/<seed>/
├── trace.csv          ← per-tick agent state
├── metrics.json       ← computed scalar metrics
└── log.txt
```

Plus a single `run_config.json` per batch with scenario combos, seeds, parameters, code commit SHA.

This convention is consumed by `scripts/run_comparison.py`.
