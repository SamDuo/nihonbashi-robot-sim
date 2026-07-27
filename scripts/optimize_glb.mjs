// Optimize a raw glb: weld duplicate verts, simplify triangles, Draco-compress.
// Used to shrink the converted PLATEAU LOD2 city (twin_view loads it via DRACOLoader).
//   node scripts/optimize_glb.mjs <in.glb> <out.glb> [ratio=0.5]
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { weld, simplify, dedup, draco } from '@gltf-transform/functions';
import { MeshoptSimplifier } from 'meshoptimizer';
import draco3d from 'draco3dgltf';

const [,, IN, OUT, RATIO = '0.5'] = process.argv;
if (!IN || !OUT) { console.error('usage: optimize_glb.mjs <in> <out> [ratio]'); process.exit(1); }

await MeshoptSimplifier.ready;
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({
    'draco3d.encoder': await draco3d.createEncoderModule(),
    'draco3d.decoder': await draco3d.createDecoderModule(),
  });

const doc = await io.read(IN);
const before = doc.getRoot().listMeshes()
  .flatMap(m => m.listPrimitives())
  .reduce((s, p) => s + (p.getIndices()?.getCount() ?? 0) / 3, 0);

await doc.transform(
  dedup(),
  weld({ tolerance: 0.0002 }),
  simplify({ simplifier: MeshoptSimplifier, ratio: parseFloat(RATIO), error: 0.012, lockBorder: false }),
  draco({ method: 'edgebreaker', quantizePosition: 14, quantizeNormal: 8, quantizeColor: 8 }),
);

await io.write(OUT, doc);
const after = doc.getRoot().listMeshes()
  .flatMap(m => m.listPrimitives())
  .reduce((s, p) => s + (p.getIndices()?.getCount() ?? 0) / 3, 0);
console.log(`tris ${Math.round(before)} -> ${Math.round(after)} (ratio ${RATIO}); wrote ${OUT}`);
