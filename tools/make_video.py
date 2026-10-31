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
    """Load default config combined with song-specific config."""
    defaults_path = Path("config/defaults.yaml")
    song_path = Path(f"songs/{song_id}.yaml")

    defaults = (
        yaml.safe_load(defaults_path.read_text(encoding="utf-8"))
        if defaults_path.exists()
        else {}
    )
    song_cfg = (
        yaml.safe_load(song_path.read_text(encoding="utf-8"))
        if song_path.exists()
        else {}
    )

    cfg = {**defaults, **song_cfg}
    if "song_id" not in cfg:
        cfg["song_id"] = song_id
    return cfg


def render_frames(cfg: dict[str, Any]) -> Path:
    """Render each frame according to active effects and audio."""
    output_dir = Path(cfg.get("output_dir", "out")) / cfg["song_id"]
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_path = cfg.get("audio_path")
    fps = cfg.get("fps", 30)
    res_str = cfg.get("resolution", "1920x1080")
    if isinstance(res_str, str):
        width, height = map(int, res_str.split("x"))
    else:
        width, height = res_str

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
    out_dir = Path(cfg.get("output_dir", "out"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{cfg['song_id']}.mp4"
    fps = cfg.get("fps", 30)

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%05d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(out_path),
    ]
    if cfg.get("audio_path") and Path(cfg["audio_path"]).exists():
        cmd.extend(["-i", str(cfg["audio_path"]), "-c:a", "aac", "-shortest"])

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
