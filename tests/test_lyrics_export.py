"""Tests for converting ASR documents to Remotion Song JSON."""
import pytest

from tools.export_lyrics_song import convert_lyrics_document


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
    assert song["detectedLanguage"] == "sn"
    assert song["languageConfidence"] == pytest.approx(0.88)
    assert song["reviewRequired"] is True
    assert song["sections"][0]["id"] == "intro"
    first_line = song["sections"][1]["lines"][0]
    assert first_line["text"] == "Ndinoda rudo"
    assert first_line["language"] == "sn"
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
    assert song["detectedLanguage"] == "und"
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
