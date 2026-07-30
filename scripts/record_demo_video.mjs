// USAGE (5 lines)
//   1. python scripts/serve_outputs.py           # serves outputs/ on :8889
//   2. node scripts/record_demo_video.mjs        # renders frames + assembles the mp4
//   3. result -> outputs/reports/demo_video.mp4  (silent, 1920x1080, 30 fps)
//   4. env knobs: DEMO_BASE DEMO_OUT DEMO_FRAMES DEMO_W DEMO_H DEMO_RENDER_FPS DEMO_FPS
//      DEMO_CRF DEMO_QUALITY DEMO_ONLY=<segment,...> DEMO_KEEP_FRAMES=1 DEMO_HEADFUL=1 FFMPEG=<path>
//
// ---------------------------------------------------------------------------
// Deterministic offline recorder for outputs/energy_cesium_view.html.
//
// Nothing here relies on wall-clock animation. Every frame is produced by
// (a) setting the camera pose explicitly with camera.setView, (b) pushing the UI
// state through the page's OWN controls (the COLOUR BY slider, the DEMAND /
// SUPPLY / AGENTS buttons and the SIM TIME slider — the same code paths a user
// drives), (c) polling the photoreal tileset until streaming has converged, and
// only then (d) screenshotting. The sim clock is never left running: the agent
// CZML clock is parked (shouldAnimate=false) and time is scrubbed one frame at
// a time, so two runs of this script produce the same video.
//
// Rendering is done at DEMO_RENDER_FPS unique frames (default 15) and the mp4 is
// written at DEMO_FPS (default 30) — ffmpeg repeats each unique frame. On a GPU
// machine set DEMO_RENDER_FPS=30 for genuinely smooth motion; on SwiftShader
// (this codespace, no GPU) 15 unique fps is the honest speed/quality trade.
//
// The Cesium / Google Maps credit line is part of the page and is NEVER cropped
// or hidden — it is visible in every frame by construction.
//
// Browser: puppeteer (already vendored in node_modules and already proven against
// these views by scripts/qa_cesium_views.mjs, which uses the same SwiftShader
// flags). Playwright would work identically; puppeteer avoids a second ~200 MB
// chromium download.
// ---------------------------------------------------------------------------
import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { execFileSync, spawnSync } from 'child_process';

const BASE        = process.env.DEMO_BASE   || 'http://localhost:8889';
const OUT_DIR     = path.resolve(process.env.DEMO_OUT    || 'outputs/reports');
const FRAME_DIR   = path.resolve(process.env.DEMO_FRAMES || path.join(OUT_DIR, '_demo_frames'));
const W           = parseInt(process.env.DEMO_W || '1920', 10);
const H           = parseInt(process.env.DEMO_H || '1080', 10);
const RENDER_FPS  = parseFloat(process.env.DEMO_RENDER_FPS || '15');   // unique frames per second
const OUT_FPS     = parseFloat(process.env.DEMO_FPS || '30');          // mp4 frame rate
const CRF         = process.env.DEMO_CRF || '20';
const JPEG_Q      = parseInt(process.env.DEMO_QUALITY || '92', 10);
const ONLY        = process.env.DEMO_ONLY ? process.env.DEMO_ONLY.split(',').map(s => s.trim()) : null;
const KEEP        = process.env.DEMO_KEEP_FRAMES === '1';
const MP4         = path.join(OUT_DIR, 'demo_video.mp4');

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const log = (...a) => console.log(...a);

// ------------------------------------------------------------------ geometry
// Study-block centroid and the metre-per-degree constants used by
// outputs/qa/camera_poses.json, so poses here are comparable with C1-C4.
const CENTER = { lon: 139.779099, lat: 35.688301 };
// The Phase 1 ABM runs in the twin's own local frame, whose agents occupy
// lon 139.7721-139.7831 / lat 35.6800-35.6862 — i.e. the pedestrian field sits
// SOUTH of the study block, not under it. The agent beat therefore drifts its
// aim point south to this midpoint and swings the camera round to heading ~180
// (eye north of the aim, looking south) so the block and the agents are in the
// same frame. Aiming at CENTER with a northward camera puts every agent behind
// the lens — which is exactly what the first pass of this script did.
const AGENT_MID = { lon: 139.7784, lat: 35.6871 };
const MLAT = 111000.0, MLNG = 90422.67473060869;

// An orbit pose: stand `range` metres back from `target` along `heading`
// (heading 0 = the camera is SOUTH of the target, looking north), at the height
// that puts the target on the optical axis for the given pitch. Verified against
// pose C1: (0, 145, -55) reproduces lon 139.779099 / lat 35.686995 / height 207.1.
function orbitPose(headingDeg, rangeM, pitchDeg, target = CENTER) {
  const h = headingDeg * Math.PI / 180;
  return {
    lon: target.lon - (rangeM * Math.sin(h)) / MLNG,
    lat: target.lat - (rangeM * Math.cos(h)) / MLAT,
    height_m: rangeM * Math.tan(-pitchDeg * Math.PI / 180),
    heading_deg: headingDeg,
    pitch_deg: pitchDeg,
  };
}
const lerpTarget = (a, b, t) => ({ lon: a.lon + (b.lon - a.lon) * t, lat: a.lat + (b.lat - a.lat) * t });
const lerp  = (a, b, t) => a + (b - a) * t;
const ease  = (t) => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;  // smooth in/out

// ------------------------------------------------------------------ storyboard
// `cam(t)` returns orbit params for normalised segment time t in [0,1].
// `ui(t)`  returns only the controls that should CHANGE (applied when different
//          from the last applied value), so held beats cost nothing.
const METRIC_INDEX = { energy: 0, intensity: 1, cost: 2, wwr: 3, occupancy: 4 };
const beat = (t, stops) => { let v = stops[0][1]; for (const [at, x] of stops) if (t >= at) v = x; return v; };

const SEGMENTS = [
  { name: 'title', seconds: 1.5, title: true },

  // 1. hero push-in on the C1 oblique: wide city, closing on the study block.
  { name: 'hero', seconds: 6.0,
    cam: t => ({ heading: lerp(0, 12, ease(t)), range: lerp(660, 400, ease(t)), pitch: lerp(-25, -34, ease(t)) }),
    ui:  () => ({ metric: 'energy', demand: 'baseline', supply: 'baseline', hour: 12, agents: false }) },

  // 2. slow orbit at constant height/range around the coloured block (~88 deg).
  { name: 'orbit', seconds: 6.0,
    cam: t => ({ heading: lerp(12, 100, ease(t)), range: 400, pitch: -34 }),
    ui:  () => ({}) },

  // 3. metric cycle, driven through the COLOUR BY slider: ENERGY -> EUI -> WWR -> OCCUPANCY.
  { name: 'metrics', seconds: 5.0,
    cam: t => ({ heading: lerp(100, 118, t), range: lerp(400, 405, t), pitch: -34 }),
    ui:  t => ({ metric: beat(t, [[0, 'energy'], [0.25, 'intensity'], [0.50, 'wwr'], [0.75, 'occupancy']]) }) },

  // 4. scenarios: demand BASE -> S1 -> S2, then supply GRID -> PV+BESS -> +CHP.
  //    Coloured by EUI, which is the scenario-aware layer (b.scn per building).
  { name: 'scenarios', seconds: 5.0,
    cam: t => ({ heading: lerp(118, 150, t), range: lerp(405, 420, t), pitch: -34 }),
    ui:  t => ({ metric: 'intensity',
                 demand: beat(t, [[0, 'baseline'], [0.18, 's1'], [0.36, 's2']]),
                 supply: beat(t, [[0, 'baseline'], [0.54, 'pv_bess'], [0.72, 'pv_bess_chp']]) }) },

  // 5. agents on, sim clock scrubbed 07:00 -> 19:00 (agent dots move, the OCCUPANCY
  //    layer is hour-dependent so the block recolours, sun swings to evening). The aim
  //    drifts south onto AGENT_MID and the heading swings to 180 so the camera ends up
  //    north of the district looking south, with the block low in frame and the
  //    pedestrian field filling the middle.
  { name: 'agents', seconds: 7.0,
    cam: t => { const s = 1 - Math.pow(1 - t, 2);   // ease-OUT: swing south fast so the
                //                                     agent field is in frame within ~1.5 s
                return { heading: lerp(150, 192, s), range: lerp(420, 650, s), pitch: -34,
                         target: lerpTarget(CENTER, AGENT_MID, s) }; },
    ui:  t => ({ agents: true, metric: 'occupancy', hour: +(7 + 12 * t).toFixed(2) }) },

  // 6. pull back and up to the wide establishing shot; last ~2 s is a held frame.
  { name: 'pullback', seconds: 6.0,
    cam: t => { const u = ease(Math.min(1, t / 0.68));
                return { heading: lerp(192, 215, u), range: lerp(650, 900, u), pitch: lerp(-34, -36, u),
                         target: lerpTarget(AGENT_MID, CENTER, u) }; },
    ui:  () => ({ agents: false, metric: 'energy', demand: 's2', supply: 'pv_bess_chp', hour: 12 }) },
];

// frame index ranges (deterministic, so DEMO_ONLY can re-render a segment in place)
let cursor = 0;
for (const s of SEGMENTS) { s.count = Math.round(s.seconds * RENDER_FPS); s.start = cursor; cursor += s.count; }
const TOTAL = cursor;

const framePath = (i) => path.join(FRAME_DIR, `frame_${String(i).padStart(5, '0')}.jpg`);

// ------------------------------------------------------------------ browser glue
const launch = () => puppeteer.launch({
  headless: process.env.DEMO_HEADFUL === '1' ? false : true,
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--use-gl=angle', '--use-angle=swiftshader',
         '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-dev-shm-usage',
         '--enable-webgl', '--hide-scrollbars', `--window-size=${W},${H}`],
  defaultViewport: { width: W, height: H },
  protocolTimeout: 900000,
});

const applyPose = (page, p) => page.evaluate((c) => {
  const v = window.__viewer; if (!v) return false;
  v.camera.setView({
    destination: Cesium.Cartesian3.fromDegrees(c.lon, c.lat, c.height_m),
    orientation: { heading: Cesium.Math.toRadians(c.heading_deg),
                   pitch:   Cesium.Math.toRadians(c.pitch_deg), roll: 0 },
  });
  v.scene.requestRender && v.scene.requestRender();
  return true;
}, p);

// Every control below is the page's own widget, so the HUD, legend and KPI text
// stay consistent with the colours — exactly as if a reviewer clicked them.
const applyUI = (page, u) => page.evaluate((u, MI) => {
  const $ = (id) => document.getElementById(id);
  const out = {};
  if (u.agents != null) {
    const ds = window.__agents, v = window.__viewer;
    const btn = document.querySelector('#layerBtns .btn');
    if (ds && btn && !!ds.show !== !!u.agents) btn.click();
    // the AGENTS button starts the CZML clock; park it so time only moves when we move it
    if (v) { v.clock.shouldAnimate = false; if (v.clockViewModel) v.clockViewModel.shouldAnimate = false; }
    out.agents = !!(ds && ds.show);
  }
  if (u.metric != null) { const s = $('metricSlider'); s.value = String(MI[u.metric]); s.dispatchEvent(new Event('input')); out.metric = u.metric; }
  for (const [k, host] of [['demand', 'demandBtns'], ['supply', 'supplyBtns']]) {
    if (u[k] == null) continue;
    for (const el of $(host).children) if (el.dataset.k === u[k]) { el.click(); out[k] = u[k]; }
  }
  if (u.hour != null) { const s = $('hourSlider'); s.value = String(u.hour); s.dispatchEvent(new Event('input')); out.hour = u.hour; }
  out.kpi = $('kpi-main')?.textContent; out.scn = $('kpi-scn')?.textContent;
  out.legend = $('leg-title')?.textContent; out.clock = $('hlabel')?.textContent;
  return out;
}, u, METRIC_INDEX);

const stats = (page) => page.evaluate(() => {
  const v = window.__viewer, t = window.__tileset, st = (t && t.statistics) || {};
  return { ready: st.numberOfTilesWithContentReady ?? 0, pending: st.numberOfPendingRequests ?? 0,
           proc: st.numberOfTilesProcessing ?? 0, sel: st.selected ?? 0,
           globe: v?.scene?.globe?.tilesLoaded ?? false };
});

// Streaming-convergence gate. globe.tilesLoaded is reported but not trusted (the
// view runs on an EllipsoidTerrainProvider with no imagery in photoreal mode, where
// it can stay false forever) — the gate is "nothing in flight and the ready count
// has not moved for `stable` consecutive polls".
async function settle(page, { maxMs = 20000, minMs = 140, stable = 2, poll = 220 } = {}) {
  const t0 = Date.now(); let prev = -1, cnt = 0, last = null;
  await sleep(minMs);
  while (Date.now() - t0 < maxMs) {
    last = await stats(page);
    const quiet = last.pending === 0 && last.proc === 0;
    cnt = (quiet && last.ready === prev) ? cnt + 1 : 0;
    prev = last.ready;
    if (cnt >= stable) return { ...last, ms: Date.now() - t0 };
    await sleep(poll);
  }
  return { ...(last || await stats(page)), ms: Date.now() - t0, timeout: true };
}

const shoot = (page, i) => page.screenshot({ path: framePath(i), type: 'jpeg', quality: JPEG_Q, optimizeForSpeed: true });

// ------------------------------------------------------------------ title card
const TITLE_HTML = `
<!doctype html><meta charset="utf-8"><style>
 html,body{margin:0;height:100%;background:#003057;color:#fff;
   font-family:"Noto Sans CJK JP","Noto Sans JP",system-ui,sans-serif;}
 .wrap{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px}
 h1{margin:0;font-size:64px;font-weight:600;letter-spacing:.01em;text-align:center;line-height:1.2}
 .rule{width:220px;height:2px;background:#35e0ff;opacity:.85}
 p{margin:0;font-size:26px;font-weight:400;color:#c8dbe8;letter-spacing:.06em}
</style><div class="wrap">
 <h1>Nihonbashi Energy Twin · 日本橋</h1>
 <div class="rule"></div>
 <p>Sam Duong · Georgia Tech Tokyo Studio</p>
</div>`;

async function renderTitle(browser, seg) {
  const page = await browser.newPage();
  await page.setContent(TITLE_HTML, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts && document.fonts.ready);
  await sleep(400);
  await shoot(page, seg.start);
  await page.close();
  const src = fs.readFileSync(framePath(seg.start));
  for (let i = 1; i < seg.count; i++) fs.writeFileSync(framePath(seg.start + i), src);
  log(`[title] ${seg.count} frames -> ${path.basename(framePath(seg.start))}..`);
}

// ------------------------------------------------------------------ main render
async function render() {
  fs.mkdirSync(FRAME_DIR, { recursive: true });
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const want = (s) => !ONLY || ONLY.includes(s.name);

  const browser = await launch();
  const notes = [];
  try {
    if (want(SEGMENTS[0])) await renderTitle(browser, SEGMENTS[0]);

    const live = SEGMENTS.filter(s => !s.title && want(s));
    if (live.length) {
      const page = await browser.newPage();
      const errors = [];
      page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 160)); });
      page.on('pageerror', e => errors.push('PAGEERROR: ' + String(e.message || e).slice(0, 160)));

      const url = `${BASE}/energy_cesium_view.html?agents=1&scenario=proactive`;
      log(`open ${url}`);
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 180000 });
      await page.waitForFunction('window.__READY === true', { timeout: 180000 });
      const mode = await page.evaluate(() => window.__MODE);
      log('mode:', JSON.stringify(mode));
      if (!mode.photoreal) log('WARNING: photoreal base unavailable — no Ion token? (outputs/ion_token.js)');

      // park the clock and the agent layer; put the UI in its opening state
      await applyUI(page, { agents: false, metric: 'energy', demand: 'baseline', supply: 'baseline', hour: 12 });

      // prime the tile cache from the first pose before timing anything
      const first = live[0].cam(0);
      await applyPose(page, orbitPose(first.heading, first.range, first.pitch, first.target));
      const primed = await settle(page, { maxMs: 120000, stable: 2, poll: 1500, minMs: 1000 });
      log('primed:', JSON.stringify(primed));

      let lastUI = {};
      for (const seg of live) {
        const t0 = Date.now(); const waits = []; let timeouts = 0;
        for (let k = 0; k < seg.count; k++) {
          const t = seg.count === 1 ? 0 : k / (seg.count - 1);
          const c = seg.cam(t);
          await applyPose(page, orbitPose(c.heading, c.range, c.pitch, c.target));
          const u = seg.ui(t);
          const delta = {};
          for (const key of Object.keys(u)) if (u[key] !== lastUI[key]) { delta[key] = u[key]; lastUI[key] = u[key]; }
          if (Object.keys(delta).length) await applyUI(page, delta);
          const s = await settle(page, k === 0 ? { maxMs: 60000, stable: 2, poll: 800, minMs: 500 } : {});
          waits.push(s.ms); if (s.timeout) timeouts++;
          await shoot(page, seg.start + k);
          if (k % 15 === 0) log(`  [${seg.name}] ${k}/${seg.count} ready=${s.ready} sel=${s.sel} wait=${s.ms}ms`);
        }
        const dur = (Date.now() - t0) / 1000;
        const note = { segment: seg.name, frames: seg.count, seconds_of_video: seg.seconds,
                       render_s: +dur.toFixed(1), per_frame_s: +(dur / seg.count).toFixed(2),
                       max_settle_ms: Math.max(...waits), settle_timeouts: timeouts };
        notes.push(note);
        log(`[${seg.name}] ${seg.count} frames in ${dur.toFixed(0)}s (${(dur / seg.count).toFixed(2)} s/frame)`);
      }
      if (errors.length) log('console errors:', [...new Set(errors)].slice(0, 6));
      await page.close();
    }
  } finally { await browser.close(); }
  return notes;
}

// ------------------------------------------------------------------ assembly
function ffmpegBin() {
  if (process.env.FFMPEG) return process.env.FFMPEG;
  if (spawnSync('ffmpeg', ['-version'], { stdio: 'ignore' }).status === 0) return 'ffmpeg';
  const py = spawnSync('python3', ['-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'], { encoding: 'utf8' });
  if (py.status === 0 && py.stdout.trim()) return py.stdout.trim();
  throw new Error('no ffmpeg: install it (apt-get install ffmpeg) or `pip install imageio-ffmpeg`');
}

function assemble() {
  const missing = [];
  for (let i = 0; i < TOTAL; i++) if (!fs.existsSync(framePath(i))) missing.push(i);
  if (missing.length) throw new Error(`missing ${missing.length} frames (first ${missing[0]})`);
  const bin = ffmpegBin();
  log(`ffmpeg: ${bin}`);
  execFileSync(bin, ['-y', '-hide_banner', '-loglevel', 'error',
    '-framerate', String(RENDER_FPS), '-i', path.join(FRAME_DIR, 'frame_%05d.jpg'),
    '-an', '-r', String(OUT_FPS), '-c:v', 'libx264', '-preset', 'slow', '-crf', String(CRF),
    '-pix_fmt', 'yuv420p', '-vf', `scale=${W}:${H}`, '-movflags', '+faststart', MP4], { stdio: 'inherit' });
  const bytes = fs.statSync(MP4).size;
  log(`\n${MP4}\n  ${TOTAL} unique frames @ ${RENDER_FPS} fps -> ${OUT_FPS} fps, ` +
      `${(TOTAL / RENDER_FPS).toFixed(1)} s, ${(bytes / 1048576).toFixed(1)} MB`);
  return { bytes, frames: TOTAL, duration_s: +(TOTAL / RENDER_FPS).toFixed(2) };
}

// ------------------------------------------------------------------ go
const t0 = Date.now();
log(`storyboard: ${TOTAL} unique frames @ ${RENDER_FPS} fps = ${(TOTAL / RENDER_FPS).toFixed(1)} s of video`);
for (const s of SEGMENTS) log(`  ${s.name.padEnd(10)} frames ${s.start}..${s.start + s.count - 1} (${s.seconds}s)`);
const notes = await render();
let info = null;
try { info = assemble(); }
catch (e) { if (!ONLY) throw e; log('skipping assembly (DEMO_ONLY set):', e.message); }
fs.writeFileSync(path.join(OUT_DIR, 'demo_video_render.json'), JSON.stringify({
  written: new Date().toISOString(), base: BASE, size: `${W}x${H}`,
  render_fps: RENDER_FPS, out_fps: OUT_FPS, crf: CRF, jpeg_quality: JPEG_Q,
  storyboard: SEGMENTS.map(s => ({ name: s.name, seconds: s.seconds, frames: s.count, start: s.start })),
  segments: notes, output: info, total_wall_s: +((Date.now() - t0) / 1000).toFixed(1),
}, null, 2));
if (!KEEP && !ONLY) fs.rmSync(FRAME_DIR, { recursive: true, force: true });
log(`done in ${((Date.now() - t0) / 60000).toFixed(1)} min`);
