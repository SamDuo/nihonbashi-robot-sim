// Focused QA: frame the 22 coloured study buildings and confirm they stand ON the
// street grid (not sunk). Pushes the split fully to the SIM side so the whole frame
// is roadmap + coloured buildings (no photoreal), plus a real|sim split shot.
import puppeteer from 'puppeteer';
import path from 'path';
const BASE = 'http://localhost:8889';
const OUT = path.resolve('outputs/qa');
const sleep = ms => new Promise(r => setTimeout(r, ms));

// camera south of the block (139.7791, 35.6882) looking north over it
const frameBlock = (page) => page.evaluate(() => {
  const v = window.__viewer;
  v.camera.setView({
    destination: Cesium.Cartesian3.fromDegrees(139.77915, 35.68575, 300),
    orientation: { heading: Cesium.Math.toRadians(4), pitch: Cesium.Math.toRadians(-40), roll: 0 },
  });
  v.scene.requestRender && v.scene.requestRender();
});
const setSplit = (page, p) => page.evaluate((pp) => {
  const v = window.__viewer; v.scene.splitPosition = pp;
  const s = document.getElementById('splitter'); if (s) s.style.left = (pp*100)+'%';
  v.scene.requestRender && v.scene.requestRender();
}, p);
const clickTime = (page, label) => page.evaluate((lab) => {
  const host = document.getElementById('timeBtns'); if (!host) return;
  for (const b of host.children) if (b.textContent.trim() === lab) b.click();
}, label);
const waitForTiles = async (page, maxMs = 45000) => {
  const t0 = Date.now();
  while (Date.now() - t0 < maxMs) {
    const r = await page.evaluate(() => ({
      g: window.__viewer?.scene?.globe?.tilesLoaded,
      r: window.__tileset?.statistics?.numberOfTilesWithContentReady ?? 0 }));
    if (r.r > 8) return r; await sleep(1500);
  }
  return { timedOut: true };
};

const browser = await puppeteer.launch({
  headless: true,
  args: ['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader',
         '--ignore-gpu-blocklist','--disable-dev-shm-usage','--enable-webgl'],
  defaultViewport: { width: 1366, height: 854 },
});

const shots = [
  { name: '5_block_sim_day',   split: 0.001, time: 'DAY'   },   // all sim: coloured buildings on street grid
  { name: '6_block_sim_night', split: 0.001, time: 'NIGHT' },   // same, night lighting
  { name: '7_block_split_day', split: 0.5,   time: 'DAY'   },   // real (left) | sim (right) over the block
];

for (const s of shots) {
  const page = await browser.newPage();
  await page.goto(BASE + '/energy_cesium_view.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction('window.__READY === true', { timeout: 30000 }).catch(() => {});
  await frameBlock(page);
  await waitForTiles(page);
  await setSplit(page, s.split);
  await clickTime(page, s.time);
  await sleep(3500);
  const d = await page.evaluate(() => ({
    entities: window.__viewer?.entities?.values?.length,
    tilesetReady: window.__tileset?.statistics?.numberOfTilesWithContentReady,
    split: window.__viewer?.scene?.splitPosition,
  }));
  await page.screenshot({ path: path.join(OUT, s.name + '.png') });
  console.log(s.name, JSON.stringify(d));
  await page.close();
}
await browser.close();
console.log('done');
