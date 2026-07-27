// QA twin_view.html after the boundary rework: confirm no offset cyan boundary wall,
// streetscape covers the modeled area, day & night render. Three.js + local glb renders
// reliably headless (no tile streaming).
import puppeteer from 'puppeteer';
import path from 'path';
const BASE = 'http://localhost:8889';
const OUT = path.resolve('outputs/qa');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const setHour = (page, h) => page.evaluate((hh) => {
  const s = document.getElementById('hour'); if (s) { s.value = String(hh); s.dispatchEvent(new Event('input')); }
}, h);
const clickBtn = (page, label) => page.evaluate((lab) => {
  for (const b of document.querySelectorAll('button,div,span')) if (b.textContent.trim() === lab) { b.click(); return true; }
  return false;
}, label);

const browser = await puppeteer.launch({ headless: true,
  args: ['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader',
         '--ignore-gpu-blocklist','--disable-dev-shm-usage','--enable-webgl'],
  defaultViewport: { width: 1366, height: 854 } });

const page = await browser.newPage();
const errs = [];
page.on('console', m => { if (m.type()==='error') errs.push(m.text().slice(0,160)); });
page.on('pageerror', e => errs.push('PAGEERR: '+String(e.message||e).slice(0,160)));

await page.goto(BASE + '/twin_view.html', { waitUntil: 'domcontentloaded' });
// wait for the city glb to finish loading (the #loading element is removed on success)
await page.waitForFunction(() => {
  const l = document.getElementById('loading');
  return !l || /FAILED/.test(l.textContent);
}, { timeout: 40000 }).catch(() => console.log('(loading wait timed out)'));
await sleep(4000);

const diag = await page.evaluate(() => ({
  loading: document.getElementById('loading')?.textContent ?? 'gone',
  canvas: !!document.querySelector('canvas'),
}));
console.log('diag:', JSON.stringify(diag), 'errs:', errs.length, [...new Set(errs)].slice(0,4));

// top-down alignment check: look straight down so building footprints vs streets read clearly
const topDown = (page) => page.evaluate(() => {
  const c = window.__cam, ct = window.__controls; if (!c || !ct) return;
  const t = ct.target; c.position.set(t.x + 1, 1100, t.z + 1); ct.target.set(t.x, 0, t.z); ct.update();
});
const oblique = (page) => page.evaluate(() => {
  const c = window.__cam, ct = window.__controls; if (!c || !ct) return;
  const t = ct.target; c.position.set(t.x - 120, 230, t.z + 360); ct.target.set(t.x, 20, t.z); ct.update();
});
const shots = [
  { name: 'T1_twin_day',     hour: 13, mode: null, cam: null },
  { name: 'T2_twin_night',   hour: 22, mode: null, cam: null },
  { name: 'T3_twin_heat',    hour: 14, mode: 'HEAT', cam: null },
  { name: 'T4_twin_topdown', hour: 13, mode: null, cam: topDown },   // alignment check
  { name: 'T5_twin_street',  hour: 13, mode: null, cam: oblique },   // close street-level align
];
for (const s of shots) {
  if (s.mode) await clickBtn(page, s.mode);
  await setHour(page, s.hour);
  if (s.cam) await s.cam(page);
  await sleep(2500);
  await page.screenshot({ path: path.join(OUT, s.name + '.png') });
  console.log('shot', s.name);
}
await browser.close();
console.log('done');
