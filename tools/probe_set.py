"""Probe several (window, candidate text) pairs with one MMS_FA model load.

spec JSON: [{"tag": "...", "start": 1.0, "end": 2.0, "text": "line one | line two"}, ...]
"""

import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from align_lyrics import BUNDLE, FRAME, SR, STAR, emissions, read_wav, word_ids  # noqa: E402


def probe(model, wav, start: float, end: float, text: str):
    chunk = wav[int(start * SR) : int(end * SR)]
    em = emissions(model, chunk)
    groups = [{"kind": "star", "ids": [STAR]} for _ in range(3)]
    for line in text.split("|"):
        for w in line.split():
            ids = word_ids([w])
            if ids:
                groups.append({"kind": "word", "text": w, "ids": ids[0]})
    groups += [{"kind": "star", "ids": [STAR]} for _ in range(3)]
    spans = BUNDLE.get_aligner()(em, [g["ids"] for g in groups])
    words = []
    for g, sp in zip(groups, spans):
        if g["kind"] != "word":
            continue
        f, t = sp[0].start * FRAME, sp[-1].end * FRAME
        words.append((f, t, float(np.mean([s.score for s in sp])), g["text"]))
    return words


def main() -> int:
    ap = __import__("argparse").ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("spec")
    args = ap.parse_args()

    wav = read_wav(pathlib.Path(args.wav))
    spec = json.loads(pathlib.Path(args.spec).read_text(encoding="utf-8"))
    model = BUNDLE.get_model(with_star=True).eval()

    for item in spec:
        a, b = float(item["start"]), float(item["end"])
        words = probe(model, wav, a, b, item["text"])
        if not words:
            print(f"\n[{item.get('tag','')}] {a:.1f}-{b:.1f}  no words")
            continue
        first, last = words[0][0], words[-1][1]
        span = last - first
        mean = float(np.mean([w[2] for w in words]))
        print(
            f"\n[{item.get('tag','')}] {b-a:5.1f}s window  {len(words):2d} words  "
            f"span {span:5.1f}s ({span/(b-a)*100:3.0f}%)  first {first+a:7.2f}  last {last+a:7.2f}  "
            f"mean {mean:.3f}"
        )
        for f, t, s, w in words:
            flag = " " if s >= 0.25 else "!"
            print(f"  {flag} {f+a:7.2f} {t+a:7.2f}  {s:.3f}  {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
