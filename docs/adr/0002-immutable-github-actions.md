# ADR 0002: Pin GitHub Actions to immutable commit SHAs

- **Status:** Accepted
- **Date:** 2026-11-01

## Context

A workflow that references a mutable action version tag can receive different code when the tag moves. This weakens build provenance for code executed with repository access.

## Decision

- Reference third-party GitHub Actions by a verified full commit SHA.
- Keep the human-readable release tag in a trailing comment.
- Use the existing weekly Dependabot GitHub Actions updates to propose controlled pin refreshes.
- Treat a pin update as a dependency change: review the upstream release, update the SHA, and require CI to pass.
- Keep workflow permissions least-privileged and do not expose deployment secrets to untrusted pull-request code.

## Consequences

- Renovation PRs are less convenient to read without the version comments but are reproducible at the action-code level.
- Maintainers must review Dependabot's SHA updates and should not blindly auto-merge workflow changes.
- SHA pinning does not replace dependency alert review, secret scanning, or workflow permission audits.
