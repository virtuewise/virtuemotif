# Media and asset provenance

This document is the repository's source-of-truth inventory for rights review. A file being present in a public Git repository does **not** establish that it may be redistributed, remixed, or used commercially.

## Policy

- Record the original source, creator/rightsholder, license or written permission, attribution requirements, allowed use, and evidence URL for every distributed audio, image, font, and texture asset.
- Do not add new third-party media without a documented license compatible with the intended distribution.
- Keep synthetic, redistributable test fixtures small and generated in tests. Never use production songs or lyric recordings as test fixtures.
- If rights are unclear, mark the asset **unverified** and do not treat it as cleared for a release. Do not infer permission from a public URL or an existing repository commit.
- Keep an asset's provenance record with the asset or in this inventory; update it when the asset is replaced.

## Current inventory requiring owner verification

The following files are present in the repository tree. Their rights status has not been independently verified by this engineering change.

| Asset group | Current paths / examples | Rights status |
| --- | --- | --- |
| Production audio | `film/public/audio/horizon.m4a`, `film/public/audio/rise.m4a`, root-level `*.m4a` | **Unverified — release blocker until rights holder/source and permission are recorded** |
| Derived audio | `timing/wav/*.wav` including vocal/mix variants | **Unverified — derived stems inherit source restrictions** |
| Artwork | `Rise Together - Vuka Zimbabwe - Simudzai Mureza.jpg` | **Unverified — source and redistribution permission required** |
| Fonts | `film/public/fonts/*.ttf` | Verify each font's exact upstream release and license; preserve required license/attribution files |
| Procedural textures | `film/public/tex/*.png` | Record whether generated in-house or derived from third-party source material |

This inventory intentionally does not claim ownership, licensing, or permission that has not been supplied by the rights holder.

## License status

The repository has no root `LICENSE` file. No open-source license should be inferred until the project owner explicitly selects a license and adds its complete text. The README must continue to disclose this status instead of displaying an unsupported license badge.

## Release gate

Before distributing source archives, rendered videos, or a public package, the release owner must review every unverified asset and do one of the following:

1. Record sufficient permission/license evidence and attribution.
2. Replace the asset with an appropriately licensed alternative.
3. Remove the asset and any generated derivatives that depend on it.

A code CI pass cannot verify legal ownership or redistribution rights.
