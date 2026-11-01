"""Run multilingual ASR, export a Remotion song, and render a lyric video end-to-end."""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILM = ROOT / "film"


def safe_song_id(value: str) -> str:
    """Convert a filename/title into a portable identifier for generated artifacts."""
    identifier = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-_").lower()
    if not identifier:
        raise ValueError("song id must contain at least one letter or number")
    return identifier


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
            "--model", args.model, "--output", str(asr_output),
        ]
        if args.language:
            transcribe.extend(["--language", args.language])
        subprocess.run(transcribe, cwd=ROOT, check=True)

        export = [
            sys.executable, "-m", "tools.export_lyrics_song", str(asr_output),
            "--audio", audio_relative.as_posix(),
            "--output", str(song_output),
            "--props-output", str(props_output),
            "--title", args.title or source.stem,
            "--artist", args.artist,
        ]
        if args.duration is not None:
            export.extend(["--duration", str(args.duration)])
        subprocess.run(export, cwd=ROOT, check=True)

        output.parent.mkdir(parents=True, exist_ok=True)
        render = [
            "npx", "remotion", "render", "src/index.ts", "AutoLyrics",
            str(output), "--props", str(props_output.relative_to(FILM)),
        ]
        subprocess.run(render, cwd=FILM, check=True)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"auto-lyrics-video: {exc}", file=sys.stderr)
        return 2

    print(f"Rendered lyric video: {output}")
    print(f"Review generated lyrics before publishing: {asr_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
