# Horizon world asset sources

The Horizon cinematic environment uses a small, explicitly curated set of external GLB assets. These are loaded through Three.js `GLTFLoader` and are separate from the lyric/timing pipeline.

## Integrated CC0 assets

| Scene role | Asset | Source | Licence | Runtime URL |
| --- | --- | --- | --- | --- |
| African landmark tree | Baobab Tree | [3DAssets.dev — Safari Camp and Bush Lodge](https://3dassets.dev/assets?category=nature&tag=low-poly) | CC0 1.0 | `https://cdn.3dassets.dev/assets/37714/v1/model.glb` |
| African savanna tree | Large Acacia Tree | [3DAssets.dev — Safari Camp and Bush Lodge](https://3dassets.dev/assets?category=nature&tag=low-poly) | CC0 1.0 | `https://cdn.3dassets.dev/assets/37713/v1/model.glb` |
| Foreground vegetation | Small Acacia Tree | [3DAssets.dev — Safari Camp and Bush Lodge](https://3dassets.dev/assets?category=nature&tag=low-poly) | CC0 1.0 | `https://cdn.3dassets.dev/assets/37712/v1/model.glb` |
| Journey vehicle | Grand Touring Coupe | [3DAssets.dev — Vehicle Collection HD](https://3dassets.dev/packs/transport-collection-hd) | CC0 1.0 | `https://cdn.3dassets.dev/assets/18681/v1/model.glb` |

3DAssets.dev documents its published GLBs as self-contained binary glTF files, metre-scale, +Y up, CC0 1.0, and compatible with Three.js `GLTFLoader`. The CDN URLs are immutable. Asset metadata and licence statements: [3DAssets.dev documentation](https://3dassets.dev/docs) and [API reference](https://3dassets.dev/docs/api).

## Runtime and reproducibility

- The four URLs are pinned in source; no live catalogue search or changing query is performed during a render.
- The world exposes a `ready` promise. The Remotion composition holds its render handle until all asset requests settle, so frames are not captured while models are still arriving.
- A failed external asset request does not reject the scene setup: the procedural environment remains available.
- Imported geometry, materials and textures are disposed with the world.
- External hosting is a current runtime dependency. For fully offline/reproducible production, mirror the approved GLBs into the repository's static asset directory after validating their bytes and record checksums; do not silently substitute different model revisions.

## Human characters: deliberately not substituted yet

The current curated integration does **not** claim to include a photorealistic human character. 3DAssets.dev's visible realistic-character results include astronaut and tactical/static-pose models that do not fit the grounded human storytelling needed by Horizon. Blender Studio has production-rigged characters, and MakeHuman provides an open human-character authoring workflow, but each candidate must be checked for its individual downloadable asset licence, rig, texture quality, facial quality, and redistribution terms before it is shipped.

Next character gate:
1. Select a production-quality, non-tactical human model with a usable rig and facial/cloth detail.
2. Confirm the exact asset licence permits bundling and commercial use.
3. Verify skeleton, skinning, materials, animation clips, scale and texture dependencies.
4. Add a reproducible local asset copy plus checksum and attribution record.
5. Retarget a small set of story actions (walk, turn, reach, embrace, look toward horizon) and validate at portrait and landscape framing.

No third-party model should be downloaded, republished, or bundled unless its exact licence and provenance are verified.
