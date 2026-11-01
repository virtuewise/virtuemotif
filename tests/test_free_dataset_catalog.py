"""Tests for the free dataset catalog validator."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from tools.free_dataset_catalog import DEFAULT_CATALOG, load_catalog, validate_catalog


def test_checked_in_catalog_is_valid() -> None:
    catalog = load_catalog()
    assert catalog["datasets"]
    assert {code for item in catalog["datasets"] for code in item["languages"]} >= {
        "sn",
        "zu",
        "xh",
        "en",
    }


def test_duplicate_dataset_ids_are_rejected() -> None:
    catalog = json.loads(DEFAULT_CATALOG.read_text(encoding="utf-8"))
    catalog["datasets"].append(copy.deepcopy(catalog["datasets"][0]))
    assert any("duplicate dataset id" in error for error in validate_catalog(catalog))


def test_non_https_source_is_rejected() -> None:
    catalog = json.loads(DEFAULT_CATALOG.read_text(encoding="utf-8"))
    catalog["datasets"][0]["source_url"] = "http://example.org/dataset"
    assert any("absolute HTTPS URL" in error for error in validate_catalog(catalog))


def test_unknown_license_fails_closed() -> None:
    catalog = json.loads(DEFAULT_CATALOG.read_text(encoding="utf-8"))
    catalog["datasets"][0]["license"] = "unknown"
    assert any("not allow-listed" in error for error in validate_catalog(catalog))


def test_speech_data_must_disclose_not_singing_limitation() -> None:
    catalog = json.loads(DEFAULT_CATALOG.read_text(encoding="utf-8"))
    catalog["datasets"][0]["limitations"] = ["Useful language data."]
    assert any("not singing" in error for error in validate_catalog(catalog))


def test_cli_filters_by_language() -> None:
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parents[1] / "tools" / "free_dataset_catalog.py"),
         "--language", "sn"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Common Voice Spontaneous Speech 5.0 - Shona" in result.stdout
    assert "Zulu" not in result.stdout
