"""Repeatable synthetic-audio render benchmark for CI and local diagnostics.

This benchmark is intentionally small and rights-cleared: it synthesizes a tone,
renders a low-resolution clip, and reports metadata rather than treating timings
as a performance promise for production songs.
"""
from __future__ import annotations

import argparse
import json
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
            "stream=codec_name,codec_type,width,height,avg_frame_rate,nb_read_frames,duration",
            "-show_entries", "format=duration,size",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


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

        video_duration = float(video.get("duration") or metadata["format"]["duration"])
        audio_duration = float(audio.get("duration") or metadata["format"]["duration"])
        frame_count = int(video["nb_read_frames"])
        if frame_count != duration_seconds * fps:
            raise RuntimeError(
                f"expected {duration_seconds * fps} frames, found {frame_count}"
            )
        if (int(video["width"]), int(video["height"])) != (width, height):
            raise RuntimeError("encoded dimensions do not match the benchmark configuration")
        if video["avg_frame_rate"] != f"{fps}/1":
            raise RuntimeError(f"unexpected frame rate: {video['avg_frame_rate']}")
        if abs(video_duration - audio_duration) > max(0.15, 2 / fps):
            raise RuntimeError(
                f"audio/video duration delta exceeds tolerance: {abs(video_duration - audio_duration):.3f}s"
            )

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
