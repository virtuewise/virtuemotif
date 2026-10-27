"""Probe a time window against candidate lyric text with MMS_FA.

Prints mean CTC score and how much of the window the words actually occupy.
A real match covers most of the window; forced nonsense collapses into a few
frames with near-zero scores.
"""

import argparse
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from align_lyrics import BUNDLE, FRAME, SR, STAR, emissions, read_wav, word_ids  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("start", type=float)
    ap.add_argument("end", type=float)
    ap.add_argument("text", help='lines separated by "|"')
    args = ap.parse_args()

    wav = read_wav(pathlib.Path(args.wav))
    a, b = args.start, args.end
    chunk = wav[int(a * SR) : int(b * SR)]
    model = BUNDLE.get_model(with_star=True).eval()
    em = emissions(model, chunk)

    groups = [{"kind": "star", "ids": [STAR]} for _ in range(3)]
    for line in args.text.split("|"):
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

    if not words:
        print("no words")
        return 1
    first, last = words[0][0], words[-1][1]
    span = last - first
    mean = float(np.mean([w[2] for w in words]))
    print(f"window {b-a:6.1f}s   words {len(words):3d}   span {span:6.1f}s ({span/(b-a)*100:3.0f}%)")
    print(f"first {first+a:7.2f}  last {last+a:7.2f}   mean score {mean:.3f}")
    for f, t, s, w in words:
        print(f"  {f+a:7.2f} {t+a:7.2f}  {s:.3f}  {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
