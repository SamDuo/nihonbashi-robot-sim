"""Build a self-contained HTML slide deck for the 5/25 review.

Reads outputs/reports/testbed_metrics.csv and embeds the three diagnostic PNGs
from outputs/figures/auto/ as base64. No external assets; no header/footer.
"""

from __future__ import annotations

import base64
import csv
import sys
from pathlib import Path


def b64(p: Path) -> str:
    return base64.b64encode(p.read_bytes()).decode("ascii")


def load_metrics(csv_path: Path) -> list[dict]:
    with csv_path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fmt(x: str, decimals: int = 2) -> str:
    try:
        v = float(x)
        if abs(v) >= 100:
            return f"{v:,.0f}"
        if abs(v) >= 1:
            return f"{v:.{decimals}f}"
        if v == 0:
            return "0"
        return f"{v:.4f}"
    except ValueError:
        return x


SCENARIO_ORDER = ("baseline", "reactive", "proactive")


def metrics_table_html(rows: list[dict]) -> str:
    by_name = {r["scenario"]: r for r in rows}
    cols = [
        ("cumulative_population_exposure", "Cumulative exposure", "lower better"),
        ("vulnerability_weighted_exposure", "Vuln-weighted exposure", "lower better"),
        ("mean_peak_hourly_exposure", "Mean peak hourly", "lower better"),
        ("sheltered_agent_hours", "Sheltered agent-hours", "higher better"),
        ("shelter_utilization_rate", "Shelter utilization", "target 0.6-0.85"),
        ("unmet_shelter_demand", "Unmet shelter demand", "lower better"),
        ("cooling_energy_kwh", "Cooling energy (kWh)", "lower better"),
        ("cooling_emissions_kgco2e", "Cooling emissions (kgCO2e)", "lower better"),
        ("equity_gap_ratio", "Equity gap ratio", "closer to 1.0"),
        ("mean_decision_latency_ms", "Decision latency (ms)", "twin"),
        ("provenance_coverage", "Provenance coverage", "twin"),
    ]
    head_cells = "".join(f'<th>{s}</th>' for s in ("Metric",) + SCENARIO_ORDER + ("Direction",))
    body_rows = []
    for key, label, direction in cols:
        cells = [f"<td class='metric-name'>{label}</td>"]
        vals = [float(by_name[s][key]) for s in SCENARIO_ORDER]
        best_idx = None
        if direction == "lower better":
            best_idx = vals.index(min(vals))
        elif direction == "higher better":
            best_idx = vals.index(max(vals))
        elif direction == "closer to 1.0":
            best_idx = min(range(3), key=lambda i: abs(vals[i] - 1.0))
        for i, s in enumerate(SCENARIO_ORDER):
            cls = " class='best'" if best_idx == i else ""
            cells.append(f"<td{cls}>{fmt(by_name[s][key])}</td>")
        cells.append(f"<td class='dir'>{direction}</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    return (
        "<table class='metrics'>"
        f"<thead><tr>{head_cells}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
    )


def main(repo_root: Path) -> int:
    metrics_csv = repo_root / "outputs" / "reports" / "testbed_metrics.csv"
    figures = repo_root / "outputs" / "figures" / "auto"
    deck_path = repo_root / "outputs" / "slides" / "stage1_review_deck.html"

    if not metrics_csv.exists():
        print(f"missing {metrics_csv}", file=sys.stderr)
        return 1

    rows = load_metrics(metrics_csv)
    metric_chart = b64(figures / "metric_comparison.png")
    timeline_chart = b64(figures / "exposure_timeline.png")
    equity_chart = b64(figures / "equity_breakdown.png")

    by_name = {r["scenario"]: r for r in rows}
    base_exp = float(by_name["baseline"]["cumulative_population_exposure"])
    react_exp = float(by_name["reactive"]["cumulative_population_exposure"])
    proact_exp = float(by_name["proactive"]["cumulative_population_exposure"])
    react_drop = (base_exp - react_exp) / base_exp * 100
    proact_drop = (base_exp - proact_exp) / base_exp * 100
    base_equity = float(by_name["baseline"]["equity_gap_ratio"])
    proact_equity = float(by_name["proactive"]["equity_gap_ratio"])

    table_html = metrics_table_html(rows)

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Group 3 - Stage One Testbed</title>
<style>
  :root {{
    --bg: #fafafa;
    --ink: #1a1a1a;
    --muted: #666;
    --accent: #c1272d;
    --shelter: #1a9850;
    --baseline: #999;
    --reactive: #377eb8;
    --proactive: #e41a1c;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--ink);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  body {{ scroll-snap-type: y mandatory; overflow-y: scroll; height: 100vh; }}
  section.slide {{
    scroll-snap-align: start;
    min-height: 100vh;
    padding: 6vh 8vw;
    display: flex;
    flex-direction: column;
    justify-content: center;
    page-break-after: always;
  }}
  h1 {{ font-size: clamp(36px, 5vw, 64px); margin: 0 0 0.3em 0; font-weight: 700; letter-spacing: -0.02em; line-height: 1.05; }}
  h2 {{ font-size: clamp(28px, 3.5vw, 42px); margin: 0 0 0.6em 0; font-weight: 600; letter-spacing: -0.01em; }}
  p, li {{ font-size: clamp(16px, 1.3vw, 22px); line-height: 1.5; color: var(--ink); }}
  ul {{ padding-left: 1.2em; }}
  .big {{ font-size: clamp(56px, 9vw, 120px); font-weight: 700; line-height: 1; letter-spacing: -0.04em; }}
  .label {{ font-size: clamp(14px, 1vw, 18px); text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); margin-bottom: 0.5em; }}
  .stat-row {{ display: flex; gap: 4vw; flex-wrap: wrap; margin-top: 1em; }}
  .stat {{ flex: 1 1 0; min-width: 200px; }}
  .stat .big {{ display: block; }}
  .stat .delta {{ color: var(--accent); font-weight: 600; font-size: clamp(18px, 1.5vw, 26px); }}
  .delta.good {{ color: var(--shelter); }}
  table.metrics {{ border-collapse: collapse; width: 100%; font-size: clamp(13px, 1.1vw, 17px); }}
  table.metrics th, table.metrics td {{ padding: 0.55em 0.8em; text-align: right; border-bottom: 1px solid #e0e0e0; }}
  table.metrics th {{ background: transparent; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.85em; }}
  table.metrics td.metric-name {{ text-align: left; font-weight: 500; }}
  table.metrics td.dir {{ text-align: left; color: var(--muted); font-style: italic; font-size: 0.9em; }}
  table.metrics td.best {{ background: rgba(26, 152, 80, 0.12); font-weight: 600; }}
  img.chart {{ max-width: 100%; max-height: 70vh; height: auto; display: block; margin: 1.2em auto 0; }}
  .caption {{ color: var(--muted); margin-top: 0.6em; font-style: italic; text-align: center; }}
  .stack {{ font-family: "SF Mono", Menlo, monospace; font-size: clamp(15px, 1.2vw, 20px); background: #f0f0f0; padding: 1em 1.2em; border-left: 4px solid var(--accent); margin-top: 1em; }}
  .meta {{ color: var(--muted); margin-top: 1.5em; font-size: clamp(14px, 1vw, 17px); }}
  a {{ color: var(--accent); text-decoration: none; border-bottom: 1px solid var(--accent); }}
  @media print {{
    body {{ scroll-snap-type: none; overflow: visible; height: auto; }}
    section.slide {{ min-height: auto; height: 100vh; }}
  }}
</style>
</head>
<body>

<section class="slide">
  <div class="label">5/25 Stage One review</div>
  <h1>Group 3 testbed</h1>
  <p>Agentic decision loop for heat-equity in a 200m Nihonbashi segment.<br>
     Synthetic G1 / G2 data; Mesa + Shapely + Folium browser twin.</p>
</section>

<section class="slide">
  <div class="label">stack</div>
  <h2>One screen, three policies</h2>
  <div class="stack">
    Mesa agents  &nbsp;|&nbsp;  Shapely footprints  &nbsp;|&nbsp;  Folium twin<br>
    240 agents &times; 24 hours &times; baseline / reactive / proactive<br>
    Anchored to 35.6840-35.6852&deg;N, 139.7735-139.7747&deg;E
  </div>
  <p style="margin-top: 1.5em;">
    <strong>Baseline:</strong> no policy intervention.<br>
    <strong>Reactive:</strong> route to nearest feasible shelter when raw heat exposure &gt; 1.0.<br>
    <strong>Proactive:</strong> pre-position agents with vulnerability &geq; 0.55 when next-hour forecast &geq; 0.8.
  </p>
</section>

<section class="slide">
  <div class="label">headline</div>
  <h2>Proactive cuts exposure by a third and closes the equity gap</h2>
  <div class="stat-row">
    <div class="stat">
      <div class="label">cumulative exposure</div>
      <div class="big">-33%</div>
      <div class="delta good">{base_exp:,.0f} &rarr; {proact_exp:,.0f}</div>
    </div>
    <div class="stat">
      <div class="label">equity gap (top vs bottom vuln quartile)</div>
      <div class="big">0.91</div>
      <div class="delta good">from {base_equity:.2f} baseline</div>
    </div>
    <div class="stat">
      <div class="label">sheltered agent-hours</div>
      <div class="big">{int(by_name['proactive']['sheltered_agent_hours']):,}</div>
      <div class="delta good">from 0 baseline</div>
    </div>
  </div>
  <p class="meta">Reactive alone: -{react_drop:.0f}% exposure, equity gap drifts to 1.00 (near parity but not preferentially protective).</p>
</section>

<section class="slide">
  <div class="label">full metric table</div>
  <h2>9 outcome + 2 twin metrics</h2>
  {table_html}
  <p class="meta">Green cell = best in row. Definitions live in <code>sim/testbed/metrics.py</code> and <code>outputs/reports/testbed_comparison.md</code>.</p>
</section>

<section class="slide">
  <div class="label">chart 1 of 3</div>
  <h2>All metrics, side by side</h2>
  <img class="chart" src="data:image/png;base64,{metric_chart}" alt="metric comparison bars">
</section>

<section class="slide">
  <div class="label">chart 2 of 3</div>
  <h2>Exposure across the day</h2>
  <img class="chart" src="data:image/png;base64,{timeline_chart}" alt="exposure timeline">
  <p class="caption">Peak hours 13:00-16:00 are where the policies do the most work.</p>
</section>

<section class="slide">
  <div class="label">chart 3 of 3</div>
  <h2>Equity breakdown</h2>
  <img class="chart" src="data:image/png;base64,{equity_chart}" alt="equity breakdown by vulnerability quartile">
  <p class="caption">Proactive pulls the most-vulnerable quartile below the least-vulnerable. That's the point.</p>
</section>

<section class="slide">
  <div class="label">live twin</div>
  <h2>The browser twin</h2>
  <p>Open <code>outputs/reports/browser_twin.html</code> from this repo. Toggle scenarios from the layer control. Each agent dot scales with vulnerability; green = sheltered.</p>
  <p class="meta">Backed by per-decision JSONL audit at <code>outputs/reports/provenance_*.jsonl</code>. Every step is auditable; provenance coverage = 1.00 across all three runs.</p>
</section>

<section class="slide">
  <div class="label">next</div>
  <h2>What Stage Two adds without changing the loop</h2>
  <ul>
    <li>Real G1 population &amp; heat raster (drops into <code>population.py</code>, <code>heat_field.py</code> loaders)</li>
    <li>Real G2 cooling envelope (replaces <code>shelter_model.py</code> synthetic)</li>
    <li>Yi's SHP &rarr; SUMO net replaces the 20&times;10 grid scene</li>
    <li>NVIDIA Omniverse twin replaces Folium (Phase 6 of the methodology)</li>
    <li>LLM-driven planner replaces the threshold policies</li>
  </ul>
</section>

</body>
</html>
"""

    deck_path.parent.mkdir(parents=True, exist_ok=True)
    deck_path.write_text(html, encoding="utf-8")
    print(f"wrote {deck_path} ({deck_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    raise SystemExit(main(root))
