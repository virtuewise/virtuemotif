# CGTrader free royalty-free asset sourcing — Horizon of Light

Research date: 2026-11-02
Project: VirtueMotif / The Horizon of Light
Budget constraint: free downloads only; no paid assets or subscriptions.

## Licensing rules

- A free download is not automatically cleared for production. Record the exact listing URL, displayed license, creator, download date, original archive name, SHA-256, and any seller-specific terms.
- CGTrader listings below display **Royalty Free License (no AI)**. CGTrader's terms define this as the Royalty Free License with the additional restriction that the product must not be used for machine-learning or neural-network training. The ordinary Royalty Free incorporated-product rules still apply, including use in rendered moving images/films and a prohibition on redistributing the source model as a standalone file.
- VirtueMotif may use a cleared model as an embedded scene asset and render it into the final video. Do not use downloaded models, textures, metadata, or previews as AI training data.
- A marketplace listing and its license label are evidence of the seller's stated terms, not a substitute for preserving the download-time license receipt and reviewing any custom terms.
- Do not change the production asset manifest to `approved-local` until the actual downloaded bytes are present, hashed, inspected, and validated.

## Candidate assets

### 1. Protagonist candidate — Realistic Male Character Rigged

- Listing: https://www.cgtrader.com/free-3d-models/character/man/realistic-male-character-rigged
- CGTrader model ID: 5718860
- Listed price: Free
- Displayed license: Royalty Free License (no AI)
- Creator: giyas3dartist
- Listing claims: Blender 4.0 source; FBX and GLTF/GLB exchange formats; rigged; ARKit morphs; modular clothing; PBR maps; 171,305 polygons / 181,842 vertices.
- CGTrader verification: FBX passed CGT Standard checks for geometry, PBR maps, UVs, manifold mesh and scene compatibility.
- Intended use: primary candidate for the hero body/face, subject to local import, topology, skinning, ARKit morph-target inventory, and animation tests.
- Known limitation: the listing does not establish ethnicity or the presence of the four story-specific animation clips required by VirtueMotif. Do not describe it as an African character or as having the required clips until inspected.
- Status: `candidate-not-downloaded`.

### 2. Facial animation fallback — Stylized Customizable Avatar, Male (FREE)

- Listing: https://www.cgtrader.com/free-3d-models/character/man/stylized-customizable-avatar-male-free
- CGTrader model ID: 3901952
- Listed price: Free
- Displayed license: Royalty Free License (no AI)
- Creator: sunboxgames
- Listing claims: Blender source; animated and rigged; 26 blend shapes including visemes and blinking; IK rig; 67 textures; 280,000 polygons / 150,000 vertices.
- Intended use: fallback/reference for facial animation pipeline tests, not the preferred photoreal hero.
- Known limitation: explicitly stylized and low-poly; the free tier's facial morph set is much smaller than the paid full version. Do not represent it as photoreal.
- Status: `candidate-not-downloaded`.

### 3. Environment candidate — Free Park Environment Scene with Trees, Bench and Grass

- Listing: https://www.cgtrader.com/free-3d-models/exterior/other/free-park-environment-scene-with-trees-bench-and-grass
- CGTrader model ID: 7693819
- Listed price: Free
- Displayed license: Royalty Free License (no AI)
- Creator: Pro-pixel
- Listing claims: native Blender scene, FBX and GLTF; trees, grass terrain, bench, lighting and atmospheric horizon.
- Listing-reported size and complexity: 146 MB Blender source; 208 MB GLTF; 8,600,000 polygons / 15,000,000 vertices.
- Intended use: reference/prototype source only; extract selected vegetation/props after inspection and optimization.
- Known limitations: park setting is not an African savanna; the full scene is too heavy for direct runtime integration without substantial reduction and scene restructuring.
- Status: `candidate-not-downloaded`; not approved as the Horizon environment.

### 4. Vegetation prop candidate — Tree and Grass

- Listing: https://www.cgtrader.com/free-3d-models/plant/grass/tree-and-grass-ea9d442f-c076-45c8-9f05-5218c5e7c982
- Listed price: Free
- Displayed license: Royalty Free License (no AI)
- Creator: Kaagan
- Listing claims: 2048 × 2048 textures; Blender source; FBX exchange; CGTrader-verified FBX.
- Intended use: inspect as a low-cost vegetation source and possible reusable prop; not a baobab/acacia substitute without visual review.
- Status: `candidate-not-downloaded`.

## Excluded

- African Man Rigged (listing title "African Man Rigged") is displayed at USD 79, so it violates the free-only budget.
- Do not use the generic low-poly tree pack or any other free listing unless its exact license and download contents are recorded.
- Do not use assets with Editorial-only terms for commercial VirtueMotif output.

## Intake and release gate

For every selected candidate:

1. Download through the user's authenticated CGTrader account; do not automate or bulk-crawl CGTrader free downloads.
2. Preserve the original archive and the download-time license evidence.
3. Compute SHA-256 for the archive and each extracted asset; record filenames, sizes, and source URLs.
4. Inspect the actual mesh in Blender: object inventory, transforms, topology, UVs, normals, materials, texture references, armature, vertex groups, morph targets, and animation actions.
5. For the protagonist, require a deforming skinned mesh, facial morph target names/count, blink/viseme coverage, and independently playable animation clips. Add or retarget the required story actions only after inspecting the rig.
6. For environment props, optimize geometry and texture sizes, retain PBR channel semantics, build GLB packages, and test the local Remotion/Three.js loader.
7. Update `film/assets/world/asset-manifest.json` only with measured hashes and verified license evidence. Keep all uninspected downloads in review status.
8. Run asset validation, current-main CI, and four-format render/visual acceptance before marking anything production-approved.

## Sources

- CGTrader free-model discovery: https://www.cgtrader.com/3d-models/free
- CGTrader help: https://help.cgtrader.com/hc/en-us/articles/360015122437-Can-I-commercially-use-a-free-model
- CGTrader Royalty Free License: https://help.cgtrader.com/hc/en-us/articles/360015124437-Royalty-Free-License
- CGTrader terms, sections 19–21A: https://www.cgtrader.com/pages/terms-and-conditions
