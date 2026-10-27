# Release Process

This document outlines how to cut a new version of the project and publish artifacts.

## Prerequisites
- All tests pass on the `main` branch.
- Documentation builds without errors.
- The version number is bumped in `pyproject.toml` (or `setup.cfg`).

## Steps
1. **Create a release branch**
   ```powershell
   git checkout -b release/vX.Y.Z
   ```
2. **Update the version**
   Edit the version field in `pyproject.toml` (or the appropriate config file).
3. **Update the changelog** – add a new heading `## [X.Y.Z] - YYYY‑MM‑DD` with bullet points.
4. **Commit and push**
   ```powershell
   git commit -am "Release vX.Y.Z"
   git push origin release/vX.Y.Z
   ```
5. **Open a Pull Request** to `main`. The CI workflow will run automatically.
6. **Merge** the PR after all checks pass.
7. **Create a Git tag** (GitHub will create it automatically when the PR is merged if you use the `vX.Y.Z` tag in the PR title, otherwise run:
   ```powershell
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```
8. **Publish to PyPI** (if applicable):
   ```powershell
   python -m build
   twine upload dist/*
   ```

## Post‑release
- Update the `README` badge showing the latest version.
- Announce the release on relevant channels (GitHub Releases, social media, etc.).
