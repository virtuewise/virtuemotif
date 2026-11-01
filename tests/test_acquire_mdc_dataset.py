"""Tests for explicit and provenance-preserving MDC acquisition."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tools.acquire_mdc_dataset import acquire_dataset
from tools.free_dataset_catalog import DEFAULT_CATALOG


def test_download_requires_explicit_terms_confirmation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MDC_API_KEY", "test-key")
    with pytest.raises(ValueError, match="review and accept"):
        acquire_dataset(
            "mozilla-common-voice-zulu-scripted-27",
            confirm_terms_accepted=False,
            provenance_dir=tmp_path,
        )


def test_download_requires_mdc_api_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("MDC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="MDC_API_KEY"):
        acquire_dataset(
            "mozilla-common-voice-zulu-scripted-27",
            confirm_terms_accepted=True,
            provenance_dir=tmp_path,
        )


def test_unverified_provider_id_cannot_be_downloaded(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MDC_API_KEY", "test-key")
    with pytest.raises(ValueError, match="no verified provider dataset ID"):
        acquire_dataset(
            "mozilla-common-voice-shona-spontaneous-5",
            confirm_terms_accepted=True,
            provenance_dir=tmp_path,
        )


def test_acquisition_writes_hash_manifest(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MDC_API_KEY", "test-key")
    downloaded = tmp_path / "provider-download"
    downloaded.mkdir()
    payload = downloaded / "sample.tsv"
    payload.write_text("sentence\nexample\n", encoding="utf-8")

    sdk = ModuleType("datacollective")

    def fake_download(provider_id: str) -> Path:
        assert provider_id == "cmu610aue00jtnq07hnb00xio"
        return downloaded

    sdk.download_dataset = fake_download
    monkeypatch.setitem(sys.modules, "datacollective", sdk)
    provenance = tmp_path / "provenance"

    result = acquire_dataset(
        "mozilla-common-voice-zulu-scripted-27",
        confirm_terms_accepted=True,
        provenance_dir=provenance,
    )

    assert result == downloaded.resolve()
    record = json.loads(
        (provenance / "mozilla-common-voice-zulu-scripted-27.json").read_text(
            encoding="utf-8"
        )
    )
    assert record["provider_dataset_id"] == "cmu610aue00jtnq07hnb00xio"
    assert record["files"][0]["sha256"]
    assert record["files"][0]["size_bytes"] == payload.stat().st_size


def test_unknown_catalog_id_is_rejected(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MDC_API_KEY", "test-key")
    with pytest.raises(ValueError, match="unknown catalog id"):
        acquire_dataset("not-in-catalog", confirm_terms_accepted=True, provenance_dir=tmp_path)


def test_south_ndebele_uses_correct_code_and_warns_about_coverage() -> None:
    catalog = json.loads(DEFAULT_CATALOG.read_text(encoding="utf-8"))
    record = next(
        item
        for item in catalog["datasets"]
        if item["id"] == "mozilla-common-voice-isindebele-south-scripted-27"
    )
    assert record["languages"] == ["nr"]
    assert record["provider_dataset_id"] == "cmu60wsiu00jjnq07t52bkrlk"
    assert any("7 clips" in note for note in record["limitations"])
