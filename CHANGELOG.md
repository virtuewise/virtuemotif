# Changelog

## [Unreleased]

### Fixed
- Reject out-of-order word timestamps during AutoLyrics export instead of sorting malformed timing into an apparently valid karaoke sequence.

### Added
- Extend conservative lexical lyric-language hints to Spanish, French, Portuguese, German, and Italian, while keeping uncertain text and code-switching reviewable.

### Fixed
- Flag low-confidence ASR output for human review and validate live microphone sample-rate/chunk-duration settings before loading optional backends.
- Normalize upstream language-timeline review reasons, deduplicate them, and fail safely to human review when reason metadata is malformed.
- Reject invalid ASR segment intervals, sanitize out-of-range confidence, and exclude malformed word timestamps while marking affected lyrics for human review. Reject out-of-order word starts as well.
- Document NumPy and SoundFile as required dependencies for the end-to-end AutoLyrics audio-cue export, avoiding a late render-time dependency failure.
- Preserve the viewport-safe 3D lyric geometry fit scale while applying deterministic beat/transition motion, preventing animation from discarding the calculated fit.
- Replace unseeded randomness in the Neon-Pulse Cityscape with repeatable procedural building geometry for stable stills and full renders.
- Place FFmpeg audio inputs before output options so end-to-end video encoding with audio works reliably.
- Validate lyric word-timing tokens and timestamp order before karaoke animation; mismatched timings fall back to deterministic staggered entrances.

### Added
- Generate versioned audio-intelligence cues as part of end-to-end AutoLyrics rendering, with one sanitized song ID shared by ASR output, Remotion props, and cue lookup.
- Connect validated beat, energy, and event cues to restrained 2D lyric scaling, scenic camera motion, and horizon lighting; missing cue files retain non-audio-reactive defaults.
- Deterministic Unicode-aware lyric sizing for long lines and CJK-width characters, scaled for landscape, portrait, square, and 4K compositions.
- Named display, whisper, neon, and editorial motion-typography presets with configurable emphasis, spacing, rule, and translation styling.
- Beat/energy-driven FurWaveSynth displacement using the same validated per-frame audio cues as lyric motion.
- Multi-aspect Remotion visual-review frame artifacts and CI checks for expected PNG dimensions.
- Deterministic end-to-end render validation with `ffprobe` checks for audio/video streams, dimensions, frame rate, frame count, and duration.
- Immutable GitHub Actions commit-SHA pins, pinned Python CI constraints, architecture decision records, asset provenance guidance, and release validation/rollback gates.
- A repeatable synthetic render benchmark that reports timing, peak memory, output size, and validated media metadata as a short-lived CI artifact.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-27

### Added
- Complete tool suite under `tools/` for audio analysis, phoneme alignment, tap sync, texture generation, and frame validation.
- General-purpose effect plugin system (`tools/effects/`) with `VisualEffect` base class, registry, and `WaveformEffect`.
- Video generation orchestration pipeline via `tools/make_video.py` driven by YAML song configurations.
- Comprehensive tool documentation in `docs/tools/`.
- CI pipeline workflow via GitHub Actions (`.github/workflows/ci.yml`) for linting and doc generation.
- Developer setup guidelines in `CONTRIBUTING.md` and `requirements-dev.txt`.
- Enhanced `README.md` with system architecture, usage instructions, and quick start guides.
