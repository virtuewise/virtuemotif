from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_gate_blocks_current_unverified_repository_state() -> None:
    result = subprocess.run(
        [sys.executable, "tools/validate_release_readiness.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "root LICENSE is missing or empty" in result.stdout
    assert "non-cleared status UNVERIFIED" in result.stdout
    assert "release evidence decision must be explicitly APPROVED" in result.stdout
    assert "release evidence must record the exact 40-character release commit SHA" in result.stdout
    assert "do not bypass this gate" in result.stdout
