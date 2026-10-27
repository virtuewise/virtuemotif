"""Per-second RMS of the Demucs stems (handles stereo properly)."""

import pathlib
import sys
import wave

import numpy as np

ROOT = pathlib.Path(r"C:\Users\Dell\Documents\Default Project")


def rms_per_sec(path: pathlib.Path, a: float, b: float):
    with wave.open(str(path), "rb") as f:
        sr = f.getframerate()
        ch = f.getnchannels()
        sw = f.getsampwidth()
        f.setpos(int(a * sr))
        raw = f.readframes(int((b - a) * sr))
    if sw != 2:
        raise SystemExit(f"expected 16-bit, got {sw*8}")
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    n = sr
    out = []
    for i in range(0, len(x) - n + 1, n):
        seg = x[i : i + n]
        r = float(np.sqrt(np.mean(seg**2)) + 1e-9)
        out.append((a + i / sr, 20 * np.log10(r)))
    return out


def main() -> None:
    a, b = (
        float(x) for x in (sys.argv[1:3] if len(sys.argv) > 2 else (128.0, 182.0))
    )
    v = rms_per_sec(ROOT / "timing/stems/htdemucs/vocals.wav", a, b)
    print(f"{'t':>6} {'dB':>7}  bar")
    for t, dv in v:
        bar = "#" * max(0, int((dv + 60) / 2))
        print(f"{t:6.0f} {dv:7.1f}  {bar}")


if __name__ == "__main__":
    main()
