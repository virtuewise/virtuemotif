# Visual regression workflow

CI publishes current review captures as the `remotion-visual-review-frames`
artifact and verifies their PNG headers and expected composition dimensions.
Those captures are useful for human inspection, but are not automatically
considered correct references.

## Approving a baseline

1. Inspect the artifact for the exact commit, including landscape, 4K, portrait,
   and square output.
2. Review typography fit, clipping, safe margins, contrast, language/translation
   readability, composition balance, and visible transition artifacts.
3. Only after the project owner approves the render, preserve the four
   `smart-fur-*.png` frames as a versioned reference set and record the source
   commit, render settings, and reviewer decision.
4. Re-approve the baseline whenever an intentional visual redesign changes it.
   Never regenerate the baseline automatically from the candidate being tested.

## Compare against an approved reference

With FFmpeg installed, compare an approved directory and a current capture
directory that both contain the four `smart-fur-*.png` frames:

```bash
node tools/compare_visual_frames.mjs path/to/approved-baseline build/visual-review 0.01
```

The final argument is the maximum allowed ratio of pixels whose largest
per-channel RGBA difference exceeds the default threshold of 8. The report also
includes mean absolute channel error. Missing frames, invalid PNG headers,
wrong dimensions, and incompatible decoded buffers fail instead of silently
skipping comparisons.

Pixel comparisons can be sensitive to browser, GPU, font, and renderer changes.
Keep runtime/tool versions fixed when possible and review diffs before accepting
a baseline change. A pixel-diff pass is not proof of musical synchronization,
legibility for every script, or accessibility compliance.

## Current status

The comparator and metric tests are available, but the repository does not yet
contain an owner-approved golden baseline. Do not claim automated visual
regression coverage until reference frames have been reviewed and the comparator
has been run against them.
