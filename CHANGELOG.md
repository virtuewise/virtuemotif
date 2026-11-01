# Changelog

## [Unreleased]

### Fixed
- Place FFmpeg audio inputs before output options so end-to-end video encoding with audio works reliably.

### Added
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
