# Production character and asset pipeline

This folder separates prototype scene dressing from production-approved local assets. Do not promote an asset to production merely because a URL loads.

## Asset intake

1. Select an asset whose exact model page states its licence and redistribution terms.
2. Record source, licence, evidence URL, role, intended local path and SHA-256 in `asset-manifest.json`.
3. Download through an approved workflow into the declared repository path; inspect the GLB in Blender and verify scale, normals, UVs, texture embedding, material response and polygon budget.
4. Calculate SHA-256 from the exact final bytes and set `status` to `approved-local` only after human provenance/licence review.
5. Run `node film/scripts/validate_world_assets.mjs --production`. It fails on missing files, unpinned hashes, invalid GLB headers, checksum mismatches and non-approved status.

The four currently used 3DAssets.dev props remain marked `remote-prototype-only`; their local files and hashes are deliberately absent. The human protagonist is marked `not-generated`. This prevents a CI green result from being misrepresented as a finished character pipeline.

## Human character generation

Use MPFB2 in Blender to create the character. MPFB2 is a generator, not a finished photoreal protagonist. An artist must approve anatomy, face, hair, layered clothing, skin/eye shading and animation quality. Export a self-contained GLB with armature skinning, morph targets and named clips. The validation/export gate is `film/scripts/export_human_character.py`; it refuses export if the rig, shape keys, materials or required actions are missing.

Required actions: `idle`, `walk`, `turn`, `look_to_horizon`. Add additional authored actions (run, reach, embrace, sit, kneel) when the story requires them. Do not substitute a static-pose model for an animated protagonist.

## Runtime integration contract

- Production assets must be local, checksummed, licence-reviewed GLBs.
- Keep prototypes separate from hero assets; use LODs for background scenery.
- Human GLBs must include skinning and morph targets, and be tested in the actual Three.js/Remotion renderer.
- Character animation must be deterministic at a given Remotion frame. Avoid wall-clock time, random runtime animation and external API calls.
- Failed asset validation blocks production renders; it must not silently swap in an unlicensed or unpinned model.


## Reproducible local staging

Run `cd film && npm run stage:assets` to download the four pinned prototype GLBs into their manifest paths. The staging script verifies the binary GLB header, declared byte length and SHA-256, then records the exact digest and sets status to `staged-review`. It never marks an asset production-approved.

Open each staged GLB in Blender and review topology, normals, scale, UVs, embedded textures, material response, visual quality and licence evidence. Only after that review may a maintainer change the row to `approved-local`; then run `npm run validate:assets:production`. The current tree/vehicle assets are explicitly low-poly scene-dressing prototypes, so staging them locally improves render reproducibility but does not satisfy the final hero-scenery quality bar. Replace them with higher-detail approved assets before close-up use.

## Authored cinematic camera direction

`film/src/fur3d/HorizonCinematicDirection.ts` defines deterministic establishing, journey, memory, revelation and intimate camera setups. It maps curated English, Shona, Ndebele and isiZulu story cues plus chorus/outro structure into composition, focal target and lens choices, then modulates push-in and camera breathing from the same frame-synchronous energy and beat cues. `FurryLyricView` now uses this director instead of its former generic orbit. The direction regression suite checks repeatability, multilingual revelation cues and portrait framing.

This is a first authored blocking pass, not a completed shot-by-shot director's storyboard. Final shot timing, actor blocking, eyelines, lens selection and transitions require review against the complete song edit and the approved protagonist performance.

## Story-driven protagonist runtime contract

`film/src/fur3d/HorizonCharacterPerformance.ts` is the deterministic animation adapter for the eventual artist-approved GLB. It requires authored `idle`, `walk`, `turn`, and `look_to_horizon` clips, selects a story action from lyric/section cues, seeks the animation mixer to absolute Remotion time, and applies restrained facial morph emphasis when compatible morph targets exist. The adapter deliberately throws if required clips are absent. It is not a model and does not fabricate facial geometry. The runtime now attempts to load the protagonist from the local film/public/assets/characters/horizon-protagonist.glb path and connects the adapter when a valid rigged GLB is present. Until that file is generated and approved, the character remains unavailable; no placeholder human is rendered.

Run the focused regression suite with `cd film && npm run test:cinematic`. This command covers the world and character performance contracts; CI inclusion and browser-render validation remain separate acceptance gates.


## Local-only runtime asset loading

The Three.js world loads scenery and the protagonist only from Remotion's local public/assets directory via staticFile. It no longer requests prototype GLBs from a third-party CDN during rendering. Missing local files are treated as optional unavailable scene dressing by the asset-readiness barrier; this is a development fallback, not production acceptance. Stage and review assets locally, pin their hashes, and run the production validator before release.
