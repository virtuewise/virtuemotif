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
