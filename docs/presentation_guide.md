# Dashboard Presentation Guide

| | |
|---|---|
| **For** | Urban Digital Twins team (Sam Duong, Yi Tai, Xilin Tang, Murugesan Devesh) |
| **Use when** | Showing the Stage One testbed to workshop coordinators (Perry Yang, Subhro, Sei) or to the Urban Risk and Urban Regeneration team leads |
| **Run time** | 4 to 5 minutes for the live walk through; 8 to 10 minutes if you take questions inline |
| **Last updated** | 2026-05-25 |

---

## Before you start

1. Make sure both servers are running.
   - **Data server**: `python scripts/start_terriajs_demo.py` (serves on `http://localhost:8889`)
   - **Streamlit dashboard**: `python -m streamlit run analysis/dashboard.py --server.port 8501`
2. Open two browser tabs:
   - **Dashboard tab**: `http://localhost:8501`
   - **Standalone twin (optional, for full screen presentation)**: `http://localhost:8889/cesium_view.html?scenario=proactive&hour=14&plateau=volumes`
3. On the dashboard, click **Digital Twin** so the 3D view is loaded before you start speaking. PLATEAU tiles take about ten seconds to stream in the first time.
4. Set the controls in the left column to: **Scenario = proactive**, **Hour of day = 14**, **PLATEAU 3D buildings = Volumes**.

---

## The 4 minute live walkthrough

### Step 1. Open the dashboard. Frame the scope. (30 seconds)

> This is the Urban Digital Twins layer of our three group workshop. We do not generate ground truth heat exposure or the cooling envelope. Those come from Urban Risk and Urban Regeneration. We synthesize, decide, and visualize.

Point at the top of the page. Read out the caption that says "Synthetic 20 by 10 Nihonbashi grid. 100 agents. 24 hours. Three policies."

### Step 2. The Digital Twin tab. (1 minute 30 seconds)

> What you are looking at is real Nihonbashi geometry from the Japanese government's PLATEAU 3D city model. Chuo-ku LOD2 buildings, clipped to the Nihonbashi neighborhood boundary you can see outlined in dark blue.

Point at the blue hexagon outline.

> The orange and grey dots are our 100 simulated residents. At hour 14, which is the midday heat peak, eighty three are at work. Seventeen are at shelters. Zero are at home.

Read the status mix in the left panel.

> The three green polygons are the candidate cooling shelters. Their height grows with how many people are sheltering inside, and the color shifts from green to red as utilization rises. At this hour they are still well under capacity.

Move the **Hour of day** slider from 14 to 06 to 18 and back to 14. Let them see the day cycle.

> Now switch the scenario from proactive to baseline.

Click the **baseline** radio. The agents redistribute. The shelters empty out.

> Baseline is what would happen with no intervention. Cooling gap closure rate is zero. Every agent stays at their planned activity location.

Click **reactive**.

> Reactive routes a vulnerable agent to the nearest feasible shelter when ambient heat at their location exceeds a threshold. Thirteen percent exposure reduction.

Click **proactive**.

> Proactive prepositions vulnerable agents three hours ahead based on a forecast lookahead. Seventeen point five percent exposure reduction. That is the headline number for Stage One.

### Step 3. Switch to the Metrics tab. (1 minute)

Click the **Metrics** tab.

> Three headline cards across the top show the cooling gap closure rate for each scenario at end of day. Then we have the six methodology metrics from the Xilin Tang framework. Heat exposure reduction, service continuity, infrastructure compatibility, pedestrian interference, and so on. All three scenarios side by side.

Point at the bar chart.

> Below that, the hourly mean cumulative heat exposure curve. You can see baseline diverges from reactive and proactive around hour 12 as the heat field peaks and the intervention policies kick in.

Point at the line chart.

> On the left we have the cooling gap residuals table. Empty right now because shelter capacity sufficed for every vulnerable agent. When we scale population from one hundred to five hundred in Stage Two, this table will get populated and that becomes feedback to the Urban Regeneration team.

Point at the residuals area.

> On the right, the most recent twenty five decisions from the agentic loop, recorded as JSON Lines. Every decision is auditable. Every agent has a rationale attached.

### Step 4. Show what Stage Two adds. (45 seconds)

> Everything you see uses synthetic data that matches the locked schemas with Urban Risk and Urban Regeneration. When their real data lands, the loaders swap and nothing else changes. Stage Two also moves visualization from this browser based stack to NVIDIA Omniverse on GT CURA HPC and adds robot level validation in NVIDIA Isaac Sim. The headline numbers are reproducible across that transition.

Mention the Stage Two requirements document at `docs/stage2_data_requirements.md` if anyone asks for specifics.

### Step 5. Invite questions. (30 seconds)

> The proposal document at `Group3_Proposal.docx` has the full architecture, six paper citations from the recent literature on heat exposure digital twins, and the Stage Two roadmap. What would be useful to dig into?

---

## What to do if a coordinator asks specific questions

### "How do you know the metrics are correct?"

> Two answers. First, every decision is logged to `outputs/reports/provenance.jsonl`. We can replay any scenario and trace every agent's trajectory. Second, the metric definitions are quoted verbatim from `docs/methodology.md` and implemented in `sim/testbed/metrics.py`. Open the file if you want.

### "What about uncertainty?"

> Stage One uses a single seed for clarity. Stage Two will run fifty paired seed replicates per scenario with Holm Bonferroni correction across the six metrics, as defined in `docs/phase3_simulation.md`.

### "Why these three policies?"

> They span the design space. Baseline tells us what happens with no intervention. Reactive is the minimum viable intervention. Proactive uses forecast lookahead. The gap between baseline and proactive is the upper bound on what an LLM driven agentic planner could achieve in Stage Two.

### "Can I see real Tokyo data?"

> The PLATEAU buildings are real. The 100 agents and heat field are synthetic. We need the heat exposure raster and population engine from Urban Risk to make agents real. We need the N-UBEM and ReOpt outputs from Urban Regeneration to make shelters real. The Stage Two data requirements document spells out exactly what each group owes.

### "How does this connect to the robot?"

> The robot is Phase 5 and 6 of the methodology. Stage One validates that the agentic decision loop reduces heat exposure for the vulnerable population. Once that closes, the design team takes the validated parameters into Phase 4 CAD optimization, then back into Phase 5 ABM verification, then into Phase 6 high fidelity NVIDIA Omniverse with Isaac Sim robot validation.

### "Where can I look without you?"

> Three URLs.
> - Dashboard with controls: <http://localhost:8501>
> - Full screen twin: <http://localhost:8889/cesium_view.html?scenario=proactive&hour=14&plateau=volumes>
> - Architecture document: `nihonbashi-robot-sim/docs/system_architecture.md` (or open the system architecture diagrams ZIP)

---

## Failure recovery

If during the demo Cesium fails or the data server is unreachable:

1. Below the 3D view there is a **2D Folium view** expander. Open it. Same agents and shelters on a clean 2D map. Works without Cesium.
2. Below that there is a **Pydeck 2.5D view** expander. Works without internet.
3. The Metrics tab does not require the 3D view at all. Pivot there.

If Streamlit itself crashes, the standalone Cesium URL above still works and can be opened directly.

---

## What to leave behind after the demo

Three artifacts the stakeholders can take with them:

1. `Group3_Proposal.docx` in the Tokyo Planning Analytics folder, with embedded diagrams and paper citations.
2. `System architecture.zip` in the same folder, with the five Mermaid diagrams and the renderer.
3. The standalone Cesium URL, which works as long as the local data server is running.

If the audience needs something outside the network, the static HTML at `cesium_view.html` plus the `outputs/` folder can be zipped and emailed. They will need to run a small HTTP server locally to view it (one line of Python).
