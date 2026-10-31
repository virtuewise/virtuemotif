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
    """Load an audio file and return a list of chunks, one per video frame.

    The audio is resampled to ``fps`` chunks per second so that each chunk
    corresponds to a single video frame.  The function returns a list of NumPy
    arrays containing the raw float32 samples for each chunk.
    """
    path = pathlib.Path(path)
    data = None
    samplerate = 22050

    if sf is not None:
        try:
            data, samplerate = sf.read(path, dtype="float32")
        except (OSError, RuntimeError, ValueError):
            data = None

    if data is None:
        # Fallback to ffmpeg – produce raw f32le PCM on stdout.
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

    # Determine chunk size (samples per frame)
    samples_per_frame = int(samplerate / fps)
    n_frames = len(data) // samples_per_frame
    chunks = [
        data[i * samples_per_frame : (i + 1) * samples_per_frame]
        for i in range(n_frames)
    ]
    return chunks
