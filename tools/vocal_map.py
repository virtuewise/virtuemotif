"""Print a compact vocal-activity map from a (separated) vocal stem.

Helps see which parts of a track actually carry a lead vocal: sustained notes,
instrumental gaps, repeated choruses. Output is one line per second plus
detected sung regions.
"""

import sys
import wave

import numpy as np

SR = 16000


def load(path: str) -> np.ndarray:
    with wave.open(path, "rb") as f:
        raw = f.readframes(f.getnframes())
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if f.getnchannels() > 1:  # pragma: no cover - stems are mono here
        x = x.reshape(-1, f.getnchannels()).mean(1)
    return x


def main() -> int:
    path = sys.argv[1]
    x = load(path)
    hop = 0.02
    n = int(hop * SR)
    frames = len(x) // n
    rms = np.sqrt((x[: frames * n].reshape(frames, n) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    # smooth ~0.4 s
    k = 20
    ker = np.ones(k) / k
    sm = np.convolve(db, ker, mode="same")
    peak = np.percentile(sm, 99.5)
    rel = sm - peak
    seconds = len(sm) / 50

    print(f"{path}  {seconds:.1f}s  peak {peak:.1f}dB")
    print("   t   dB   activity")
    for s in range(int(seconds)):
        chunk = rel[int(s * 50) : int((s + 1) * 50)]
        v = float(np.mean(chunk))
        bar = "#" * int(max(0, (v + 45)) / 1.5)
        print(f"{s:4d} {v:6.1f}  {bar}")

    # contiguous sung regions: above -18 dB relative to peak, >=0.35 s
    active = rel > -18
    regions = []
    start = None
    for i, a in enumerate(active):
        if a and start is None:
            start = i
        elif not a and start is not None:
            if (i - start) * hop >= 0.35:
                regions.append((start * hop, i * hop))
            start = None
    if start is not None:
        regions.append((start * hop, len(active) * hop))
    print("\nregions:")
    for a, b in regions:
        print(f"  {a:7.2f} .. {b:7.2f}   ({b-a:5.2f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
