"""Tests for the end-to-end auto-lyrics CLI helpers."""
import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

from tools.make_auto_lyrics_video import (
    export_song_audio_cues,
    parse_audio_duration,
    resolve_output_format,
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


@pytest.mark.parametrize(
    ("name", "composition", "width", "height"),
    [
        ("landscape", "AutoLyrics", 1920, 1080),
        ("portrait", "AutoLyricsPortrait", 1080, 1920),
        ("square", "AutoLyricsSquare", 1024, 1024),
        ("4k", "AutoLyrics4K", 3840, 2160),
    ],
)
def test_resolve_output_format_maps_supported_aspects(name, composition, width, height) -> None:
    result = resolve_output_format(name)
    assert result["composition"] == composition
    assert (result["width"], result["height"], result["fps"]) == (width, height, 30)


@pytest.mark.parametrize("name", ["", "ultrawide", "vertical-4k"])
def test_resolve_output_format_rejects_unknown_formats(name: str) -> None:
    with pytest.raises(ValueError, match="unsupported output format"):
        resolve_output_format(name)


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


def test_validate_rendered_video_accepts_portrait_dimensions(tmp_path, monkeypatch) -> None:
    output = tmp_path / "portrait.mp4"
    output.write_bytes(b"synthetic test placeholder")
    monkeypatch.setattr(
        "tools.make_auto_lyrics_video.subprocess.run",
        lambda *args, **kwargs: _ffprobe_result(width=1080, height=1920),
    )

    report = validate_rendered_video(
        output,
        expected_duration=12.5,
        expected_width=1080,
        expected_height=1920,
    )

    assert (report["width"], report["height"]) == (1080, 1920)


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

def test_export_song_audio_cues_uses_the_song_id_expected_by_film(monkeypatch, tmp_path) -> None:
    source = tmp_path / "song.m4a"
    fake_exporter = ModuleType("tools.export_audio_cues")
    calls = {}

    def fake_export_audio_cues(output_dir, songs):
        calls["output_dir"] = output_dir
        calls["songs"] = songs
        return [output_dir / "shona-night.audio-intelligence.json"]

    fake_exporter.export_audio_cues = fake_export_audio_cues
    monkeypatch.setitem(sys.modules, "tools.export_audio_cues", fake_exporter)

    result = export_song_audio_cues(source, "shona-night")

    assert result == calls["output_dir"] / "shona-night.audio-intelligence.json"
    assert calls["output_dir"].name == "audio-cues"
    assert calls["songs"] == {"shona-night": source}


def test_export_song_audio_cues_rejects_missing_output(monkeypatch, tmp_path) -> None:
    fake_exporter = ModuleType("tools.export_audio_cues")
    fake_exporter.export_audio_cues = lambda *_args, **_kwargs: []
    monkeypatch.setitem(sys.modules, "tools.export_audio_cues", fake_exporter)

    with pytest.raises(RuntimeError, match="expected one audio-cue file"):
        export_song_audio_cues(tmp_path / "song.wav", "song")
