"""Regression tests for beat and energy analysis."""
import numpy as np
import pytest

from tools.audio_intelligence import analyze_samples


def test_analyzer_rejects_invalid_audio_inputs() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        analyze_samples(np.zeros(100), 0)
    with pytest.raises(ValueError, match="mono"):
        analyze_samples(np.zeros((100, 2)), 16000)
    with pytest.raises(ValueError, match="no samples"):
        analyze_samples(np.zeros(0), 16000)


def test_silence_has_no_confident_tempo_or_events() -> None:
    result = analyze_samples(np.zeros(16000 * 5, dtype=np.float32), 16000)
    assert result["duration"] == 5.0
    assert result["tempo"]["bpm"] is None
    assert result["beats"] == []
    assert result["events"] == []
    assert len(result["energy_curve"]) == 5


def test_click_track_produces_beat_grid_near_known_tempo() -> None:
    sample_rate = 16000
    duration = 12
    samples = np.zeros(sample_rate * duration, dtype=np.float32)
    pulse = np.hanning(400).astype(np.float32)
    for start in range(0, len(samples), sample_rate // 2):
        samples[start : start + pulse.size] += pulse
    result = analyze_samples(samples, sample_rate)
    bpm = result["tempo"]["bpm"]
    assert bpm is not None
    assert 110 <= bpm <= 130
    assert len(result["beats"]) >= 15
    assert result["downbeats"]
    assert result["schema_version"] == 1


def test_energy_curve_and_events_are_chronological() -> None:
    sample_rate = 16000
    quiet = np.zeros(sample_rate * 2, dtype=np.float32)
    loud = np.sin(np.arange(sample_rate * 2) * 2 * np.pi * 440 / sample_rate).astype(np.float32) * 0.8
    samples = np.concatenate([quiet, loud, quiet])
    result = analyze_samples(samples, sample_rate)
    assert result["duration"] == 6.0
    assert [row["time"] for row in result["energy_curve"]] == sorted(row["time"] for row in result["energy_curve"])
    assert [row["time"] for row in result["events"]] == sorted(row["time"] for row in result["events"])
    assert any(event["type"] == "energy-rise" for event in result["events"])



def test_analysis_is_deterministic_for_identical_synthetic_audio() -> None:
    sample_rate = 16_000
    time = np.arange(sample_rate * 6, dtype=np.float32) / sample_rate
    samples = (
        0.2 * np.sin(2 * np.pi * 220 * time)
        + 0.1 * np.sin(2 * np.pi * 440 * time)
    ).astype(np.float32)

    first = analyze_samples(samples, sample_rate)
    second = analyze_samples(samples.copy(), sample_rate)

    assert first == second


def test_analyzer_rejects_non_finite_samples_and_boolean_sample_rate() -> None:
    with pytest.raises(ValueError, match="NaN or infinite"):
        analyze_samples(np.array([0.0, np.nan, 0.0], dtype=np.float32), 16_000)
    with pytest.raises(ValueError, match="positive integer"):
        analyze_samples(np.zeros(100, dtype=np.float32), True)
