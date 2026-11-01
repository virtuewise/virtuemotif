"""Fast deterministic regression tests for the Python audio/video pipeline."""

import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
import yaml
from PIL import Image, ImageChops

from tools import check_timeline, utils
from tools.effects import EFFECT_REGISTRY
from tools.effects.waveform import WaveformEffect


def test_default_config_is_valid_yaml() -> None:
    config_path = Path("config/defaults.yaml")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert isinstance(config, dict)
    assert config["fps"] > 0
    assert config["resolution"]
    assert "waveform" in config["visual_effects"]



@pytest.mark.parametrize("fps", [0, -1, 29.97, True, "30", None])
def test_render_config_rejects_invalid_fps(fps: object) -> None:
    from tools.make_video import validate_render_config

    with pytest.raises(ValueError, match="fps must be a positive integer"):
        validate_render_config({"song_id": "test", "fps": fps})


@pytest.mark.parametrize(
    "resolution",
    [
        "",
        "1920",
        "1920x",
        "x1080",
        "1920x1080x3",
        "1920x-1080",
        "wide x tall",
        (1920,),
        (1920, 1080, 3),
        (1920, 0),
        (1920, True),
        None,
    ],
)
def test_render_config_rejects_invalid_resolution(resolution: object) -> None:
    from tools.make_video import validate_render_config

    with pytest.raises(ValueError, match="resolution"):
        validate_render_config({"song_id": "test", "resolution": resolution})


@pytest.mark.parametrize(
    ("resolution", "expected"),
    [
        ("1920x1080", (30, 1920, 1080)),
        (" 640 X 360 ", (30, 640, 360)),
        ((640, 360), (30, 640, 360)),
        ([320, 180], (30, 320, 180)),
        ("1x1", (30, 1, 1)),
    ],
)
def test_render_config_accepts_valid_settings(
    resolution: object, expected: tuple[int, int, int]
) -> None:
    from tools.make_video import validate_render_config

    assert validate_render_config(
        {"song_id": "test", "resolution": resolution}
    ) == expected


@pytest.mark.parametrize("song_id", ["", "  ", None, 12])
def test_render_config_rejects_missing_song_id(song_id: object) -> None:
    from tools.make_video import validate_render_config

    with pytest.raises(ValueError, match="song_id must be a non-empty string"):
        validate_render_config({"song_id": song_id})


def test_invalid_render_config_does_not_create_output_directory(
    tmp_path: Path,
) -> None:
    from tools.make_video import render_frames

    output_dir = tmp_path / "output"
    with pytest.raises(ValueError, match="fps must be a positive integer"):
        render_frames(
            {
                "song_id": "test",
                "fps": 0,
                "resolution": "64x36",
                "output_dir": str(output_dir),
            }
        )

    assert not output_dir.exists()


def test_waveform_effect_is_registered_and_renders_deterministically() -> None:
    assert "waveform" in EFFECT_REGISTRY

    effect = WaveformEffect({"resolution": (64, 36)})
    audio = np.ones(735, dtype=np.float32)
    frame_a = effect.apply(audio, [])
    frame_b = effect.apply(audio, [])

    assert isinstance(frame_a, Image.Image)
    assert frame_a.size == (64, 36)
    assert frame_a.mode == "RGB"
    assert ImageChops.difference(frame_a, frame_b).getbbox() is None
    assert len(set(frame_a.get_flattened_data())) > 1


def test_audio_loader_returns_expected_chunks(tmp_path: Path) -> None:
    sample_rate = 22_050
    audio_path = tmp_path / "fixture.wav"
    samples = np.zeros(sample_rate, dtype=np.float32)
    sf.write(audio_path, samples, sample_rate)

    chunks = utils.load_audio(audio_path, fps=30)

    assert len(chunks) == 30
    assert all(chunk.size > 0 for chunk in chunks)
    assert [chunk.size for chunk in chunks] == [
        ((i + 1) * sample_rate) // 30 - (i * sample_rate) // 30
        for i in range(30)
    ]


def test_audio_loader_preserves_samples_when_frame_rate_does_not_divide_rate(
    tmp_path: Path,
) -> None:
    sample_rate = 22_050
    audio_path = tmp_path / "fractional-frame.wav"
    samples = np.linspace(-1, 1, sample_rate, dtype=np.float32)
    sf.write(audio_path, samples, sample_rate, subtype="FLOAT")

    chunks = utils.load_audio(audio_path, fps=24)

    assert len(chunks) == 24
    assert sum(chunk.size for chunk in chunks) == samples.size
    assert np.concatenate(chunks) == pytest.approx(samples)
    assert [chunk.size for chunk in chunks] == [
        min(((i + 1) * sample_rate) // 24, sample_rate)
        - (i * sample_rate) // 24
        for i in range(24)
    ]


def test_audio_loader_rejects_non_positive_frame_rate(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="fps must be a positive integer"):
        utils.load_audio(tmp_path / "does-not-need-to-exist.wav", fps=0)


def test_audio_loader_converts_stereo_to_mono(tmp_path: Path) -> None:
    sample_rate = 22_050
    audio_path = tmp_path / "stereo.wav"
    left = np.full(sample_rate, 0.25, dtype=np.float32)
    right = np.full(sample_rate, -0.25, dtype=np.float32)
    sf.write(audio_path, np.column_stack((left, right)), sample_rate)

    chunks = utils.load_audio(audio_path, fps=30)

    assert len(chunks) == 30
    assert all(chunk.ndim == 1 for chunk in chunks)
    assert np.concatenate(chunks) == pytest.approx(np.zeros(sample_rate))


def test_timeline_checker_accepts_valid_timing_fixture(tmp_path: Path) -> None:
    timeline = {
        "id": "test-song",
        "duration": 2.0,
        "sections": [
            {
                "id": "verse",
                "start": 0.0,
                "end": 2.0,
                "lines": [
                    {
                        "text": "Hello world",
                        "from": 0.1,
                        "to": 1.8,
                        "words": [
                            {"w": "Hello", "from": 0.1, "to": 0.7},
                            {"w": "world", "from": 0.8, "to": 1.4},
                        ],
                    }
                ],
            }
        ],
    }
    path = tmp_path / "timeline.json"
    path.write_text(json.dumps(timeline), encoding="utf-8")

    assert check_timeline.check(path) == 0


def test_timeline_checker_rejects_invalid_line_window(tmp_path: Path) -> None:
    timeline = {
        "id": "invalid-test-song",
        "duration": 2.0,
        "sections": [
            {
                "id": "verse",
                "start": 0.0,
                "end": 2.0,
                "lines": [{"text": "Bad timing", "from": 1.5, "to": 1.0}],
            }
        ],
    }
    path = tmp_path / "invalid-timeline.json"
    path.write_text(json.dumps(timeline), encoding="utf-8")

    assert check_timeline.check(path) > 0



def test_end_to_end_render_has_expected_video_and_audio_metadata(tmp_path: Path) -> None:
    """Exercise frame generation, FFmpeg encoding, and output stream metadata."""
    import subprocess

    from tools.make_video import encode_video, render_frames

    sample_rate = 22_050
    fps = 10
    duration_seconds = 1
    samples = np.sin(
        2 * np.pi * 440 * np.arange(sample_rate * duration_seconds) / sample_rate
    ).astype(np.float32) * 0.2
    audio_path = tmp_path / "tone.wav"
    sf.write(audio_path, samples, sample_rate, subtype="FLOAT")

    cfg = {
        "song_id": "e2e-smoke",
        "fps": fps,
        "resolution": "64x36",
        "output_dir": str(tmp_path / "out"),
        "audio_path": str(audio_path),
        "visual_effects": ["waveform"],
        "visual_params": {"waveform": {"resolution": (64, 36)}},
    }
    frames_dir = render_frames(cfg)
    assert len(list(frames_dir.glob("frame_*.png"))) == fps
    video_path = encode_video(frames_dir, cfg)
    assert video_path.is_file() and video_path.stat().st_size > 0

    probe = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-count_frames",
            "-show_entries",
            "stream=codec_type,width,height,avg_frame_rate,nb_read_frames,duration",
            "-show_entries", "format=duration",
            "-of", "json",
            str(video_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    metadata = json.loads(probe.stdout)
    streams = metadata["streams"]
    video = next(stream for stream in streams if stream["codec_type"] == "video")
    audio = next(stream for stream in streams if stream["codec_type"] == "audio")

    assert (video["width"], video["height"]) == (64, 36)
    assert video["avg_frame_rate"] == "10/1"
    assert int(video["nb_read_frames"]) == fps
    assert 0.9 <= float(metadata["format"]["duration"]) <= 1.2
    assert float(audio["duration"]) > 0



def test_encode_video_propagates_ffmpeg_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed encoder must remain visible to callers and CI."""
    import subprocess

    from tools import make_video

    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    (frames_dir / "frame_00000.png").write_bytes(b"not-a-real-png")
    cfg = {
        "song_id": "encoder-failure",
        "fps": 30,
        "resolution": "64x36",
        "output_dir": str(tmp_path / "out"),
    }

    def fail_encode(*args: object, **kwargs: object) -> None:
        raise subprocess.CalledProcessError(1, ["ffmpeg"], stderr="synthetic encoder failure")

    monkeypatch.setattr(make_video.subprocess, "run", fail_encode)
    with pytest.raises(subprocess.CalledProcessError, match="Command"):
        make_video.encode_video(frames_dir, cfg)



def test_load_config_fails_early_for_missing_or_unsafe_song_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools.make_video import load_config

    monkeypatch.chdir(tmp_path)
    (tmp_path / "songs").mkdir()
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "defaults.yaml").write_text("fps: 30\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="song configuration not found"):
        load_config("does-not-exist")
    with pytest.raises(ValueError, match="file-safe identifier"):
        load_config("../outside")


def test_load_config_rejects_non_mapping_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tools.make_video import load_config

    monkeypatch.chdir(tmp_path)
    (tmp_path / "songs").mkdir()
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "defaults.yaml").write_text("fps: 30\n", encoding="utf-8")
    (tmp_path / "songs" / "broken.yaml").write_text("- not-a-mapping\n", encoding="utf-8")

    with pytest.raises(TypeError, match="YAML mapping"):
        load_config("broken")
