# Release readiness gates

This checklist is intentionally fail-closed. A green CI run demonstrates the checks
that ran; it does not establish language accuracy, ownership of media, or production
readiness by itself. Record evidence for each release candidate and leave a gate open
when evidence is missing.

## 1. Functional and visual validation

- [ ] Required Python lint, unit tests, schema validation, documentation build, and multilingual smoke benchmark pass.
- [ ] Remotion type-check and composition validation pass.
- [ ] Review uploaded frames for landscape (16:9), portrait (9:16), square (1:1), and 4K; verify exact dimensions and inspect text clipping, safe margins, glyph fallback, contrast, and line wrapping.
- [ ] Verify audio/video duration and synchronization on rendered output; synthetic-tone checks are smoke tests, not proof of musical synchronization.
- [ ] Confirm audio-reactive effects are deterministic for a fixed input, seed, configuration, and dependency set.
- [ ] Review representative long lyrics, punctuation, diacritics, mixed scripts, and long words at every supported aspect ratio.

## 2. Transcription, alignment, and language quality

- [ ] Use only recordings with documented permission for the intended testing and redistribution scope.
- [ ] Record source, rights holder, permission/license reference, consent scope, source checksum, sample rate, and preprocessing steps in a private or approved provenance ledger.
- [ ] Native speakers review reference transcripts and language/span boundaries; disagreements are adjudicated and documented.
- [ ] Split data by recording/source and speaker before model or heuristic tuning. Keep the held-out test split untouched until final evaluation.
- [ ] Publish per-language support, precision, recall, F1, accuracy, confusion matrix, unknown rate, code-switch precision/recall, and timing error summaries with sample counts and uncertainty where appropriate.
- [ ] Report separate results for text-only language hints, audio transcription, word alignment, and code-switch span detection. Do not describe synthetic smoke metrics as real-world accuracy.
- [ ] Inspect word-level timing against audio and report median/95th-percentile absolute boundary error; timestamp monotonicity alone is insufficient.
- [ ] For under-resourced languages (including Shona, isiNdebele, isiZulu, and isiXhosa), report results only for languages with enough independently reviewed held-out examples.

## 3. Asset licensing and privacy

- [ ] Decide and publish the repository's own license before inviting external redistribution or contributions.
- [ ] Audit every bundled audio, image, font, video, model, and dataset asset. Record exact path, source/provenance, creator or rights holder, license/permission, attribution requirements, modification status, and allowed redistribution/use.
- [ ] Confirm music and lyric rights separately: permission to test a recording does not automatically grant rights to redistribute it or publish lyrics.
- [ ] Remove assets with unclear provenance from release artifacts; do not infer a license from a filename, public URL, or repository presence.
- [ ] Ensure consent records and reviewer identities remain private; use pseudonymous IDs in public benchmark metadata.
- [ ] Verify third-party model and font licenses cover the intended runtime, commercial use (if applicable), and distribution mode.

## 4. Dependency and supply-chain security

- [ ] Run Semgrep and review findings; do not treat a clean static scan as a dependency audit.
- [ ] Run dependency vulnerability audits for both Python and npm dependency graphs; triage all high/critical findings or document an approved, time-bounded exception.
- [ ] Keep the npm lockfile in sync with package manifests and use lockfile-based installs in CI.
- [ ] Pin Python dependencies for release builds, record Python/Node/FFmpeg/OS versions, and retain an SBOM or machine-readable dependency inventory.
- [ ] Review licenses of direct and transitive dependencies and retain the audit output with the release evidence.
- [ ] Avoid downloading model weights or executable assets without verifying their origin, checksum, license, and integrity.

## 5. Reproducibility and rollback

- [ ] Build from a clean checkout at an immutable commit SHA using lockfile/pinned dependencies.
- [ ] Record configuration, model identifiers and versions, source-audio checksums, generated cue hashes, render dimensions/FPS, FFmpeg version, and final artifact checksums.
- [ ] Re-run a representative render and compare output metadata plus approved visual/audio tolerances. Document expected nondeterminism from platform codecs.
- [ ] Tag the release commit and preserve CI reports, visual-review artifacts, benchmark JSON, SBOM, and licensing audit.
- [ ] Define the previous known-good release, artifact location, rollback owner, and tested rollback steps before deployment.
- [ ] Verify rollback restores both application code and compatible schemas/assets; document migrations that are not reversible.

## Current evidence limitations

The repository's synthetic multilingual fixtures are regression tests only. They are
not a native-speaker-reviewed held-out corpus, and repository metadata cannot prove
consent or licensing. A release must remain blocked for any language-quality or asset
whose evidence has not been collected and reviewed. This checklist records required
gates; it does not claim that those gates have already passed.
