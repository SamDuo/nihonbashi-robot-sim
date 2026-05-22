# Testbed comparison — Stage One (5/25)

Three policies on synthetic G1/G2 data matching docs/system_architecture.md sections 4a-4b.

## Metrics table

| scenario   |   cumulative_population_exposure |   vulnerability_weighted_exposure |   mean_peak_hourly_exposure |   sheltered_agent_hours |   shelter_utilization_rate |   unmet_shelter_demand |   cooling_energy_kwh |   cooling_emissions_kgco2e |   equity_gap_ratio |   mean_decision_latency_ms |   provenance_coverage |
|:-----------|---------------------------------:|----------------------------------:|----------------------------:|------------------------:|---------------------------:|-----------------------:|---------------------:|---------------------------:|-------------------:|---------------------------:|----------------------:|
| baseline   |                          4871.15 |                           1990.35 |                      1.8248 |                       0 |                     0      |                   2482 |                 0    |                      0     |             0.9909 |                     0.0009 |                     1 |
| reactive   |                          3325.59 |                           1365.23 |                      1.5277 |                    1066 |                     0.244  |                   1416 |              1224.72 |                    589.345 |             0.9976 |                     0.0025 |                     1 |
| proactive  |                          3277.66 |                           1314.7  |                      1.5608 |                    1144 |                     0.2619 |                   1338 |              1304.81 |                    631.17  |             0.9068 |                     0.0036 |                     1 |

## Metric definitions

- **cumulative_population_exposure** — Sum over agents and hours of (heat_value_in_current_cell * (0 if sheltered else 1)). Lower is better.
- **vulnerability_weighted_exposure** — Same sum but each term multiplied by vulnerability_score. Lower is better.
- **mean_peak_hourly_exposure** — Average over agents of their max hourly exposure across the 24-hour run. Lower is better.
- **sheltered_agent_hours** — Count of (agent, hour) tuples where the agent was inside a shelter. Higher is better.
- **shelter_utilization_rate** — Mean across hours of (occupants_summed / capacity_summed) for all shelters. Target ~0.6-0.85; >0.95 indicates undersupply.
- **unmet_shelter_demand** — Count of policy decisions that wanted shelter but found none feasible. Lower is better.
- **cooling_energy_kwh** — Sum of cooling_kwh across hours weighted by the fraction of capacity used. Cost lever; lower is better all else equal.
- **cooling_emissions_kgco2e** — cooling_energy_kwh weighted by hourly emissions_intensity (kgCO2e/kWh).
- **equity_gap_ratio** — Mean exposure of the top vulnerability quartile divided by mean exposure of the bottom quartile. 1.0 = perfect parity; >1 = inequity; proactive policies should drive this toward 1.
- **mean_decision_latency_ms** — Mean wall-clock time per policy decision in milliseconds. Twin-loop health.
- **provenance_coverage** — Provenance events written divided by (agents * hours). 1.0 = every step audited.

## How to read it

- Lower is better for: cumulative_population_exposure, vulnerability_weighted_exposure, mean_peak_hourly_exposure, unmet_shelter_demand, cooling_energy_kwh, cooling_emissions_kgco2e, equity_gap_ratio (closer to 1.0), mean_decision_latency_ms.
- Higher is better for: sheltered_agent_hours, provenance_coverage.
- shelter_utilization_rate has a target band (≈ 0.6–0.85). Above 0.95 indicates undersupply; below 0.3 indicates the policy isn't moving the right people.

## Headline visual

`outputs/reports/browser_twin.html` is the Folium twin. Open it locally; toggle scenarios from the layer control. Anchored to Nihonbashi 35.6840-35.6852°N, 139.7735-139.7747°E.