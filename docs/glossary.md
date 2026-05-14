# Glossary

| Term | Meaning |
|---|---|
| **ABM** | Agent-Based Model. Microscopic simulation where each agent (pedestrian, robot) follows local rules; macroscopic phenomena emerge. |
| **SUMO** | Simulation of Urban Mobility. Open-source traffic simulator we use for pedestrian and robot routing on a real street network. |
| **Digital twin** | Modifiable, observable virtual environment that mirrors the Nihonbashi scene. |
| **NWS Heat Index** | National Weather Service heat-index formula (apparent temperature from temp + humidity). Used by the parent Tokyo Studio Random Forest classifier. |
| **UTCI** | Universal Thermal Climate Index. International standard for outdoor thermal comfort; under consideration for Phase 4. |
| **CTHI** | Compound Thermal-Health Index. Combines heat + air quality + humidity into a single score. |
| **Service node** | Fixed location where the robot docks for restock, recharge, or transfer. |
| **Friction point** | Specific spatial / temporal event where the robot creates measurable system inefficiency. |
| **Variable matrix** | Canonical table of all variables under study, with baseline and proposal values. |
| **Pareto-non-dominated** | A solution that is no worse than the baseline on every metric and strictly better on at least one. |
| **Iteration** | One full pass through the Phase 3 simulation loop (run A/B → diagnose → update variables). |
| **METI 2023 sidewalk-robot rule** | Japanese regulation classifying sidewalk delivery robots as pedestrians, capped at 6 km/h. |
| **UPDM** | Utility and Pipeline Data Model (Esri). Not used in this repo but referenced for adjacency. |
