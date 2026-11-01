"""Tests for the fail-closed language evaluation release gate."""
import json
from pathlib import Path

from tools.language_release_gate import release_errors
from tools.validate_language_dataset import REVIEWED_STATUS, SMOKE_STATUS

SMOKE_CORPUS = Path("tests/fixtures/multilingual_language_smoke_v1.json")


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
        "governance": {
            "rights_status": "rights_cleared",
            "consent_status": "documented",
            "review_status": "native_speaker_reviewed",
            "adjudication_policy": "Two independent labels; steward resolves disagreements.",
            "split_policy": "Group by source and speaker before split assignment.",
        },
        "examples": [
            {
                "id": "train-1",
                "text": "Example training sentence",
                "language": "en",
                "split": "train",
                "source_id": "source-a",
                "speaker_id": "speaker-a",
                "review_status": "native_speaker_reviewed",
                "consent_ref": "private-ledger:consent-a",
                "reviewer_ids": ["reviewer-a", "reviewer-b"],
            },
            {
                "id": "test-1",
                "text": "Example held-out sentence",
                "language": "en",
                "split": "test",
                "source_id": "source-b",
                "speaker_id": "speaker-b",
                "review_status": "native_speaker_reviewed",
                "consent_ref": "private-ledger:consent-b",
                "reviewer_ids": ["reviewer-a", "reviewer-b"],
            },
        ],
    }
    assert release_errors(corpus) == []


def test_release_gate_rejects_cross_split_speaker_leakage() -> None:
    corpus = {
        "schema_version": 1,
        "dataset_id": "leakage-test",
        "status": REVIEWED_STATUS,
        "labels": ["en"],
        "governance": {
            "rights_status": "rights_cleared",
            "consent_status": "documented",
            "review_status": "native_speaker_reviewed",
            "adjudication_policy": "Two independent labels.",
            "split_policy": "Group by source and speaker.",
        },
        "examples": [
            {
                "id": "train-1", "text": "Training example", "language": "en",
                "split": "train", "source_id": "source-a", "speaker_id": "speaker-a",
                "review_status": "native_speaker_reviewed", "consent_ref": "ref-a",
                "reviewer_ids": ["reviewer-a"],
            },
            {
                "id": "test-1", "text": "Held out example", "language": "en",
                "split": "test", "source_id": "source-b", "speaker_id": "speaker-a",
                "review_status": "native_speaker_reviewed", "consent_ref": "ref-b",
                "reviewer_ids": ["reviewer-a"],
            },
        ],
    }
    assert any("speaker_id 'speaker-a' crosses dataset splits" in error
               for error in release_errors(corpus))
