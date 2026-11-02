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
