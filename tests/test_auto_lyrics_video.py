"""Tests for the end-to-end auto-lyrics CLI helpers."""
import pytest

from tools.make_auto_lyrics_video import safe_song_id


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
