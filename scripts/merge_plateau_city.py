"""Merge per-building PLATEAU glTF tiles into one optimized city mesh.

The PLATEAU "modelLib" library stores every building as an individual glTF
(LOD00 = detailed, LOD01 = block). Loading thousands of textured glTFs in a
browser is hopeless on a modest GPU, so we weld all the building *geometry*
(position + normal) from one map-tile into a single mesh — one draw call — and
recenter it on the local origin. Textures are dropped; the detailed PLATEAU
roof/facade geometry alone reads as a real city and shades cleanly under the
twin's lighting.

Output: a binary .glb with one POSITION/NORMAL/indexed primitive, plus a small
JSON sidecar describing the recentred bounds so the viewer can place it.

Usage:
    python scripts/merge_plateau_city.py <indir> <out.glb> [--lod 00|01]

<indir> holds the extracted <id>_LOD00.gltf + .bin pairs for one tile.
"""
from __future__ import annotations

import glob
import io
import json
import os
import struct
import sys
import zipfile

import numpy as np

DTYPE = {5120: "<i1", 5121: "<u1", 5122: "<i2", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}

# ---- optional vertex-colour baking: average each building's real texture -----
_TEX_MAP = {}        # basename -> zip entry name
_TEX_CACHE = {}      # basename -> linear RGB float32[3]
_ZIP = None


def srgb_to_linear(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _load_tex(uri):
    """Decode a texture from the zip into an (H,W,3) float32 sRGB array."""
    entry = _TEX_MAP.get(os.path.basename(uri))
    if entry is None:
        return None
    try:
        from PIL import Image
        with _ZIP.open(entry) as fh:
            im = Image.open(io.BytesIO(fh.read())).convert("RGB")
        return np.asarray(im, np.float32)
    except Exception:
        return None


def mean_color(uri):
    """Average colour (linear RGB) of a texture (fallback for UV-less prims)."""
    if uri in _TEX_CACHE:
        return _TEX_CACHE[uri]
    arr = _load_tex(uri)
    rgb = (srgb_to_linear(arr.reshape(-1, 3).mean(axis=0)).astype(np.float32)
           if arr is not None else np.array([0.62, 0.66, 0.72], np.float32))
    _TEX_CACHE[uri] = rgb
    return rgb


def sample_texture(uri, uvs):
    """Sample a texture at per-vertex UVs -> linear RGB (N,3). Wraps UVs."""
    n = len(uvs)
    arr = _load_tex(uri)
    if arr is None:
        return np.full((n, 3), 0.66, np.float32)
    h, w = arr.shape[:2]
    u = uvs[:, 0] - np.floor(uvs[:, 0])                    # wrap to [0,1)
    v = uvs[:, 1] - np.floor(uvs[:, 1])
    px = np.clip((u * w).astype(np.int32), 0, w - 1)
    py = np.clip((v * h).astype(np.int32), 0, h - 1)       # glTF V: 0 = top row
    return srgb_to_linear(arr[py, px]).astype(np.float32)


def read_accessor(gltf, bindata, idx):
    """Return an (count, ncomp) array for accessor idx, handling interleaving."""
    acc = gltf["accessors"][idx]
    bv = gltf["bufferViews"][acc["bufferView"]]
    dtype = np.dtype(DTYPE[acc["componentType"]])
    ncomp = NCOMP[acc["type"]]
    count = acc["count"]
    comp_bytes = dtype.itemsize * ncomp
    stride = bv.get("byteStride") or comp_bytes
    start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    need = stride * (count - 1) + comp_bytes
    rows = np.frombuffer(bindata, np.uint8, count=need, offset=start)
    if stride != comp_bytes:                       # interleaved: slice each row
        pad = stride * count - need
        if pad:
            rows = np.concatenate([rows, np.zeros(pad, np.uint8)])
        rows = rows.reshape(count, stride)[:, :comp_bytes]
        rows = np.ascontiguousarray(rows)
    return rows.view(dtype).reshape(count, ncomp)


def prim_texture_uri(gltf, prim):
    """Return (uri, baseColorFactor) for a primitive's material."""
    mats = gltf.get("materials", [])
    imgs = gltf.get("images", [])
    texs = gltf.get("textures", [])
    mi = prim.get("material")
    if mi is None or mi >= len(mats):
        return None, None
    pbr = mats[mi].get("pbrMetallicRoughness", {})
    bcf = pbr.get("baseColorFactor")
    tex = pbr.get("baseColorTexture")
    if not tex:
        return None, bcf
    src = texs[tex["index"]].get("source")
    if src is None or src >= len(imgs):
        return None, bcf
    return imgs[src]["uri"], bcf


def load_building(path, bake=False, per_vertex=False):
    """Yield (positions, normals, indices, colors|None) per primitive.

    bake=True averages each primitive's texture into a flat per-face colour
    (clean at street level). per_vertex=True instead samples the texture at
    every vertex UV (finer at a distance, but noisy on decimated geometry).
    """
    with open(path) as f:
        gltf = json.load(f)
    buf = gltf["buffers"][0]["uri"]
    with open(os.path.join(os.path.dirname(path), buf), "rb") as f:
        bindata = f.read()
    for mesh in gltf.get("meshes", []):
        for prim in mesh["primitives"]:
            attr = prim["attributes"]
            if "POSITION" not in attr:
                continue
            pos = read_accessor(gltf, bindata, attr["POSITION"]).astype(np.float32)
            if "NORMAL" in attr:
                nrm = read_accessor(gltf, bindata, attr["NORMAL"]).astype(np.float32)
            else:
                nrm = np.zeros_like(pos)
            if "indices" in prim:
                idx = read_accessor(gltf, bindata, prim["indices"]).reshape(-1).astype(np.uint32)
            else:
                idx = np.arange(len(pos), dtype=np.uint32)
            col = None
            if bake:
                uri, bcf = prim_texture_uri(gltf, prim)
                if uri and per_vertex and "TEXCOORD_0" in attr:
                    uv = read_accessor(gltf, bindata, attr["TEXCOORD_0"]).astype(np.float32)
                    col = sample_texture(uri, uv)          # per-vertex (noisy when decimated)
                elif uri:
                    col = np.tile(mean_color(uri), (len(pos), 1))   # clean per-face average
                elif bcf:
                    col = np.tile(np.array(bcf[:3], np.float32), (len(pos), 1))
                else:
                    col = np.full((len(pos), 3), 0.66, np.float32)
            yield pos, nrm, idx, col


def write_glb(path, positions, normals, indices, meta, colors=None):
    """Write a minimal single-primitive binary glTF (optional COLOR_0)."""
    pmin = positions.min(axis=0).tolist()
    pmax = positions.max(axis=0).tolist()
    pos_b = positions.astype("<f4").tobytes()
    nrm_b = normals.astype("<f4").tobytes()
    idx_b = indices.astype("<u4").tobytes()
    has_col = colors is not None
    col_b = colors.astype("<f4").tobytes() if has_col else b""

    def pad4(b, fill=b"\x00"):
        return b + fill * (-len(b) % 4)

    pos_o, nrm_o = 0, len(pos_b)
    col_o = nrm_o + len(nrm_b)
    idx_o = col_o + len(col_b)
    bindata = pad4(pos_b + nrm_b + col_b + idx_b)

    bviews = [
        {"buffer": 0, "byteOffset": pos_o, "byteLength": len(pos_b), "target": 34962},
        {"buffer": 0, "byteOffset": nrm_o, "byteLength": len(nrm_b), "target": 34962},
    ]
    accessors = [
        {"bufferView": 0, "componentType": 5126, "count": len(positions),
         "type": "VEC3", "min": pmin, "max": pmax},
        {"bufferView": 1, "componentType": 5126, "count": len(normals), "type": "VEC3"},
    ]
    attrs = {"POSITION": 0, "NORMAL": 1}
    if has_col:
        bviews.append({"buffer": 0, "byteOffset": col_o, "byteLength": len(col_b), "target": 34962})
        accessors.append({"bufferView": 2, "componentType": 5126, "count": len(colors), "type": "VEC3"})
        attrs["COLOR_0"] = 2
    idx_bv = len(bviews)
    bviews.append({"buffer": 0, "byteOffset": idx_o, "byteLength": len(idx_b), "target": 34963})
    accessors.append({"bufferView": idx_bv, "componentType": 5125, "count": len(indices), "type": "SCALAR"})
    idx_acc = len(accessors) - 1

    gltf = {
        "asset": {"version": "2.0", "generator": "merge_plateau_city"},
        "extras": meta,
        "buffers": [{"byteLength": len(bindata)}],
        "bufferViews": bviews,
        "accessors": accessors,
        "materials": [{
            "name": "plateau_city",
            "pbrMetallicRoughness": {"baseColorFactor": [1.0, 1.0, 1.0, 1.0],
                                     "metallicFactor": 0.0, "roughnessFactor": 0.85},
        }],
        "meshes": [{"primitives": [{
            "attributes": attrs, "indices": idx_acc, "material": 0}]}],
        "nodes": [{"mesh": 0}],
        "scenes": [{"nodes": [0]}],
        "scene": 0,
    }
    json_b = pad4(json.dumps(gltf, separators=(",", ":")).encode("utf-8"), b" ")
    total = 12 + 8 + len(json_b) + 8 + len(bindata)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))            # glTF magic, v2
        f.write(struct.pack("<II", len(json_b), 0x4E4F534A))          # JSON chunk
        f.write(json_b)
        f.write(struct.pack("<II", len(bindata), 0x004E4942))         # BIN chunk
        f.write(bindata)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    indir, out = sys.argv[1], sys.argv[2]
    lod = "00"
    if "--lod" in sys.argv:
        lod = sys.argv[sys.argv.index("--lod") + 1]

    bake = "--zip" in sys.argv
    per_vertex = "--per-vertex" in sys.argv
    if bake:
        global _ZIP, _TEX_MAP
        zpath = sys.argv[sys.argv.index("--zip") + 1]
        _ZIP = zipfile.ZipFile(zpath)
        for n in _ZIP.namelist():
            if "_LOD00_" in n and n.lower().endswith(".png"):
                _TEX_MAP[os.path.basename(n.replace("\\", "/"))] = n
        print(f"baking vertex colours from {len(_TEX_MAP)} textures in {zpath}")

    files = sorted(glob.glob(os.path.join(indir, f"*_LOD{lod}.gltf")))
    print(f"merging {len(files)} buildings (LOD{lod}) from {indir}")

    all_pos, all_nrm, all_idx, all_col = [], [], [], []
    bases = []                                       # per-building min-Y (footing)
    vbase = 0
    nverts = ntris = nbad = 0
    for i, path in enumerate(files):
        try:
            b_ymin = np.inf
            for pos, nrm, idx, col in load_building(path, bake=bake, per_vertex=per_vertex):
                all_pos.append(pos)
                all_nrm.append(nrm)
                all_idx.append(idx + vbase)
                if bake:
                    all_col.append(col)
                vbase += len(pos)
                nverts += len(pos)
                ntris += len(idx) // 3
                b_ymin = min(b_ymin, float(pos[:, 1].min()))
            if np.isfinite(b_ymin):
                bases.append(b_ymin)
        except Exception as e:
            nbad += 1
            continue
        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{len(files)}  ({nverts/1e6:.1f}M verts, {len(_TEX_CACHE)} textures sampled)")

    positions = np.concatenate(all_pos)
    normals = np.concatenate(all_nrm)
    indices = np.concatenate(all_idx)
    colors = np.concatenate(all_col) if bake and all_col else None
    del all_pos, all_nrm, all_idx, all_col

    # recenter X/Z on the cluster centroid; drop Y so the *typical* street
    # level sits at 0. Using the median building footing (not the single
    # lowest vertex) avoids one deep outlier lifting the whole city off the
    # ground plane.
    cx = (positions[:, 0].min() + positions[:, 0].max()) / 2
    cz = (positions[:, 2].min() + positions[:, 2].max()) / 2
    ground = float(np.median(bases)) if bases else float(positions[:, 1].min())
    positions[:, 0] -= cx
    positions[:, 2] -= cz
    positions[:, 1] -= ground                        # median street level -> Y=0

    bb_min = positions.min(axis=0)
    bb_max = positions.max(axis=0)
    meta = {
        "buildings": len(files) - nbad,
        "source_center_xz": [float(cx), float(cz)],
        "bounds_min": bb_min.tolist(),
        "bounds_max": bb_max.tolist(),
        "extent_x": float(bb_max[0] - bb_min[0]),
        "extent_z": float(bb_max[2] - bb_min[2]),
    }
    meta["vertex_colors"] = bool(colors is not None)
    write_glb(out, positions, normals, indices, meta, colors=colors)
    side = out.rsplit(".", 1)[0] + "_meta.json"
    with open(side, "w") as f:
        json.dump(meta, f, indent=2)

    mb = os.path.getsize(out) / 1048576
    print(f"\nwrote {out}  ({mb:.0f} MB raw glb)")
    print(f"  buildings: {meta['buildings']}  (skipped {nbad})")
    print(f"  vertices:  {nverts/1e6:.2f}M   triangles: {ntris/1e6:.2f}M")
    print(f"  extent:    {meta['extent_x']:.0f}m x {meta['extent_z']:.0f}m,"
          f" height {bb_max[1]:.0f}m")
    print(f"  sidecar:   {side}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
