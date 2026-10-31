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
    assert len(set(frame_a.getdata())) > 1


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
