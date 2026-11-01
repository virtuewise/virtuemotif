"""Repeatable synthetic-audio render benchmark for CI and local diagnostics.

This benchmark is intentionally small and rights-cleared: it synthesizes a tone,
renders a low-resolution clip, and reports metadata rather than treating timings
as a performance promise for production songs.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from tools.make_video import encode_video, render_frames


def _probe_video(path: Path) -> dict[str, Any]:
    """Return stable, relevant stream and container metadata from ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-count_frames",
            "-show_entries",
            "stream=codec_name,codec_type,width,height,avg_frame_rate,nb_read_frames,duration,start_time",
            "-show_entries", "format=duration,size",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def _validate_av_sync(
    video: dict[str, Any], audio: dict[str, Any], format_duration: Any, fps: int
) -> tuple[float, float, float]:
    """Validate stream durations and start-time alignment; return durations and start delta."""
    try:
        fallback_duration = float(format_duration)
        video_duration = float(video.get("duration") or fallback_duration)
        audio_duration = float(audio.get("duration") or fallback_duration)
        video_start = float(video.get("start_time") or 0.0)
        audio_start = float(audio.get("start_time") or 0.0)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("ffprobe returned missing or invalid audio/video timing metadata") from exc
    values = (fallback_duration, video_duration, audio_duration, video_start, audio_start)
    if not all(math.isfinite(value) for value in values):
        raise RuntimeError("ffprobe returned non-finite audio/video timing metadata")
    if fallback_duration <= 0 or video_duration <= 0 or audio_duration <= 0:
        raise RuntimeError("ffprobe returned non-positive audio/video duration")
    tolerance = max(0.15, 2 / fps)
    duration_delta = abs(video_duration - audio_duration)
    start_delta = abs(video_start - audio_start)
    if duration_delta > tolerance:
        raise RuntimeError(f"audio/video duration delta exceeds tolerance: {duration_delta:.3f}s")
    if start_delta > tolerance:
        raise RuntimeError(f"audio/video start-time delta exceeds tolerance: {start_delta:.3f}s")
    return video_duration, audio_duration, start_delta

def run_benchmark(duration_seconds: int, width: int, height: int, fps: int) -> dict[str, Any]:
    """Render deterministic synthetic audio and return measurements with metadata."""
    if duration_seconds < 1 or width < 16 or height < 16 or fps < 1:
        raise ValueError("duration, dimensions, and FPS must be positive and dimensions at least 16x16")

    sample_rate = 22_050
    sample_count = sample_rate * duration_seconds
    time_axis = np.arange(sample_count, dtype=np.float64) / sample_rate
    samples = (0.2 * np.sin(2 * np.pi * 440 * time_axis)).astype(np.float32)

    with tempfile.TemporaryDirectory(prefix="virtuemotif-benchmark-") as temp_name:
        temp = Path(temp_name)
        audio_path = temp / "synthetic-tone.wav"
        sf.write(audio_path, samples, sample_rate, subtype="FLOAT")
        cfg = {
            "song_id": "synthetic-benchmark",
            "fps": fps,
            "resolution": (width, height),
            "output_dir": str(temp / "out"),
            "audio_path": str(audio_path),
            "visual_effects": ["waveform"],
            "visual_params": {"waveform": {"resolution": (width, height)}},
        }

        started = time.perf_counter()
        frames_started = time.perf_counter()
        frames_dir = render_frames(cfg)
        render_seconds = time.perf_counter() - frames_started
        encode_started = time.perf_counter()
        video_path = encode_video(frames_dir, cfg)
        encode_seconds = time.perf_counter() - encode_started
        total_seconds = time.perf_counter() - started
        metadata = _probe_video(video_path)
        streams = metadata["streams"]
        video = next((item for item in streams if item["codec_type"] == "video"), None)
        audio = next((item for item in streams if item["codec_type"] == "audio"), None)
        if video is None or audio is None:
            raise RuntimeError("benchmark output must contain both video and audio streams")

        video_duration, audio_duration, av_start_delta = _validate_av_sync(
            video, audio, metadata["format"]["duration"], fps
        )
        frame_count = int(video["nb_read_frames"])
        if frame_count != duration_seconds * fps:
            raise RuntimeError(
                f"expected {duration_seconds * fps} frames, found {frame_count}"
            )
        if (int(video["width"]), int(video["height"])) != (width, height):
            raise RuntimeError("encoded dimensions do not match the benchmark configuration")
        if video["avg_frame_rate"] != f"{fps}/1":
            raise RuntimeError(f"unexpected frame rate: {video['avg_frame_rate']}")
        ffmpeg_version = subprocess.run(
            ["ffmpeg", "-version"], check=True, capture_output=True, text=True
        ).stdout.splitlines()[0]
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            peak_rss /= 1024
        return {
            "schema_version": 1,
            "fixture": "generated 440 Hz sine wave; no third-party media",
            "python": platform.python_version(),
            "platform": platform.platform(),
            "ffmpeg": ffmpeg_version,
            "input": {
                "duration_seconds": duration_seconds,
                "sample_rate": sample_rate,
                "channels": 1,
                "bytes": audio_path.stat().st_size,
            },
            "render": {
                "width": width,
                "height": height,
                "fps": fps,
                "frame_count": frame_count,
                "render_seconds": round(render_seconds, 4),
                "encode_seconds": round(encode_seconds, 4),
                "total_seconds": round(total_seconds, 4),
                "peak_rss_mb": round(peak_rss / 1024, 2),
                "output_bytes": video_path.stat().st_size,
                "video_duration_seconds": round(video_duration, 4),
                "audio_duration_seconds": round(audio_duration, 4),
                "av_duration_delta_seconds": round(abs(video_duration - audio_duration), 4),
                "av_start_delta_seconds": round(av_start_delta, 4),
                "video_codec": video.get("codec_name"),
                "audio_codec": audio.get("codec_name"),
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration-seconds", type=int, default=3)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=180)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    args = parser.parse_args()
    report = run_benchmark(args.duration_seconds, args.width, args.height, args.fps)
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
