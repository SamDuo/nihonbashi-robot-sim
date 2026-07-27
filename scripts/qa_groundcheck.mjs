// Diagnostic: measure the actual heights at the study block so we can pin the buildings
// to the right ground (no guessing). Logs terrain height, photoreal tileset base height,
// and the rendered surface height at the block centroid.
import puppeteer from 'puppeteer';
const BASE = 'http://localhost:8889';
const sleep = ms => new Promise(r => setTimeout(r, ms));

const browser = await puppeteer.launch({ headless: true,
  args: ['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader',
         '--ignore-gpu-blocklist','--disable-dev-shm-usage','--enable-webgl'],
  defaultViewport: { width: 1200, height: 800 } });
const page = await browser.newPage();
page.on('console', m => { const t = m.text(); if (/GROUNDCHECK|Error/i.test(t)) console.log(' page:', t); });
await page.goto(BASE + '/energy_cesium_view.html', { waitUntil: 'domcontentloaded' });
await page.waitForFunction('window.__READY === true', { timeout: 30000 }).catch(()=>{});
// frame the block + let terrain/tiles load
await page.evaluate(() => {
  const v = window.__viewer;
  v.camera.setView({ destination: Cesium.Cartesian3.fromDegrees(139.77915, 35.6857, 300),
    orientation: { heading: 0, pitch: Cesium.Math.toRadians(-45), roll: 0 } });
});
await sleep(30000);

const out = await page.evaluate(async () => {
  const v = window.__viewer, sc = v.scene;
  const lng = 139.7791, lat = 35.6882;
  const res = {};
  // 1) terrain height at the block centroid
  try {
    const c = [Cesium.Cartographic.fromDegrees(lng, lat)];
    const u = await Cesium.sampleTerrainMostDetailed(v.terrainProvider, c);
    res.terrainH = +u[0].height.toFixed(2);
  } catch (e) { res.terrainErr = String(e).slice(0, 80); }
  // 2) photoreal tileset base (bounding sphere center height minus radius is rough; use root)
  try {
    const t = window.__tileset;
    const carto = Cesium.Cartographic.fromCartesian(t.boundingSphere.center);
    res.tilesetCenterH = +carto.height.toFixed(2);
    res.tilesetRadius = +t.boundingSphere.radius.toFixed(0);
  } catch (e) { res.tileErr = String(e).slice(0, 80); }
  // 3) rendered surface height at the block centroid (depth pick)
  try {
    sc.globe.depthTestAgainstTerrain = true;
    const h = sc.sampleHeight(Cesium.Cartographic.fromDegrees(lng, lat));
    res.sceneH = (h == null) ? null : +h.toFixed(2);
    const h2 = sc.sampleHeight(Cesium.Cartographic.fromDegrees(139.7770, 35.6870)); // a street point west
    res.sceneH_street = (h2 == null) ? null : +h2.toFixed(2);
  } catch (e) { res.sampleErr = String(e).slice(0, 80); }
  return res;
});
console.log('GROUNDCHECK', JSON.stringify(out, null, 1));
await browser.close();
