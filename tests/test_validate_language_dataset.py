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
    assert any("speaker_id is required" in error for error in errors)
    assert any("reviewer_ids" in error for error in errors)


def _valid_reviewed_corpus() -> dict[str, object]:
    languages = ["sn", "nd", "zu", "en", "mul"]
    examples = []
    for split in ("train", "test"):
        for language in languages:
            example_id = f"{split}-{language}"
            examples.append({
                "id": example_id,
                "text": f"reviewed {language} sample phrase",
                "language": language,
                "split": split,
                "source_id": f"source-{example_id}",
                "speaker_id": f"speaker-{example_id}",
                "review_status": "native_speaker_reviewed",
                "reviewer_ids": ["reviewer-pseudo-1"],
                "consent_ref": f"private-consent-record-{example_id}",
            })
    return {
        "schema_version": 1,
        "dataset_id": "reviewed-test",
        "status": REVIEWED_STATUS,
        "labels": languages,
        "governance": {
            "rights_status": "rights_cleared",
            "consent_status": "documented",
            "review_status": "native_speaker_reviewed",
            "adjudication_policy": "Two independent annotations; disagreements adjudicated.",
            "split_policy": "Source/song/speaker groups do not cross train and test.",
        },
        "examples": examples,
    }

def test_reviewed_corpus_accepts_documented_governance_shape() -> None:
    assert validate_corpus(_valid_reviewed_corpus()) == []


def test_reviewed_corpus_rejects_source_or_speaker_leakage() -> None:
    corpus = _valid_reviewed_corpus()
    examples = corpus["examples"]
    assert isinstance(examples, list)
    examples[5]["source_id"] = examples[0]["source_id"]
    examples[5]["speaker_id"] = examples[0]["speaker_id"]
    errors = validate_corpus(corpus)
    assert any("source_id" in error and "crosses dataset splits" in error for error in errors)
    assert any("speaker_id" in error and "crosses dataset splits" in error for error in errors)


def test_non_object_corpus_returns_actionable_error() -> None:
    assert validate_corpus([]) == ["corpus must be a JSON object"]



def test_reviewed_corpus_requires_each_release_language_in_held_out_test() -> None:
    corpus = _valid_reviewed_corpus()
    examples = corpus["examples"]
    assert isinstance(examples, list)
    corpus["examples"] = [
        example for example in examples
        if not (example["split"] == "test" and example["language"] == "nd")
    ]
    errors = validate_corpus(corpus)
    assert any("missing required release cohorts: nd" in error for error in errors)
