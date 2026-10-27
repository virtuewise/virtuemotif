# Linting Guidelines

We use the following tools to keep the codebase clean and consistent:

| Tool | Purpose | Config File |
|------|---------|-------------|
| **ruff** | Fast linter + autofixer | `ruff.toml` (root) |
| **black** | Code formatter (line length 100) | none (uses defaults) |
| **isort** | Import sorting | `pyproject.toml` (section `tool.isort`) |
| **mypy** | Optional static type checking | `mypy.ini` |

## Recommended Workflow
1. Install the dev dependencies:
   ```powershell
   pip install -r requirements-dev.txt
   ```
2. Run the full lint suite locally before committing:
   ```powershell
   ruff check .
   ruff format . --check   # ensure black formatting
   isort --check-only .
   ```
3. Fix issues automatically where possible:
   ```powershell
   ruff --fix .
   black .
   isort .
   ```
4. CI will enforce the same checks on every PR.

> **Tip:** Add a pre‑commit hook (`pre-commit install`) that runs these tools on `git commit`.
