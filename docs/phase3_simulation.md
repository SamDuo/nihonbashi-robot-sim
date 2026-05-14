# Phase 3 — SUMO/ABM Initial A/B Simulation + Iteration

**Owners:** Yi Tai (sim execution) · Sam (analysis + dashboard) · Xilin (design review of residuals)
**Status:** queued — starts when Phase 2 parameter file lands
**Deliverables:**
1. Paired A/B run set under identical scenarios as Phase 1 (`sim/runs/phase3_initial/`)
2. Comparison report with the six evaluation metrics (`outputs/reports/phase3_comparison.md`, generated)
3. Ranked residual-issue list feeding the next iteration (`docs/phase3_residuals.md`, generated)
4. Variable update PR — what changed for iteration 2

---

## A/B protocol

For each of the 12 scenario × window combinations:

- Side A: Starship baseline parameters (Phase 1)
- Side B: Heat-Support Robot v1 parameters (Phase 2)
- Same RNG seed list, same pedestrian-generation script, same heat-cost field
- 50 replicates per side, paired by seed
- Statistical comparison: paired t-test (or Wilcoxon if non-normal) per metric, with Holm-Bonferroni correction across the six metrics

---

## Six evaluation metrics

Implemented in `analysis/metrics.py`. Each function takes a SUMO/ABM run output and returns a scalar.

| Metric | Definition | Direction |
|---|---|---|
| `labor_substitution_rate` | Fraction of outdoor delivery / patrol tasks executed by robots | ↑ better |
| `heat_exposure_reduction` | Mean cumulative heat-exposure for human-staff agents vs. baseline | ↑ better |
| `service_continuity` | Service uptime during heat-scenario window | ↑ better |
| `delivery_efficiency` | Throughput (tasks completed / wall time) | ↑ better |
| `pedestrian_interference` | Composite: mean detour length + mean speed reduction + docking-conflict count | ↓ better |
| `infrastructure_compatibility` | Penalty for incompatible docking, charging, or service-node use | ↓ better |

---

## Output structure

```
sim/runs/phase3_initial/
├── run_config.json          ← seeds, scenario combos, ABM version
├── side_a/                  ← Starship baseline replicates
│   └── <seed>/
│       ├── trace.csv
│       ├── metrics.json
│       └── log.txt
└── side_b/                  ← Heat-Support Robot v1 replicates
    └── <seed>/
        └── ...
```

`scripts/run_comparison.py` consumes this and writes `outputs/reports/phase3_comparison.md`.

---

## Decision gate to enter Phase 4

Phase 3 may iterate up to 3 times. On each iteration:

1. Diagnose residual issues from the comparison report.
2. Designer (Xilin) reviews; selects which variables to update.
3. Update the proposal column of the variable matrix.
4. Re-run side B with new parameters; side A stays as the Starship anchor.

**Exit conditions (any one):**
- The proposal is Pareto-non-dominated against the baseline on the six metrics, with statistical significance on ≥ 4 metrics.
- Three iterations completed without statistically significant improvement on any new metric.
- Designer signs off with documented rationale in `docs/decisions/`.

On exit, the final proposal parameters and the residual-issue list hand off to Phase 4 (AI + CAD optimization) in the downstream environment.
