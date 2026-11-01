"""Tests for multilingual auto-lyrics language hints and output contracts."""
from types import SimpleNamespace

import pytest

from tools.lyrics_engine import _normalise_segment, build_lyrics_document, detect_text_language


@pytest.mark.parametrize(("text", "expected"), [
    ("I love you with all my heart", "en"),
    ("Ndinoda rudo rwako moyo wangu", "sn"),
    ("yami yakho yami", "zu"),
    ("Die liefde is vir ons", "af"),
    ("", "und"),
    ("123 !!!", "und"),
])
def test_detect_text_language(text: str, expected: str) -> None:
    assert detect_text_language(text)["language"] == expected


def test_script_detector_handles_non_latin_text() -> None:
    result = detect_text_language("Привет, как дела?")
    assert result["language"] == "ru"
    assert result["method"] == "script"


def test_ambiguous_short_phrase_does_not_claim_certainty() -> None:
    result = detect_text_language("mina wena")
    assert result["language"] == "und"
    assert result["confidence"] <= 0.25


def test_normalised_segment_preserves_asr_and_heuristic_language() -> None:
    segment = SimpleNamespace(start=1.25, end=2.5, text="Ndinoda rudo rwako",
        words=[SimpleNamespace(word=" Ndinoda", start=1.25, end=1.8, probability=0.91)])
    result = _normalise_segment(segment, "en", 0.62)
    assert result["language"] == "sn"
    assert result["asr_language"] == "en"
    assert result["words"][0]["text"] == "Ndinoda"
    assert result["words"][0]["probability"] == 0.91


def test_unknown_text_falls_back_to_asr_language() -> None:
    segment = SimpleNamespace(start=0.0, end=1.0, text="xylophone glimmer", words=[])
    result = _normalise_segment(segment, "fr", 0.87)
    assert result["language"] == "fr"
    assert result["language_method"] == "asr-segment-fallback"


def test_document_marks_machine_lyrics_for_review() -> None:
    doc = build_lyrics_document("sample", [{"text": "hello", "start": 0, "end": 1}])
    assert doc["schema_version"] == 1
    assert doc["id"] == "sample"
    assert doc["review_required"] is True
