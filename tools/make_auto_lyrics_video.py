"""Run multilingual ASR, export a Remotion song, and render a lyric video end-to-end."""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from tools.export_lyrics_song import SUPPORTED_TYPOGRAPHY_PRESETS

ROOT = Path(__file__).resolve().parents[1]
FILM = ROOT / "film"

OUTPUT_FORMATS: dict[str, dict[str, str | int]] = {
    "landscape": {"composition": "AutoLyrics", "width": 1920, "height": 1080, "fps": 30},
    "portrait": {"composition": "AutoLyricsPortrait", "width": 1080, "height": 1920, "fps": 30},
    "square": {"composition": "AutoLyricsSquare", "width": 1024, "height": 1024, "fps": 30},
    "4k": {"composition": "AutoLyrics4K", "width": 3840, "height": 2160, "fps": 30},
}


def resolve_output_format(value: str) -> dict[str, str | int]:
    """Resolve a supported render format to its composition and output dimensions."""
    try:
        return dict(OUTPUT_FORMATS[value])
    except KeyError as exc:
        raise ValueError(f"unsupported output format: {value}") from exc


def export_song_audio_cues(audio_path: Path, song_id: str) -> Path:
    """Generate the versioned cue file consumed by Remotion's Film composition."""
    try:
        from tools.export_audio_cues import export_audio_cues
    except ImportError as exc:
        raise RuntimeError(
            "Audio-reactive AutoLyrics requires NumPy and SoundFile; install them with "
            "'python -m pip install numpy soundfile'."
        ) from exc

    output_dir = FILM / "public" / "audio-cues"
    written = export_audio_cues(output_dir, {song_id: audio_path})
    if len(written) != 1:
        raise RuntimeError(f"expected one audio-cue file for {song_id!r}, got {len(written)}")
    return written[0]


def safe_song_id(value: str) -> str:
    """Convert a filename/title into a portable identifier for generated artifacts."""
    identifier = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-_").lower()
    if not identifier:
        raise ValueError("song id must contain at least one letter or number")
    return identifier


def parse_audio_duration(value: str) -> float:
    """Parse and validate an ffprobe duration or an explicit duration value."""
    try:
        duration = float(value.strip())
    except (AttributeError, ValueError) as exc:
        raise ValueError("audio duration must be a finite positive number") from exc
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("audio duration must be a finite positive number")
    return duration


def probe_audio_duration(audio_path: Path) -> float:
    """Read the full media duration, including instrumental intros and outros."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path),
        ],
        check=True, capture_output=True, text=True,
    )
    return parse_audio_duration(result.stdout)


def _parse_frame_rate(value: Any) -> float:
    """Parse ffprobe's rational frame-rate representation."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("rendered video is missing a valid average frame rate")
    try:
        if "/" in value:
            numerator, denominator = value.split("/", maxsplit=1)
            rate = float(numerator) / float(denominator)
        else:
            rate = float(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("rendered video is missing a valid average frame rate") from exc
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError("rendered video is missing a valid average frame rate")
    return rate


def validate_rendered_video(
    video_path: Path,
    *,
    expected_duration: float,
    expected_width: int = 1920,
    expected_height: int = 1080,
    expected_fps: float = 30.0,
    duration_tolerance: float = 0.5,
    av_sync_tolerance: float = 0.25,
) -> dict[str, float | int | str]:
    """Fail closed when the rendered MP4 has invalid streams or unexpected metadata."""
    path = Path(video_path)
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(f"rendered video is missing or empty: {path}")
    if not math.isfinite(expected_duration) or expected_duration <= 0:
        raise ValueError("expected duration must be a finite positive number")
    if expected_width <= 0 or expected_height <= 0:
        raise ValueError("expected video dimensions must be positive integers")
    if not math.isfinite(expected_fps) or expected_fps <= 0:
        raise ValueError("expected frame rate must be a finite positive number")
    if not math.isfinite(duration_tolerance) or duration_tolerance < 0:
        raise ValueError("duration tolerance must be finite and non-negative")
    if not math.isfinite(av_sync_tolerance) or av_sync_tolerance < 0:
        raise ValueError("A/V sync tolerance must be finite and non-negative")

    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration:stream=codec_type,width,height,avg_frame_rate,duration",
            "-of", "json", str(path),
        ],
        check=True, capture_output=True, text=True,
    )
    try:
        metadata = json.loads(result.stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("ffprobe returned invalid JSON for rendered video") from exc

    if not isinstance(metadata, dict):
        raise TypeError("ffprobe metadata must be a JSON object")
    streams = metadata.get("streams")
    if not isinstance(streams, list) or any(not isinstance(stream, dict) for stream in streams):
        raise TypeError("ffprobe metadata streams must be an array of objects")
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    if video is None:
        raise ValueError("rendered video is missing a video stream")
    if audio is None:
        raise ValueError("rendered video is missing an audio stream")
    if video.get("width") != expected_width or video.get("height") != expected_height:
        raise ValueError(
            f"unexpected video dimensions: {video.get('width')}x{video.get('height')}; "
            f"expected {expected_width}x{expected_height}"
        )

    fps = _parse_frame_rate(video.get("avg_frame_rate"))
    if not math.isclose(fps, expected_fps, rel_tol=0.001, abs_tol=0.01):
        raise ValueError(f"unexpected video frame rate: {fps:g}; expected {expected_fps:g}")

    format_data = metadata.get("format")
    if not isinstance(format_data, dict) or format_data.get("duration") is None:
        raise ValueError("ffprobe metadata is missing the container duration")
    duration = parse_audio_duration(str(format_data["duration"]))
    if abs(duration - expected_duration) > duration_tolerance:
        raise ValueError(
            f"rendered duration {duration:.3f}s differs from source duration "
            f"{expected_duration:.3f}s by more than {duration_tolerance:.3f}s"
        )

    video_duration = parse_audio_duration(str(video["duration"])) if video.get("duration") is not None else duration
    audio_duration = parse_audio_duration(str(audio["duration"])) if audio.get("duration") is not None else duration
    if abs(video_duration - audio_duration) > av_sync_tolerance:
        raise ValueError(
            f"audio/video stream durations differ by {abs(video_duration - audio_duration):.3f}s; "
            f"tolerance is {av_sync_tolerance:.3f}s"
        )

    return {
        "path": str(path),
        "duration": duration,
        "video_duration": video_duration,
        "audio_duration": audio_duration,
        "width": expected_width,
        "height": expected_height,
        "fps": fps,
    }


def _rooted(path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Transcribe audio, export multilingual lyrics, and render an AutoLyrics video."
    )
    parser.add_argument("audio", type=Path, help="Source audio file (must be rights-cleared)")
    parser.add_argument("--output", type=Path, default=Path("out/auto-lyrics.mp4"))
    parser.add_argument("--song-id", help="Optional identifier for generated files")
    parser.add_argument("--title", help="Song title shown in the video")
    parser.add_argument("--artist", default="virtuemotif")
    parser.add_argument("--model", default="small", help="faster-whisper model size/name")
    parser.add_argument("--language", help="Force an ASR language code; omit for auto-detection")
    parser.add_argument("--duration", type=float, help="Full audio duration in seconds")
    parser.add_argument(
        "--format",
        choices=tuple(OUTPUT_FORMATS),
        default="landscape",
        help="Output format: landscape (1920x1080), portrait (1080x1920), square (1024x1024), or 4k (3840x2160)",
    )
    parser.add_argument(
        "--typography-preset",
        choices=SUPPORTED_TYPOGRAPHY_PRESETS,
        default="display",
        help="Lyric visual preset: display, editorial, neon, or whisper",
    )
    parser.add_argument("--force", action="store_true", help="Allow replacing an existing video")
    args = parser.parse_args()

    try:
        source = args.audio.expanduser().resolve()
        if not source.is_file():
            raise ValueError(f"audio file does not exist: {source}")
        song_id = safe_song_id(args.song_id or source.stem)
        output = _rooted(args.output)
        if output.exists() and not args.force:
            raise ValueError(f"output already exists: {output} (pass --force to replace it)")
        duration = parse_audio_duration(str(args.duration)) if args.duration is not None else probe_audio_duration(source)
        output_format = resolve_output_format(args.format)

        audio_relative = Path("audio") / "auto-lyrics" / f"{song_id}{source.suffix.lower()}"
        audio_destination = FILM / "public" / audio_relative
        audio_destination.parent.mkdir(parents=True, exist_ok=True)
        if source != audio_destination.resolve():
            shutil.copy2(source, audio_destination)

        asr_output = ROOT / "timing" / f"{song_id}.auto.json"
        song_output = FILM / "src" / "data" / f"{song_id}.auto.json"
        props_output = FILM / "src" / "data" / f"{song_id}.auto.props.json"
        asr_output.parent.mkdir(parents=True, exist_ok=True)
        song_output.parent.mkdir(parents=True, exist_ok=True)

        transcribe = [
            sys.executable, "-m", "tools.lyrics_engine", str(source),
            "--song-id", song_id, "--model", args.model, "--output", str(asr_output),
        ]
        if args.language:
            transcribe.extend(["--language", args.language])
        subprocess.run(transcribe, cwd=ROOT, check=True)

        export = [
            sys.executable, "-m", "tools.export_lyrics_song", str(asr_output),
            "--audio", audio_relative.as_posix(),
            "--output", str(song_output),
            "--props-output", str(props_output),
            "--song-id", song_id,
            "--title", args.title or source.stem,
            "--artist", args.artist,
            "--typography-preset", args.typography_preset,
        ]
        export.extend(["--duration", str(duration)])
        subprocess.run(export, cwd=ROOT, check=True)

        # Film resolves cues by Song.id, so keep the sanitized id consistent across
        # transcription, export, the copied audio asset, and the cue filename.
        export_song_audio_cues(audio_destination, song_id)

        output.parent.mkdir(parents=True, exist_ok=True)
        render = [
            "npx", "remotion", "render", "src/index.ts", str(output_format["composition"]),
            str(output), "--props", str(props_output.relative_to(FILM)),
        ]
        subprocess.run(render, cwd=FILM, check=True)
        validation = validate_rendered_video(
            output,
            expected_duration=duration,
            expected_width=int(output_format["width"]),
            expected_height=int(output_format["height"]),
            expected_fps=float(output_format["fps"]),
        )
    except (OSError, TypeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"auto-lyrics-video: {exc}", file=sys.stderr)
        return 2

    print(
        f"Validated video: {validation['width']}x{validation['height']} at "
        f"{validation['fps']:g} fps, {validation['duration']:.3f}s"
    )
    print(f"Rendered lyric video: {output}")
    print(f"Review generated lyrics before publishing: {asr_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
