"""Probe audio file for vocal segments.
Runs ffmpeg to extract raw PCM and analyses frequency content.
"""
import numpy as np
import subprocess

SR = 22050

def main():
    raw = subprocess.run([
        "ffmpeg",
        "-v",
        "error",
        "-i",
        "film/public/audio/horizon.m4a",
        "-ac",
        "1",
        "-ar",
        str(SR),
        "-f",
        "f32le",
        "-",
    ], capture_output=True, check=True).stdout
    y = np.frombuffer(raw, dtype=np.float32)
    hop = SR // 2
    n = len(y) // hop
    feat = []
    for i in range(n):
        seg = y[i * hop : (i + 1) * hop]
        if len(seg) < hop:
            break
        w = np.hanning(hop).astype(np.float32)
        m = np.abs(np.fft.rfft(seg * w))
        f = np.fft.rfftfreq(hop, 1 / SR)
        feat.append(
            (
                np.sqrt((seg ** 2).mean()),
                m[(f > 300) & (f < 3200)].sum(),
                m[(f < 150)].sum(),
            )
        )
    a = np.array(feat)
    t = np.arange(len(a)) * 0.5
    v = a[:, 1] / (a[:, 2] + 1e-9)
    v = v / np.percentile(v, 98)
    e = a[:, 0] / (a[:, 0].max() + 1e-9)
    print("t   rms   vocalRatio  flag")
    for i in range(0, min(len(t), 130), 2):
        flag = "VOCAL" if (v[i] > 0.35 and e[i] > 0.06) else ""
        print(f"{t[i]:5.1f} {e[i]:.2f}  {v[i]:.2f}  {flag}")
    print("--- first strong vocal ratio ---")
    cand = [i for i in range(len(t)) if v[i] > 0.5 and e[i] > 0.08]
    print([round(t[i], 1) for i in cand[:12]])

if __name__ == "__main__":
    main()
