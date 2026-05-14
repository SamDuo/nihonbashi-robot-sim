# Phase 2 — Product Conceptual Design Based on Baseline Problems

**Owners:** Xilin Tang (industrial design lead) · Yi Tai (variable parameterization) · Sam (data layer)
**Status:** queued — starts when Phase 1 ranked friction points land
**Deliverables:**
1. Nihonbashi Heat-Support Robot concept brief
2. Variable matrix with "Initial Proposal" column populated (`data/robot_params/variable_matrix.csv`)
3. ABM-readable parameter file (`data/robot_params/heat_support_robot_v1.csv`)
4. Concept renders and module diagram (`design/concept/`)

---

## Design hypothesis

A modular autonomous service robot for extreme-heat support in dense Nihonbashi-type districts. Compact body (680 × 980 × 1050 mm per Xilin's draft), interchangeable cargo module, multi-modal interaction cues, pedestrian-first behavior.

Target tasks:
- Cold-water and supply delivery
- Medicine and emergency-kit drop-off
- Heatstroke first-aid kit deployment
- Information / wayfinding for vulnerable populations

---

## Variables to define (must match Phase 1's column structure)

- Body: width, length, height, mass
- Mobility: max speed (heat-scenario-dependent), turning radius, climb capability
- Service: payload per module, docking method (slot-in vs. lift-off), docking duration, service tasks
- Interaction cues: lighting pattern, screen content, sound profile, motion-rhythm signaling, body-orientation cues
- Behavioral: avoidance rule, peripheral-waiting-zone use, peak-hour throttling, vulnerable-pedestrian detection
- Infrastructure: charging mode, supply-restock cadence, service-node compatibility

Each variable lands as a row in `data/robot_params/variable_matrix.csv`.

---

## AI-assisted concept expansion (Phase 2 workflow)

1. Friction points from Phase 1 become design prompts (e.g. "docking conflicts at service nodes" → "explore peripheral-waiting + lift-off cargo").
2. Generative AI produces 8–12 concept variants (form, module layout, interaction style).
3. Industrial designer (Xilin) selects 2–3 that respect Nihonbashi constraints — pedestrian-first, METI 2023 sidewalk-robot rules, infrastructure compatibility.
4. Selected variants are parameterized into the matrix.

---

## Constraint checklist

- [ ] Body width ≤ 700 mm (Nihonbashi sidewalk minimum widths)
- [ ] Max speed ≤ 6 km/h (METI 2023 sidewalk-robot regulation)
- [ ] Audible + visual intent cues (pedestrian-first design)
- [ ] Heat-tolerant electronics rated to 40 °C+ ambient
- [ ] Charging compatible with existing district infrastructure (or proposed new nodes)
- [ ] Cargo modules swappable in < 60 s by a single operator

---

## Hand-off to Phase 3

Phase 3 consumes the ABM-readable parameter file and runs the proposal under the same scenarios / windows / seeds as Phase 1, then performs paired-difference comparison.
