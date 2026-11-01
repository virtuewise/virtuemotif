# ADR 0001: Versioned, deterministic audio cue contract

- **Status:** Accepted
- **Date:** 2026-11-01
- **Decision owners:** VirtueMotif maintainers

## Context

The Python analysis pipeline and the Remotion lyric director need to share beat, energy, and event information without coupling the browser render to Python runtime dependencies. Missing or malformed analysis output must not make ordinary compositions impossible to render.

## Decision

- Serialize audio analysis as versioned JSON with an explicit `schema_version`.
- Generate cue files from the same analysis implementation used by the Python CLI.
- Validate schema, normalized ranges, ordering, and timestamp bounds at the Remotion boundary.
- Evaluate cue values deterministically from zero-based frame timestamps.
- Use deterministic frame-derived fallback motion when cue data is missing or invalid.
- Treat estimated tempo and downbeats as reviewable heuristics, not ground-truth annotations.

## Consequences

- The cue schema is a compatibility boundary and must be versioned when required fields or semantics change.
- CI regenerates cue files from source audio rather than requiring generated cue JSON to be committed.
- Tests cover schema rejection, time conversion, beat snapping, interpolation, event intensity, and fallback behavior.
- Cue generation and rendering remain dependent on the documented source-media rights and FFmpeg availability.

## Alternatives considered

- **Run analysis inside Remotion:** rejected because it would duplicate audio-analysis logic and increase browser bundle/runtime complexity.
- **Commit generated cue JSON as the source of truth:** rejected because it can become stale relative to source audio.
- **Fail every render if cues are missing:** rejected because fallback behavior makes compositions robust for previews and assets that have not yet been analyzed.
