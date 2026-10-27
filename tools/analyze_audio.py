"""Decode the songs, measure structure, and draw an analysis sheet to look at."""
import json
import subprocess
import numpy as np
from PIL import Image, ImageDraw

ROOT = r"C:\Users\Dell\Documents\Default Project"
SR = 22050


def decode(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def analyse(y):
    hop, win = 256, 1024
    n = 1 + (len(y) - win) // hop
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    frames = y[idx] * np.hanning(win).astype(np.float32)
    mag = np.abs(np.fft.rfft(frames, axis=1)).astype(np.float32)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    rms = np.sqrt((frames ** 2).mean(axis=1))
    vocal = mag[:, (freqs > 300) & (freqs < 3600)].sum(axis=1)
    low = mag[:, freqs <= 200].sum(axis=1)
    voice = vocal / (low + 1e-6)
    t = hop * np.arange(n) / SR
    return t, mag, freqs, rms, voice


def phrases(t, rms, voice, hop=256):
    e = rms / (rms.max() + 1e-9)
    v = voice / (np.percentile(voice, 99) + 1e-9)
    act = (e > 0.10) & (v > 0.20)
    # close small gaps
    gap = int(0.30 * SR / hop)
    act = np.convolve(act.astype(np.float32), np.ones(gap) / gap, "same") > 0.5
    segs, i = [], 0
    while i < len(act):
        if act[i]:
            j = i
            while j < len(act) and act[j]:
                j += 1
            if t[j - 1] - t[i] > 0.45:
                segs.append([round(float(t[i]), 2), round(float(t[j - 1]), 2)])
            i = j
        else:
            i += 1
    # merge segments closer than 0.45s
    merged = []
    for s in segs:
        if merged and s[0] - merged[-1][1] < 0.45:
            merged[-1][1] = s[1]
        else:
            merged.append(s[:])
    return merged


def sheet(t, mag, freqs, rms, voice, segs, out):
    W, H = 2200, 760
    img = Image.new("RGB", (W, H), (10, 12, 20))
    d = ImageDraw.Draw(img)
    # ---- spectrogram ----
    spec_h = 430
    band = (freqs >= 60) & (freqs <= 8000)
    m = mag[:, band]
    m = 20 * np.log10(m + 1e-6)
    m = np.clip((m - m.max() + 78) / 78, 0, 1)
    m = np.flipud(m.T)
    small = Image.fromarray((m * 255).astype(np.uint8), "L").resize((W, spec_h), Image.BILINEAR)
    a = np.asarray(small, dtype=np.float32) / 255.0
    # teal -> ochre ramp
    r = (a ** 0.7 * 232 + (1 - a) * 8).astype(np.uint8)
    g = (a ** 0.9 * 163 + (1 - a) * 12).astype(np.uint8)
    b = (a ** 1.4 * 61 + (1 - a) * 28).astype(np.uint8)
    img.paste(Image.fromarray(np.dstack([r, g, b])), (0, 0))
    # ---- rms ----
    y0, y1 = spec_h + 30, spec_h + 180
    d.line([(0, y1), (W, y1)], fill=(50, 60, 70))
    xs = (t / t[-1] * W).astype(int)
    e = rms / (rms.max() + 1e-9)
    pts = [(int(x), int(y1 - e[i] * (y1 - y0))) for i, x in enumerate(xs)]
    d.line(pts, fill=(246, 231, 200), width=2)
    # ---- voice ratio ----
    y2, y3 = spec_h + 200, spec_h + 300
    v = voice / (np.percentile(voice, 99) + 1e-9)
    pts = [(int(x), int(y3 - min(v[i], 1) * (y3 - y2))) for i, x in enumerate(xs)]
    d.line(pts, fill=(232, 163, 61), width=2)
    # ---- phrase markers ----
    for s, en in segs:
        x0, x1 = int(s / t[-1] * W), int(en / t[-1] * W)
        d.rectangle([x0, spec_h + 5, max(x1, x0 + 2), spec_h + 18], fill=(224, 102, 43))
        d.text((x0 + 3, spec_h + 305), f"{s:.0f}", fill=(200, 200, 210))
    # second ruler
    for sec in range(0, int(t[-1]) + 1, 10):
        x = int(sec / t[-1] * W)
        d.line([(x, H - 26), (x, H - 16)], fill=(120, 130, 140))
        d.text((x + 2, H - 14), f"{sec}", fill=(190, 195, 205))
    img.save(out)


if __name__ == "__main__":
    for name in ("horizon", "rise"):
        y = decode(f"{ROOT}/film/public/audio/{name}.m4a")
        t, mag, freqs, rms, voice = analyse(y)
        segs = phrases(t, rms, voice)
        sheet(t, mag, freqs, rms, voice, segs, f"{ROOT}/out/analysis_{name}.png")
        with open(f"{ROOT}/out/phrases_{name}.json", "w") as f:
            json.dump({"duration": round(len(y) / SR, 2), "phrases": segs}, f, indent=1)
        print(name, "dur", round(len(y) / SR, 2), "phrases", len(segs))
