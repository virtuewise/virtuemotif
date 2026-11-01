"""Tests for the end-to-end auto-lyrics CLI helpers."""
import json
from types import SimpleNamespace

import pytest

from tools.make_auto_lyrics_video import (
    parse_audio_duration,
    safe_song_id,
    validate_rendered_video,
)


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


@pytest.mark.parametrize(("value", "expected"), [(" 12.5 ", 12.5), ("0.25", 0.25)])
def test_parse_audio_duration_accepts_positive_finite_values(value: str, expected: float) -> None:
    assert parse_audio_duration(value) == expected


@pytest.mark.parametrize("value", ["", "nan", "inf", "-inf", "0", "-1", "unknown"])
def test_parse_audio_duration_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError, match="finite positive number"):
        parse_audio_duration(value)


def _ffprobe_result(
    *,
    width: int = 1920,
    height: int = 1080,
    fps: str = "30/1",
    video_duration: str = "12.5",
    audio_duration: str = "12.48",
    include_audio: bool = True,
) -> SimpleNamespace:
    streams = [{
        "codec_type": "video",
        "width": width,
        "height": height,
        "avg_frame_rate": fps,
        "duration": video_duration,
    }]
    if include_audio:
        streams.append({"codec_type": "audio", "duration": audio_duration})
    return SimpleNamespace(stdout=json.dumps({"streams": streams, "format": {"duration": "12.5"}}))


def test_validate_rendered_video_accepts_expected_audio_video_output(tmp_path, monkeypatch) -> None:
    output = tmp_path / "render.mp4"
    output.write_bytes(b"synthetic test placeholder")
    monkeypatch.setattr(
        "tools.make_auto_lyrics_video.subprocess.run",
        lambda *args, **kwargs: _ffprobe_result(),
    )

    report = validate_rendered_video(output, expected_duration=12.5)

    assert report["duration"] == 12.5
    assert report["video_duration"] == 12.5
    assert report["audio_duration"] == pytest.approx(12.48)
    assert (report["width"], report["height"], report["fps"]) == (1920, 1080, 30)


def test_validate_rendered_video_rejects_missing_audio_stream(tmp_path, monkeypatch) -> None:
    output = tmp_path / "render.mp4"
    output.write_bytes(b"synthetic test placeholder")
    monkeypatch.setattr(
        "tools.make_auto_lyrics_video.subprocess.run",
        lambda *args, **kwargs: _ffprobe_result(include_audio=False),
    )

    with pytest.raises(ValueError, match="missing an audio stream"):
        validate_rendered_video(output, expected_duration=12.5)


def test_validate_rendered_video_rejects_wrong_dimensions_and_frame_rate(tmp_path, monkeypatch) -> None:
    output = tmp_path / "render.mp4"
    output.write_bytes(b"synthetic test placeholder")
    monkeypatch.setattr(
        "tools.make_auto_lyrics_video.subprocess.run",
        lambda *args, **kwargs: _ffprobe_result(width=1280, height=720),
    )
    with pytest.raises(ValueError, match="unexpected video dimensions"):
        validate_rendered_video(output, expected_duration=12.5)

    monkeypatch.setattr(
        "tools.make_auto_lyrics_video.subprocess.run",
        lambda *args, **kwargs: _ffprobe_result(fps="25/1"),
    )
    with pytest.raises(ValueError, match="unexpected video frame rate"):
        validate_rendered_video(output, expected_duration=12.5)


def test_validate_rendered_video_rejects_audio_video_duration_drift(tmp_path, monkeypatch) -> None:
    output = tmp_path / "render.mp4"
    output.write_bytes(b"synthetic test placeholder")
    monkeypatch.setattr(
        "tools.make_auto_lyrics_video.subprocess.run",
        lambda *args, **kwargs: _ffprobe_result(audio_duration="11.0"),
    )

    with pytest.raises(ValueError, match="audio/video stream durations differ"):
        validate_rendered_video(output, expected_duration=12.5)


def test_validate_rendered_video_rejects_missing_output(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="missing or empty"):
        validate_rendered_video(tmp_path / "missing.mp4", expected_duration=12.5)
