"""Download the PLATEAU LOD2 (Cesium 3D Tiles) buildings over the Nihonbashi twin
area and merge them into ONE georeferenced glb, in the SAME local-metre frame as the
OSM streets (scene.json anchor). Because every vertex is placed by its true ECEF
position, the buildings line up with the street grid by construction — no rotation hack.

Pipeline per tile:  b3dm → strip header → glTF(Draco) → decode → (y-up→z-up) + CESIUM_RTC
→ ECEF → geodetic → local metres (x=east, y=height, z=north) about the scene anchor.

Run:  python scripts/fetch_plateau_lod2.py
Out:  outputs/twin/plateau/nihonbashi_lod2.glb
"""
from __future__ import annotations
import json, urllib.request, struct, math, sys
from pathlib import Path
import numpy as np
import DracoPy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "twin" / "plateau" / "nihonbashi_lod2.glb"
BASE = ('https://assets.cms.plateau.reearth.io/assets/01/8c112f-4957-409a-9b43-d86308c7b74a/'
        '13102_chuo-ku_pref_2023_citygml_1_op_bldg_3dtiles_13102_chuo-ku_lod2/')

# scene anchor (must match outputs/twin/scene.json grid.anchor_*) so buildings share the
# street frame.
A_LAT, A_LNG = 35.681, 139.772
MLAT = 111320.0
MLNG = 111320.0 * math.cos(math.radians(A_LAT))
# twin area in degrees (a little past the boundary bbox) to pick which tiles to fetch
LNG0, LNG1, LAT0, LAT1 = 139.766, 139.789, 35.675, 35.693

def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read() if binary else r.read().decode('utf-8', 'replace')

# WGS84 ECEF -> geodetic (lat, lon, height)
_A = 6378137.0; _F = 1/298.257223563; _B = _A*(1-_F); _E2 = _F*(2-_F); _EP2 = (_A*_A-_B*_B)/(_B*_B)
def ecef2geo(x, y, z):
    p = np.hypot(x, y); th = np.arctan2(_A*z, _B*p)
    lat = np.arctan2(z + _EP2*_B*np.sin(th)**3, p - _E2*_A*np.cos(th)**3)
    lon = np.arctan2(y, x)
    N = _A/np.sqrt(1-_E2*np.sin(lat)**2)
    h = p/np.cos(lat) - N
    return np.degrees(lat), np.degrees(lon), h

def leaf_tiles():
    ts = json.loads(fetch(BASE + 'tileset.json'))
    tiles = []
    def walk(t):
        kids = t.get('children', [])
        c = t.get('content'); bv = t.get('boundingVolume', {})
        if c and not kids and 'region' in bv:           # leaf = deepest detail
            tiles.append((c['uri'], bv['region']))
        for ch in kids:
            walk(ch)
    walk(ts['root'])
    def overlap(r):
        return not (math.degrees(r[2]) < LNG0 or math.degrees(r[0]) > LNG1
                    or math.degrees(r[3]) < LAT0 or math.degrees(r[1]) > LAT1)
    return [(u, r) for u, r in tiles if overlap(r)]

def b3dm_gltf(data):
    h = struct.unpack('<IIIIII', data[4:28])
    off = 28 + h[2] + h[3] + h[4] + h[5]
    glb = data[off:]
    o = 12; js = bn = None
    while o < len(glb):
        clen, ctype = struct.unpack('<II', glb[o:o+8]); o += 8
        if ctype == 0x4E4F534A: js = json.loads(glb[o:o+clen])
        elif ctype == 0x004E4942: bn = glb[o:o+clen]
        o += clen
    return js, bn

def decode_tile(js, bn):
    """Return Nx3 local-frame vertices and Mx3 int faces for every primitive."""
    rtc = js.get('extensions', {}).get('CESIUM_RTC', {}).get('center')
    if not rtc:
        return None
    verts, faces = [], []
    base = 0
    for mesh in js.get('meshes', []):
        for prim in mesh.get('primitives', []):
            dext = prim.get('extensions', {}).get('KHR_draco_mesh_compression')
            if not dext:
                continue
            bv = js['bufferViews'][dext['bufferView']]
            bo = bv.get('byteOffset', 0)
            blob = bn[bo:bo + bv['byteLength']]
            try:
                dm = DracoPy.decode(blob)
            except Exception:
                continue
            P = np.asarray(dm.points, dtype=np.float64).reshape(-1, 3)
            f = np.asarray(dm.faces, dtype=np.int64).reshape(-1, 3)
            # y-up -> z-up, then + RTC (ECEF)
            ex = P[:, 0] + rtc[0]
            ey = -P[:, 2] + rtc[1]
            ez = P[:, 1] + rtc[2]
            lat, lon, hgt = ecef2geo(ex, ey, ez)
            lx = (lon - A_LNG) * MLNG          # east
            lz = (lat - A_LAT) * MLAT          # north
            ly = hgt                           # height (ellipsoidal; grounded later)
            verts.append(np.column_stack([lx, ly, lz]))
            faces.append(f + base)
            base += len(P)
    if not verts:
        return None
    return np.vstack(verts), np.vstack(faces)

def vertex_normals(V, F):
    n = np.zeros(V.shape, np.float64)
    tri = V[F]
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    for i in range(3):
        np.add.at(n, F[:, i], fn)
    ln = np.linalg.norm(n, axis=1, keepdims=True); ln[ln == 0] = 1
    return (n / ln).astype(np.float32)

def pad4(b, fill=b'\x00'):
    return b + fill * ((4 - len(b) % 4) % 4)

def write_glb(path, V, N, F, color=(0.62, 0.64, 0.69)):
    V = V.astype(np.float32); N = N.astype(np.float32); F = F.astype(np.uint32)
    C = np.tile(np.array(color, np.float32), (len(V), 1))
    pos_b = V.tobytes(); nrm_b = N.tobytes(); col_b = C.tobytes(); idx_b = F.tobytes()
    parts = [pos_b, nrm_b, col_b, idx_b]; offs = []; cur = 0
    for p in parts:
        offs.append(cur); cur += len(p)
    bin_blob = b''.join(parts)
    mn = V.min(axis=0).tolist(); mx = V.max(axis=0).tolist()
    n = len(V)
    gltf = {
        "asset": {"version": "2.0", "generator": "fetch_plateau_lod2"},
        "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": "nihonbashi_lod2"}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "COLOR_0": 2},
                                    "indices": 3, "mode": 4}]}],
        "buffers": [{"byteLength": len(bin_blob)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": offs[0], "byteLength": len(pos_b), "target": 34962},
            {"buffer": 0, "byteOffset": offs[1], "byteLength": len(nrm_b), "target": 34962},
            {"buffer": 0, "byteOffset": offs[2], "byteLength": len(col_b), "target": 34962},
            {"buffer": 0, "byteOffset": offs[3], "byteLength": len(idx_b), "target": 34963},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": n, "type": "VEC3", "min": mn, "max": mx},
            {"bufferView": 1, "componentType": 5126, "count": n, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": n, "type": "VEC3"},
            {"bufferView": 3, "componentType": 5125, "count": len(F)*3, "type": "SCALAR"},
        ],
    }
    json_b = pad4(json.dumps(gltf, separators=(",", ":")).encode("utf-8"), b" ")
    bin_b = pad4(bin_blob)
    glb = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(json_b) + 8 + len(bin_b))
    glb += struct.pack('<II', len(json_b), 0x4E4F534A) + json_b
    glb += struct.pack('<II', len(bin_b), 0x004E4942) + bin_b
    path.write_bytes(glb)

# clip to the twin boundary bbox (local metres, from scene.json) + margin, so we don't
# carry buildings far outside the modeled area.
CLIP = (-367.6 - 60, -461.7 - 60, 1358.3 + 60, 1161.0 + 60)   # x0,z0,x1,z1

def main():
    cache = OUT.parent / "_lod2_raw.npz"
    if "--from-cache" in sys.argv and cache.exists():
        d = np.load(cache); V, F = d["V"], d["F"]
        print(f"loaded cache: {len(V)} verts, {len(F)} tris")
    else:
        tiles = leaf_tiles()
        print(f"leaf tiles over twin area: {len(tiles)}")
        Vs, Fs = [], []; base = 0; ok = 0
        for i, (u, r) in enumerate(tiles):
            try:
                data = fetch(BASE + u, binary=True)
                js, bn = b3dm_gltf(data)
                res = decode_tile(js, bn)
                if res is None:
                    continue
                V, F = res
                Vs.append(V); Fs.append(F + base); base += len(V); ok += 1
                if (i+1) % 15 == 0:
                    print(f"  {i+1}/{len(tiles)} tiles, {base} verts so far")
            except Exception as e:
                print(f"  tile {u} failed: {e}")
        if not Vs:
            print("no geometry decoded"); sys.exit(1)
        V = np.vstack(Vs); F = np.vstack(Fs)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cache, V=V, F=F)
        print(f"merged {ok} tiles, cached -> {cache}")

    # ground so buildings sit on the street plane
    ground = np.percentile(V[:, 1], 1.0); V = V.copy(); V[:, 1] -= ground
    # clip faces to the twin boundary (keep a face if its centroid is inside)
    cx = V[F, 0].mean(axis=1); cz = V[F, 2].mean(axis=1)
    keep = (cx > CLIP[0]) & (cx < CLIP[2]) & (cz > CLIP[1]) & (cz < CLIP[3])
    F = F[keep]
    used = np.unique(F); remap = -np.ones(len(V), np.int64); remap[used] = np.arange(len(used))
    V = V[used]; F = remap[F]
    N = vertex_normals(V, F)
    write_glb(OUT, V, N, F)
    span_x = (V[:,0].min(), V[:,0].max()); span_z = (V[:,2].min(), V[:,2].max())
    print(f"clipped: {len(V)} verts, {len(F)} tris -> {OUT} ({OUT.stat().st_size/1e6:.1f} MB)")
    print(f"  local span x[{span_x[0]:.0f},{span_x[1]:.0f}] z[{span_z[0]:.0f},{span_z[1]:.0f}] m, ground={ground:.1f}")

if __name__ == "__main__":
    main()
