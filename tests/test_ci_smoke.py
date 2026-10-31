"""Fast smoke tests for the Python pipeline used by GitHub Actions."""

from pathlib import Path

import numpy as np
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
