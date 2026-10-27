"""Word-level ASR dump (faster-whisper) used as an independent timing witness.

--from/--to really slice the audio (so short-region re-checks are cheap) and
reported times stay in whole-song coordinates.
"""

import argparse
import json
import pathlib
import sys
import tempfile
import time
import wave

from faster_whisper import WhisperModel

ROOT = pathlib.Path(r"C:\Users\Dell\Documents\Default Project")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def slice_wav(src: pathlib.Path, t0: float, t1: float) -> tuple[pathlib.Path, float]:
    """Return (temp wav path, start offset in seconds)."""
    with wave.open(str(src), "rb") as f:
        sr = f.getframerate()
        ch = f.getnchannels()
        sw = f.getsampwidth()
        start = max(0, int(t0 * sr))
        f.setpos(min(start, f.getnframes()))
        n = int((t1 - t0) * sr) if t1 > t0 else f.getnframes() - start
        data = f.readframes(n)
    tmp = pathlib.Path(tempfile.gettempdir()) / f"asr_{src.stem}_{int(t0)}_{int(t1)}.wav"
    with wave.open(str(tmp), "wb") as g:
        g.setnchannels(ch)
        g.setsampwidth(sw)
        g.setframerate(sr)
        g.writeframes(data)
    return tmp, t0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("song")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--language", default=None)
    ap.add_argument("--from", dest="t0", type=float, default=0.0)
    ap.add_argument("--to", dest="t1", type=float, default=0.0)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    wav = ROOT / "timing" / "wav" / f"{args.song}.wav"
    offset = 0.0
    if args.t0 or args.t1:
        wav, offset = slice_wav(wav, args.t0, args.t1)
        print(f"[asr] slice {args.t0:.2f}-{args.t1:.2f} -> {wav.name}", flush=True)

    t0 = time.time()
    model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=4)
    segments, info = model.transcribe(
        str(wav),
        language=args.language,
        word_timestamps=True,
        vad_filter=False,
        beam_size=5,
        condition_on_previous_text=False,
    )
    rows = []
    for s in segments:
        words = [
            {"w": w.word.strip(), "from": round(w.start + offset, 2), "to": round(w.end + offset, 2)}
            for w in (s.words or [])
        ]
        rows.append(
            {
                "from": round(s.start + offset, 2),
                "to": round(s.end + offset, 2),
                "text": s.text.strip(),
                "words": words,
            }
        )
        print(f"{s.start + offset:7.2f} {s.end + offset:7.2f}  {s.text.strip()[:90]}", flush=True)
        print("        " + " ".join(f"{w['w']}@{w['from']:.1f}" for w in words), flush=True)

    out = {
        "id": args.song,
        "model": args.model,
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "window": [args.t0, args.t1],
        "segments": rows,
    }
    name = f"{args.song}.asr-{args.model}" + (f".{args.tag}" if args.tag else "") + ".json"
    p = ROOT / "timing" / name
    p.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[asr] {args.model} {len(rows)} segs in {time.time()-t0:.0f}s -> {p.name}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
