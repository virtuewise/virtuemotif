# Release evidence record

Use one copy of this template per candidate release. Keep the completed record with the release artifacts and CI links. This template is a record of human and machine observations, not proof that an assertion is true. Do not commit private audio, identity details, consent forms, or restricted legal documents; reference access-controlled records using stable internal IDs.

## Candidate identity

- Product/version (owner-approved):
- Repository:
- Release commit SHA:
- Previous known-good commit/tag for rollback:
- Release owner:
- Review date (UTC):
- Decision: `NOT REVIEWED` / `BLOCKED` / `APPROVED` / `REJECTED`

## Automated checks

| Check | Workflow run URL | Commit SHA | Result | Notes / artifact reference |
|---|---|---|---|---|
| Python lint and tests | | | PENDING | |
| Remotion type check and compositions | | | PENDING | |
| Render/ffprobe validation | | | PENDING | |
| Semgrep | | | PENDING | |
| Python dependency audit | | | PENDING | |
| npm dependency audit | | | PENDING | |
| License and attribution review | | | PENDING | |

Only mark a check PASS if its workflow/result was inspected and corresponds to the candidate commit. Link retained artifacts; do not copy secrets or private data.

## Media rights and consent

For every source asset, refer to a row in `docs/asset-provenance-ledger.csv` and record:

- Asset identifier and SHA-256:
- Rights-holder/source record reference (access-controlled where needed):
- Composition and master recording permission scope, if audio:
- Performer/voice and likeness consent scope, if applicable:
- Lyrics/transcription permission scope, if applicable:
- Commercial use, modification, redistribution, territory and duration:
- Attribution requirement and rendered attribution verification:
- Reviewer role / pseudonymous reviewer ID:
- Decision and date:

**Gate:** no asset may be described as cleared if evidence is missing, ambiguous, expired, or out of scope. Repository presence is not permission.

## Multilingual annotation and held-out evaluation

Complete one entry per language, dialect, or code-switch test cohort. Keep train/validation/test source and speaker groups separated.

| Field | Record |
|---|---|
| Language / dialect / code-switch pair | |
| Dataset ID and version | |
| Test example count and duration | |
| Source and speaker separation verified by | |
| Rights / consent record references | |
| Native-speaker reviewer IDs (pseudonymous) | |
| Independent annotation protocol/version | |
| Disagreement and adjudication summary | |
| Prediction commit/model/backend versions | |
| Evaluation command and workflow run | |
| Word-match precision / recall | |
| Start-boundary MAE / median / p95 (seconds) | |
| End-boundary MAE / median / p95 (seconds) | |
| Manual listening audit sample and findings | |
| Known limitations and remediation | |
| Decision / reviewer / date | |

Do not claim language support from a label alone. Report unsupported/uncertain speech, code-switching, low-confidence output and transcription omissions explicitly. Synthetic fixtures are CI smoke tests, not real-world accuracy evidence.

## Visual, audio, and synchronization review

For each representative output (landscape, portrait, square, 4K where supported), record:

- Workflow run, artifact name, composition and output SHA-256:
- Resolution, frame rate, duration, audio/video stream details:
- Text clipping, Unicode shaping, diacritics and line-break observations:
- Safe margins, contrast, legibility and translation layout:
- Transition/motion intensity and beat synchronization:
- Audio/video sync observations and measurement method:
- Reviewer ID, review date, defects, disposition and follow-up issue:

Attach or reference before/after evidence. Automated still renders do not substitute for human visual inspection or listening.

## Reproducibility, performance, and rollback

- Build environment / OS / runtime versions:
- Input identifiers and checksums (only rights-cleared samples):
- Exact commands and configuration:
- Render duration, peak memory, output size and ffprobe report:
- Re-run comparison and expected deterministic tolerances:
- Previous known-good artifact/tag and verified restoration steps:
- Rollback rehearsal date, operator and result:
- Outstanding risks, accepted deviations and accountable owner:

## Final release decision

- [ ] Required automated checks passed on the candidate commit.
- [ ] All distributed assets have verified permission and required attribution.
- [ ] Held-out multilingual results are based on genuinely reviewed, rights-cleared samples.
- [ ] Human visual/audio review is complete for supported output formats.
- [ ] Reproducibility and rollback have been demonstrated.
- [ ] Known limitations are documented and user-facing claims are accurate.
- [ ] Release owner approved this exact commit.

**Final decision:** `BLOCKED` until all applicable gates are evidenced. Record approver, UTC date, exact commit SHA, and rationale:
