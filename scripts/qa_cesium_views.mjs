// QA + figure harness for the Nihonbashi twins. Loads each view headless (swiftshader
// WebGL), POLLS until the globe / 3D tileset / city mesh actually finish streaming,
// applies a camera pose and a UI state, screenshots, and records console errors +
// scene diagnostics.
//
// Two modes:
//
//   node scripts/qa_cesium_views.mjs                 # smoke mode: the legacy day/night
//                                                    # cases, 1366x854 -> outputs/qa/
//   node scripts/qa_cesium_views.mjs --poses         # figure mode: read the committed
//                                                    # poses in outputs/qa/camera_poses.json
//                                                    # and capture every curated view
//                                                    # (C1-C4 + variants) -> outputs/figures/
//
// Figure-mode flags:
//   --poses[=path]   pose file (default outputs/qa/camera_poses.json)
//   --out=DIR        output dir  (default outputs/figures)
//   --only=C1,C4     capture a subset by pose id
//
// Figure mode drives BOTH engines:
//   engine "cesium" -> outputs/energy_cesium_view.html, outputs/cesium_view.html
//                      (geodetic pose applied with camera.setView)
//   engine "three"  -> outputs/twin_view.html (three.js, OSM street frame): the geodetic
//                      pose is converted to local metres with the constants recorded in
//                      the pose file and passed as ?cam=px,py,pz,tx,ty,tz
//
// Server must be up on :8889 (python scripts/serve_outputs.py).
import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

const BASE = process.env.QA_BASE || 'http://localhost:8889';
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const argv = process.argv.slice(2);
const flag = (name, dflt) => {
  const hit = argv.find(a => a === `--${name}` || a.startsWith(`--${name}=`));
  if (!hit) return undefined;
  const eq = hit.indexOf('=');
  return eq === -1 ? (dflt ?? true) : hit.slice(eq + 1);
};
const POSE_MODE = flag('poses') !== undefined;

// ---------------------------------------------------------------- shared helpers

// Poll until the 3D tileset content has actually streamed in and STOPPED changing.
//
// NOTE on globe.tilesLoaded: energy_cesium_view.html runs on an EllipsoidTerrainProvider
// with NO imagery layer by default, and in that configuration globe.tilesLoaded can stay
// false indefinitely. It is therefore reported but NOT used as the gate. The gate is
// "tileset has >= minTiles content-ready tiles, nothing in flight, and the ready count has
// not moved for two consecutive polls" - i.e. streaming has converged.
const waitForTiles = async (page, maxMs = 60000, minTiles = 4) => {
  const t0 = Date.now();
  let last = null, prevReady = -1, stable = 0;
  while (Date.now() - t0 < maxMs) {
    last = await page.evaluate(() => {
      const v = window.__viewer; const t = window.__tileset;
      const st = t && t.statistics ? t.statistics : {};
      return {
        globe: v?.scene?.globe?.tilesLoaded ?? false,
        ready: st.numberOfTilesWithContentReady ?? 0,
        pending: st.numberOfPendingRequests ?? 0,
        processing: st.numberOfTilesProcessing ?? 0,
        sel: st.selected ?? 0,
      };
    });
    const quiet = last.pending === 0 && last.processing === 0;
    stable = (last.ready === prevReady && quiet) ? stable + 1 : 0;
    prevReady = last.ready;
    if (last.ready >= minTiles && quiet && stable >= 2)
      return { ...last, converged: true, waited_s: +((Date.now() - t0) / 1000).toFixed(1) };
    await sleep(1500);
  }
  return { ...last, timedOut: true, waited_s: +((Date.now() - t0) / 1000).toFixed(1) };
};

const diag = (page) => page.evaluate(() => {
  const v = window.__viewer; const t = window.__tileset;
  return {
    ready: window.__READY ?? null,
    baseAsset: window.__BASE_ASSET ?? null,
    tilesetReady: t?.statistics?.numberOfTilesWithContentReady ?? null,
    globeTilesLoaded: v?.scene?.globe?.tilesLoaded ?? null,
    primitives: v?.scene?.primitives?.length ?? null,
    entities: v?.entities?.values?.length ?? null,
    lighting: v?.scene?.globe?.enableLighting ?? null,
    status: document.getElementById('status')?.textContent ?? null,
    // animated-layer state: with the agent CZML adopted the clock must be RUNNING and
    // requestRenderMode must be OFF, or the time-dynamic entities render as a frozen frame.
    mode: window.__MODE ?? null,
    notice: window.__NOTICE ?? null,
    agents: window.__agents?.entities?.values?.length ?? null,
    clockRunning: v?.clock?.shouldAnimate ?? null,
    requestRenderMode: v?.scene?.requestRenderMode ?? null,
  };
});

// Blankness proof. Both viewers create their WebGL context WITHOUT preserveDrawingBuffer,
// so drawImage() off the live canvas reads back all zeros; the numbers have to come from
// the composited PNG instead. Decoded here with a tiny inline PNG reader (no dependency)
// on a downscaled screenshot: mean luminance, stddev and 5-bit unique-colour count.
// A grey unloaded globe scores stddev near 0.
import zlib from 'zlib';

function pngStats(buf) {
  // minimal PNG decode: IHDR + concatenated IDAT, 8-bit RGB/RGBA, no interlace
  let pos = 8, width = 0, height = 0, bitDepth = 0, colorType = 0, interlace = 0;
  const idat = [];
  while (pos < buf.length) {
    const len = buf.readUInt32BE(pos);
    const type = buf.toString('ascii', pos + 4, pos + 8);
    const data = buf.subarray(pos + 8, pos + 8 + len);
    if (type === 'IHDR') {
      width = data.readUInt32BE(0); height = data.readUInt32BE(4);
      bitDepth = data[8]; colorType = data[9]; interlace = data[12];
    } else if (type === 'IDAT') idat.push(data);
    else if (type === 'IEND') break;
    pos += 12 + len;
  }
  if (bitDepth !== 8 || interlace !== 0 || (colorType !== 2 && colorType !== 6))
    return { error: `unsupported png depth=${bitDepth} color=${colorType} interlace=${interlace}` };
  const ch = colorType === 6 ? 4 : 3;
  const raw = zlib.inflateSync(Buffer.concat(idat));
  const stride = width * ch;
  const out = Buffer.alloc(height * stride);
  const paeth = (a, b, c) => { const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
    return (pa <= pb && pa <= pc) ? a : (pb <= pc ? b : c); };
  for (let y = 0, ri = 0; y < height; y++) {
    const f = raw[ri++];
    for (let x = 0; x < stride; x++) {
      const v = raw[ri++];
      const a = x >= ch ? out[y * stride + x - ch] : 0;
      const b = y > 0 ? out[(y - 1) * stride + x] : 0;
      const c = (x >= ch && y > 0) ? out[(y - 1) * stride + x - ch] : 0;
      out[y * stride + x] = (f === 0 ? v : f === 1 ? v + a : f === 2 ? v + b :
                             f === 3 ? v + ((a + b) >> 1) : v + paeth(a, b, c)) & 0xff;
    }
  }
  let sum = 0, sum2 = 0, n = 0; const uniq = new Set();
  const step = Math.max(1, Math.floor(height / 400));                 // subsample rows
  for (let y = 0; y < height; y += step) for (let x = 0; x < width; x += step) {
    const i = y * stride + x * ch, r = out[i], g = out[i + 1], b = out[i + 2];
    const lum = 0.299 * r + 0.587 * g + 0.114 * b;
    sum += lum; sum2 += lum * lum; n++;
    uniq.add((r >> 3 << 10) | (g >> 3 << 5) | (b >> 3));
  }
  const mean = sum / n;
  return { width, height, mean: +mean.toFixed(2),
           stddev: +Math.sqrt(Math.max(0, sum2 / n - mean * mean)).toFixed(2),
           unique_colors: uniq.size, sampled_px: n };
}

const launch = (w, h) => puppeteer.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--use-gl=angle', '--use-angle=swiftshader',
         '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-dev-shm-usage',
         '--enable-webgl', `--window-size=${w},${h}`],
  defaultViewport: { width: w, height: h },
  protocolTimeout: 600000,
});

// ---------------------------------------------------------------- smoke mode (legacy)

const setHourLegacy = (page, h) => page.evaluate((hh) => {
  const v = window.__viewer; if (v) v.clock.shouldAnimate = false;
  const s = document.getElementById('hslider');
  if (s) { s.value = String(hh); s.dispatchEvent(new Event('input')); }
}, h);

const clickTime = (page, label) => page.evaluate((lab) => {
  const host = document.getElementById('timeBtns'); if (!host) return false;
  for (const b of host.children) if (b.textContent.trim() === lab) { b.click(); return true; }
  return false;
}, label);

// The energy view now defaults to base=google (full-screen photoreal), which streams Google
// Photorealistic 3D Tiles. That is deliberately OUT of scope for headless QA: SwiftShader
// streams it slowly and the deliverable's photoreal quality is verified on the user's GPU.
// Smoke therefore PINS ?base=streetscape, the designed-ground path, and exercises the agent
// layer in its own case so the CZML/clock path is still covered headlessly.
const ENERGY_QA_BASE = '/energy_cesium_view.html?base=streetscape';
const setEnergyHour = (page, h) => page.evaluate((hh) => {
  const s = document.getElementById('hourSlider');
  if (s) { s.value = String(hh); s.dispatchEvent(new Event('input')); return true; }
  return false;
}, h);

const SMOKE_CASES = [
  // agents=0 keeps these two deterministic: with the agent CZML loaded the clock runs at 600x
  // and the time of day would drift between runs.
  { name: '1_energy_day',   url: ENERGY_QA_BASE + '&agents=0', after: p => setEnergyHour(p, 12) },
  { name: '2_energy_night', url: ENERGY_QA_BASE + '&agents=0', after: p => setEnergyHour(p, 21) },
  { name: '3_heat_day',     url: '/cesium_view.html?plateau=textured&hour=12', after: p => setHourLegacy(p, 12) },
  { name: '4_heat_night',   url: '/cesium_view.html?plateau=textured&hour=12', after: p => setHourLegacy(p, 21) },
  // agent layer: CZML loads, clock is unfrozen, entities exist. Recorded in the report by diag().
  { name: '5_energy_agents', url: ENERGY_QA_BASE + '&agents=1&scenario=proactive' },
];

// Oblique buildings+sky camera over Nihonbashi (same geography for both twins).
const frameSmoke = (page) => page.evaluate(() => {
  const v = window.__viewer; if (!v) return;
  v.camera.setView({
    destination: Cesium.Cartesian3.fromDegrees(139.7770, 35.6800, 320),
    orientation: { heading: Cesium.Math.toRadians(25), pitch: Cesium.Math.toRadians(-16), roll: 0 },
  });
  v.scene.requestRender && v.scene.requestRender();
});

async function runSmoke() {
  const OUT = path.resolve('outputs/qa');
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await launch(1366, 854);
  const report = [];
  for (const c of SMOKE_CASES) {
    const page = await browser.newPage();
    const errors = [];
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 160)); });
    page.on('pageerror', e => errors.push('PAGEERROR: ' + String(e.message || e).slice(0, 160)));
    console.log(`\n=== ${c.name} -> ${c.url}`);
    try {
      await page.goto(BASE + c.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await page.waitForFunction('window.__READY === true', { timeout: 30000 }).catch(() => console.log('  (no __READY)'));
      await frameSmoke(page);
      const tiles = await waitForTiles(page, 48000);
      console.log('  tiles:', JSON.stringify(tiles));
      if (c.after) await c.after(page);
      await sleep(4000);
      const d = await diag(page);
      const file = path.join(OUT, c.name + '.png');
      await page.screenshot({ path: file });
      report.push({ name: c.name, url: c.url, tiles, ...d, errorCount: errors.length, errors: [...new Set(errors)].slice(0, 5) });
      console.log('  diag:', JSON.stringify(d));
      console.log('  shot:', file);
    } catch (e) {
      report.push({ name: c.name, url: c.url, fatal: String(e).slice(0, 200) });
      console.log('  FATAL', e);
    }
    await page.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
  console.log('\nReport -> outputs/qa/report.json');
}

// ---------------------------------------------------------------- figure mode

// geodetic pose -> twin_view.html local street frame (x east, y up, z north)
function poseToLocal(cam, F) {
  const x = (cam.lon - F.anchor_lng) * F.m_per_deg_lng;
  const z = (cam.lat - F.anchor_lat) * F.m_per_deg_lat;
  const y = cam.height_m - F.ground_ellipsoid_m;
  const D = F.look_distance_m ?? 200;
  const hd = (cam.heading_deg ?? 0) * Math.PI / 180;
  const pd = (cam.pitch_deg ?? 0) * Math.PI / 180;
  // heading 0 = north (+z), clockwise; pitch negative = down
  const tx = x + D * Math.sin(hd);
  const tz = z + D * Math.cos(hd);
  const ty = y + D * Math.tan(pd);
  return [x, y, z, tx, ty, tz].map(v => +v.toFixed(2));
}

const applyCesiumPose = (page, cam) => page.evaluate((c) => {
  const v = window.__viewer; if (!v) return false;
  v.camera.setView({
    destination: Cesium.Cartesian3.fromDegrees(c.lon, c.lat, c.height_m),
    orientation: {
      heading: Cesium.Math.toRadians(c.heading_deg || 0),
      pitch: Cesium.Math.toRadians(c.pitch_deg || 0),
      roll: Cesium.Math.toRadians(c.roll_deg || 0),
    },
  });
  v.scene.requestRender && v.scene.requestRender();
  return true;
}, cam);

// Drive the energy view through its OWN controls, so the screenshot reflects a UI state a
// user can actually reach (and the HUD/legend text stays consistent with the colours).
const applyEnergyUI = (page, ui) => page.evaluate((u) => {
  const out = {};
  const $ = id => document.getElementById(id);
  if (u.metric != null) {
    const KEYS = ['energy', 'intensity', 'cost', 'wwr', 'occupancy'];
    const i = KEYS.indexOf(u.metric);
    const s = $('metricSlider');
    if (i >= 0 && s) { s.value = String(i); s.dispatchEvent(new Event('input')); out.metric = u.metric; }
    else out.metric = `UNAVAILABLE:${u.metric}`;
  }
  const click = (hostId, key) => {
    const host = $(hostId); if (!host) return false;
    for (const el of host.children) if (el.dataset.k === key) { el.click(); return true; }
    return false;
  };
  if (u.demand != null) out.demand = click('demandBtns', u.demand) ? u.demand : `UNAVAILABLE:${u.demand}`;
  if (u.supply != null) out.supply = click('supplyBtns', u.supply) ? u.supply : `UNAVAILABLE:${u.supply}`;
  if (u.hour != null) {
    const s = $('hourSlider');
    if (s) { s.value = String(u.hour); s.dispatchEvent(new Event('input')); out.hour = u.hour; }
  }
  // The view ships a draggable real/sim splitter down the middle of the screen. For a still
  // figure we park it fully on the "sim" side (photoreal context everywhere, study block
  // clipped out of it so the coloured entities show) and hide the cyan splitter bar.
  if (u.split === 'sim' || u.split === 'real') {
    const v = window.__viewer;
    if (v) { v.scene.splitPosition = (u.split === 'sim') ? 0.0 : 1.0; v.scene.requestRender(); }
    const bar = document.getElementById('splitter'); if (bar) bar.style.display = 'none';
    out.split = u.split;
  }
  out.legend = $('leg-title')?.textContent ?? null;
  out.legend_min = $('lmin')?.textContent ?? null;
  out.legend_max = $('lmax')?.textContent ?? null;
  out.kpi = $('kpi-main')?.textContent ?? null;
  out.kpi_scn = $('kpi-scn')?.textContent ?? null;
  return out;
}, ui);

const applyTwinUI = (page, ui) => page.evaluate((u) => {
  const out = {};
  const tog = (id, want) => {
    const el = document.getElementById(id); if (!el) return null;
    const on = el.classList.contains('on');
    if (on !== want) el.click();
    return document.getElementById(id).classList.contains('on');
  };
  if (u.heat != null) out.heat = tog('t-heat', !!u.heat);
  if (u.det != null) out.det = tog('t-det', !!u.det);
  if (u.trk != null) out.trk = tog('t-trk', !!u.trk);
  if (u.thermal != null) out.thermal = tog('t-therm', !!u.thermal);
  if (u.hour != null) {
    const s = document.getElementById('hour');
    if (s) { s.value = String(u.hour); s.dispatchEvent(new Event('input')); out.hour = u.hour; }
  }
  if (u.paused) {                                   // freeze the sim clock for a still frame
    const p = document.getElementById('play');
    if (p && p.classList.contains('on')) p.click();
    out.paused = !document.getElementById('play')?.classList.contains('on');
  }
  out.clock = document.getElementById('clock')?.textContent ?? null;
  out.heat_label = document.getElementById('heat-label')?.textContent ?? null;
  out.scenario = document.getElementById('scen-label')?.textContent ?? null;
  return out;
}, ui);

function buildUrl(pose, extraQuery) {
  const q = new URLSearchParams({ ...(pose.query || {}), ...(extraQuery || {}) });
  const s = q.toString();
  return BASE + pose.view + (s ? (pose.view.includes('?') ? '&' : '?') + s : '');
}

async function capturePanel(browser, pose, panel, outDir, POSES) {
  const isEnergy = pose.view.includes('energy_cesium_view');
  const ui = { ...(pose.ui || {}), ...((panel && panel.ui) || {}) };
  const name = pose.name + (panel ? `__${panel.label}` : '');
  const file = path.join(outDir, name + '.png');

  const page = await browser.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 200)); });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + String(e.message || e).slice(0, 200)));

  const rec = { id: pose.id, name, file: path.relative(process.cwd(), file), engine: pose.engine, camera: pose.camera, ui_requested: ui };
  try {
    if (pose.engine === 'three') {
      const local = poseToLocal(pose.camera, POSES.frames.twin_local);
      rec.local_camera = { position: local.slice(0, 3), target: local.slice(3) };
      const url = buildUrl(pose, { cam: local.join(','), hour: String(ui.hour ?? pose.query?.hour ?? 14) });
      rec.url = url;
      console.log(`  -> ${url}`);
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 120000 });
      // readiness: the city glb loader removes #loading only after the mesh is placed
      const t0 = Date.now();
      await page.waitForFunction("!document.getElementById('loading')", { timeout: 240000 });
      rec.city_load_s = +((Date.now() - t0) / 1000).toFixed(1);
      rec.ui_applied = await applyTwinUI(page, ui);
      await sleep(8000);                                   // let swiftshader draw a full frame
    } else {
      const url = buildUrl(pose, {});
      rec.url = url;
      console.log(`  -> ${url}`);
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 120000 });
      await page.waitForFunction('window.__READY === true', { timeout: 90000 });
      await applyCesiumPose(page, pose.camera);
      // UI first, THEN wait for tiles: parking the real/sim splitter changes which half of
      // each split tileset is on screen, and Cesium only streams what it can see, so the
      // split has to be set before the streaming-convergence wait or half the frame stays
      // empty. applyEnergyUI is idempotent, so it is re-run afterwards to read final labels.
      if (isEnergy) await applyEnergyUI(page, ui);
      rec.tiles = await waitForTiles(page, 90000, 4);
      rec.ui_applied = isEnergy ? await applyEnergyUI(page, ui) : null;
      await sleep(6000);
      rec.diag = await diag(page);
    }
    await page.screenshot({ path: file });
    rec.bytes = fs.statSync(file).size;
    rec.image = pngStats(fs.readFileSync(file));
    console.log(`     ${JSON.stringify(rec.image)}  ${(rec.bytes / 1024).toFixed(0)} kB -> ${rec.file}`);
  } catch (e) {
    rec.fatal = String(e.message || e).slice(0, 300);
    console.log('     FATAL', rec.fatal);
    try { await page.screenshot({ path: file.replace(/\.png$/, '_FAILED.png') }); } catch {}
  }
  rec.errorCount = errors.length;
  rec.errors = [...new Set(errors)].slice(0, 6);
  await page.close();
  return rec;
}

async function runPoses() {
  const posePath = path.resolve(typeof flag('poses') === 'string' ? flag('poses') : 'outputs/qa/camera_poses.json');
  const outDir = path.resolve(flag('out') || 'outputs/figures');
  fs.mkdirSync(outDir, { recursive: true });
  const POSES = JSON.parse(fs.readFileSync(posePath, 'utf8'));
  const only = flag('only') ? String(flag('only')).split(',').map(s => s.trim()) : null;
  const all = [...(POSES.poses || []), ...(POSES.variants || [])].filter(p => !only || only.includes(p.id));

  const { width, height } = POSES.render || { width: 1920, height: 1200 };
  console.log(`poses: ${posePath}\nout:   ${outDir}\nsize:  ${width}x${height}\n`);
  const browser = await launch(width, height);
  const report = [];
  for (const pose of all) {
    console.log(`\n=== ${pose.id} ${pose.title || pose.name}`);
    const panels = pose.panels && pose.panels.length ? pose.panels : [null];
    for (const panel of panels) report.push(await capturePanel(browser, pose, panel, outDir, POSES));
  }
  await browser.close();
  const reportPath = path.join(outDir, 'capture_report.json');
  fs.writeFileSync(reportPath, JSON.stringify({ pose_file: path.relative(process.cwd(), posePath), render: POSES.render, captured: report }, null, 2));
  console.log(`\nReport -> ${path.relative(process.cwd(), reportPath)}`);
  const bad = report.filter(r => r.fatal || !r.image || r.image.error || (r.image.stddev ?? 0) < 8 || (r.image.unique_colors ?? 0) < 200);
  if (bad.length) { console.log('\nSUSPECT/FAILED:', bad.map(b => b.name).join(', ')); process.exitCode = 1; }
}

await (POSE_MODE ? runPoses() : runSmoke());
