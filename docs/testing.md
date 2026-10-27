# Testing Guide

## Overview
This project includes a set of unit and integration tests for the Python tools located in `tools/`. Tests are written with **pytest** and use fixtures for sample audio/lyric data.

## Running Tests
```powershell
# Ensure the dev environment
python -m venv .venv-dev
.\.venv-dev\Scripts\Activate.ps1
pip install -r requirements-dev.txt

# Execute the test suite
pytest
```

## Test Structure
- `tests/unit/` – pure unit tests for individual functions.
- `tests/integration/` – end‑to‑end tests that run a tool on a small sample dataset (e.g., `align_lyrics.py` on a 5‑second audio clip).
- `tests/data/` – minimal test assets (short wav files, tiny lyric JSONs).

## Coverage
We aim for **≥ 80 %** line coverage. Generate a coverage report with:
```powershell
pytest --cov=tools --cov-report=html
```
The HTML report will be placed in `htmlcov/`.

## Continuous Integration
The GitHub Actions workflow (see `.github/workflows/ci.yml`) runs the tests on each PR and fails on coverage drops.

---

**Tip:** Add new tests for any new functionality you contribute and update the coverage target if necessary.
