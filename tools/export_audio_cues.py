"""Generate Remotion-ready versioned audio-intelligence JSON for film assets."""
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from tools.audio_intelligence import analyze_file


DEFAULT_SONGS = {
    "horizon": Path("film/public/audio/horizon.m4a"),
    "rise": Path("film/public/audio/rise.m4a"),
}


def export_audio_cues(output_dir: Path, songs: dict[str, Path] | None = None) -> list[Path]:
    """Analyze configured audio assets and write one schema-versioned JSON file per song."""
    written: list[Path] = []
    for song_id, audio_path in (songs or DEFAULT_SONGS).items():
        if not audio_path.is_file():
            raise FileNotFoundError(f"audio asset for {song_id!r} was not found: {audio_path}")
        # libsndfile support for AAC varies by runner, so normalize source audio with FFmpeg.
        with tempfile.TemporaryDirectory(prefix="virtuemotif-cues-") as temp_dir:
            wav_path = Path(temp_dir) / f"{song_id}.wav"
            subprocess.run(
                ["ffmpeg", "-v", "error", "-i", str(audio_path), "-ac", "1", "-ar", "22050", "-f", "wav", str(wav_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            result = analyze_file(wav_path)
        output = output_dir / f"{song_id}.audio-intelligence.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json_dumps(result), encoding="utf-8")
        written.append(output)
    return written


def json_dumps(value: object) -> str:
    """Serialize JSON consistently for reproducible commits and CI artifacts."""
    import json

    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + chr(10)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("film/public/audio-cues"),
        help="Directory for Remotion static cue JSON (default: film/public/audio-cues)",
    )
    args = parser.parse_args()
    for path in export_audio_cues(args.output_dir):
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
