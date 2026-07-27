// QA the energy view's stylized glb context (?context=glb): verify the georeferenced
// LOD2 model loads, sits aligned on the streets, and lights its windows at night.
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
const setHour = (page, h) => page.evaluate((hh) => {
  const s = document.getElementById('hourSlider'); if (s) { s.value = String(hh); s.dispatchEvent(new Event('input')); }
}, h);

const browser = await puppeteer.launch({ headless: true,
  args: ['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader',
         '--ignore-gpu-blocklist','--disable-dev-shm-usage','--enable-webgl'],
  defaultViewport: { width: 1366, height: 854 } });

const page = await browser.newPage();
const errs = [];
page.on('console', m => { if (m.type()==='error') errs.push(m.text().slice(0,160)); });
page.on('pageerror', e => errs.push('PAGEERR: '+String(e.message||e).slice(0,160)));
await page.goto(BASE + '/energy_cesium_view.html?context=glb', { waitUntil: 'domcontentloaded' });
await page.waitForFunction('window.__READY === true', { timeout: 30000 }).catch(()=>{});
await sleep(9000);   // model loads (1.6MB local, no streaming)
const d = await page.evaluate(() => ({ ready: window.__READY, tilesLoaded: window.__tilesLoaded,
  prims: window.__viewer?.scene?.primitives?.length, status: document.getElementById('status')?.textContent }));
console.log('diag:', JSON.stringify(d), 'errs:', errs.length, [...new Set(errs)].slice(0,4));

for (const c of [
  { name: 'G1_glb_day',     hour: 13, cam: [139.7775,35.6800,470,16,-21] },
  { name: 'G2_glb_night',   hour: 22, cam: [139.7775,35.6800,470,16,-21] },
  { name: 'G3_glb_topdown', hour: 13, cam: [139.7785,35.6840,900,0,-80] },
]) {
  await view(page, ...c.cam);
  await setHour(page, c.hour);
  await sleep(2500);
  await page.screenshot({ path: path.join(OUT, c.name + '.png') });
  console.log('shot', c.name);
}
await browser.close();
console.log('done');
