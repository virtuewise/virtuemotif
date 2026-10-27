"""Transcribe a song with faster-whisper (word timestamps) for structure discovery.

We already have the *intended* lyric sheet; this pass answers a different
question: what is actually audible, where, and in what order. That tells us
whether the generated track repeats / skips / improvises sections before we
snap the sheet to the audio.
"""

import argparse
import json
import pathlib
import sys
import time

from faster_whisper import WhisperModel

ROOT = pathlib.Path(r"C:\Users\Dell\Documents\Default Project")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("song")
    ap.add_argument("--model", default="small")
    ap.add_argument("--language", default=None)
    args = ap.parse_args()

    wav = ROOT / "timing" / "wav" / f"{args.song}.wav"
    t0 = time.time()
    model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=4)
    segments, info = model.transcribe(
        str(wav),
        language=args.language,
        word_timestamps=True,
        vad_filter=True,
        beam_size=5,
        condition_on_previous_text=False,
    )
    print(f"[asr] {args.model} lang={info.language} p={info.language_probability:.2f}", flush=True)

    rows = []
    for s in segments:
        words = [{"w": w.word.strip(), "from": round(w.start, 2), "to": round(w.end, 2)} for w in (s.words or [])]
        rows.append({"from": round(s.start, 2), "to": round(s.end, 2), "text": s.text.strip(), "words": words})
        print(f"  {s.start:7.2f} {s.end:7.2f}  {s.text.strip()}", flush=True)

    out = {
        "id": args.song,
        "model": args.model,
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "segments": rows,
    }
    p = ROOT / "timing" / f"{args.song}.asr.json"
    p.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[asr] {len(rows)} segments in {time.time()-t0:.0f}s -> {p}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
