# Release validation checklist

This checklist defines observable release gates; passing a single CI workflow is not a release by itself.

## Before release

- [ ] Confirm the intended source license with the rights holder and add a matching root `LICENSE`, or explicitly keep the project unlicensed and do not advertise a license.
- [ ] Review [media and asset provenance](assets-and-provenance.md); no unverified asset may be represented as cleared for redistribution.
- [ ] Confirm dependency alerts and secret-scanning / push-protection settings in repository Security settings. Record the actual state; do not infer it from the presence of a workflow.
- [ ] Review the pull request and require the current CI checks to pass.
- [ ] Run Python tests, including the deterministic synthetic-audio end-to-end render and `ffprobe` output validation.
- [ ] Run Remotion type-check, composition validation, and representative still renders for each maintained composition.
- [ ] Inspect the `remotion-visual-review-frames` CI artifact at landscape, portrait, square, and 4K resolutions; verify text fit, safe margins, contrast, translation readability, and visual continuity. Record the reviewed run and commit.
- [ ] Compare against owner-approved reference frames when a baseline exists; do not treat unreviewed captures as golden references or claim automated visual-regression coverage before such baselines are approved.
- [ ] Review audio/video stream presence, dimensions, frame rate, frame count, duration, and sync where applicable.
- [ ] Review known audio-intelligence limitations and any manual timing corrections.
- [ ] Update `CHANGELOG.md` with user-visible changes and known limitations.
- [ ] Preserve CI run links and release commit SHA as provenance.

## Release and rollback

- [ ] Tag a tested commit using the project's chosen versioning convention only after the owner confirms the release version.
- [ ] Publish only artifacts generated from that tested commit.
- [ ] Keep the previous known-good artifact / tag available for rollback.
- [ ] If a release artifact fails validation or has a rights/security issue, withdraw it where possible, identify the affected commit/tag, and publish a corrected release only after checks pass.

## Performance baseline

For a representative, rights-cleared sample, record:
- machine/runner and tool versions;
- input duration, sample rate, channels, and file size;
- render resolution and frame rate;
- render wall-clock time and peak memory where measurable;
- output size, duration, dimensions, frame rate, and audio/video stream metadata.

Do not compare measurements made with different inputs or tool versions as if they were equivalent. Keep benchmarks informational until stable baselines and tolerances have been agreed.
