"""Tests for multilingual dataset schema and governance validation."""
from __future__ import annotations

import json
from pathlib import Path

from tools.validate_language_dataset import (
    REVIEWED_STATUS,
    SMOKE_STATUS,
    validate_corpus,
)

FIXTURE = Path("tests/fixtures/multilingual_language_smoke_v1.json")


def test_existing_synthetic_smoke_fixture_is_structurally_valid() -> None:
    corpus = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert validate_corpus(corpus) == []


def test_duplicate_ids_and_unknown_labels_are_rejected() -> None:
    corpus = {
        "schema_version": 1,
        "dataset_id": "test",
        "status": SMOKE_STATUS,
        "labels": ["en"],
        "examples": [
            {"id": "same", "text": "one phrase", "language": "en", "split": "smoke"},
            {"id": "same", "text": "other phrase", "language": "sn", "split": "smoke"},
        ],
    }
    errors = validate_corpus(corpus)
    assert any("duplicates" in error for error in errors)
    assert any("absent from labels" in error for error in errors)


def test_smoke_fixture_rejects_non_smoke_split() -> None:
    corpus = {
        "schema_version": 1,
        "dataset_id": "test",
        "status": SMOKE_STATUS,
        "labels": ["en"],
        "examples": [{"id": "one", "text": "some words", "language": "en", "split": "test"}],
    }
    assert any("must be 'smoke'" in error for error in validate_corpus(corpus))


def test_reviewed_corpus_requires_governance_and_per_example_provenance() -> None:
    corpus = {
        "schema_version": 1,
        "dataset_id": "reviewed-test",
        "status": REVIEWED_STATUS,
        "labels": ["en"],
        "examples": [
            {"id": "a", "text": "sample text", "language": "en", "split": "train"},
            {"id": "b", "text": "held out text", "language": "en", "split": "test"},
        ],
    }
    errors = validate_corpus(corpus)
    assert any("governance object" in error for error in errors)
    assert any("consent_ref is required" in error for error in errors)
    assert any("reviewer_ids" in error for error in errors)


def test_reviewed_corpus_accepts_documented_governance_shape() -> None:
    example_fields = {
        "source_id": "source-anon-1",
        "review_status": "native_speaker_reviewed",
        "reviewer_ids": ["reviewer-pseudo-1"],
        "consent_ref": "private-consent-record-001",
    }
    corpus = {
        "schema_version": 1,
        "dataset_id": "reviewed-test",
        "status": REVIEWED_STATUS,
        "labels": ["en"],
        "governance": {
            "rights_status": "rights_cleared",
            "consent_status": "documented",
            "review_status": "native_speaker_reviewed",
            "adjudication_policy": "Two independent annotations; disagreements adjudicated.",
            "split_policy": "Source/song/speaker groups do not cross train and test.",
        },
        "examples": [
            {"id": "train-1", "text": "sample phrase", "language": "en", "split": "train", **example_fields},
            {"id": "test-1", "text": "held out phrase", "language": "en", "split": "test", **example_fields},
        ],
    }
    assert validate_corpus(corpus) == []


def test_non_object_corpus_returns_actionable_error() -> None:
    assert validate_corpus([]) == ["corpus must be a JSON object"]
