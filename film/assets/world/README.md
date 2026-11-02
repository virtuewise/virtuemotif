# Horizon world asset sources

The Horizon cinematic environment currently has a **first-pass scene-dressing integration**, not a final photoreal asset pack. The selected GLBs are low-poly, real-world-scale African vegetation and a detailed vehicle model. They establish the asset-loading pipeline and can serve as distant/background dressing; they do not yet meet the hero-asset realism bar for close-up cinematic shots. These are loaded through Three.js `GLTFLoader` and are separate from the lyric/timing pipeline.

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

## Human characters: recommended production path

The current scene does **not** yet contain a human character. The visible realistic-character catalogue results I inspected include astronaut/tactical/static-pose figures, which do not fit Horizon's grounded human storytelling. They are intentionally excluded.

The most actionable open pipeline is **[MPFB2 (MakeHuman for Blender)](https://github.com/makehumancommunity/mpfb2/)**. MPFB2 creates human meshes, supports parametric body shaping, automatic rigging, skin/eye materials and asset-based clothing. Its source code is GPLv3+, while the bundled graphical assets (base meshes, targets, clothes, rigs, poses, textures) are CC0 1.0; the project states that generated output is not restricted by the add-on's source-code licence. See the [MPFB licence](https://github.com/makehumancommunity/mpfb2/blob/master/LICENSE.md), [export guide](https://www.makehumancommunity.org/mpfb/docs/exporting/index.html), and [rigging/material guidance](https://www.makehumancommunity.org/mpfb/docs/index.html). For export, use the GameEngine material, bake shape keys, remove helper objects, and validate the resulting rig/skin weights in Three.js. This is a generator pipeline, not a ready-made photoreal character: a character artist still needs to author believable faces, hair, clothing, textures and expressions.

A second candidate is [Blender Studio's Rain rig](https://studio.blender.org/characters/rain/v3/), a free, fully rigged CC-BY character with facial controls. It is stylized rather than photorealistic and requires the credit `Rain Rig (CC) Blender Foundation | studio.blender.org`; use it only where that art direction is appropriate.

Next character gate:
1. Generate or select a grounded human character with varied body proportions, detailed face, hair, layered clothing and facial shape keys.
2. Confirm the exact source assets and generated textures are licensed for bundling and commercial use.
3. Export a self-contained GLB with PBR materials, armature, skinning, facial blend shapes and named animation clips.
4. Add a reproducible local asset copy plus SHA-256 checksum and licence record.
5. Retarget story actions (walk, turn, reach, embrace, look toward horizon) and validate at portrait and landscape framing.

No third-party model should be downloaded, republished, or bundled unless its exact licence and provenance are verified.
