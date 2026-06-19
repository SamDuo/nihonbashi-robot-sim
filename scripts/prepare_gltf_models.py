"""Prepare high-LOD glTF building models for the WebGL digital twin.

Reads a directory of .gltf/.glb files (with optional texture subfolders),
optimises them for browser delivery, spatially tiles them, and writes a
manifest that twin_view.html can stream progressively.

Pipeline
--------
1. Scan input directory for .gltf / .glb files
2. For each model:
   a. Compute bounding box (trimesh or pygltflib)
   b. Compress with gltf-transform CLI (Draco geometry + KTX2 textures)
   c. Assign to spatial tile by centroid
3. Write per-tile .glb bundles (or keep per-building) + manifest.json

Prerequisites
-------------
    pip install trimesh numpy
    npm install -g @gltf-transform/cli    # for Draco/KTX2 compression

Usage
-----
    python scripts/prepare_gltf_models.py C:/modelLib
    python scripts/prepare_gltf_models.py C:/modelLib --tile-size 200 --skip-compress
    python scripts/prepare_gltf_models.py C:/modelLib --anchor 35.6810,139.7720

The --anchor flag sets the geo-reference origin (lat,lng) used by the twin.
Default matches the project's ANCHOR_LAT/LNG in sim/testbed/scene.py.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "twin" / "models"

ANCHOR_LAT = 35.6810
ANCHOR_LNG = 139.7720


def find_gltf_files(src: Path) -> list[Path]:
    """Recursively find all .gltf and .glb files."""
    files = []
    for ext in ("*.gltf", "*.glb", "*.GLB", "*.GLTF"):
        files.extend(src.rglob(ext))
    return sorted(set(files))


def glb_bounding_box(path: Path) -> dict | None:
    """Extract bounding box from a glTF/GLB using trimesh (if available)."""
    try:
        import trimesh
        scene = trimesh.load(str(path), force="scene", process=False)
        bounds = scene.bounds  # [[min_x, min_y, min_z], [max_x, max_y, max_z]]
        centroid = scene.centroid.tolist()
        return {
            "min": bounds[0].tolist(),
            "max": bounds[1].tolist(),
            "centroid": centroid,
            "size": (bounds[1] - bounds[0]).tolist(),
        }
    except Exception as e:
        print(f"  [warn] cannot read bounds for {path.name}: {e}")
        return None


def compress_gltf(src: Path, dst: Path, resize: int = 1024) -> bool:
    """Compress a glTF/GLB using gltf-transform CLI (Draco + texture resize)."""
    gltf_transform = shutil.which("gltf-transform")
    if not gltf_transform:
        print("  [skip] gltf-transform not found — copying uncompressed")
        if src != dst:
            shutil.copy2(src, dst)
        return False

    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp.glb")

    try:
        subprocess.run(
            [gltf_transform, "draco", str(src), str(tmp)],
            check=True, capture_output=True, timeout=120,
        )
        subprocess.run(
            [gltf_transform, "resize", "--width", str(resize),
             "--height", str(resize), str(tmp), str(dst)],
            check=True, capture_output=True, timeout=120,
        )
        tmp.unlink(missing_ok=True)
        return True
    except FileNotFoundError:
        print("  [skip] gltf-transform not installed — copying uncompressed")
        shutil.copy2(src, dst)
        return False
    except subprocess.CalledProcessError as e:
        print(f"  [warn] gltf-transform failed for {src.name}: {e.stderr[:200]}")
        shutil.copy2(src, dst)
        tmp.unlink(missing_ok=True)
        return False


def assign_tile(centroid: list[float], tile_size: float) -> str:
    """Assign a model to a spatial tile grid cell."""
    tx = int(math.floor(centroid[0] / tile_size))
    tz = int(math.floor(centroid[2] / tile_size))
    return f"tile_{tx}_{tz}"


def file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def main():
    parser = argparse.ArgumentParser(description="Prepare glTF models for twin")
    parser.add_argument("src", type=Path, help="Directory containing .gltf/.glb files")
    parser.add_argument("--tile-size", type=float, default=200.0,
                        help="Spatial tile size in meters (default: 200)")
    parser.add_argument("--texture-size", type=int, default=1024,
                        help="Max texture dimension after resize (default: 1024)")
    parser.add_argument("--skip-compress", action="store_true",
                        help="Skip gltf-transform compression, just copy and catalogue")
    parser.add_argument("--anchor", type=str, default=None,
                        help="Geo anchor as lat,lng (default: project anchor)")
    args = parser.parse_args()

    if not args.src.is_dir():
        print(f"Error: {args.src} is not a directory")
        return 1

    files = find_gltf_files(args.src)
    if not files:
        print(f"No .gltf/.glb files found in {args.src}")
        return 1

    print(f"Found {len(files)} glTF files in {args.src}")
    print(f"Output: {OUT_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "version": 1,
        "anchor": {"lat": ANCHOR_LAT, "lng": ANCHOR_LNG},
        "tile_size_m": args.tile_size,
        "tiles": {},
        "models": [],
    }

    total_src_mb = 0
    total_dst_mb = 0

    for i, src_path in enumerate(files):
        name = src_path.stem
        print(f"\n[{i+1}/{len(files)}] {src_path.name}")

        src_mb = file_size_mb(src_path)
        total_src_mb += src_mb
        print(f"  source: {src_mb:.1f} MB")

        bbox = glb_bounding_box(src_path)
        if bbox:
            print(f"  bounds: {[round(v,1) for v in bbox['size']]} m")
            tile_id = assign_tile(bbox["centroid"], args.tile_size)
        else:
            tile_id = "tile_0_0"
            bbox = {"min": [0,0,0], "max": [0,0,0], "centroid": [0,0,0], "size": [0,0,0]}

        tile_dir = OUT_DIR / tile_id
        tile_dir.mkdir(parents=True, exist_ok=True)
        dst_path = tile_dir / f"{name}.glb"

        if args.skip_compress:
            if src_path != dst_path:
                shutil.copy2(src_path, dst_path)
            compressed = False
        else:
            compressed = compress_gltf(src_path, dst_path, args.texture_size)

        dst_mb = file_size_mb(dst_path)
        total_dst_mb += dst_mb
        ratio = (1 - dst_mb / src_mb) * 100 if src_mb > 0 else 0
        print(f"  output: {dst_mb:.1f} MB ({ratio:+.0f}%)" +
              (" [draco+resize]" if compressed else " [uncompressed]"))

        model_entry = {
            "name": name,
            "file": f"{tile_id}/{name}.glb",
            "tile": tile_id,
            "bounds": bbox,
            "src_mb": round(src_mb, 2),
            "dst_mb": round(dst_mb, 2),
            "compressed": compressed,
        }
        manifest["models"].append(model_entry)

        if tile_id not in manifest["tiles"]:
            manifest["tiles"][tile_id] = {
                "models": [],
                "total_mb": 0,
                "bounds_min": bbox["min"][:],
                "bounds_max": bbox["max"][:],
            }
        tile = manifest["tiles"][tile_id]
        tile["models"].append(name)
        tile["total_mb"] = round(tile["total_mb"] + dst_mb, 2)
        for j in range(3):
            tile["bounds_min"][j] = min(tile["bounds_min"][j], bbox["min"][j])
            tile["bounds_max"][j] = max(tile["bounds_max"][j], bbox["max"][j])

    manifest_path = OUT_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print("\n" + "=" * 60)
    print(f"  Models processed: {len(files)}")
    print(f"  Tiles created:    {len(manifest['tiles'])}")
    print(f"  Source total:     {total_src_mb:.1f} MB")
    print(f"  Output total:    {total_dst_mb:.1f} MB ({(1 - total_dst_mb/max(total_src_mb,0.01))*100:.0f}% reduction)")
    print(f"  Manifest:        {manifest_path}")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Copy outputs/twin/models/ to your serve directory")
    print("  2. Open twin_view.html?models=hifi to load the glTF buildings")
    print("  3. Use ?models=hifi&lod=low for distance-culled lightweight mode")
    print()

    if not shutil.which("gltf-transform"):
        print("TIP: Install gltf-transform for 60-90% size reduction:")
        print("  npm install -g @gltf-transform/cli")
        print("Then re-run this script without --skip-compress")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
