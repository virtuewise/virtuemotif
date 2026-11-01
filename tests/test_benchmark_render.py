"""Unit tests for render benchmark stream timing validation."""
import pytest

from tools.benchmark_render import _validate_av_sync, _validate_render_metadata


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


@pytest.mark.parametrize(
    ("metadata", "message"),
    [
        ({"nb_read_frames": "89", "width": "320", "height": "180", "avg_frame_rate": "30/1"},
         "expected 90 frames"),
        ({"nb_read_frames": "90", "width": "640", "height": "180", "avg_frame_rate": "30/1"},
         "encoded dimensions"),
        ({"nb_read_frames": "90", "width": "320", "height": "180", "avg_frame_rate": "25/1"},
         "unexpected frame rate"),
        ({"width": "320", "height": "180", "avg_frame_rate": "30/1"},
         "missing or invalid render metadata"),
    ],
)
def test_render_metadata_rejects_frame_dimension_rate_or_missing_fields(metadata, message):
    with pytest.raises(RuntimeError, match=message):
        _validate_render_metadata(metadata, duration_seconds=3, width=320, height=180, fps=30)


def test_render_metadata_accepts_exact_requested_output():
    metadata = {
        "nb_read_frames": "90",
        "width": "320",
        "height": "180",
        "avg_frame_rate": "30/1",
    }
    assert _validate_render_metadata(metadata, 3, 320, 180, 30) == 90
