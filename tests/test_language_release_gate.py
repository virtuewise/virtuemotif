"""Tests for the fail-closed language evaluation release gate."""
import json
from pathlib import Path

from tools.language_release_gate import release_errors
from tools.validate_language_dataset import REVIEWED_STATUS

SMOKE_CORPUS = Path("tests/fixtures/multilingual_language_smoke_v1.json")

GOVERNANCE = {
    "rights_status": "rights_cleared",
    "consent_status": "documented",
    "review_status": "native_speaker_reviewed",
    "adjudication_policy": "Two independent labels; disagreements are adjudicated.",
    "split_policy": "Group by source and speaker before split assignment.",
    "dataset_version": "test-fixture-1",
    "annotation_protocol_version": "test-protocol-1",
    "provenance_manifest_ref": "restricted://release-gate-test-manifest",
}


def _reviewed_example(example_id, split, speaker_id, source_id):
    return {
        "id": example_id,
        "text": "Example reviewed sentence",
        "language": "en",
        "split": split,
        "source_id": source_id,
        "speaker_id": speaker_id,
        "review_status": "native_speaker_reviewed",
        "consent_ref": f"private-ledger:{example_id}",
        "reviewer_ids": ["reviewer-a", "reviewer-b"],
    }


def test_synthetic_smoke_fixture_is_never_release_eligible() -> None:
    corpus = json.loads(SMOKE_CORPUS.read_text(encoding="utf-8"))
    errors = release_errors(corpus)
    assert any("synthetic smoke datasets are not releasable" in error for error in errors)


def test_reviewed_status_still_requires_all_validator_checks() -> None:
    corpus = {
        "schema_version": 1,
        "dataset_id": "incomplete-review-claim",
        "status": REVIEWED_STATUS,
        "labels": ["en"],
        "examples": [
            {"id": "e1", "text": "Hello world", "language": "en", "split": "train"},
            {"id": "e2", "text": "Good morning", "language": "en", "split": "test"},
        ],
    }
    errors = release_errors(corpus)
    assert errors
    assert any("source_id" in error for error in errors)
    assert any("governance object is required" in error for error in errors)


def test_release_gate_accepts_structurally_valid_reviewed_metadata() -> None:
    corpus = {
        "schema_version": 1,
        "dataset_id": "reviewed-structure-test",
        "status": REVIEWED_STATUS,
        "labels": ["en"],
        "governance": GOVERNANCE,
        "examples": [
            _reviewed_example("train-1", "train", "speaker-a", "source-a"),
            _reviewed_example("test-1", "test", "speaker-b", "source-b"),
        ],
    }
    assert release_errors(corpus) == []


def test_release_gate_rejects_cross_split_speaker_leakage() -> None:
    corpus = {
        "schema_version": 1,
        "dataset_id": "leakage-test",
        "status": REVIEWED_STATUS,
        "labels": ["en"],
        "governance": GOVERNANCE,
        "examples": [
            _reviewed_example("train-1", "train", "speaker-a", "source-a"),
            _reviewed_example("test-1", "test", "speaker-a", "source-b"),
        ],
    }
    assert any(
        "speaker_id 'speaker-a' crosses dataset splits" in error
        for error in release_errors(corpus)
    )
