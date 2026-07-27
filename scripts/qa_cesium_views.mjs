// QA harness for the Cesium twins. Loads each view headless (swiftshader WebGL),
// POLLS until the globe + 3D tileset actually finish streaming, frames an oblique
// camera that includes sky (so day/night sun shading is visible), drives day/night,
// screenshots, and records console errors + scene diagnostics.
//
//   node scripts/qa_cesium_views.mjs
//
// Server must be up on :8889 (python scripts/serve_outputs.py).
import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

const BASE = process.env.QA_BASE || 'http://localhost:8889';
const OUT = path.resolve('outputs/qa');
fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// Oblique buildings+sky camera over Nihonbashi (same geography for both twins).
// Lower pitch keeps the horizon/sky in frame so day vs night reads clearly.
const frame = (page) => page.evaluate(() => {
  const v = window.__viewer; if (!v) return;
  v.camera.setView({
    destination: Cesium.Cartesian3.fromDegrees(139.7770, 35.6800, 320),
    orientation: { heading: Cesium.Math.toRadians(25), pitch: Cesium.Math.toRadians(-16), roll: 0 },
  });
  v.scene.requestRender && v.scene.requestRender();
});

// Poll until terrain/imagery + tileset content have actually streamed in (or timeout).
const waitForTiles = async (page, maxMs = 48000) => {
  const t0 = Date.now();
  while (Date.now() - t0 < maxMs) {
    const s = await page.evaluate(() => {
      const v = window.__viewer; const t = window.__tileset;
      const st = t && t.statistics ? t.statistics : {};
      return {
        globe: v?.scene?.globe?.tilesLoaded ?? false,
        ready: st.numberOfTilesWithContentReady ?? 0,
        sel: st.selected ?? 0,
      };
    });
    if (s.globe && s.ready > 8) return s;        // enough buildings on screen
    await sleep(1500);
  }
  return page.evaluate(() => ({ globe: window.__viewer?.scene?.globe?.tilesLoaded, ready: window.__tileset?.statistics?.numberOfTilesWithContentReady ?? 0, timedOut: true }));
};

const setHour = (page, h) => page.evaluate((hh) => {
  const v = window.__viewer; if (v) v.clock.shouldAnimate = false;
  const s = document.getElementById('hslider');
  if (s) { s.value = String(hh); s.dispatchEvent(new Event('input')); }
}, h);

const clickTime = (page, label) => page.evaluate((lab) => {
  const host = document.getElementById('timeBtns'); if (!host) return false;
  for (const b of host.children) if (b.textContent.trim() === lab) { b.click(); return true; }
  return false;
}, label);

const CASES = [
  { name: '1_energy_day',   url: '/energy_cesium_view.html', after: p => clickTime(p, 'DAY') },
  { name: '2_energy_night', url: '/energy_cesium_view.html', after: p => clickTime(p, 'NIGHT') },
  { name: '3_heat_day',     url: '/cesium_view.html?plateau=textured&hour=12', after: p => setHour(p, 12) },
  { name: '4_heat_night',   url: '/cesium_view.html?plateau=textured&hour=12', after: p => setHour(p, 21) },
];

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
  };
});

const browser = await puppeteer.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--use-gl=angle', '--use-angle=swiftshader',
         '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-dev-shm-usage',
         '--enable-webgl', '--window-size=1366,854'],
  defaultViewport: { width: 1366, height: 854 },
});

const report = [];
for (const c of CASES) {
  const page = await browser.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 160)); });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + String(e.message || e).slice(0, 160)));

  console.log(`\n=== ${c.name} -> ${c.url}`);
  try {
    await page.goto(BASE + c.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForFunction('window.__READY === true', { timeout: 30000 }).catch(() => console.log('  (no __READY)'));
    await frame(page);                              // oblique buildings + sky
    const tiles = await waitForTiles(page);         // stream the visible tiles in
    console.log('  tiles:', JSON.stringify(tiles));
    if (c.after) await c.after(page);               // set day / night
    await sleep(4000);                              // re-render lit + heat
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
