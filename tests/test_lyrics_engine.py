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

