# Visual regression workflow

CI publishes current review captures as the `remotion-visual-review-frames`
artifact and verifies their PNG headers and expected composition dimensions.
The 12-frame artifact covers the classic Horizon/Rise smoke frames, Smart Fur
landscape/4K/portrait/square, generic AutoLyrics landscape/portrait/square/4K,
and the deterministic rainfall and audio-reactive glitch scenes. These captures
are useful for human inspection, but are not automatically considered correct
references.

## Approving a baseline

1. Inspect the artifact for the exact commit. Review every frame for typography
   fit, clipping, safe margins, contrast, language/translation readability,
   composition balance, shader artifacts, and continuity.
2. Only after the project owner approves the render, preserve the full set of
   12 PNGs as a versioned reference set and record the source commit, render
   settings, and reviewer decision.
3. Re-approve the baseline whenever an intentional visual redesign changes it.
   Never regenerate the baseline automatically from the candidate being tested.

## Compare against an approved reference

With FFmpeg installed, compare an approved directory and a current capture
directory containing the complete set of required frames:

```bash
node tools/compare_visual_frames.mjs path/to/approved-baseline build/visual-review 0.01
```

The comparator uses the same frame manifest as CI, so a missing baseline or
candidate capture cannot be silently skipped. The final argument is the maximum
allowed ratio of pixels whose largest per-channel RGBA difference exceeds the
default threshold of 8. The report also includes mean absolute channel error.
Missing frames, invalid PNG headers, wrong dimensions, and incompatible decoded
buffers fail rather than producing a misleading pass.

Pixel comparisons can be sensitive to browser, GPU, font, and renderer changes.
Keep runtime/tool versions fixed when possible and review diffs before accepting
a baseline change. A pixel-diff pass is not proof of musical synchronization,
legibility for every script, or accessibility compliance.

## Current status

The comparator and metric tests are available, and CI now captures every frame
that the comparator expects. The repository still does not contain an
owner-approved golden baseline, so automated visual regression is not yet an
active release gate. Do not claim baseline-backed regression coverage until the
reference images have been reviewed and the comparator has been run against them.
