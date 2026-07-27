// Capture the study block under each COLOUR BY metric, from ONE fixed camera, for the
// presentation. Same angle + location, only the colour metric changes.
import puppeteer from 'puppeteer';
import path from 'path';
const BASE = 'http://localhost:8889';
const OUT = path.resolve('outputs/qa');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const frameBlock = (page) => page.evaluate(() => {
  const v = window.__viewer;
  v.camera.setView({ destination: Cesium.Cartesian3.fromDegrees(139.77915, 35.68565, 300),
    orientation: { heading: Cesium.Math.toRadians(6), pitch: Cesium.Math.toRadians(-42), roll: 0 } });
  v.scene.requestRender && v.scene.requestRender();
});
const setSplit = (page, p) => page.evaluate((pp) => {
  const v = window.__viewer; v.scene.splitPosition = pp;
  const s = document.getElementById('splitter'); if (s) s.style.left = (pp*100)+'%';
  v.scene.requestRender && v.scene.requestRender();
}, p);
const setMetric = (page, i) => page.evaluate((ii) => {
  const s = document.getElementById('metricSlider'); s.value = String(ii); s.dispatchEvent(new Event('input'));
}, i);
const setHour = (page, h) => page.evaluate((hh) => {
  const s = document.getElementById('hourSlider'); s.value = String(hh); s.dispatchEvent(new Event('input'));
}, h);
// wait for the GLOBE terrain to settle — the coloured buildings clamp to terrain, so they
// only render once the visible terrain tiles have loaded.
const settle = async (page, ms=55000) => { const t0=Date.now();
  while (Date.now()-t0<ms){ const r=await page.evaluate(()=>({
      g: window.__viewer?.scene?.globe?.tilesLoaded,
      t: window.__tileset?.statistics?.numberOfTilesWithContentReady??0 }));
    if (r.g && r.t>5) return r; await sleep(2000);} return {timeout:true}; };

const browser = await puppeteer.launch({ headless: true,
  args: ['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader',
         '--ignore-gpu-blocklist','--disable-dev-shm-usage','--enable-webgl'],
  defaultViewport: { width: 1366, height: 854 } });
const page = await browser.newPage();
await page.goto(BASE + '/energy_cesium_view.html', { waitUntil: 'domcontentloaded' });
await page.waitForFunction('window.__READY === true', { timeout: 30000 }).catch(()=>{});
await frameBlock(page);
await setSplit(page, 0.001);   // all sim side: clean coloured buildings on the street grid
await setHour(page, 13);
await frameBlock(page);        // re-assert the camera, then wait for terrain to load
const st = await settle(page);
console.log('settle:', JSON.stringify(st));
await sleep(3000);
const METRICS = ['energy','eui','cost','wwr'];
for (let i = 0; i < 4; i++) {
  await setMetric(page, i);
  await page.evaluate(() => window.__viewer.scene.requestRender());
  await sleep(3000);
  await page.screenshot({ path: path.join(OUT, `M${i}_${METRICS[i]}.png`) });
  console.log('shot', `M${i}_${METRICS[i]}`);
}
await browser.close();
console.log('done');
