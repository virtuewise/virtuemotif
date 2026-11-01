"""Tests for the deterministic language-ID benchmark harness."""
import json
from pathlib import Path

from tools.benchmark_language_id import evaluate

CORPUS = Path("tests/fixtures/multilingual_language_smoke_v1.json")


def test_smoke_corpus_is_repeatable_and_has_explicit_limitations() -> None:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    first = evaluate(corpus)
    second = evaluate(corpus)
    assert first == second
    assert first["examples"] == len(corpus["examples"])
    assert first["dataset_status"] == "synthetic_smoke_only_requires_native_speaker_review"
    assert "not native-speaker reviewed" in first["limitations"]


def test_report_contains_per_language_metrics_and_predictions() -> None:
    report = evaluate(json.loads(CORPUS.read_text(encoding="utf-8")))
    assert {"sn", "nd", "zu", "en", "mul", "und"} <= set(report["per_language"])
    assert len(report["predictions"]) == report["examples"]
    assert all("correct" in item and "method" in item for item in report["predictions"])
