# Contributing Guidelines

We welcome contributions! Please follow these steps:

1. **Fork the repository** and clone your fork locally.
2. **Create a virtual environment** and install the development dependencies:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   ```
3. **Create a feature branch** (`git checkout -b my-feature`).
4. **Make your changes** adhering to the coding style (see `docs/linting.md`).
5. **Run tests** to ensure everything passes:
   ```powershell
   pytest
   ```
6. **Update documentation** if you add/modify functionality (see `docs/`).
7. **Commit** with a clear message and **open a Pull Request**.
8. **CI** will run automatically; address any failures before merging.

> **Tip:** If you need help, open an issue first to discuss the proposed change.
