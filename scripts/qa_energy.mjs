// QA for the rebuilt energy view: designed streetscape, real context kept on the sim
// side, solid study buildings, auto-play colour/time sliders, day vs night.
import puppeteer from 'puppeteer';
import path from 'path';
const BASE = 'http://localhost:8889';
const OUT = path.resolve('outputs/qa');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const view = (page, lng, lat, alt, head, pit) => page.evaluate((a) => {
  const v = window.__viewer;
  v.camera.setView({ destination: Cesium.Cartesian3.fromDegrees(a.lng, a.lat, a.alt),
    orientation: { heading: Cesium.Math.toRadians(a.head), pitch: Cesium.Math.toRadians(a.pit), roll: 0 } });
  v.scene.requestRender && v.scene.requestRender();
}, { lng, lat, alt, head, pit });
const setSplit = (page, p) => page.evaluate((pp) => {
  const v = window.__viewer; v.scene.splitPosition = pp;
  const s = document.getElementById('splitter'); if (s) s.style.left = (pp*100)+'%';
  v.scene.requestRender && v.scene.requestRender();
}, p);
const setHour = (page, h) => page.evaluate((hh) => {
  const s = document.getElementById('hourSlider'); if (s) { s.value = String(hh); s.dispatchEvent(new Event('input')); }
}, h);
const setMetric = (page, i) => page.evaluate((ii) => {
  const s = document.getElementById('metricSlider'); if (s) { s.value = String(ii); s.dispatchEvent(new Event('input')); }
}, i);
const waitForTiles = async (page, maxMs = 45000) => {
  const t0 = Date.now();
  while (Date.now() - t0 < maxMs) {
    const r = await page.evaluate(() => ({ g: window.__viewer?.scene?.globe?.tilesLoaded,
      r: window.__tileset?.statistics?.numberOfTilesWithContentReady ?? 0 }));
    if (r.r > 8) return r; await sleep(1500);
  }
  return { timedOut: true };
};
const diag = (page) => page.evaluate(() => ({
  ready: window.__READY, base: window.__BASE_ASSET ?? 'designed',
  tilesetReady: window.__tileset?.statistics?.numberOfTilesWithContentReady,
  primitives: window.__viewer?.scene?.primitives?.length, entities: window.__viewer?.entities?.values?.length,
  status: document.getElementById('status')?.textContent }));

const browser = await puppeteer.launch({ headless: true,
  args: ['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader',
         '--ignore-gpu-blocklist','--disable-dev-shm-usage','--enable-webgl'],
  defaultViewport: { width: 1366, height: 854 } });

const CASES = [
  { name: 'E1_wide_split_day',  split: 0.5,  hour: 13, metric: 0, cam: [139.7791,35.6858,330,22,-17] },
  { name: 'E2_block_sim_day',   split: 0.18, hour: 13, metric: 0, cam: [139.77915,35.68585,280,6,-38] },
  { name: 'E3_block_sim_night', split: 0.18, hour: 21, metric: 0, cam: [139.77915,35.68585,280,6,-38] },
  { name: 'E4_block_eui_day',   split: 0.18, hour: 13, metric: 1, cam: [139.77915,35.68585,280,6,-38] },
];
const report = [];
for (const c of CASES) {
  const page = await browser.newPage();
  const errs = [];
  page.on('console', m => { if (m.type()==='error') errs.push(m.text().slice(0,140)); });
  page.on('pageerror', e => errs.push('PAGEERR: '+String(e.message||e).slice(0,140)));
  await page.goto(BASE + '/energy_cesium_view.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction('window.__READY === true', { timeout: 30000 }).catch(()=>{});
  await view(page, ...c.cam);
  await waitForTiles(page);
  await setSplit(page, c.split);
  await setMetric(page, c.metric);
  await setHour(page, c.hour);
  await sleep(4000);
  const d = await diag(page);
  await page.screenshot({ path: path.join(OUT, c.name + '.png') });
  report.push({ name: c.name, ...d, errs: [...new Set(errs)].slice(0,4) });
  console.log(c.name, JSON.stringify(d), errs.length ? ('ERR:'+errs.length) : '');
  await page.close();
}
await browser.close();
console.log('\n', JSON.stringify(report, null, 1));
