"""Entry point to generate a visual-lyric video for a given song.

Usage:
    python -m tools.make_video <song_id>
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from tools import utils
from tools.effects import EFFECT_REGISTRY


def load_config(song_id: str) -> dict[str, Any]:
    """Load and validate default config merged with a required song config."""
    if (
        not isinstance(song_id, str)
        or not song_id.strip()
        or Path(song_id).name != song_id
        or song_id in {".", ".."}
    ):
        raise ValueError("song_id must be a non-empty file-safe identifier")

    defaults_path = Path("config/defaults.yaml")
    song_path = Path("songs") / f"{song_id}.yaml"
    if not song_path.is_file():
        raise FileNotFoundError(f"song configuration not found: {song_path}")

    def read_mapping(path: Path, *, optional: bool = False) -> dict[str, Any]:
        if optional and not path.is_file():
            return {}
        try:
            parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise ValueError(f"unable to read YAML configuration {path}: {exc}") from exc
        if parsed is None:
            return {}
        if not isinstance(parsed, dict):
            raise TypeError(f"configuration root must be a YAML mapping: {path}")
        return parsed

    defaults = read_mapping(defaults_path, optional=True)
    song_cfg = read_mapping(song_path)
    cfg = {**defaults, **song_cfg}
    cfg.setdefault("song_id", song_id)
    return cfg


def validate_render_config(cfg: dict[str, Any]) -> tuple[int, int, int]:
    """Validate required render settings before creating output or processing media.

    Returns (fps, width, height). Raises ValueError with an actionable message
    when a setting is malformed or outside the supported positive-integer domain.
    """
    song_id = cfg.get("song_id")
    if not isinstance(song_id, str) or not song_id.strip():
        raise ValueError("song_id must be a non-empty string")

    fps = cfg.get("fps", 30)
    if isinstance(fps, bool) or not isinstance(fps, int) or fps <= 0:
        raise ValueError("fps must be a positive integer")

    resolution = cfg.get("resolution", "1920x1080")
    if isinstance(resolution, str):
        parts = resolution.lower().split("x")
        if len(parts) != 2 or not all(part.strip().isdigit() for part in parts):
            raise ValueError(
                "resolution must be formatted as 'WIDTHxHEIGHT' with positive integers"
            )
        width, height = (int(part.strip()) for part in parts)
    elif isinstance(resolution, (tuple, list)) and len(resolution) == 2:
        width, height = resolution
    else:
        raise ValueError(
            "resolution must be formatted as 'WIDTHxHEIGHT' or a two-item sequence"
        )

    for dimension_name, dimension in (("width", width), ("height", height)):
        if (
            isinstance(dimension, bool)
            or not isinstance(dimension, int)
            or dimension <= 0
        ):
            raise ValueError(f"resolution {dimension_name} must be a positive integer")

    return fps, width, height


def render_frames(cfg: dict[str, Any]) -> Path:
    """Render each frame according to active effects and audio."""
    fps, width, height = validate_render_config(cfg)
    output_dir = Path(cfg.get("output_dir", "out")) / cfg["song_id"]
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_path = cfg.get("audio_path")

    effects = []
    for name in cfg.get("visual_effects", []):
        if name in EFFECT_REGISTRY:
            eff_cls = EFFECT_REGISTRY[name]
            params = cfg.get("visual_params", {}).get(name, {})
            params.setdefault("resolution", (width, height))
            effects.append(eff_cls(params))
        else:
            print(f"Warning: Effect '{name}' not found in registry. Skipping.")

    if not effects:
        from tools.effects.waveform import WaveformEffect

        effects = [WaveformEffect({"resolution": (width, height)})]

    if audio_path and Path(audio_path).exists():
        audio = utils.load_audio(audio_path, fps)
    else:
        import numpy as np

        audio = [np.zeros(int(22050 / fps), dtype=np.float32) for _ in range(fps)]

    prev = []
    for i, chunk in enumerate(audio):
        frame = Image.new("RGB", (width, height), "black")
        for eff in effects:
            overlay = eff.apply(chunk, prev)
            frame.paste(overlay, (0, 0))
        frame_path = output_dir / f"frame_{i:05d}.png"
        frame.save(frame_path)
        prev.append(frame)

    return output_dir


def encode_video(frames_dir: Path, cfg: dict[str, Any]) -> Path:
    """Encode rendered frames into an MP4 video using ffmpeg."""
    fps, _, _ = validate_render_config(cfg)
    out_dir = Path(cfg.get("output_dir", "out"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{cfg['song_id']}.mp4"

    # Declare every input before output options and the output path. FFmpeg treats
    # options and inputs in command-line order, so appending an audio input after
    # the output path can make otherwise valid audio/video renders fail.
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%05d.png"),
    ]
    audio_path = cfg.get("audio_path")
    has_audio = bool(audio_path and Path(audio_path).is_file())
    if has_audio:
        cmd.extend(["-i", str(audio_path)])
    cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p"])
    if has_audio:
        cmd.extend(["-c:a", "aac", "-shortest"])
    cmd.append(str(out_path))

    subprocess.run(cmd, check=True)
    print(f"Video written to {out_path}")
    return out_path


def main() -> None:
    """Main orchestration entry point."""
    parser = argparse.ArgumentParser(description="Generate visual-lyric video.")
    parser.add_argument("song_id", help="Song ID corresponding to songs/<song_id>.yaml")
    args = parser.parse_args()

    cfg = load_config(args.song_id)
    frames_dir = render_frames(cfg)
    encode_video(frames_dir, cfg)


if __name__ == "__main__":
    main()
