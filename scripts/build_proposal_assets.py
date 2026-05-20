"""Generate the team proposal .pptx and .docx from the markdown drafts.

Scope: Unified proposal covering ALL SIX PHASES of Xilin Tang's research
methodology (Phases 1-3 data test bed + baseline + A/B comparison, and
Phases 4-6 M&V pipeline). NO timeline or project length is mentioned --
the proposal describes scope, methodology, and deliverables only.

Architecture splits compute (headless on IAC-VLABB-2021 server) from UX
(laptops + browser). NVIDIA Isaac Sim + RTX content is preserved ONLY as
a stretch goal slide / section with explicit constraints, because the
team has no RTX GPU access.

Outputs:
- outputs/slides/team_proposal_deck.pptx  (22 slides)
- outputs/reports/proposal_draft.docx     (7 pages)

Style for slides matches Xilin Tang's Research_XilinTang_0512.pdf.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as PColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches as PInches, Pt as PPt


REPO_ROOT = Path(__file__).resolve().parents[1]
SLIDES_OUT = REPO_ROOT / "outputs" / "slides" / "team_proposal_deck.pptx"
DOCX_OUT = REPO_ROOT / "outputs" / "reports" / "proposal_draft.docx"

SLIDE_TOTAL = 23
TITLE_FONT = "Aptos"
BODY_FONT = "Aptos"

GRAY = PColor(0x6B, 0x6B, 0x6B)
LIGHT_GRAY = PColor(0xB0, 0xB0, 0xB0)
BLACK = PColor(0x10, 0x10, 0x10)


# ---------- slide helpers ----------


def add_chrome(slide, prs, section_tag: str, page_num: int, source: str) -> None:
    line = slide.shapes.add_connector(1, PInches(0.5), PInches(0.95), PInches(12.83), PInches(0.95))
    line.line.color.rgb = BLACK
    line.line.width = Emu(6350)

    tag_box = slide.shapes.add_textbox(PInches(11.5), PInches(0.35), PInches(1.83), PInches(0.3))
    tf = tag_box.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    run = p.add_run()
    run.text = section_tag
    run.font.name = BODY_FONT
    run.font.size = PPt(9)
    run.font.color.rgb = GRAY

    page_box = slide.shapes.add_textbox(PInches(12.0), PInches(7.0), PInches(1.0), PInches(0.3))
    tf = page_box.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    run = p.add_run()
    run.text = f"{page_num} / {SLIDE_TOTAL}"
    run.font.name = BODY_FONT
    run.font.size = PPt(8)
    run.font.color.rgb = LIGHT_GRAY

    src_box = slide.shapes.add_textbox(PInches(0.5), PInches(7.0), PInches(11.0), PInches(0.3))
    tf = src_box.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = source
    run.font.name = BODY_FONT
    run.font.size = PPt(8)
    run.font.color.rgb = LIGHT_GRAY


def add_title(slide, title: str) -> None:
    box = slide.shapes.add_textbox(PInches(0.5), PInches(0.4), PInches(11.0), PInches(0.5))
    tf = box.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = title
    run.font.name = TITLE_FONT
    run.font.size = PPt(22)
    run.font.bold = True
    run.font.color.rgb = BLACK


def add_lead(slide, text: str, top_in: float = 1.15) -> None:
    box = slide.shapes.add_textbox(PInches(0.5), PInches(top_in), PInches(12.33), PInches(0.95))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = text
    run.font.name = BODY_FONT
    run.font.size = PPt(13)
    run.font.bold = True
    run.font.color.rgb = BLACK


def add_bullets(
    slide,
    bullets,
    left_in: float = 0.5,
    top_in: float = 2.25,
    width_in: float = 12.33,
    height_in: float = 4.5,
    font_size: int = 12,
) -> None:
    box = slide.shapes.add_textbox(
        PInches(left_in), PInches(top_in), PInches(width_in), PInches(height_in)
    )
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, text in enumerate(bullets):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = f"•   {text}"
        run.font.name = BODY_FONT
        run.font.size = PPt(font_size)
        run.font.color.rgb = BLACK
        p.space_after = PPt(6)


def add_columns(slide, columns, top_in: float = 2.25, height_in: float = 4.5) -> None:
    n = len(columns)
    page_left = 0.5
    page_width = 12.33
    gap = 0.3
    col_w = (page_width - gap * (n - 1)) / n

    for i, (heading, bullets) in enumerate(columns):
        left = page_left + i * (col_w + gap)
        h_box = slide.shapes.add_textbox(PInches(left), PInches(top_in), PInches(col_w), PInches(0.35))
        tf = h_box.text_frame
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = heading
        run.font.name = BODY_FONT
        run.font.size = PPt(12)
        run.font.bold = True
        run.font.color.rgb = BLACK
        rule = slide.shapes.add_connector(
            1,
            PInches(left),
            PInches(top_in + 0.35),
            PInches(left + col_w * 0.5),
            PInches(top_in + 0.35),
        )
        rule.line.color.rgb = GRAY
        rule.line.width = Emu(3175)
        b_box = slide.shapes.add_textbox(
            PInches(left), PInches(top_in + 0.45), PInches(col_w), PInches(height_in - 0.45)
        )
        tf = b_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        for j, text in enumerate(bullets):
            if j == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()
            run = p.add_run()
            run.text = f"•  {text}"
            run.font.name = BODY_FONT
            run.font.size = PPt(11)
            run.font.color.rgb = BLACK
            p.space_after = PPt(4)


def add_table(slide, headers, rows, top_in: float = 2.2, height_in: float = 4.5) -> None:
    n_cols = len(headers)
    n_rows = len(rows) + 1
    table_shape = slide.shapes.add_table(
        n_rows, n_cols, PInches(0.5), PInches(top_in), PInches(12.33), PInches(height_in)
    )
    table = table_shape.table
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = ""
        p = cell.text_frame.paragraphs[0]
        run = p.add_run()
        run.text = h
        run.font.name = BODY_FONT
        run.font.size = PPt(10)
        run.font.bold = True
        run.font.color.rgb = PColor(0xFF, 0xFF, 0xFF)
        cell.fill.solid()
        cell.fill.fore_color.rgb = PColor(0x33, 0x33, 0x33)
    for r, row in enumerate(rows, start=1):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            run = p.add_run()
            run.text = value
            run.font.name = BODY_FONT
            run.font.size = PPt(9)
            run.font.color.rgb = BLACK


# ---------- slide content ----------


def slide_01_cover(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Smart City Service Robots under Extreme Climate Challenges")
    add_lead(
        s,
        "Team proposal -- full six-stage research methodology covering baseline ABM, concept "
        "design, A/B simulation, AI-assisted CAD optimization, ABM re-validation, and "
        "browser-deliverable digital twin. Nihonbashi, Tokyo case study.",
    )
    add_bullets(
        s,
        [
            "Cross-scale industrial-design framework combining ABM / Digital Twin and Industrial Design",
            "Research scenario: Nihonbashi, Tokyo  --  200 m hero scene inside 500 m station catchment",
            "Keywords: Extreme Climate · Aging Society · Human Heat Exposure · Urban Delivery · Emergency Services",
            "Authors: Sam M. Duong  ·  Xilin Tang  ·  Yi Tai  ·  Qinghao  ·  Advisor: TBD",
            "Repository: github.com/SamDuo/nihonbashi-robot-sim",
        ],
        top_in=2.6,
    )
    add_chrome(s, prs, "Proposal Cover", 1, "Based on Xilin Tang's six-stage research methodology document.")


def slide_02_summary(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Executive Summary")
    add_lead(
        s,
        "Run the complete six-stage methodology end to end -- from baseline ABM through "
        "high-fidelity browser-deliverable twin -- using only tools and compute the team has "
        "access to today.",
    )
    add_bullets(
        s,
        [
            "Phase 1  --  Baseline ABM of an existing Starship-type robot in the Nihonbashi scene",
            "Phase 2  --  Heat-Support Robot concept + variable matrix translating friction points into design",
            "Phase 3  --  A/B SUMO + ABM simulation with iterative feedback against the baseline",
            "Phase 4  --  AI + CAD optimization in Rhino / Grasshopper, Fusion 360 engineering pass",
            "Phase 5  --  ABM re-simulation at scale on IAC-VLABB-2021  --  200+ replicates per scenario",
            "Phase 6  --  Browser-deliverable 3D twin + geometric sensor / motion validation",
            "Stretch  --  NVIDIA Isaac Sim hero video IF dedicated RTX hardware materializes",
        ],
    )
    add_chrome(s, prs, "Summary", 2, "Architecture aligned to IAC-VLABB-2021 capacity + GT-licensed software stack.")


def slide_03_problem(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "The Compound Problem  --  Extreme Climate x Aging Society")
    add_lead(
        s,
        "Tokyo's compound risk  --  extreme heat compounded by an aging population  --  is "
        "increasing faster than passive infrastructure (cooling shelters, ambulance dispatch) "
        "can adapt.",
    )
    add_bullets(
        s,
        [
            "Heat-island effect intensified by high humidity and dense construction",
            "Outdoor workers and elderly residents bear disproportionate heat-exposure burden",
            "Fixed cooling shelters cover only fragments of Nihonbashi",
            "Service robots are the most direct lightweight intervention -- mobile, modular, dispatchable",
            "Existing designs (Starship-type) have not been tested against Nihonbashi-specific scenarios",
            "Without a reproducible test bed, design decisions are anecdotal -- not evidence-based",
        ],
    )
    add_chrome(s, prs, "Context", 3, "Source: Xilin Tang slides 2-3; methodology PDF Phase One rationale.")


def slide_03b_rqs(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Research Questions")
    add_lead(s, "Three questions, each anchored to a part of the methodology.")
    add_columns(
        s,
        [
            (
                "RQ1  --  Phases 1-3",
                [
                    "Can a Nihonbashi-specific service robot reduce human heat exposure during extreme heat without making sidewalks worse for pedestrians?",
                    "Build a baseline ABM of a Starship-type robot in the catchment",
                    "Identify macroscopic friction points (detours, docking, speed mismatches)",
                    "Translate frictions into the Heat-Support Robot concept + variable matrix",
                    "Run A/B simulation; iterate until Pareto-non-dominated on six metrics",
                ],
            ),
            (
                "RQ2  --  Phases 4-5",
                [
                    "Do the simulation gains hold up once the robot is designed as a real, manufacturable thing?",
                    "Convert the variable matrix into a parametric Rhino + Fusion 360 CAD model",
                    "Re-abstract CAD geometry into ABM parameters",
                    "Re-run A/B at scale on the VLAB server (200+ replicates per scenario)",
                    "Verify gains with statistical significance on >= 4 of 6 metrics",
                ],
            ),
            (
                "RQ3  --  Phase 6",
                [
                    "Can we show all of this in a browser-based 3D twin that planners and residents actually understand?",
                    "Assemble the 500 m catchment as a 3D scene in ArcGIS Urban or CesiumJS",
                    "Overlay heat-cost field, robot trajectories, vulnerable population, service nodes",
                    "Validate sensor coverage + motion geometrically in Mesa with Shapely",
                    "Demo to stakeholders; collect structured feedback",
                ],
            ),
        ],
    )
    add_chrome(s, prs, "Research Questions", 4, "Source: team RQ framing 2026-05-19.")


def slide_04_methodology(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Six-Stage Research Methodology")
    add_lead(
        s,
        "A closed-loop workflow from problem identification through high-fidelity validation. "
        "Each phase produces a typed artifact the next phase consumes.",
    )
    add_table(
        s,
        ["Phase", "Name", "Primary task"],
        [
            ["1", "Baseline ABM testing", "Abstract a Starship-type robot into ABM; surface macroscopic friction points"],
            ["2", "Product concept design", "Translate friction points into Heat-Support Robot concept + variable matrix"],
            ["3", "Initial A/B simulation", "SUMO + ABM comparison of baseline vs. proposal; iterate the design"],
            ["4", "AI + CAD optimization", "Convert ABM output into manufacturable CAD model (Rhino + Fusion 360)"],
            ["5", "ABM re-simulation verification", "Verify macroscopic gains hold under CAD-derived parameters"],
            ["6", "High-fidelity digital twin", "Browser-deliverable 3D scene + geometric sensor / motion validation"],
        ],
        top_in=2.1,
        height_in=4.5,
    )
    add_chrome(s, prs, "Methodology", 5, "Source: methodology PDF Section 7; Xilin slide 8.")


def slide_05_scales(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Spatial Scope  --  Nested Scales for Three Systems")
    add_lead(
        s,
        "Mobility, resilience, and robot service each have a natural scale. We use three nested "
        "rings so each system is observed where its dynamics actually occur.",
    )
    add_table(
        s,
        ["Ring", "Size", "System captured", "Role"],
        [
            ["Inner  --  hero scene", "~200 m segment", "Visualization detail", "Photo-quality renders + close-ups"],
            ["Middle  --  service catchment", "~500 m around station", "Mobility OD + resilience integral + robot routes", "ABM agent simulation + Pareto comparison (Phases 1, 3, 5)"],
            ["Outer  --  district context", "Full Nihonbashi", "Policy + stakeholder framing", "ArcGIS dashboard + map"],
        ],
        top_in=2.1,
        height_in=2.6,
    )
    add_bullets(
        s,
        [
            "Three systems intersect at the station-catchment scale  --  not the street segment",
            "Inner 200 m is a focal sample of the catchment, not the operational boundary",
            "Candidate catchments: Nihonbashi Station or Mitsukoshi-mae Station (Tokyo Metro)",
            "ABM compute at the catchment scale is trivially fast on the IAC-VLABB-2021 server",
        ],
        top_in=4.9,
        height_in=2.0,
        font_size=11,
    )
    add_chrome(s, prs, "Spatial Scope", 6, "Source: team review of system-boundary question.")


def slide_06_phase1(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Phase 1  --  Starship Baseline ABM Test")
    add_lead(
        s,
        "Abstract an existing sidewalk delivery robot into ABM-readable parameters. Drop it into "
        "the Nihonbashi catchment. Surface macroscopic friction points that motivate the design.",
    )
    add_columns(
        s,
        [
            (
                "Starship parameters (abstracted)",
                [
                    "Body 569 x 697 x 616 mm",
                    "Max speed 6 km/h (METI 2023 cap)",
                    "Turning radius ~ 0.8 m",
                    "Payload 10 kg, docking 30 s",
                    "Reactive avoidance behavior",
                ],
            ),
            (
                "Friction points we will observe",
                [
                    "Pedestrian detours from docking",
                    "Mainline / robot trajectory intersections",
                    "Docking conflicts at service nodes",
                    "Speed mismatches with crowd flow",
                    "Task delays under heat conditions",
                    "Heat-exposure overlap (shade vs. heat island)",
                ],
            ),
        ],
    )
    add_chrome(s, prs, "Phase 1", 7, "Source: methodology PDF Phase One; Xilin slide 9.")


def slide_07_heatfield(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Heat-Cost Field  --  GIS Bridge from Phase 1-3 Classifier into ABM")
    add_lead(
        s,
        "The Random Forest heat-scenario classifier from the parent Tokyo Studio repo joins the "
        "OSM sidewalk graph and becomes a scalar field consumed by every agent in the ABM.",
    )
    add_bullets(
        s,
        [
            "Per-parcel heat-scenario label (Low / Moderate / High / Extreme) from the Tokyo Studio RF classifier",
            "Spatial join to OSM sidewalk segments by centroid intersection",
            "Compute heat_cost = base_cost x (1 + heat_factor)  with factor in {0.0, 0.5, 1.0, 1.5}",
            "Write to ABM as an edge attribute",
            "Pedestrian agents use heat_cost in route choice (weighted Dijkstra)",
            "Robot uses heat_cost for service-path optimization",
            "Per-agent heat_exposure accumulator integrates heat_cost x dwell_time along trajectory",
            "Script: scripts/build_heat_cost_field.py  --  Sam owns",
        ],
    )
    add_chrome(s, prs, "Phase 1 Detail", 8, "Source: docs/phase1_baseline.md and parent Tokyo Studio repo.")


def slide_08_phase2(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Phase 2  --  Heat-Support Robot Concept Design")
    add_lead(
        s,
        "Transform Phase 1 friction points into a design hypothesis: a modular autonomous service "
        "robot purpose-built for extreme-heat support in dense Nihonbashi-type districts.",
    )
    add_columns(
        s,
        [
            (
                "Body + mobility",
                [
                    "Body ~ 680 x 980 x 1050 mm",
                    "Heat-resilient electronics 40 C+",
                    "Speed throttled in dense windows",
                    "Tighter turning radius (~ 0.6 m)",
                    "Lift-off docking module",
                ],
            ),
            (
                "Service modules",
                [
                    "Cold water + supply delivery",
                    "Medicine + first-aid kit drop-off",
                    "Heatstroke response kit",
                    "Information / wayfinding for elderly",
                    "Modular cargo bays, swap < 60 s",
                ],
            ),
            (
                "Interaction cues",
                [
                    "Directional intent-light strip",
                    "Top-mounted status screen",
                    "Soft chime on docking",
                    "Slow-for-crowd motion rhythm",
                    "Vulnerable-pop detection mode",
                ],
            ),
        ],
    )
    add_chrome(s, prs, "Phase 2", 9, "Source: methodology PDF Phase Two; Xilin slide 11.")


def slide_09_matrix(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Variable Matrix  --  Contract Across All Six Phases")
    add_lead(
        s,
        "One CSV is the single source of truth. Each iteration of Phase 3 fills a new column. "
        "Phases 4-6 consume the converged final column.",
    )
    add_table(
        s,
        ["Column", "Meaning"],
        [
            ["category", "product / task / design cue / environmental / human behavior"],
            ["variable", "snake_case variable name"],
            ["unit", "mm, km/h, s, enum, etc."],
            ["baseline_value", "Starship value from Phase 1"],
            ["proposal_v1_value", "Heat-Support Robot v1 from Phase 2"],
            ["proposal_v2_value, v3_value", "After Phase 3 iterations 1, 2"],
            ["final_value", "Converged value handed off to Phase 4 CAD"],
            ["design_rationale", "Why the proposal differs from baseline"],
            ["friction_point_ids", "Phase 1-3 friction points motivating this row"],
            ["owner", "Team member who edits this row"],
        ],
        top_in=2.1,
        height_in=4.5,
    )
    add_chrome(s, prs, "Variable Matrix", 10, "Source: data/robot_params/variable_matrix.csv; docs/variable_matrix.md.")


def slide_10_phase3(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Phase 3  --  Initial A/B Simulation Protocol")
    add_lead(
        s,
        "Drop the Heat-Support Robot proposal into the same Nihonbashi scene as the Starship "
        "baseline. Same scenarios, same windows, same RNG seeds. Paired statistics.",
    )
    add_bullets(
        s,
        [
            "Scene: 500 m station catchment (with 200 m hero zone)",
            "Scenarios: 4 heat scenarios (cool / moderate / high / extreme) x 3 traffic windows (morning peak / midday / afternoon heat)  =  12 combinations",
            "Replicates: 50+ paired per combination per side, with matched RNG seeds",
            "Side A: Starship baseline parameters     Side B: Heat-Support Robot v1 parameters",
            "Statistical analysis: paired t-test or Wilcoxon, Holm-Bonferroni correction across six metrics",
            "Output: outputs/reports/phase3_comparison.md and ranked residual-issue list",
            "Run convention: sim/runs/<phase>_<batch>/<side>/<seed>/  with run_config.json provenance",
        ],
    )
    add_chrome(s, prs, "Phase 3", 11, "Source: methodology PDF Phase Three; docs/phase3_simulation.md.")


def slide_11_metrics(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Six Evaluation Metrics  --  Pareto, Not Weighted Sum")
    add_lead(
        s,
        "Six independent metrics, scored per replicate. Pareto-non-dominated means: not worse than "
        "baseline on any metric AND strictly better on at least one. Preserves trade-offs instead "
        "of hiding them in a weighted score.",
    )
    add_table(
        s,
        ["Metric", "Direction", "Definition"],
        [
            ["Labor Substitution Rate", "Up", "Fraction of outdoor delivery / patrol / resupply replaced by robots"],
            ["Heat Exposure Reduction", "Up", "Cumulative human-staff heat exposure reduction vs. baseline"],
            ["Service Continuity", "Up", "Service uptime during heat-scenario window"],
            ["Delivery Efficiency", "Up", "Tasks completed per wall hour"],
            ["Pedestrian Interference", "Down", "Detour length + speed reduction + docking conflicts"],
            ["Infrastructure Compatibility", "Down", "Penalty for incompatible docking, charging, service-node use"],
        ],
        top_in=2.1,
        height_in=4.3,
    )
    add_chrome(s, prs, "Metrics", 12, "Source: Xilin slide 10; analysis/metrics.py.")


def slide_12_loop(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Phase 3 Iterative Feedback Loop")
    add_lead(
        s,
        "Phase 3 is the inner loop of the methodology. Diagnose residuals, update variables, "
        "re-run. Exit on convergence -- not on time budget.",
    )
    add_bullets(
        s,
        [
            "Run side B (proposal) against side A (baseline) with paired seeds",
            "Compute the six metrics for every replicate; paired-difference statistics",
            "Designer (Xilin) reviews ranked residual-issue list with the team",
            "Selectively update the proposal column of the variable matrix",
            "Re-run side B with new parameters; side A stays anchored to Starship",
            "Up to three iterations before escalating to Phase 4",
            "Exit criteria: (a) Pareto-non-dominated with sig on >= 4 of 6 metrics, OR (b) 3 iterations w/o significant improvement, OR (c) designer override with documented rationale",
            "Hand-off: final variable column + residual issues  -->  Phase 4",
        ],
    )
    add_chrome(s, prs, "Phase 3 Loop", 13, "Source: methodology PDF Phase Three; docs/methodology.md exit-criteria.")


def slide_13_phase4(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Phase 4  --  AI + CAD Optimization")
    add_lead(
        s,
        "Translate the converged variable matrix into a parametric CAD model. Generative AI "
        "proposes; Xilin selects and integrates; CAD locks down dimensions and manufacturability.",
    )
    add_bullets(
        s,
        [
            "AI step  --  summarize friction points; propose form, module placement, docking strategy, sensor placement",
            "Designer step (Xilin)  --  select, critique, integrate against Nihonbashi + METI 2023 sidewalk-robot rules",
            "CAD step  --  Rhino + Grasshopper primary (Xilin's existing tool), Fusion 360 (educational) for engineering pass",
            "Round-trip mapping  --  every variable matrix row maps to a Rhino / Grasshopper parameter",
            "Output  --  .3dm + .stp neutral export + .gltf for browser-side display",
            "Acceptance  --  manufacturability review passes; every variable maps cleanly to a CAD parameter",
        ],
    )
    add_chrome(s, prs, "Phase 4", 14, "Source: methodology PDF Phase Five.")


def slide_14_phase5(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Phase 5  --  ABM Re-simulation at Scale on IAC-VLABB-2021")
    add_lead(
        s,
        "Re-run the A/B comparison with CAD-derived parameters. 72 logical CPUs + 768 GB RAM "
        "let us scale from 50 replicates per scenario to 200+, finishing in hours instead of days.",
    )
    add_bullets(
        s,
        [
            "Re-abstract CAD-derived geometry into ABM parameters: width, length, speed, turning radius, docking duration",
            "Three-tier comparison: Starship baseline (Phase 1) · Heat-Support v3 (Phase 3) · CAD-optimized (Phase 4)",
            "Scale up: 200+ replicates per scenario across the full 500 m catchment",
            "Parallelization: ~36 simultaneous Mesa workers on the VLAB server",
            "Same six metrics; alpha = 0.05, power >= 0.8 thanks to the higher replicate count",
            "Goal: confirm Pareto-non-dominance and statistical significance hold on >= 4 of 6 metrics",
            "Output: outputs/reports/phase5_revalidation.md with three-way Pareto + parameter-sensitivity sweeps",
        ],
    )
    add_chrome(s, prs, "Phase 5", 15, "Source: methodology PDF Phase Six (Part 1); IAC-VLABB-2021 compute confirmation.")


def slide_15_phase61(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Phase 6.1  --  Browser-Deliverable 3D Twin")
    add_lead(
        s,
        "Deliver a 3D twin of the 500 m catchment that any stakeholder can open in a browser  --  "
        "no client GPU, no plugin, no install. Primary: ArcGIS Experience Builder. Alternative: "
        "CesiumJS web app.",
    )
    add_bullets(
        s,
        [
            "PLATEAU LOD2 across the full catchment  -->  USD / glTF tiles served from the VLAB server",
            "Sidewalk + heat-cost field  -->  ArcGIS feature service / Cesium 3D Tiles overlay",
            "Animated robot trajectories  --  played back from Phase 5 simulation traces",
            "Pedestrian density heatmap  --  per-scenario, time-animated",
            "Toggleable layers: heat scenario, robot fleet, vulnerable population, service nodes, friction-point overlays",
            "Primary: ArcGIS Urban scene  -->  Experience Builder app (matches existing Tokyo Studio pipeline)",
            "Alternative: CesiumJS open-source twin (more programmable, browser-native)",
            "Trade-off: production-quality, not photoreal. LOD2 is sufficient for stakeholder map view.",
        ],
    )
    add_chrome(s, prs, "Phase 6.1", 16, "Source: ArcGIS Urban + CesiumJS docs; matches existing Tokyo Studio publishing pipeline.")


def slide_16_phase62(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Phase 6.2  --  Geometric Sensor + Motion Validation")
    add_lead(
        s,
        "Validate the question that actually matters  --  'do the sensors see what they need to "
        "see, and does the robot fit where it needs to fit?'  --  without expensive photoreal "
        "physics. Pure geometry in Mesa.",
    )
    add_bullets(
        s,
        [
            "Robot footprint  --  imported from Rhino CAD as 2D polygon with per-segment turning kinematics",
            "Sensor coverage as 2D polygons: camera vision cones, lidar range disc, ultrasonic ring  --  Shapely",
            "Compute coverage % per service-node approach, blind-spot risk per docking maneuver",
            "Motion validation: turning radius, docking, peripheral-waiting, slope handling (proxied from elevation)",
            "Acceptance: trajectories within 0.5 m of CAD-specified turning radius; coverage gaps identified per service node",
            "What this validates: 'does the sensor placement work?'  --  the load-bearing question",
            "What this does NOT validate: photoreal sensor fidelity, RL policies, real-hardware transfer",
        ],
    )
    add_chrome(s, prs, "Phase 6.2", 17, "Source: Mesa + Shapely approach replacing NVIDIA Isaac Sim photoreal stack.")


def slide_17_stretch(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Stretch Goal  --  NVIDIA Isaac Sim Hero Demo (Conditional)")
    add_lead(
        s,
        "IF dedicated RTX hardware materializes, we add a single 60-90 second Isaac Sim hero video. "
        "NOT load-bearing for the research conclusions. Hard constraints below.",
    )
    add_columns(
        s,
        [
            (
                "Hard constraints (all must be true)",
                [
                    "Dedicated RTX 4080+ GPU  --  IAC-VLABB-2021 has none",
                    "Windows 10/11 or Ubuntu 22/24  --  NOT Server 2019",
                    "16 GB+ VRAM, 64 GB+ RAM, 500 GB SSD",
                    "Driver Linux 580.65+ or Windows 580.88+",
                    "Team learning curve for Isaac Sim (unfamiliar tool)",
                    "Robot URDF export from Rhino (Xilin time)",
                ],
            ),
            (
                "If unlocked  --  what we deliver",
                [
                    "60-90 sec hero video: robot navigating peak-commute crowd under heat",
                    "Crude URDF (primitive boxes / cylinders)  --  not photoreal CAD",
                    "Kinematic motion validation only  --  no sensor fidelity",
                    "Visual impact for final demo; not new research evidence",
                    "Possible hosts: GT IDEaS / PACE, NVIDIA Inception, personal RTX desktop",
                ],
            ),
        ],
    )
    add_chrome(s, prs, "Stretch", 18, "Source: NVIDIA Isaac Sim system requirements + IAC-VLABB-2021 DxDiag.")


def slide_18_inventory(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Data Inventory  --  What We Have")
    add_lead(s, "Seven primary layers exist today. Quality stars reflect readiness across all six phases.")
    add_table(
        s,
        ["#", "Layer", "Source", "Format", "Quality", "Owner"],
        [
            ["1", "Heat scenarios (RF classifier)", "Parent Tokyo Studio repo", "CSV / GeoJSON", "****", "Sam, Qinghao"],
            ["2", "Pedestrian GPS visits", "Nihonbashi 2023 study", "CSV", "***", "Yi Tai"],
            ["3", "OSM sidewalk graph", "OSMnx", "GraphML / .net.xml", "****", "Yi Tai"],
            ["4", "PLATEAU CityGML LOD1/LOD2", "PLATEAU VIEW 4.0", "CityGML", "****", "Sam"],
            ["5", "Elderly pop per parcel", "e-Stat + Tokyo Metro", "Shapefile", "****", "Sam, Qinghao"],
            ["6", "Evacuation shelters", "Tokyo Open Data", "CSV", "****", "Sam"],
            ["7", "Starship robot specs", "Public spec", "CSV", "**", "Yi Tai"],
        ],
        top_in=2.1,
        height_in=4.5,
    )
    add_chrome(s, prs, "Data: Inventory", 19, "Source: data/README.md + parent Tokyo Studio inventory.")


def slide_19_gaps(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Data Gaps  --  What We Need to Acquire or Build")
    add_lead(s, "Critical gaps block specific phases. Should-have gaps lift fidelity but are not required.")
    add_columns(
        s,
        [
            (
                "Critical (block downstream phases)",
                [
                    "1. Weather forecast (6-48 hr) for proactive dispatch  --  Phase 1-3",
                    "2. Tokyo Fire Dept heatstroke transport data  --  vulnerable-pop modeling",
                    "3. METI 2023 sidewalk-robot regulation  --  design constraint",
                    "4. Pedestrian behavior under heat (GPS by temp bin)  --  Phase 3",
                    "5. Per-segment sidewalk widths  --  Phase 3, Phase 6.2",
                    "6. PLATEAU LOD2 catchment USD/glTF tiles  --  Phase 6.1",
                    "7. Robot CAD source from Rhino  --  Phase 5, Phase 6",
                    "8. Sensor specs (FOV, lidar range, ultrasonic placement)  --  Phase 6.2",
                ],
            ),
            (
                "Should have",
                [
                    "9. e-Stat 6th mesh (125 m) demographic resolution",
                    "10. WBGT  <->  NWS Heat Index reconciliation",
                    "11. Vulnerable-pop dwell-time map",
                    "12. Nihonbashi service-node inventory (CVS, vending, toilets, transit exits)",
                    "13. Japanese-language signage overlay",
                    "14. Pre-rendered Blender hero shots for slides + video",
                    "15. (Stretch only) Photoreal CAD for Isaac Sim",
                ],
            ),
        ],
    )
    add_chrome(s, prs, "Data: Gaps", 20, "Source: team M&V triage; methodology PDF Phase One data layer.")


def slide_20_compute(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Compute Architecture  --  Server + Laptops, No GPU Required")
    add_lead(
        s,
        "IAC-VLABB-2021 (Xeon Gold 6254, 72 logical CPUs, 768 GB RAM) does the heavy ABM. Team "
        "laptops drive UX and light 3D. Stakeholder browsers consume the output.",
    )
    add_table(
        s,
        ["Resource", "Specification", "Role"],
        [
            ["IAC-VLABB-2021 server", "Xeon Gold 6254 x 2 sockets · 36 physical / 72 logical CPUs · 768 GB RAM · Windows Server 2019 · no GPU", "Headless compute + hosting: ABM runs (Phases 1, 3, 5), data prep, Cesium tile server, Flask backend"],
            ["Sam laptop", "Standard student / research laptop", "ArcGIS Pro, browser viewing, Blender renders, slide / doc work"],
            ["Xilin laptop", "Standard laptop with Rhino license", "CAD modeling in Rhino + Grasshopper (Phase 4)"],
            ["Yi Tai laptop", "Standard laptop", "Python / Mesa development, ABM debugging at small scale"],
            ["Qinghao laptop", "Standard laptop", "Thermal validation, browser viewing"],
            ["Stakeholder devices", "Any browser, any device", "View Experience Builder / Cesium twin"],
        ],
        top_in=2.1,
        height_in=4.5,
    )
    add_chrome(s, prs, "Compute", 21, "Source: DxDiag of IAC-VLABB-2021 + GT software inventory.")


def slide_21_tooling(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Tooling Stack and Team / RACI")
    add_lead(s, "Every tool is free, educational, or already GT-licensed. Four contributors, async-first workflow.")
    add_columns(
        s,
        [
            (
                "Tooling by phase",
                [
                    "Phases 1, 3, 5  --  Python · Mesa · SUMO · GeoPandas · scikit-learn",
                    "Phase 2  --  team review + AI assist for concept expansion",
                    "Phase 4  --  Rhino + Grasshopper · Fusion 360 (edu) · Blender",
                    "Phase 6.1  --  ArcGIS Urban · Experience Builder · CesiumJS",
                    "Phase 6.2  --  Mesa + Shapely · GeoPandas",
                    "Hosting  --  Flask · Streamlit · ArcGIS Online",
                    "Stretch  --  NVIDIA Isaac Sim (conditional)",
                ],
            ),
            (
                "Team and RACI",
                [
                    "Sam (M&V lead): R/A for data, GIS, twin, server orchestration, slides",
                    "Xilin (Design lead): R/A for Phase 2 concept, Phase 4 CAD, materials",
                    "Yi Tai (ABM lead): R/A for Phases 1, 3, 5 simulation + metrics + Phase 6.2",
                    "Qinghao (Domain): C for heat-risk, thermal validation, vulnerable-pop",
                    "Advisor: I on all workstreams; sign-off on milestone reviews",
                ],
            ),
        ],
    )
    add_chrome(s, prs, "Tooling + Team", 22, "Source: existing GT software inventory; CONTRIBUTING.md ownership map.")


def slide_22_decisions(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "Decisions, Asks, Risks")
    add_lead(s, "Four risks. Light asks. Four decisions to lock the proposal.")
    add_columns(
        s,
        [
            (
                "Top risks + mitigations",
                [
                    "VLAB admin / firewall lockdown  --  confirm dev shell + outbound network with IT early",
                    "Stage 4 CAD lags Phase 3 hand-off  --  parameter-only Phase 5 dry run while CAD in flight",
                    "Browser performance at full crowd density  --  aggregate to heatmap; tile pyramids fallback",
                    "LOD2 underwhelms stakeholders  --  Blender hero shots provide the wow moment",
                ],
            ),
            (
                "Asks + decisions",
                [
                    "Asks: VLAB server dev access (Python env, Docker, outbound ports, shared storage)",
                    "Asks: ArcGIS Online credits (~$50); stakeholder demo slot; weekly 30-min team sync",
                    "Stretch ask (conditional): RTX 4080+ machine IF Isaac Sim demo is approved",
                    "Decisions: approve six-phase scope; approve RACI; approve VLAB access; approve repo workflow",
                ],
            ),
        ],
    )
    add_chrome(s, prs, "Next Steps", 23, "Source: team proposal. Repo: github.com/SamDuo/nihonbashi-robot-sim")


def build_pptx() -> Path:
    prs = Presentation()
    prs.slide_width = PInches(13.33)
    prs.slide_height = PInches(7.5)

    for fn in [
        slide_01_cover, slide_02_summary, slide_03_problem,
        slide_03b_rqs, slide_04_methodology, slide_05_scales,
        slide_06_phase1, slide_07_heatfield, slide_08_phase2,
        slide_09_matrix, slide_10_phase3, slide_11_metrics,
        slide_12_loop, slide_13_phase4, slide_14_phase5,
        slide_15_phase61, slide_16_phase62, slide_17_stretch,
        slide_18_inventory, slide_19_gaps, slide_20_compute,
        slide_21_tooling, slide_22_decisions,
    ]:
        fn(prs)

    SLIDES_OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(SLIDES_OUT)
    return SLIDES_OUT


# ---------- docx helpers ----------


def add_heading(doc, text: str, size_pt: int = 14) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(size_pt)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x10, 0x10, 0x10)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)


def add_para(doc, text: str, italic: bool = False, size_pt: int = 11) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(size_pt)
    run.font.italic = italic
    p.paragraph_format.space_after = Pt(6)


def add_bullet(doc, text: str) -> None:
    p = doc.add_paragraph(text, style="List Bullet")
    for run in p.runs:
        run.font.name = "Calibri"
        run.font.size = Pt(11)


def add_dtable(doc, headers, rows) -> None:
    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.style = "Light Grid Accent 1"
    for c, h in enumerate(headers):
        cell = table.rows[0].cells[c]
        cell.text = h
        for p in cell.paragraphs:
            for run in p.runs:
                run.font.bold = True
                run.font.size = Pt(10)
    for r, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            cell = table.rows[r].cells[c]
            cell.text = val
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(10)
    doc.add_paragraph()


# ---------- docx content ----------


def build_docx() -> Path:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    title = doc.add_paragraph()
    r = title.add_run("Smart City Service Robots under Extreme Climate Challenges")
    r.bold = True
    r.font.size = Pt(18)
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_para(doc, "Team proposal -- full six-stage research methodology (Phases 1-6)", italic=True, size_pt=12)
    add_para(doc, "Authors: Sam M. Duong, Xilin Tang, Yi Tai, Qinghao  --  Advisor: TBD")
    add_para(doc, "Repository: https://github.com/SamDuo/nihonbashi-robot-sim")
    add_para(doc, "Status: Draft v0.4 -- unified six-phase proposal", italic=True, size_pt=10)

    # Page 1
    add_heading(doc, "1. Executive Summary, Context, and Methodology Overview", size_pt=15)
    add_heading(doc, "Summary", size_pt=12)
    add_para(
        doc,
        "We propose to run the full six-stage research methodology authored by Xilin Tang, end to "
        "end, for the Nihonbashi service-robot study. The work moves from baseline ABM testing of "
        "an existing Starship-type sidewalk delivery robot, through industrial-design translation "
        "into a new Heat-Support Robot concept, through paired A/B simulation that surfaces "
        "system-level gains, through AI-assisted CAD optimization, through statistically rigorous "
        "ABM re-simulation at scale, and finally to a browser-deliverable digital twin that any "
        "stakeholder can interact with. The architecture splits compute (heavy ABM and data work "
        "on the IAC-VLABB-2021 server, 72 logical CPUs and 768 GB RAM) from UX (laptops and "
        "browsers). The proposal uses only tools the team already has access to, with NVIDIA "
        "Isaac Sim retained as a stretch goal conditional on dedicated RTX hardware.",
    )
    add_heading(doc, "Why this study, and why Nihonbashi", size_pt=12)
    add_para(
        doc,
        "Tokyo's compound risk -- extreme heat compounded by an aging population -- is increasing "
        "faster than passive infrastructure (cooling shelters, ambulance dispatch) can adapt. "
        "Outdoor workers and elderly residents bear a disproportionate heat-exposure burden; "
        "fixed cooling shelters cover only fragments of Nihonbashi; ambulance dispatch is "
        "reactive rather than preventive. Service robots are the most direct lightweight "
        "intervention an urban service system can offer -- mobile, modular, dispatchable -- but "
        "existing designs have not been tested against Nihonbashi-specific scenarios in any "
        "reproducible way. This study fills that gap with a rigorous, simulation-first methodology.",
    )
    add_heading(doc, "Six-stage methodology", size_pt=12)
    add_dtable(
        doc,
        ["Phase", "Name", "Primary task"],
        [
            ["1", "Baseline ABM testing", "Abstract a Starship-type robot into ABM; surface macroscopic friction points"],
            ["2", "Product concept design", "Translate friction points into Heat-Support Robot concept + variable matrix"],
            ["3", "Initial A/B simulation", "SUMO + ABM comparison of baseline vs. proposal; iterate the design"],
            ["4", "AI + CAD optimization", "Convert ABM output into manufacturable CAD (Rhino + Fusion 360)"],
            ["5", "ABM re-simulation verification", "Verify macroscopic gains hold under CAD-derived parameters"],
            ["6", "High-fidelity digital twin", "Browser-deliverable 3D scene + geometric sensor / motion validation"],
        ],
    )
    add_heading(doc, "Research questions", size_pt=12)
    add_para(
        doc,
        "Three questions frame the work. Each is anchored to a specific part of the methodology.",
    )
    add_para(
        doc,
        "RQ1 -- Can a Nihonbashi-specific service robot reduce human heat exposure during extreme "
        "heat without making sidewalks worse for pedestrians?  Phases 1-3 answer this.",
    )
    add_bullet(doc, "Build a baseline ABM of a Starship-type robot in the catchment.")
    add_bullet(doc, "Identify macroscopic friction points (detours, docking, speed mismatches, heat-exposure overlap).")
    add_bullet(doc, "Translate frictions into the Heat-Support Robot concept and variable matrix.")
    add_bullet(doc, "Run A/B simulation; iterate until Pareto-non-dominated on the six metrics.")
    add_para(
        doc,
        "RQ2 -- Do the simulation gains hold up once the robot is designed as a real, "
        "manufacturable thing?  Phases 4-5 answer this.",
    )
    add_bullet(doc, "Convert the converged variable matrix into a parametric Rhino + Fusion 360 CAD model.")
    add_bullet(doc, "Re-abstract CAD geometry back into ABM parameters.")
    add_bullet(doc, "Re-run A/B at scale on the IAC-VLABB-2021 server with 200+ replicates per scenario.")
    add_bullet(doc, "Verify macroscopic gains hold with statistical significance on at least four of six metrics.")
    add_para(
        doc,
        "RQ3 -- Can we show all of this in a browser-based 3D twin that planners and residents "
        "actually understand?  Phase 6 answers this.",
    )
    add_bullet(doc, "Assemble the 500 m catchment as a 3D scene in ArcGIS Urban or CesiumJS.")
    add_bullet(doc, "Overlay heat-cost field, robot trajectories, vulnerable population, service nodes, friction-point markers.")
    add_bullet(doc, "Validate sensor coverage and robot motion plausibility geometrically in Mesa with Shapely.")
    add_bullet(doc, "Demo the twin to stakeholders; collect structured feedback and document what made the evidence interpretable.")
    add_para(
        doc,
        "Definitions  --  Pareto-non-dominated: not worse than the baseline on any metric AND "
        "strictly better on at least one. Preserves trade-offs instead of hiding them in a "
        "weighted score.",
        italic=True,
        size_pt=10,
    )

    doc.add_page_break()

    # Page 2
    add_heading(doc, "2. Spatial Scope and Phase 1 -- Baseline ABM", size_pt=15)
    add_heading(doc, "Spatial scope -- nested scales", size_pt=12)
    add_para(
        doc,
        "Mobility, resilience, and robot service each have a natural scale; none of them is a "
        "single street segment. We use three nested rings so each system is observed where its "
        "dynamics actually occur. The inner ring is a ~200 m hero segment used for close-up "
        "renders; the middle ring is a ~500 m subway-station catchment used for ABM agent "
        "simulation and the Pareto comparison; the outer ring is the full Nihonbashi district "
        "used for stakeholder dashboards. The middle-ring catchment (Nihonbashi Station or "
        "Mitsukoshi-mae) is the operational boundary where the three systems genuinely intersect.",
    )
    add_heading(doc, "Phase 1 -- Starship Baseline ABM", size_pt=12)
    add_para(
        doc,
        "Phase 1 abstracts an existing Starship-type sidewalk delivery robot into ABM-readable "
        "parameters (body 569 x 697 x 616 mm, max speed 6 km/h per METI 2023, turning radius "
        "~0.8 m, payload 10 kg, docking 30 s, reactive avoidance) and drops it into the Nihonbashi "
        "catchment. The objective is not to evaluate Starship's commercial merits but to surface "
        "macroscopic friction points that motivate the Phase 2 design: pedestrian detours, "
        "mainline / robot trajectory intersections, docking conflicts, speed mismatches, task "
        "delays under heat conditions, and heat-exposure overlap between robot paths and pedestrian "
        "shade-seeking behavior.",
    )
    add_heading(doc, "Heat-cost field -- GIS bridge from classifier into ABM", size_pt=12)
    add_para(
        doc,
        "The Random Forest heat-scenario classifier from the parent Tokyo Studio repository "
        "(Low / Moderate / High / Extreme labels per parcel) joins the OSM sidewalk graph by "
        "spatial intersection and becomes a scalar field consumed by every agent in the ABM. "
        "Pedestrian agents use the resulting heat_cost in weighted-Dijkstra route choice; the "
        "robot uses it for service-path optimization; per-agent heat_exposure accumulates along "
        "the trajectory. This bridge is the GIS contribution that ties the Tokyo Studio platform "
        "to the robot simulation -- it is what allows heat to influence both pedestrian and robot "
        "behavior in one consistent way.",
    )

    doc.add_page_break()

    # Page 3
    add_heading(doc, "3. Phase 2 (Concept) and Phase 3 (A/B Simulation)", size_pt=15)
    add_heading(doc, "Phase 2 -- Heat-Support Robot concept and variable matrix", size_pt=12)
    add_para(
        doc,
        "Phase 2 translates ranked friction points into a new design hypothesis: the Nihonbashi "
        "Heat-Support Robot. The concept is a modular autonomous service robot purpose-built for "
        "extreme-heat support in dense Nihonbashi-type districts. Body ~680 x 980 x 1050 mm, with "
        "heat-resilient electronics rated to 40 C+ ambient. Modular cargo bays serve water, "
        "medicine, first-aid, and information / wayfinding tasks. Lift-off docking, directional "
        "intent-lighting strip, top-mounted status screen, soft chime on docking, slow-for-crowd "
        "motion rhythm, and vulnerable-pop detection are the interaction design choices that "
        "answer Phase 1 friction.",
    )
    add_para(
        doc,
        "Each design choice maps to a row in the variable matrix -- a single CSV that becomes the "
        "contract across every subsequent phase. Columns include baseline_value (Starship), "
        "proposal_v1 (Heat-Support v1 from Phase 2), v2 / v3 (after Phase 3 iterations), and "
        "final_value (handed off to Phase 4 CAD). Each row carries design_rationale, "
        "friction_point_ids, and owner. The matrix is version-controlled in git so every change "
        "is a PR with reasoning.",
    )
    add_heading(doc, "Phase 3 -- A/B simulation, six metrics, iterative feedback", size_pt=12)
    add_para(
        doc,
        "Phase 3 runs the proposal under the same scenarios, windows, and seeds as the baseline. "
        "Twelve scenario x window combinations (four heat scenarios x three traffic windows) with "
        "at least 50 paired replicates each, paired across A/B sides under matched RNG seeds. "
        "Statistical analysis uses paired t-test or Wilcoxon, with Holm-Bonferroni correction "
        "across six metrics: labor substitution rate (up), heat exposure reduction (up), service "
        "continuity (up), delivery efficiency (up), pedestrian interference (down), and "
        "infrastructure compatibility (down). Comparison is Pareto-based, not weighted-sum, so "
        "the designer can see the matrix of trade-offs.",
    )
    add_para(
        doc,
        "Residual issues feed a designer review; Xilin updates the proposal column; we re-run "
        "side B with new parameters while side A stays anchored to Starship. Up to three "
        "iterations. Exit conditions: (a) Pareto-non-dominated against baseline with statistical "
        "significance on >= 4 of 6 metrics, OR (b) three iterations completed without significant "
        "new improvement, OR (c) designer override with documented rationale. On exit, the final "
        "proposal parameters and the residual-issue list hand off to Phase 4.",
    )

    doc.add_page_break()

    # Page 4
    add_heading(doc, "4. Phase 4 (CAD), Phase 5 (Re-Sim), Phase 6 (Twin + Sensor)", size_pt=15)
    add_heading(doc, "Phase 4 -- AI + CAD optimization", size_pt=12)
    add_para(
        doc,
        "Generative AI summarizes Phase 3 friction points and proposes CAD-level modifications. "
        "Xilin selects, critiques, and integrates against Nihonbashi context and METI 2023 "
        "sidewalk-robot rules. The result is a parametric Rhino + Grasshopper source with an "
        "engineering pass in Fusion 360 (educational), exported as STEP for engineering hand-off "
        "and glTF for downstream browser display. Every variable matrix row maps to a Rhino "
        "parameter so design changes propagate. Acceptance criteria: manufacturability review "
        "passes and every variable maps cleanly to a CAD parameter.",
    )
    add_heading(doc, "Phase 5 -- ABM re-simulation at scale", size_pt=12)
    add_para(
        doc,
        "CAD-derived parameters are re-abstracted into the ABM. We run a three-tier comparison -- "
        "Starship baseline (Phase 1), initial Heat-Support proposal (Phase 3), CAD-optimized "
        "robot (Phase 4) -- under identical scenarios, windows, seeds, and metrics. The "
        "IAC-VLABB-2021 server runs roughly 36 Mesa workers in parallel, finishing 200+ replicates "
        "per scenario across the full 500 m catchment. This is the central evidence layer: alpha "
        "= 0.05, statistical power >= 0.8, three-way Pareto comparison plus parameter-sensitivity "
        "sweeps. Output: outputs/reports/phase5_revalidation.md.",
    )
    add_heading(doc, "Phase 6.1 -- Browser-deliverable 3D twin", size_pt=12)
    add_para(
        doc,
        "The twin is delivered in the browser at LOD2 fidelity across the catchment. Primary path "
        "is ArcGIS Urban + Experience Builder (which the team already operates in production for "
        "the Tokyo Studio); the alternative is CesiumJS for an open-source web-native build. The "
        "scene carries toggleable layers for heat scenario, robot fleet, vulnerable population, "
        "service nodes, and friction points. Robot trajectories from Phase 5 play back as animated "
        "paths. Production-quality and browser-deliverable, not photoreal -- LOD2 is sufficient "
        "for stakeholder map view.",
    )
    add_heading(doc, "Phase 6.2 -- Geometric sensor + motion validation", size_pt=12)
    add_para(
        doc,
        "Sensor coverage is modeled as 2D polygons in Shapely: camera vision cones, lidar range "
        "discs, ultrasonic ring footprints. We compute coverage percentage per service-node "
        "approach and blind-spot risk per docking maneuver. Robot motion is validated against the "
        "CAD-specified turning radius and docking duration. This intentionally avoids photoreal "
        "sensor fidelity simulation -- the geometric question (does the sensor see what it needs "
        "to see) is the load-bearing one and is fully answered here.",
    )

    doc.add_page_break()

    # Page 5
    add_heading(doc, "5. Data Inventory and Gaps", size_pt=15)
    add_heading(doc, "Inventory (assets available today)", size_pt=12)
    add_dtable(
        doc,
        ["#", "Layer", "Source", "Quality", "Owner"],
        [
            ["1", "Heat scenarios (RF classifier)", "Tokyo Studio repo", "****", "Sam, Qinghao"],
            ["2", "Pedestrian GPS visits", "Nihonbashi 2023 study", "***", "Yi Tai"],
            ["3", "OSM sidewalk graph", "OSMnx", "****", "Yi Tai"],
            ["4", "PLATEAU CityGML LOD1/LOD2", "PLATEAU VIEW 4.0", "****", "Sam"],
            ["5", "Elderly pop per parcel", "e-Stat + Tokyo Metro", "****", "Sam, Qinghao"],
            ["6", "Evacuation shelters", "Tokyo Open Data", "****", "Sam"],
            ["7", "Starship robot specs", "Public spec", "**", "Yi Tai"],
        ],
    )
    add_heading(doc, "Critical gaps (block specific phases)", size_pt=12)
    add_bullet(doc, "1. Weather forecast (6-48 hr) for proactive dispatch -- enables Phase 1-3 forward-look")
    add_bullet(doc, "2. Tokyo Fire Dept heatstroke ambulance-transport data -- vulnerable-pop ground truth")
    add_bullet(doc, "3. METI 2023 sidewalk-robot regulation -- design constraint")
    add_bullet(doc, "4. Pedestrian behavior under heat (GPS re-analysis by temperature bin)")
    add_bullet(doc, "5. Per-segment sidewalk widths -- ABM and Phase 6.2 sensor coverage")
    add_bullet(doc, "6. PLATEAU LOD2 catchment USD / glTF tiles -- Phase 6.1 browser twin")
    add_bullet(doc, "7. Robot CAD source from Rhino -- gating for Phases 5 and 6")
    add_bullet(doc, "8. Sensor specs (camera FOV, lidar range, ultrasonic placement) -- Phase 6.2 coverage polygons")
    add_heading(doc, "Should-have gaps (lift fidelity)", size_pt=12)
    add_bullet(doc, "9. e-Stat 6th mesh (125 m) demographic resolution")
    add_bullet(doc, "10. WBGT  <->  NWS Heat Index reconciliation table")
    add_bullet(doc, "11. Vulnerable-population dwell-time map (parks, benches, shaded areas)")
    add_bullet(doc, "12. Nihonbashi service-node inventory (CVS, vending, public toilets, transit exits)")
    add_bullet(doc, "13. Japanese-language signage overlay for the browser twin")
    add_bullet(doc, "14. Pre-rendered Blender hero shots for slide covers + walkthrough video")
    add_bullet(doc, "15. (Stretch only) Photoreal CAD suitable for Isaac Sim hero video")

    doc.add_page_break()

    # Page 6
    add_heading(doc, "6. Compute, Tooling, and Team", size_pt=15)
    add_heading(doc, "Compute architecture", size_pt=12)
    add_para(
        doc,
        "IAC-VLABB-2021 (Xeon Gold 6254 dual-socket, 36 physical / 72 logical CPUs, 768 GB RAM, "
        "Windows Server 2019) provides headless compute and hosting. The VM has no GPU, which "
        "rules out RTX-dependent workloads on the server itself. Team laptops handle CAD (Rhino), "
        "ArcGIS Pro 3D editing, Blender rendering, and browser viewing. Stakeholder browsers "
        "consume the output -- no client-side GPU is required.",
    )
    add_heading(doc, "Tooling stack", size_pt=12)
    add_para(
        doc,
        "All software is free, educational, or already GT-licensed. Phases 1, 3, and 5 use Python "
        "with Mesa, SUMO, GeoPandas, scikit-learn (re-using the Tokyo Studio classifier). Phase 4 "
        "uses Rhino + Grasshopper (Xilin's existing tool), Fusion 360 (educational free) for an "
        "engineering pass, and Blender for export. Phase 6.1 uses ArcGIS Urban + Experience "
        "Builder (already in production) as the primary 3D twin platform, with CesiumJS as an "
        "open-source alternative. Phase 6.2 uses Mesa + Shapely + GeoPandas for geometric sensor "
        "and motion validation. Hosting uses Flask, Streamlit, and ArcGIS Online. NVIDIA Isaac "
        "Sim is reserved for the conditional stretch goal.",
    )
    add_heading(doc, "Team and RACI", size_pt=12)
    add_dtable(
        doc,
        ["Workstream", "Sam", "Xilin", "Yi Tai", "Qinghao"],
        [
            ["Data acquisition + GIS layer", "R/A", "C", "C", "C"],
            ["Phase 1  --  baseline ABM", "C", "I", "R/A", "C"],
            ["Phase 2  --  concept design", "C", "R/A", "C", "C"],
            ["Phase 3  --  A/B simulation + iteration", "R", "C", "R/A", "C"],
            ["Phase 4  --  CAD optimization", "C", "R/A", "I", "I"],
            ["Phase 5  --  re-sim on VLAB server", "C", "C", "R/A", "C"],
            ["Phase 6.1  --  Browser 3D twin", "R/A", "C", "I", "C"],
            ["Phase 6.2  --  Sensor + motion validation", "R", "C", "R/A", "I"],
            ["Variable matrix maintenance", "C", "R/A", "C", "C"],
            ["Slides + reports", "R/A", "C", "C", "C"],
        ],
    )

    doc.add_page_break()

    # Page 7
    add_heading(doc, "7. Risks, Asks, Decisions, and Stretch Goal", size_pt=15)
    add_heading(doc, "Risks and mitigations", size_pt=12)
    add_dtable(
        doc,
        ["Risk", "Severity", "Mitigation"],
        [
            ["VLAB admin / firewall lockdown blocks dev work", "High", "Confirm dev shell + outbound network with IT early"],
            ["Phase 4 CAD lags Phase 3 hand-off", "High", "Parameter-only Phase 5 dry run while CAD is in flight"],
            ["Browser performance at full crowd density", "Medium", "Aggregate to heatmap; fall back to tile pyramids"],
            ["LOD2 underwhelms stakeholders visually", "Medium", "Pre-rendered Blender hero shots provide the wow moment"],
            ["Data gap closure stalls (item 4, 5, or 8)", "Medium", "Parallelize acquisition; use OSM defaults as fallback"],
        ],
    )
    add_heading(doc, "Asks", size_pt=12)
    add_bullet(doc, "VLAB server dev access: Python environment, Docker, outbound network ports, shared storage.")
    add_bullet(doc, "ArcGIS Online credits (~$50) for the published web scene.")
    add_bullet(doc, "Stakeholder demo slot for the final twin presentation.")
    add_bullet(doc, "Weekly 30-minute team sync (async-first repo workflow in between).")
    add_heading(doc, "Stretch goal -- NVIDIA Isaac Sim hero video (conditional)", size_pt=12)
    add_para(
        doc,
        "IF dedicated RTX hardware (RTX 4080 or better, 16 GB+ VRAM, Windows 10/11 or Ubuntu "
        "22/24, driver 580+) becomes available, we add a single 60-90 second Isaac Sim hero video "
        "showing the optimized robot navigating a peak-commute crowd under high heat. The robot "
        "is represented in URDF with primitive shapes derived from Rhino (NOT photoreal CAD); "
        "sensor simulation is skipped (no ground truth); only kinematic motion is validated. This "
        "is purely a visual deliverable for the final stakeholder demo -- it adds no new research "
        "evidence beyond what Phases 5 and 6.2 already provide. Possible hosts: GT IDEaS / PACE "
        "allocations, NVIDIA Inception grant, a personal RTX desktop. The proposal does not "
        "commit to this deliverable; it is documented here so that if hardware appears, the path "
        "is clear.",
    )
    add_heading(doc, "Decisions requested at proposal review", size_pt=12)
    add_bullet(doc, "Approve the six-phase scope and methodology.")
    add_bullet(doc, "Approve team allocation per the RACI table.")
    add_bullet(doc, "Approve VLAB server dev access and the listed asks.")
    add_bullet(doc, "Approve the async-first git workflow on github.com/SamDuo/nihonbashi-robot-sim.")

    add_para(doc, "End of draft v0.4. Comments and revisions welcome via PR against outputs/reports/proposal_draft.md.", italic=True, size_pt=10)

    DOCX_OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(DOCX_OUT)
    return DOCX_OUT


def main() -> None:
    pptx_path = build_pptx()
    print(f"pptx -> {pptx_path}")
    docx_path = build_docx()
    print(f"docx -> {docx_path}")


if __name__ == "__main__":
    main()
