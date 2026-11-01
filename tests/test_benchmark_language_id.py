"""Tests for the deterministic language-ID benchmark harness."""
import json
from pathlib import Path

from tools.benchmark_language_id import evaluate
from tools.validate_language_dataset import SMOKE_STATUS

CORPUS = Path("tests/fixtures/multilingual_language_smoke_v1.json")


def test_smoke_corpus_is_repeatable_and_has_explicit_limitations() -> None:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    first = evaluate(corpus)
    second = evaluate(corpus)
    assert first == second
    assert first["examples"] == len(corpus["examples"])
    assert first["dataset_status"] == SMOKE_STATUS
    assert first["evidence_level"] == "synthetic_smoke_only"
    assert "Synthetic smoke scores are regression plumbing only" in first["limitations"]


def test_report_contains_per_language_metrics_and_predictions() -> None:
    report = evaluate(json.loads(CORPUS.read_text(encoding="utf-8")))
    assert {"sn", "nd", "zu", "en", "mul", "und"} <= set(report["per_language"])
    assert len(report["predictions"]) == report["examples"]
    assert all("correct" in item and "method" in item for item in report["predictions"])
    assert all("split" in item for item in report["predictions"])
    assert all(
        {"support", "precision", "recall", "f1", "accuracy"} <= set(metrics)
        for metrics in report["per_language"].values()
    )
    assert {"precision", "recall", "f1", "accuracy"} <= set(report["macro_average"])
    assert report["unknown_behavior"]["reference_unknown"] == 2
    assert "predicted_unknown_rate" in report["unknown_behavior"]

    assert report["code_switch_detection"]["positive_label"] == "mul"
    assert report["code_switch_detection"]["support"] == 2
    calibration = report["confidence_calibration"]
    assert calibration["method"] == "top_label_confidence_vs_correctness"
    assert 0.0 <= calibration["expected_calibration_error"] <= 1.0
    assert 0.0 <= calibration["brier_score"] <= 1.0
    assert calibration["bin_stats"]
    assert "heuristic scores" in calibration["warning"]


def test_metrics_handle_labels_never_predicted() -> None:
    corpus = {
        "schema_version": 1,
        "dataset_id": "never-predicted-label-smoke",
        "status": SMOKE_STATUS,
        "labels": ["xx", "en"],
        "examples": [
            {
                "id": "e1",
                "text": "I love you forever",
                "language": "xx",
                "split": "smoke",
            }
        ],
    }
    report = evaluate(corpus)
    assert report["per_language"]["xx"]["recall"] == 0.0
    assert report["per_language"]["xx"]["f1"] == 0.0
    assert report["per_language"]["en"]["support"] == 0



def _reviewed_split_corpus() -> dict:
    return {
        "schema_version": 1,
        "dataset_id": "split-selection-test",
        "status": "reviewed",
        "labels": ["en", "sn"],
        "governance": {
            "rights_status": "rights_cleared",
            "consent_status": "documented",
            "review_status": "native_speaker_reviewed",
            "adjudication_policy": "Two independent labels; disagreements adjudicated.",
            "split_policy": "Group by source and speaker before assigning splits.",
        },
        "examples": [
            {
                "id": "train-en", "text": "Good morning everyone", "language": "en",
                "split": "train", "source_id": "source-train", "speaker_id": "speaker-train",
                "review_status": "native_speaker_reviewed", "consent_ref": "ledger:train",
                "reviewer_ids": ["reviewer-a", "reviewer-b"],
            },
            {
                "id": "test-sn", "text": "Mangwanani mose", "language": "sn",
                "split": "test", "source_id": "source-test", "speaker_id": "speaker-test",
                "review_status": "native_speaker_reviewed", "consent_ref": "ledger:test",
                "reviewer_ids": ["reviewer-a", "reviewer-b"],
            },
        ],
    }


def test_reviewed_benchmark_defaults_to_held_out_test_split() -> None:
    report = evaluate(_reviewed_split_corpus())
    assert report["evaluated_split"] == "test"
    assert report["examples"] == 1
    assert [item["id"] for item in report["predictions"]] == ["test-sn"]
    assert report["available_split_counts"] == {"test": 1, "train": 1}
    assert report["per_language"]["en"]["support"] == 0
    assert report["per_language"]["sn"]["support"] == 1


def test_reviewed_benchmark_all_splits_requires_explicit_opt_in() -> None:
    report = evaluate(_reviewed_split_corpus(), split="all")
    assert report["evaluated_split"] == "all"
    assert report["examples"] == 2
    assert {item["split"] for item in report["predictions"]} == {"train", "test"}


def test_benchmark_rejects_requested_split_without_examples() -> None:
    import pytest

    with pytest.raises(ValueError, match="requested split 'dev' has no examples"):
        evaluate(_reviewed_split_corpus(), split="dev")
