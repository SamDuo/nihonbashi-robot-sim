"""Footprint registration: align the welded PLATEAU city onto the real OSM lots.

Rasterises PLATEAU building footprints (per-chunk XZ bbox, recentred like the
merge) and OSM building footprints (scene.json polys) into occupancy grids,
then searches rotations around the dominant-angle estimate and uses FFT
cross-correlation to find the translation that maximises footprint overlap.

Prints the viewer transform (rot deg, dx, dz) and writes /tmp/registration.png
(OSM = red, registered PLATEAU = green) so alignment is visible directly.
"""
import glob, json
import numpy as np
from PIL import Image, ImageDraw
from scipy.signal import fftconvolve

C = 2.0  # raster cell size (m)

# ---- PLATEAU chunk XZ bboxes (from gltf headers, recentred on cluster) ----
boxes = []
for f in glob.glob('/tmp/t352_lod00/*_LOD00.gltf'):
    try:
        g = json.load(open(f))
    except Exception:
        continue
    pos = [a for a in g.get('accessors', []) if a.get('name') == 'POSITION' and a.get('min')]
    if not pos:
        continue
    boxes.append((min(a['min'][0] for a in pos), max(a['max'][0] for a in pos),
                  min(a['min'][2] for a in pos), max(a['max'][2] for a in pos)))
boxes = np.array(boxes)
cx = (boxes[:, 0].min() + boxes[:, 1].max()) / 2
cz = (boxes[:, 2].min() + boxes[:, 3].max()) / 2
rb = boxes - np.array([cx, cx, cz, cz])     # recentred [x0,x1,z0,z1]
print(f"PLATEAU: {len(rb)} chunks, recenter (cx,cz)=({cx:.1f},{cz:.1f})")

# ---- OSM occupancy raster (scene coords) ----
s = json.load(open('outputs/twin/scene.json'))
polys = [np.array(b['poly']) for b in s['buildings']]
allp = np.concatenate(polys)
x0, x1 = allp[:, 0].min() - 60, allp[:, 0].max() + 60
z0, z1 = allp[:, 1].min() - 60, allp[:, 1].max() + 60
W, H = int((x1 - x0) / C), int((z1 - z0) / C)
def px(x, z): return ((x - x0) / C, (z - z0) / C)
oimg = Image.new('L', (W, H), 0)
od = ImageDraw.Draw(oimg)
for p in polys:
    od.polygon([px(x, z) for x, z in p], fill=1)
O = np.asarray(oimg, np.float32)
print(f"OSM raster {W}x{H} cells, {O.sum():.0f} filled")

def rasterize(theta, tx, tz):
    """Rasterize PLATEAU footprints at scene = Rot_y(theta)*recentred + (tx,tz)."""
    ct, st = np.cos(theta), np.sin(theta)
    img = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(img)
    for x0b, x1b, z0b, z1b in rb:
        pts = []
        for ux, uz in ((x0b, z0b), (x1b, z0b), (x1b, z1b), (x0b, z1b)):
            rx = ux * ct + uz * st          # three.js rotation.y convention
            rz = -ux * st + uz * ct
            pts.append(px(rx + tx, rz + tz))
        d.polygon(pts, fill=1)
    return np.asarray(img, np.float32)

# ---- search rotation; correlate to find best translation ----
best = None
for deg in range(-44, -25):
    T = rasterize(np.radians(deg), 0, 0)          # centred at scene origin... shift to grid centre
    # build a centred template (cluster origin at grid centre) for correlation
    Tc = rasterize(np.radians(deg), x0 + W * C / 2, z0 + H * C / 2)
    corr = fftconvolve(O, Tc[::-1, ::-1], mode='same')
    pr, pc = np.unravel_index(int(np.argmax(corr)), corr.shape)
    tx, tz = x0 + pc * C, z0 + pr * C
    score = corr.max()
    if best is None or score > best[0]:
        best = (score, deg, tx, tz)
    print(f"  rot={deg:4d}  -> dx,dz=({tx:6.0f},{tz:6.0f})  overlap={score:.0f}")

score, deg, tx, tz = best
print(f"\n>>> BEST: rot={deg} deg, place at ({tx:.0f},{tz:.0f})  overlap={score:.0f}")
print(f">>> viewer: ?rot={deg}&dx={tx-500:.0f}&dz={tz-250:.0f}   (dx/dz are vs agent-grid centre 500,250)")

# ---- overlay preview: OSM red, registered PLATEAU green ----
P = rasterize(np.radians(deg), tx, tz)
rgb = np.zeros((H, W, 3), np.uint8)
rgb[..., 0] = (O > 0) * 200           # OSM red
rgb[..., 1] = (P > 0) * 220           # PLATEAU green  (overlap -> yellow)
Image.fromarray(rgb).save('/tmp/registration.png')
overlap_frac = ((O > 0) & (P > 0)).sum() / max((P > 0).sum(), 1)
print(f">>> {overlap_frac*100:.0f}% of PLATEAU footprint lands on an OSM building")
print(">>> wrote /tmp/registration.png")
