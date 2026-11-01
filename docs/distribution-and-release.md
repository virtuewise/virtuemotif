# Distribution and release pipeline

## Chosen distribution format

VirtueMotif is currently an application/toolchain (Python media pipeline plus a Remotion application), not a stable, public npm library. The first distribution target is therefore a **versioned GitHub Release containing a source archive, SHA-256 checksum, and build provenance**. GitHub Packages is intentionally not used until a separately versioned reusable engine API exists.

The release workflow lives at `.github/workflows/release.yml`. A `vMAJOR.MINOR.PATCH` tag triggers validation; publication only happens after the tagged source passes the release evidence gate, Python tests, multilingual dataset governance, npm vulnerability audit, TypeScript checks, and Remotion composition validation. The publish job alone receives `contents: write`; build and validation jobs use read-only permissions. Workflow actions are pinned to full commit SHAs.

## Fail-closed policy

`tools/validate_release_readiness.py` blocks release candidates unless:
- the project owner has supplied a non-empty root `LICENSE`;
- the asset provenance ledger is populated and every row is cleared or explicitly removed;
- each cleared asset records the rights holder, source/evidence record, permission/license, and reviewer;
- removed assets are actually absent from the source tree;
- `CHANGELOG.md` retains an `Unreleased` section.

This validates the presence and structure of evidence; it does not independently establish that legal statements are true. The current repository has no root license and contains assets marked `UNVERIFIED`, so a real release is expected to fail closed until the owner resolves those blockers. Do not change asset statuses to make CI green without the underlying evidence.

## Operating procedure

1. Obtain owner approval for the project license and resolve the provenance inventory using `docs/release-checklist.md`.
2. Review the changelog, run the full CI suite, and record human visual/audio and multilingual benchmark review in `docs/release-evidence-record.md`.
3. Tag the exact reviewed commit as `vMAJOR.MINOR.PATCH` and push the tag. The workflow re-runs release checks against that tag, then creates a GitHub Release with source archive, checksum, build information, and generated release notes.
4. If a check fails, no GitHub Release is published. Fix the underlying issue and use a new tag for a corrected candidate; do not overwrite an existing release.
5. Verify the release page and download/checksum after publication. Keep the prior known-good release available for rollback.

A manual `workflow_dispatch` run validates a supplied existing version tag and uploads a short-lived candidate artifact for review; it intentionally does not publish. This gives maintainers a dry-run path before creating a release tag.

## Scope and known limitations

The source archive is not a prebuilt desktop installer or container image. No npm package is published because the project does not yet define a stable package API. Release gates do not replace human approval of audio/video synchronization, typography, native-speaker benchmark quality, rights, or consent evidence.
