"""Tests for confidence-aware lyric language timelines."""
import pytest

from tools.language_timeline import build_language_timeline


def test_timeline_preserves_timestamps_confidence_and_detects_transitions() -> None:
    report = build_language_timeline([
        {"start": 0, "end": 2, "text": "I love you tonight", "language": "en",
         "language_confidence": 0.91, "language_method": "asr"},
        {"start": 2, "end": 4, "text": "Ndinoda rudo rwako", "language": "sn",
         "language_confidence": 0.72, "language_method": "lexical-hint"},
    ])
    assert report["segments"][0]["start"] == 0
    assert report["segments"][1]["language_confidence"] == 0.72
    assert report["transitions"] == [{
        "at": 2.0, "from": "en", "to": "sn", "candidate": True, "review_required": False
    }]
    assert report["review_required"] is False


def test_short_mixed_unknown_and_low_confidence_segments_need_review() -> None:
    report = build_language_timeline([
        {"start": 0, "end": 0.5, "text": "yo", "language": "en",
         "language_confidence": 0.9},
        {"start": 0.5, "end": 1.2, "text": "maybe language", "language": "mul",
         "language_confidence": 0.4},
        {"start": 1.2, "end": 2, "text": "unknown phrase", "language": "und"},
    ])
    assert all(row["review_required"] for row in report["segments"])
    assert "short_segment" in report["segments"][0]["uncertainty_reasons"]
    assert report["transitions"][0]["review_required"] is True
    assert report["review_required"] is True


def test_timeline_does_not_force_missing_confidence_to_zero_or_certainty() -> None:
    row = build_language_timeline([
        {"start": 0, "end": 1, "text": "This is a longer phrase", "language": "en"}
    ])["segments"][0]
    assert row["language_confidence"] is None
    assert row["review_required"] is True
    assert "confidence_missing" in row["uncertainty_reasons"]


def test_transition_requires_review_when_previous_segment_is_uncertain() -> None:
    report = build_language_timeline([
        {"start": 0, "end": 1, "text": "longer English phrase", "language": "en"},
        {"start": 1, "end": 2, "text": "Ndinoda rudo rwako", "language": "sn",
         "language_confidence": 0.9},
    ])
    assert report["segments"][0]["review_required"] is True
    assert report["segments"][1]["review_required"] is False
    assert report["transitions"][0]["review_required"] is True


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_timestamps_are_rejected(value: float) -> None:
    with pytest.raises(ValueError, match="timestamps must be finite"):
        build_language_timeline([
            {"start": value, "end": 2, "text": "a longer phrase", "language": "en"}
        ])


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_confidence_becomes_uncertain(value: float) -> None:
    row = build_language_timeline([
        {"start": 0, "end": 1, "text": "a longer phrase", "language": "en",
         "language_confidence": value}
    ])["segments"][0]
    assert row["language_confidence"] is None
    assert row["review_required"] is True
    assert "confidence_missing" in row["uncertainty_reasons"]


@pytest.mark.parametrize("segments", [
    [{"start": -1, "end": 1, "text": "bad", "language": "en"}],
    [{"start": 2, "end": 1, "text": "bad", "language": "en"}],
    [
        {"start": 0, "end": 2, "text": "first phrase", "language": "en"},
        {"start": 1, "end": 3, "text": "overlap phrase", "language": "sn"},
    ],
    [{"start": 0, "text": "missing end", "language": "en"}],
])
def test_invalid_timestamp_intervals_are_rejected(segments: list[dict[str, object]]) -> None:
    with pytest.raises(ValueError):
        build_language_timeline(segments)


@pytest.mark.parametrize("threshold", [float("nan"), float("inf"), float("-inf"), -0.1, 1.1])
def test_invalid_confidence_threshold_is_rejected(threshold: float) -> None:
    with pytest.raises(ValueError, match="finite number between 0 and 1"):
        build_language_timeline([], min_confidence=threshold)
