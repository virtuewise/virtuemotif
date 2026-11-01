"""Tests for governance-gated language-ID benchmark evaluation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import benchmark_language_id
from tools.validate_language_dataset import REVIEWED_STATUS, SMOKE_STATUS

FIXTURE = Path("tests/fixtures/multilingual_language_smoke_v1.json")


def test_smoke_report_explicitly_labels_evidence_level() -> None:
    corpus = json.loads(FIXTURE.read_text(encoding="utf-8"))
    report = benchmark_language_id.evaluate(corpus)
    assert report["dataset_status"] == SMOKE_STATUS
    assert report["evidence_level"] == "synthetic_smoke_only"
    assert report["examples"] == len(corpus["examples"])
    assert all("split" in item for item in report["predictions"])


def test_invalid_governance_metadata_is_rejected_before_scoring() -> None:
    corpus = json.loads(FIXTURE.read_text(encoding="utf-8"))
    corpus["examples"][0]["split"] = "test"
    with pytest.raises(ValueError, match="invalid language dataset"):
        benchmark_language_id.evaluate(corpus)


def test_reviewed_status_is_reported_only_for_structurally_valid_reviewed_corpus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    corpus = {
        "schema_version": 1,
        "dataset_id": "reviewed-fixture",
        "status": REVIEWED_STATUS,
        "labels": ["en"],
        "governance": {
            "rights_status": "rights_cleared",
            "consent_status": "documented",
            "review_status": "native_speaker_reviewed",
            "adjudication_policy": "Two independent reviews with adjudication.",
            "split_policy": "Sources and speakers remain isolated between train and test.",
        },
        "examples": [
            {
                "id": "train-1",
                "text": "example train text",
                "language": "en",
                "split": "train",
                "source_id": "source-train",
                "speaker_id": "speaker-train",
                "review_status": "native_speaker_reviewed",
                "reviewer_ids": ["reviewer-a"],
                "consent_ref": "private-record-a",
            },
            {
                "id": "test-1",
                "text": "example test text",
                "language": "en",
                "split": "test",
                "source_id": "source-test",
                "speaker_id": "speaker-test",
                "review_status": "native_speaker_reviewed",
                "reviewer_ids": ["reviewer-a"],
                "consent_ref": "private-record-b",
            },
        ],
    }
    monkeypatch.setattr(
        benchmark_language_id,
        "detect_text_language",
        lambda text: {"language": "en", "confidence": 0.8, "method": "test-double"},
    )
    report = benchmark_language_id.evaluate(corpus)
    assert report["evidence_level"] == "human_reviewed_rights_cleared"
    assert report["dataset_status"] == REVIEWED_STATUS
