"""Unit tests for render benchmark stream timing validation."""
import pytest

from tools.benchmark_render import _validate_av_sync


def test_av_sync_accepts_matching_stream_starts_and_durations():
    video = {"duration": "2.000", "start_time": "0.000"}
    audio = {"duration": "2.020", "start_time": "0.010"}

    video_duration, audio_duration, start_delta = _validate_av_sync(video, audio, "2.020", 30)

    assert video_duration == pytest.approx(2.0)
    assert audio_duration == pytest.approx(2.02)
    assert start_delta == pytest.approx(0.01)


def test_av_sync_rejects_large_start_time_offset():
    video = {"duration": "2.000", "start_time": "0.000"}
    audio = {"duration": "2.000", "start_time": "0.500"}

    with pytest.raises(RuntimeError, match="start-time delta"):
        _validate_av_sync(video, audio, "2.000", 30)


def test_av_sync_rejects_non_finite_duration():
    video = {"duration": "nan", "start_time": "0.000"}
    audio = {"duration": "2.000", "start_time": "0.000"}

    with pytest.raises(RuntimeError, match="non-finite"):
        _validate_av_sync(video, audio, "2.000", 30)


def test_av_sync_rejects_non_positive_duration():
    video = {"duration": "0", "start_time": "0.000"}
    audio = {"duration": "2.000", "start_time": "0.000"}

    with pytest.raises(RuntimeError, match="non-positive"):
        _validate_av_sync(video, audio, "2.000", 30)
