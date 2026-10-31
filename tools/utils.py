from __future__ import annotations

import pathlib
import subprocess
import sys

# Ensure local imports work when this module is run as a script
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import numpy as np

try:
    import soundfile as sf
except ImportError:
    sf = None


def load_audio(path: str | pathlib.Path, fps: int) -> list[np.ndarray]:
    """Load audio and partition it into frame-aligned chunks.

    Chunk boundaries are derived from the sample rate and frame index rather
    than a truncated, fixed chunk size. This preserves every input sample when
    the sample rate is not evenly divisible by fps. Multichannel audio is
    converted to mono so the SoundFile and FFmpeg paths have the same shape.
    """
    if fps <= 0:
        raise ValueError("fps must be a positive integer")

    path = pathlib.Path(path)
    data = None
    samplerate = 22050

    if sf is not None:
        try:
            data, samplerate = sf.read(path, dtype="float32")
        except (OSError, RuntimeError, ValueError):
            data = None

    if data is None:
        # Fallback to ffmpeg – produce raw mono f32le PCM on stdout.
        cmd = [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            "22050",
            "-f",
            "f32le",
            "-",
        ]
        raw = subprocess.run(cmd, capture_output=True, check=True).stdout
        data = np.frombuffer(raw, dtype=np.float32)
        samplerate = 22050
    elif data.ndim > 1:
        data = np.mean(data, axis=1, dtype=np.float32)

    if samplerate <= 0:
        raise ValueError(f"Audio sample rate must be positive; got {samplerate}")

    # Rational frame boundaries avoid cumulative rounding drift and include a
    # final partial chunk instead of silently dropping its samples.
    n_frames = (len(data) * fps + samplerate - 1) // samplerate
    chunks = []
    for i in range(n_frames):
        start = (i * samplerate) // fps
        end = min(((i + 1) * samplerate) // fps, len(data))
        if end > start:
            chunks.append(data[start:end])
    return chunks
