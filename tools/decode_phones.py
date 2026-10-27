"""Greedy CTC phone decode of one or more windows with MMS_FA.

MMS_FA emits 28 phone log-probs plus a star (silence) log-prob at index 28.
One model load handles several ranges: `--ranges "44-54,86-96"`.
"""

import argparse
import pathlib
import sys

import torch

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from align_lyrics import BUNDLE, FRAME, SR, emissions, read_wav  # noqa: E402

STAR_IDX = 28


def decode_window(em: torch.Tensor, labels, a: float, floor: float):
    star = em[:, STAR_IDX]
    ids = em[:, :STAR_IDX].argmax(-1).tolist()
    seq = []
    prev = -1
    for k, i in enumerate(ids):
        if i != prev:
            seq.append((a + k * FRAME, i, float(star[k]) > floor))
        prev = i
    out = []
    last_t = None
    for t, i, quiet in seq:
        if quiet:
            if last_t is None or t - last_t > 0.4:
                out.append(f" {t:.1f}|_")
                last_t = t
            continue
        if last_t is None or t - last_t >= 0.5:
            out.append(f" {t:.1f}|")
            last_t = t
        out.append(labels[i])
    return " ".join(out), len(seq)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("ranges", help='e.g. "137-160,158-174" or a single "137 160"')
    ap.add_argument("--floor", type=float, default=1e9, help="star logprob above this = silence")
    args = ap.parse_args()

    d = BUNDLE.get_dict()
    labels = [f"<{i}>" for i in range(29)]
    for ch, i in d.items():
        labels[i] = ch

    ranges = []
    for part in args.ranges.split(","):
        part = part.strip().replace(" ", "-")
        a, b = part.split("-")
        ranges.append((float(a), float(b)))

    wav = read_wav(pathlib.Path(args.wav))
    model = BUNDLE.get_model(with_star=True).eval()
    for a, b in ranges:
        em = emissions(model, wav[int(a * SR) : int(b * SR)])
        text, n = decode_window(em, labels, a, args.floor)
        print(f"\n== {a:.1f}-{b:.1f}  ({n} events)\n{text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
