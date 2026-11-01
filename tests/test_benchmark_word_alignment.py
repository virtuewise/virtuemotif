"""Tests for the reviewed word-alignment evaluation harness."""
import pytest

from tools.benchmark_word_alignment import evaluate_alignment
from tools.validate_language_dataset import REVIEWED_STATUS, SMOKE_STATUS


def _corpus(status=REVIEWED_STATUS):
    return {
        "schema_version": 1,
        "dataset_id": "alignment-test-fixture",
        "status": status,
        "labels": ["en", "sn"],
        "governance": {
            "rights_status": "rights_cleared",
            "consent_status": "documented",
            "review_status": "native_speaker_reviewed",
            "adjudication_policy": "Two independent reviews; disagreements adjudicated.",
            "split_policy": "Source and speaker groups are isolated between train and test.",
        },
        "examples": [
            {
                "id": "test-en", "text": "hello world", "language": "en", "split": "test",
                "source_id": "source-test", "speaker_id": "speaker-test",
                "review_status": "native_speaker_reviewed", "reviewer_ids": ["reviewer-a"],
                "consent_ref": "private-ledger:test",
                "words": [
                    {"text": "hello", "start": 0.1, "end": 0.4},
                    {"text": "world", "start": 0.5, "end": 0.9},
                ],
            },
            {
                "id": "train-sn", "text": "mangwanani mose", "language": "sn", "split": "train",
                "source_id": "source-train", "speaker_id": "speaker-train",
                "review_status": "native_speaker_reviewed", "reviewer_ids": ["reviewer-a"],
                "consent_ref": "private-ledger:train",
                "words": [{"text": "mangwanani", "start": 0.0, "end": 0.4}],
            },
        ],
    }


def test_alignment_benchmark_reports_per_language_timing_error():
    report = evaluate_alignment(_corpus(), {
        "test-en": [
            {"text": "hello", "start": 0.2, "end": 0.5},
            {"text": "world", "start": 0.6, "end": 1.0},
        ],
    })
    assert report["evidence_level"] == "human_reviewed_rights_cleared_reference_alignment"
    assert report["evaluated_split"] == "test"
    assert report["matching_method"] == "longest_common_subsequence_normalized_tokens"
    metrics = report["per_language"]["en"]
    assert metrics["matched_words"] == 2
    assert metrics["word_match_precision"] == 1.0
    assert metrics["word_match_recall"] == 1.0
    assert metrics["start_boundary_mae_seconds"] == pytest.approx(0.1)
    assert metrics["end_boundary_p95_absolute_error_seconds"] == pytest.approx(0.1)


def test_alignment_benchmark_fails_closed_for_smoke_data():
    corpus = _corpus(SMOKE_STATUS)
    for example in corpus["examples"]:
        example["split"] = "smoke"
    with pytest.raises(ValueError, match="requires a reviewed rights-cleared corpus"):
        evaluate_alignment(corpus, {"test-en": []})


def test_alignment_benchmark_reports_unmatched_tokens_without_fake_timing():
    report = evaluate_alignment(_corpus(), {
        "test-en": [
            {"text": "hello", "start": 0.1, "end": 0.4},
            {"text": "there", "start": 0.5, "end": 0.9},
        ],
    })
    metrics = report["per_language"]["en"]
    assert metrics["matched_words"] == 1
    assert metrics["word_match_recall"] == 0.5
    assert metrics["start_boundary_mae_seconds"] == 0.0
    assert metrics["insertions"] == 1
    assert metrics["deletions"] == 1


def test_alignment_benchmark_matches_tokens_after_insertions_without_shifting_timing():
    report = evaluate_alignment(_corpus(), {
        "test-en": [
            {"text": "hello", "start": 0.1, "end": 0.4},
            {"text": "unexpected", "start": 0.42, "end": 0.48},
            {"text": "world", "start": 0.52, "end": 0.92},
        ],
    })
    metrics = report["per_language"]["en"]
    assert metrics["matched_words"] == 2
    assert metrics["insertions"] == 1
    assert metrics["deletions"] == 0
    assert metrics["start_boundary_mae_seconds"] == pytest.approx(0.01)


def test_alignment_benchmark_rejects_invalid_unmatched_prediction_timestamps():
    with pytest.raises(ValueError, match="invalid interval"):
        evaluate_alignment(_corpus(), {
            "test-en": [
                {"text": "hello", "start": 0.1, "end": 0.4},
                {"text": "extra", "start": 0.5, "end": 0.5},
            ],
        })


def test_alignment_benchmark_requires_reference_words_for_selected_split():
    corpus = _corpus()
    corpus["examples"][0].pop("words")
    with pytest.raises(ValueError, match="requires reference words"):
        evaluate_alignment(corpus, {"test-en": []})
