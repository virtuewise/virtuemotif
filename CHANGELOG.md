# Changelog

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
