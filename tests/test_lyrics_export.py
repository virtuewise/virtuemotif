"""Tests for converting ASR documents to Remotion Song JSON."""
import pytest

from tools.export_lyrics_song import (
    SUPPORTED_TYPOGRAPHY_PRESETS,
    build_remotion_props,
    convert_lyrics_document,
)


def test_export_preserves_language_word_timing_and_instrumental_gaps() -> None:
    document = {
        "schema_version": 1,
        "id": "shona-track",
        "duration": 20,
        "review_required": True,
        "segments": [
            {
                "start": 4.0,
                "end": 5.0,
                "text": "Ndinoda rudo",
                "language": "sn",
                "language_confidence": 0.84,
                "words": [
                    {"text": "Ndinoda", "start": 4.0, "end": 4.5, "probability": 0.9},
                    {"text": "rudo", "start": 4.5, "end": 5.0, "probability": 0.8},
                ],
            },
            {
                "start": 12.0,
                "end": 13.0,
                "text": "We are one",
                "language": "en",
                "language_confidence": 0.92,
                "words": [],
            },
        ],
    }

    song = convert_lyrics_document(document, audio="audio/song.m4a")

    assert song["id"] == "shona-track"
    assert song["audio"] == "audio/song.m4a"
    assert song["duration"] == 20
    assert song["detectedLanguage"] == "Shona"
    assert song["detectedLanguageCode"] == "sn"
    assert song["languageConfidence"] == pytest.approx(0.88)
    assert song["reviewRequired"] is True
    assert song["sections"][0]["id"] == "intro"
    first_line = song["sections"][1]["lines"][0]
    assert first_line["text"] == "Ndinoda rudo"
    assert first_line["language"] == "sn"
    assert first_line["style"] == "display"
    assert first_line["words"][0] == {"w": "Ndinoda", "from": 4.0, "to": 4.5}
    assert any(section["label"] == "Instrumental interlude" for section in song["sections"])


def test_export_handles_instrumental_audio_without_fabricating_lyrics() -> None:
    song = convert_lyrics_document(
        {"schema_version": 1, "id": "instrumental", "duration": 9, "segments": []},
        audio="audio/instrumental.wav",
    )

    assert song["sections"] == [{
        "id": "instrumental",
        "label": "Instrumental",
        "look": "wide",
        "start": 0.0,
        "end": 9.0,
        "lines": [],
    }]
    assert song["detectedLanguage"] == "Unknown / undetected"
    assert song["detectedLanguageCode"] == "und"
    assert song["languageConfidence"] == 0


def test_export_rejects_word_timing_outside_segment() -> None:
    document = {
        "schema_version": 1,
        "segments": [{
            "start": 1.0,
            "end": 2.0,
            "text": "hello",
            "words": [{"text": "hello", "start": 0.9, "end": 1.5}],
        }],
    }

    with pytest.raises(ValueError, match="timing outside segment"):
        convert_lyrics_document(document, audio="audio/song.wav")


def test_export_requires_supported_schema_version() -> None:
    with pytest.raises(ValueError, match="schema_version 1"):
        convert_lyrics_document({"schema_version": 2, "segments": []}, audio="audio/song.wav")


def test_export_applies_selected_typography_preset_to_every_lyric_line() -> None:
    document = {
        "schema_version": 1,
        "duration": 3,
        "segments": [
            {"start": 0.5, "end": 1.5, "text": "Rudo runako", "language": "sn"},
            {"start": 2.0, "end": 2.8, "text": "Rise together", "language": "en"},
        ],
    }

    song = convert_lyrics_document(document, audio="audio/song.wav", typography_preset="neon")
    lines = [line for section in song["sections"] for line in section["lines"]]

    assert [line["style"] for line in lines] == ["neon", "neon"]
    assert set(SUPPORTED_TYPOGRAPHY_PRESETS) == {"display", "editorial", "neon", "whisper"}


def test_export_rejects_unknown_typography_preset() -> None:
    with pytest.raises(ValueError, match="unsupported typography preset"):
        convert_lyrics_document(
            {"schema_version": 1, "duration": 1, "segments": []},
            audio="audio/song.wav",
            typography_preset="glow",
        )


def test_remotion_props_wrap_song_for_generic_composition() -> None:
    song = {"id": "sample", "duration": 12.5, "sections": []}
    assert build_remotion_props(song) == {"song": song}


def test_export_rejects_out_of_order_word_timestamps() -> None:
    document = {
        "schema_version": 1,
        "segments": [{
            "start": 0, "end": 3, "text": "first second third", "language": "en",
            "words": [
                {"text": "first", "start": 0.0, "end": 0.4},
                {"text": "second", "start": 1.2, "end": 1.5},
                {"text": "third", "start": 0.8, "end": 1.0},
            ],
        }],
    }
    with pytest.raises(ValueError, match="ordered and non-overlapping"):
        convert_lyrics_document(document, audio="audio/test.wav")


def test_export_preserves_valid_word_timestamp_order() -> None:
    document = {
        "schema_version": 1,
        "segments": [{
            "start": 0, "end": 2, "text": "hello world", "language": "en",
            "words": [
                {"text": "hello", "start": 0.1, "end": 0.5},
                {"text": "world", "start": 0.6, "end": 1.0},
            ],
        }],
    }
    song = convert_lyrics_document(document, audio="audio/test.wav")
    words = song["sections"][0]["lines"][0]["words"]
    assert [word["w"] for word in words] == ["hello", "world"]
    assert [word["from"] for word in words] == [0.1, 0.6]


def test_export_rejects_overlapping_word_timestamps() -> None:
    document = {
        "schema_version": 1,
        "segments": [{
            "start": 0, "end": 2, "text": "hello world", "language": "en",
            "words": [
                {"text": "hello", "start": 0.1, "end": 0.8},
                {"text": "world", "start": 0.7, "end": 1.0},
            ],
        }],
    }
    with pytest.raises(ValueError, match="ordered and non-overlapping"):
        convert_lyrics_document(document, audio="audio/test.wav")


def test_export_accepts_adjacent_word_boundaries() -> None:
    document = {
        "schema_version": 1,
        "segments": [{
            "start": 0, "end": 1, "text": "hello world", "language": "en",
            "words": [
                {"text": "hello", "start": 0.0, "end": 0.5},
                {"text": "world", "start": 0.5, "end": 1.0},
            ],
        }],
    }
    song = convert_lyrics_document(document, audio="audio/test.wav")
    words = song["sections"][0]["lines"][0]["words"]
    assert [word["from"] for word in words] == [0.0, 0.5]
