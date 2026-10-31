"""Fast smoke tests for the Python pipeline used by GitHub Actions."""

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
import yaml
from PIL import Image

from tools import utils
from tools.effects import EFFECT_REGISTRY
from tools.effects.waveform import WaveformEffect


def test_default_config_is_valid_yaml() -> None:
    config_path = Path("config/defaults.yaml")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert isinstance(config, dict)
    assert config["fps"] > 0
    assert config["resolution"]
    assert "waveform" in config["visual_effects"]


def test_waveform_effect_is_registered_and_renders_frame() -> None:
    assert "waveform" in EFFECT_REGISTRY

    effect = WaveformEffect({"resolution": (64, 36)})
    frame = effect.apply(np.ones(735, dtype=np.float32), [])

    assert isinstance(frame, Image.Image)
    assert frame.size == (64, 36)


def test_audio_loader_returns_expected_chunks(tmp_path: Path) -> None:
    sample_rate = 22_050
    audio_path = tmp_path / "fixture.wav"
    samples = np.zeros(sample_rate, dtype=np.float32)
    sf.write(audio_path, samples, sample_rate)

    chunks = utils.load_audio(audio_path, fps=30)

    assert len(chunks) == 30
    assert all(chunk.size > 0 for chunk in chunks)


def test_audio_loader_preserves_samples_when_frame_rate_does_not_divide_rate(
    tmp_path: Path,
) -> None:
    sample_rate = 22_050
    audio_path = tmp_path / "fractional-frame.wav"
    samples = np.linspace(-1, 1, sample_rate, dtype=np.float32)
    sf.write(audio_path, samples, sample_rate)

    chunks = utils.load_audio(audio_path, fps=24)

    assert len(chunks) == 24
    assert sum(chunk.size for chunk in chunks) == samples.size
    assert np.concatenate(chunks) == pytest.approx(samples)


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
