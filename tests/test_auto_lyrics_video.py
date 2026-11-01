"""Tests for the end-to-end auto-lyrics CLI helpers."""
import pytest

from tools.make_auto_lyrics_video import parse_audio_duration, safe_song_id


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("My Song (Live).m4a", "my-song-live-m4a"),
        ("  RISE_Together  ", "rise_together"),
        ("Shona / Ndebele", "shona-ndebele"),
    ],
)
def test_safe_song_id_is_portable(value: str, expected: str) -> None:
    assert safe_song_id(value) == expected


@pytest.mark.parametrize("value", ["", " !!! ", "///"])
def test_safe_song_id_rejects_empty_identifiers(value: str) -> None:
    with pytest.raises(ValueError, match="at least one letter or number"):
        safe_song_id(value)


@pytest.mark.parametrize(("value", "expected"), [("12.5\\n", 12.5), ("0.25", 0.25)])
def test_parse_audio_duration_accepts_positive_finite_values(value: str, expected: float) -> None:
    assert parse_audio_duration(value) == expected


@pytest.mark.parametrize("value", ["", "nan", "inf", "-inf", "0", "-1", "unknown"])
def test_parse_audio_duration_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError, match="finite positive number"):
        parse_audio_duration(value)
