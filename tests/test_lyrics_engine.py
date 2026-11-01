"""Tests for multilingual auto-lyrics language hints and output contracts."""
import sys
from types import ModuleType, SimpleNamespace

import pytest

from tools.lyrics_engine import (
    _normalise_segment,
    build_lyrics_document,
    detect_text_language,
)


@pytest.mark.parametrize(("text", "expected"), [
    ("I love you with all my heart", "en"),
    ("Ndinoda rudo rwako moyo wangu", "sn"),
    ("yami yakho yami", "zu"),
    ("lami lakho khona ngikhona", "nd"),
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
    assert doc["language_timeline"] is not None
    assert doc["language_timeline"]["segments"][0]["review_required"] is True


def test_document_records_forced_language_and_language_distribution() -> None:
    segments = [
        {"text": "hello there my friend", "start": 0, "end": 1, "language": "en", "language_confidence": 0.9},
        {"text": "mangwanani shamwari yangu", "start": 1, "end": 2, "language": "sn", "language_confidence": 0.8},
        {"text": "uncertain phrase here", "start": 2, "end": 3},
    ]
    doc = build_lyrics_document("sample", segments, language_mode="en")
    assert doc["language_mode"] == "en"
    assert doc["language_summary"] == {"en": 1, "sn": 1, "und": 1}
    assert doc["review_required"] is True
    assert doc["language_timeline"]["language_counts"] == {"en": 1, "sn": 1, "und": 1}
    assert doc["language_timeline"]["transitions"][0]["to"] == "sn"
    assert doc["language_timeline"]["review_required"] is True


def test_document_language_summary_is_empty_for_no_segments() -> None:
    doc = build_lyrics_document("empty", [])
    assert doc["language_mode"] == "auto"
    assert doc["language_summary"] == {}
    assert doc["language_timeline"]["segments"] == []


def test_legacy_segments_without_timestamps_remain_supported() -> None:
    doc = build_lyrics_document("legacy", [{"text": "hello", "language": "en"}])
    assert doc["language_timeline"] is None
    assert doc["review_required"] is True


def test_live_transcription_offsets_each_microphone_chunk(monkeypatch: pytest.MonkeyPatch) -> None:
    from tools.lyrics_engine import transcribe_live

    class FakeSamples:
        def reshape(self, *_shape: int) -> "FakeSamples":
            return self

    class FakeSoundDevice(ModuleType):
        calls = 0

        def rec(self, *_args: object, **_kwargs: object) -> FakeSamples:
            self.calls += 1
            if self.calls == 3:
                raise KeyboardInterrupt
            return FakeSamples()

    segment = SimpleNamespace(
        start=0.5,
        end=1.2,
        text="Ndinoda rudo rwako",
        words=[SimpleNamespace(word=" Ndinoda", start=0.5, end=0.8, probability=0.9)],
    )
    info = SimpleNamespace(language="sn", language_probability=0.81)

    class FakeWhisperModel:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.transcribe_calls: list[dict[str, object]] = []

        def transcribe(self, _samples: object, **kwargs: object) -> tuple[list[object], object]:
            self.transcribe_calls.append(kwargs)
            return [segment], info

    sounddevice = FakeSoundDevice("sounddevice")
    model = FakeWhisperModel()
    faster_whisper = ModuleType("faster_whisper")
    faster_whisper.WhisperModel = lambda *_args, **_kwargs: model  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sounddevice", sounddevice)
    monkeypatch.setitem(sys.modules, "faster_whisper", faster_whisper)

    stream = transcribe_live(chunk_seconds=5.0)
    first = next(stream)
    second = next(stream)
    with pytest.raises(KeyboardInterrupt):
        next(stream)

    assert first["start"] == 0.5
    assert first["end"] == 1.2
    assert first["language"] == "sn"
    assert second["start"] == 5.5
    assert second["end"] == 6.2
    assert second["words"][0]["start"] == 5.5
    assert second["capture_mode"] == "microphone"
    assert len(model.transcribe_calls) == 2
    assert all(call["language"] is None for call in model.transcribe_calls)
    assert all(call["word_timestamps"] is True for call in model.transcribe_calls)


@pytest.mark.parametrize(("text", "expected"), [
    ("Mangwanani shamwari yangu, ndinoda rudo rwako", "sn"),
    ("Lami lakho ngikhona ngiyahamba", "nd"),
    ("Yami yakho ngiyacula kakhulu", "zu"),
    ("I love you forever, we are together", "en"),
    ("I love you, ndinoda rudo rwako", "mul"),
])
def test_reviewable_multilingual_benchmark_examples(text: str, expected: str) -> None:
    assert detect_text_language(text)["language"] == expected


def test_shared_nguni_words_remain_ambiguous() -> None:
    result = detect_text_language("mina wena thina uthando")
    assert result["language"] in {"und", "mul"}
    assert result["method"] in {"text-heuristic", "ambiguous-lexical", "code-switched-lexical"}


def test_code_switched_method_is_explicit() -> None:
    result = detect_text_language("I love you ndinoda rudo rwako")
    assert result["language"] == "mul"
    assert result["method"] == "code-switched-lexical"


@pytest.mark.parametrize("text", [
    "ngiyabonga",
    "ngiyakuthanda",
    "ngiyazi",
    "ngiyabona",
    "ngikhumbula",
    "ngizobuya",
])
def test_shared_or_overlapping_nguni_markers_do_not_force_a_single_language(text: str) -> None:
    result = detect_text_language(text)
    assert result["language"] in {"und", "mul"}
    assert result["confidence"] <= 0.4


def test_short_language_change_stays_a_candidate_and_requires_review() -> None:
    from tools.language_timeline import build_language_timeline

    report = build_language_timeline([
        {"start": 0, "end": 1, "text": "A longer English phrase", "language": "en", "language_confidence": 0.9},
        {"start": 1, "end": 1.2, "text": "yebo", "language": "zu", "language_confidence": 0.9},
    ])
    assert len(report["transitions"]) == 1
    assert report["transitions"][0]["review_required"] is True


def test_normalised_segment_preserves_asr_lexical_disagreement_for_review() -> None:
    segment = SimpleNamespace(start=0.0, end=1.4, text="Ndinoda rudo rwako", words=[])
    result = _normalise_segment(segment, "en", 0.91)
    assert result["language"] == "sn"
    assert result["asr_language"] == "en"
    assert result["language_evidence"] == {
        "asr_language": "en",
        "asr_confidence": 0.91,
        "lexical_language": "sn",
        "lexical_confidence": result["language_evidence"]["lexical_confidence"],
        "lexical_method": "lexical-hint",
        "disagreement": True,
    }
    assert result["review_required"] is True
    assert result["review_reasons"] == ["asr_lexical_disagreement"]


def test_normalised_segment_does_not_flag_agreeing_asr_and_lexical_evidence() -> None:
    segment = SimpleNamespace(start=0.0, end=1.4, text="I love you with all my heart", words=[])
    result = _normalise_segment(segment, "en", 0.91)
    assert result["language_evidence"]["disagreement"] is False
    assert result["review_required"] is False
    assert result["review_reasons"] == []
