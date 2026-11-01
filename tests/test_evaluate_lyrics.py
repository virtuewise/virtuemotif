"""Tests for offline multilingual ASR evaluation."""
import pytest

from tools.evaluate_lyrics import evaluate_documents, word_error_rate


def _document(segments: list[dict[str, object]]) -> dict[str, object]:
    return {"schema_version": 1, "segments": segments}


def test_word_error_rate_counts_insertions_and_normalizes_case() -> None:
    assert word_error_rate("We are one", "we are the one") == pytest.approx(1 / 3)


def test_word_error_rate_is_undefined_for_empty_reference() -> None:
    assert word_error_rate("", "unexpected words") is None


def test_evaluation_scores_language_by_timestamp_overlap() -> None:
    reference = _document([
        {"start": 0, "end": 2, "text": "Ndinoda rudo", "language": "sn"},
        {"start": 3, "end": 5, "text": "We are one", "language": "en"},
    ])
    hypothesis = _document([
        {"start": 0.1, "end": 1.9, "text": "Ndinoda rudo", "language": "sn"},
        {"start": 3.1, "end": 4.9, "text": "We are one", "language": "zu"},
    ])

    report = evaluate_documents(reference, hypothesis)
    assert report["word_error_rate"] == 0
    assert report["language_segments_scored"] == 2
    assert report["language_accuracy"] == 0.5
    assert report["per_language"] == {
        "en": {"correct": 0, "total": 1, "accuracy": 0},
        "sn": {"correct": 1, "total": 1, "accuracy": 1},
    }


def test_unknown_reference_language_is_excluded_from_language_accuracy() -> None:
    reference = _document([
        {"start": 0, "end": 1, "text": "hello", "language": "und"},
    ])
    hypothesis = _document([
        {"start": 0, "end": 1, "text": "hello", "language": "en"},
    ])
    report = evaluate_documents(reference, hypothesis)
    assert report["language_accuracy"] is None
    assert report["unknown_reference_segments_ignored"] == 1


def test_evaluation_rejects_invalid_schema_and_timing() -> None:
    with pytest.raises(ValueError, match="schema_version 1"):
        evaluate_documents({"schema_version": 2}, _document([]))
    with pytest.raises(ValueError, match="finite timing"):
        evaluate_documents(
            _document([{"start": 2, "end": 1, "text": "bad"}]),
            _document([]),
        )
