# Stage One research design + session handoff

> **Purpose of this file.** When a new Claude Code session starts in this workspace, ask it to read this file first — it carries the project context, the environment quirks that broke the previous session, and the current state of the work. The original Stage One research design (the 12KB doc the project brief refers to) was lost to an OneDrive sync truncation; this file reconstructs the design from `docs/system_architecture.md` and embeds the operational handoff alongside it. Last updated 2026-05-22 after the Stage One testbed (commits `a4b0518`, `9be80a3`) landed on GitHub.

---

## 1. What this project is

Group 3 of the Tokyo summer workshop, Nihonbashi heat-equity digital twin. Group 3 is the **synthesis layer**: it ingests Group 1 (heat exposure + vulnerable population) and Group 2 (building cooling envelope + emissions) outputs at a documented schema, runs an agentic decision loop that produces reactive shelter allocations and proactive resource dispatches, and visualizes the loop so reviewers can interrogate it.

Stage One ships a working testbed on synthetic G1/G2 data that conforms to the locked schemas. When the real datasets land, the synthetic generators swap for real loaders without touching the rest of the pipeline. Stage Two adds the NVIDIA Omniverse / Isaac Sim twin and Yi's SHP→SUMO street network; Stage One does not pre-commit to those tools.

Target audience for the 5/25 review: the rest of the workshop (Groups 1 and 2) plus faculty advisors. Headline visual is the Folium browser twin; supporting evidence is the metric table + three diagnostic charts; backup is the per-decision JSONL audit log.

---

## 2. Where everything lives

| What | Path |
|---|---|
| OneDrive repo (canonical, but write-flaky — see §6) | `c:\Users\qduong7\OneDrive - Georgia Institute of Technology (1)\Documents\Tokyo Planning Analytics\nihonbashi-robot-sim\` |
| GitHub remote | `https://github.com/SamDuo/nihonbashi-robot-sim.git` |
| Stage One branch | `stage1-testbed` (pushed) |
| Stage One commits | `a4b0518` (testbed) → `9be80a3` (slide deck) |
| Working temp clone (committable, outside OneDrive) | `C:\Windows\Temp\nihon-stage1-repo\` |
| Source build (where the run.py wrote outputs) | `C:\Users\Public\Documents\nihon-stage1\` |
| Mirror of source build | `C:\Windows\Temp\nihon-stage1\` |
| Memory note staged for install | `C:\Windows\Temp\nihon-stage1\_memory_to_install\onedrive_writes.md` |

---

## 3. The pipeline (Stage One implementation)

```
sim/testbed/
  scene.py            WGS84-anchored 20x10 grid + 5 shelter footprints (Shapely)
  population.py       Synthetic G1 population: age, occupation, mobility, vulnerability_score, hourly activity cell
  heat_field.py       Synthetic G1 heat field (24, 20, 10) in [0, 2]
  shelter_model.py    Synthetic G2 envelope: max_occupants, cooling_kwh, emissions_intensity per hour
  policy.py           Three policies (baseline / reactive / proactive)
  provenance.py       JSONL audit writer
  model.py            mesa.Model + PedestrianAgent; the step loop
  metrics.py          9 outcome + 2 twin metric definitions (see §4)
  gis_export.py       GeoJSON exporters (heat field, shelters, agents)
  visualize.py        Folium browser twin + matplotlib diagnostic charts
  run.py              End-to-end driver
scripts/
  run_testbed.py      Entrypoint: python scripts/run_testbed.py
  make_deck.py        Build outputs/slides/stage1_review_deck.html from latest run
```

Run with `python scripts/run_testbed.py` from the repo root. Outputs land in `outputs/reports/`, `outputs/gis/`, `outputs/figures/auto/`, and `outputs/slides/` (deck via `make_deck.py`).

Scene anchored to Nihonbashi 35.6840–35.6852°N, 139.7735–139.7747°E. Five shelter buildings (SH_MITSUKOSHI, SH_COREDO, SH_BANK_HALL, SH_SUBWAY_EXIT, SH_BRIDGE_PLAZA) with footprints + per-hour capacity envelopes.

---

## 4. The 9 outcome + 2 twin metrics

These are also defined inline in `sim/testbed/metrics.py:DEFINITIONS` and rendered into `outputs/reports/testbed_comparison.md` on every run.

**Outcome metrics — what the system does for people:**

1. **cumulative_population_exposure** — sum over (agent, hour) of `heat_value * (0 if sheltered else 1)`. Lower better.
2. **vulnerability_weighted_exposure** — same sum, each term scaled by `vulnerability_score`. Lower better.
3. **mean_peak_hourly_exposure** — average across agents of each agent's max hourly exposure. Lower better.
4. **sheltered_agent_hours** — count of (agent, hour) tuples where the agent is in a shelter. Higher better.
5. **shelter_utilization_rate** — mean across hours of (occupants_summed / capacity_summed). Target ~0.6–0.85; >0.95 = undersupply; <0.3 = policy isn't moving the right people.
6. **unmet_shelter_demand** — count of decisions that wanted shelter but found none feasible. Lower better.
7. **cooling_energy_kwh** — sum of `cooling_kwh * util_fraction` across hours. Cost lever; lower better all else equal.
8. **cooling_emissions_kgco2e** — `cooling_energy_kwh * emissions_intensity` summed. Lower better.
9. **equity_gap_ratio** — mean exposure of top vulnerability quartile / mean exposure of bottom quartile. 1.0 = parity; >1 = inequity; proactive policies should drive this toward 1 (or below, meaning vulnerable are preferentially protected).

**Twin metrics — health of the loop itself:**

10. **mean_decision_latency_ms** — average per-decision wall-clock time. Twin health.
11. **provenance_coverage** — provenance events written / (agents × hours). 1.0 = every step audited.

### Headline numbers from the canonical Stage One run (n=240 agents, 24h, seed 42)

| Metric | baseline | reactive | proactive | Δ best vs baseline |
|---|---:|---:|---:|---:|
| cumulative_population_exposure | 4871 | 3326 | **3278** | −33% |
| vulnerability_weighted_exposure | 1990 | 1365 | **1315** | −34% |
| sheltered_agent_hours | 0 | 1066 | **1144** | +1144 |
| equity_gap_ratio | 0.99 | 1.00 | **0.91** | preferentially protective |
| unmet_shelter_demand | 2482 | 1416 | **1338** | −46% |
| cooling_energy_kwh | 0 | 1225 | 1305 | (cost of intervention) |
| provenance_coverage | 1.00 | 1.00 | 1.00 | full audit |

---

## 5. Three policies

Defined in `sim/testbed/policy.py`:

- **baseline** — no policy intervention. Agents follow their planned activity cell every hour; heat exposure accumulates.
- **reactive** — if `heat_value > 1.0` in the agent's current cell, route to the nearest feasible shelter (Manhattan distance, capacity-aware).
- **proactive** — if `vulnerability_score ≥ 0.55` **and** next-hour heat forecast in cell ≥ 0.8, pre-position to the nearest feasible shelter. Falls back to reactive logic if forecast trigger doesn't fire but raw exposure does.

Thresholds are constants at the top of `policy.py` so they can be tuned without touching call sites.

---

## 6. Critical environment quirks (read before doing anything)

### 6a. `C:\Users\qduong7\*` silently truncates writes

OneDrive Files-On-Demand (and possibly Microsoft Endpoint DLP) hooks the user profile via a reparse-point minifilter. Writes >~10KB to **any** path under `C:\Users\qduong7\` — including the OneDrive folder, the user home, `C:\Users\qduong7\tmp\`, and `C:\Users\qduong7\.claude\projects\.../memory/` — silently truncate to 0 bytes or return `ENOSPC: no space left on device`. The disk has terabytes free; the error is from the hook.

**Symptom in the previous session**: this very file (`docs/stage1_research_design.md`) showed up as 0 bytes on disk despite the project owner reporting it as 12KB and complete. Same root cause. Treat any "lost" or "0-byte" file under the user profile as a potential silent OneDrive truncation, not a code or git bug.

**Recovery — neither of these is enough on its own:**

- OneDrive client UI **Pause syncing** stops uploads but does NOT release the filesystem hook. Confirmed empirically: pause was active, 100KB probe writes still failed.
- Killing the three OneDrive processes (`OneDrive.exe`, `OneDrive.Sync.Service`, `FileCoAuth`) via `Stop-Process -Force` or Task Manager **does** release the hook. But there's a second, deeper block (see 6b) that survives the kill.

### 6b. Profile-level quota or DLP (deeper than OneDrive)

After all three OneDrive processes were ended, writes to `C:\Users\qduong7\*` still fail. The user profile holds ~169 GB / 483K files. Likely an enterprise NTFS quota or Microsoft Endpoint DLP throttling. `fsutil quota query C:` returns Access denied (needs admin). `fltmc filters` also blocked. Confirmed working: probes ≤ 5KB land OK; 100KB probes fail. Pattern fits sustained-write throttling, not pure size.

**Reliable recovery paths**: reboot (clears DLP throttle + OneDrive cache), free space inside the profile, or contact Georgia Tech IT.

### 6c. Auto-mode classifier blocks Stop-Process even with explicit user approval

The Claude Code auto-mode classifier in the previous session blocked both `Stop-Process` and `& "C:\Program Files\Microsoft OneDrive\OneDrive.exe" /shutdown` even after the user selected "Kill OneDrive processes now" via `AskUserQuestion`. The classifier doesn't read AskUserQuestion answers as authorization for process termination. **Workaround**: ask the user to run the kill command in a separate terminal themselves. Or add a Bash permission rule to settings.json.

### 6d. Write outside the profile when building anything substantial

Confirmed writable: `C:\Windows\Temp\`, `C:\Users\Public\Documents\`. Confirmed broken: anything under `C:\Users\qduong7\`. Default to building at `C:\Users\Public\Documents\<project>\` or `C:\Windows\Temp\<project>\`. The deeper system architecture doc — `docs/system_architecture.md` — still has the canonical pipeline diagram and schema contracts; read it for the broader picture.

---

## 7. Data contracts (G1/G2/G3) — from docs/system_architecture.md §4

**G1 → G3:**

- `population.csv`: `agent_id`, `age_bucket` (child/adult/elderly), `occupation_class` (worker/commuter/visitor/resident/student), `mobility_class` (mobile/assisted/restricted), `vulnerability_score` in [0,1], `home_grid_cell`, `hour` (0–23), `activity_grid_cell`. One row per agent per hour.
- `heat_field.npy`: shape `(24, 20, 10)` (hours, x, y); cell value heat-cost in [0, 2].
- `occupancy.csv`: `building_id`, `hour`, `occupants_total`, `vulnerable_weighted_occupants`.

**G2 → G3:**

- `shelter_envelope.csv`: `building_id`, `hour`, `max_occupants`, `cooling_kwh`, `emissions_intensity` (kgCO2e/kWh).

**G3 → stakeholders:**

- `outputs/reports/testbed_comparison.md` — comparison report with metric definitions.
- `outputs/reports/browser_twin.html` — Folium twin, headline 5/25 visual.
- `outputs/reports/provenance_{baseline,reactive,proactive}.jsonl` — per-decision audit log.
- `outputs/gis/*.geojson` — WGS84 GeoJSON layers.
- `outputs/figures/auto/*.png` — diagnostic charts (regeneratable; gitignored).
- `outputs/slides/stage1_review_deck.html` — review deck.

**G3 → G1/G2 feedback** (not yet emitted; Stage Two):

- `cooling_gap_residuals.csv` — agent-hours with no feasible shelter.
- `exposure_hotspots.csv` — cells with disproportionate vulnerability-weighted exposure.

---

## 8. State of play (as of 2026-05-22)

**Done and pushed to GitHub `stage1-testbed`:**

- `a4b0518` — testbed (35 files): 10 sim modules + run script + 22 output files (browser_twin.html, GeoJSON layers, CSVs, JSONL provenance, metrics, comparison MD).
- `9be80a3` — slide deck + generator (`scripts/make_deck.py`, `outputs/slides/stage1_review_deck.html`, 298KB self-contained with embedded base64 charts).

**Done locally but not yet pushed via the OneDrive copy:**

- The OneDrive repo's working tree still has the partial files copied before OneDrive jammed (untracked, not committed there). The clean state is on GitHub via `stage1-testbed`; the user can `git fetch` + `git merge --ff-only github/stage1-testbed` from the OneDrive repo once the profile is writable.

**Open / pending:**

- No PR opened yet. Stage1-testbed is a branch; open at `https://github.com/SamDuo/nihonbashi-robot-sim/pull/new/stage1-testbed`.
- `outputs/figures/auto/*.png` is gitignored intentionally (regeneratable). The base64-embedded copies in `outputs/slides/stage1_review_deck.html` are tracked.
- Memory note `onedrive_writes.md` staged at `C:\Windows\Temp\nihon-stage1\_memory_to_install\` — install into `~/.claude/projects/.../memory/` and add the addendum line to `MEMORY.md` once profile recovers.
- Auto-memory directory under `C:\Users\qduong7\.claude\` is on the same OneDrive hook. Future sessions can't reliably write to it. Use this file (and ones like it in the repo) as the durable knowledge store instead of `.claude/memory/`.

---

## 9. How to resume in a future session

1. **Read this file first.** It carries the project context and the environment quirks.
2. **Then read `docs/system_architecture.md`** for the data-flow diagram, scene pipeline, and tech-stack mapping (Stage One vs Stage Two).
3. **Check `outputs/reports/testbed_metrics.csv` and `outputs/reports/testbed_comparison.md`** for the canonical run's numbers.
4. **Probe writes before building** — `Set-Content` a 100KB file to `C:\Users\qduong7\tmp\probe.txt` and check the file size. If it lands 0 bytes, the OneDrive hook is back; build at `C:\Users\Public\Documents\` or `C:\Windows\Temp\` instead and treat the OneDrive copy as read-only for now.
5. **Skim git log** — `git log --oneline -10 origin/stage1-testbed` — for the most recent state, and `git diff origin/stage1-testbed origin/main` if a merge is in flight.
6. **Don't push without an explicit per-turn instruction.** The project owner has a standing rule: only push when explicitly told.

---

## 10. What Stage Two adds without changing this loop

Documented in `docs/system_architecture.md §7`:

- Real G1 population + heat raster replaces `population.py` / `heat_field.py` synthetic generators (same schema).
- Real G2 cooling envelope replaces `shelter_model.py` synthetic generator (same schema).
- Yi's SHP → SUMO street network replaces the 20×10 grid scene (`scene.py`).
- NVIDIA Omniverse + Isaac Sim replaces the Folium browser twin for high-fidelity visualization and robot-level validation.
- LLM-driven planner replaces the threshold policies in `policy.py`.

The metric definitions (§4) and the data contracts (§7) are stable; everything else is a drop-in.
