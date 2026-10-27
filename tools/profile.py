"""Profile audio files for RMS and vocal ratio.
Runs ffmpeg to extract raw PCM and analyses frequency content.
"""
import numpy as np
import subprocess

SR = 22050

def prof(p: str):
    """Return RMS and vocal ratio arrays for audio file *p*.
    """
    raw = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            p,
            "-ac",
            "1",
            "-ar",
            str(SR),
            "-f",
            "f32le",
            "-",
        ],
        capture_output=True,
        check=True,
    ).stdout
    y = np.frombuffer(raw, dtype=np.float32)
    hop = SR * 2
    n = len(y) // hop
    rows = []
    for i in range(n):
        s = y[i * hop : (i + 1) * hop]
        w = np.hanning(len(s)).astype(np.float32)
        m = np.abs(np.fft.rfft(s * w))
        f = np.fft.rfftfreq(len(s), 1 / SR)
        rows.append(
            (
                np.sqrt((s ** 2).mean()),
                m[(f > 300) & (f < 3200)].sum(),
                m[(f < 150)].sum(),
            )
        )
    a = np.array(rows)
    rms = a[:, 0] / (a[:, 0].max() + 1e-9)
    v = a[:, 1] / (a[:, 2] + 1e-9)
    v = v / np.percentile(v, 98)
    return rms, v

def main():
    for name in ("horizon", "rise"):
        rms, v = prof(f"film/public/audio/{name}.m4a")
        print("=== ", name, " ===  (t: rms/voice)")
        line = []
        for i in range(len(rms)):
            line.append(f"{i * 2}:{rms[i]:.2f}/{v[i]:.2f}")
            if len(line) == 8:
                print("  ".join(line))
                line = []
        if line:
            print("  ".join(line))

if __name__ == "__main__":
    main()
