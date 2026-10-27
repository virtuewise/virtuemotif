"""Correlation between the Demucs vocal and music stems, per window.

High |r| means the 'vocal' stem is mostly leakage from the music bed.
"""

import pathlib
import sys
import wave

import numpy as np

ROOT = pathlib.Path(r"C:\Users\Dell\Documents\Default Project")


def read(path: pathlib.Path, a: float, b: float):
    with wave.open(str(path), "rb") as f:
        sr = f.getframerate()
        ch = f.getnchannels()
        f.setpos(int(a * sr))
        raw = f.readframes(int((b - a) * sr))
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x, sr


def band(x, sr, lo, hi):
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / sr)
    spec[(freqs < lo) | (freqs > hi)] = 0
    return np.fft.irfft(spec, len(x))


def main() -> int:
    v = ROOT / "timing/stems/htdemucs/vocals.wav"
    m = ROOT / "timing/stems/htdemucs/no_vocals.wav"
    wins = [(90, 100), (137, 147), (147, 157), (161, 171), (192, 202), (30, 40)]
    for a, b in wins:
        x, sr = read(v, a, b)
        y, _ = read(m, a, b)
        n = min(len(x), len(y))
        x, y = x[:n], y[:n]
        # high-pass the music bed to remove bass masking the correlation
        yh = band(y, sr, 300, 3400)
        xh = band(x, sr, 300, 3400)
        r = float(np.corrcoef(xh, yh)[0, 1])
        rv = float(np.corrcoef(x, y)[0, 1])
        print(f"{a:5.0f}-{b:<5.0f}  r={rv:+.3f}  r(300-3400Hz)={r:+.3f}  vocalRMS={20*np.log10(np.sqrt((x**2).mean())+1e-9):6.1f}dB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
