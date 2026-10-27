"""Normalise a Remotion --sequence folder to element-00000.png ... so ffmpeg can read it."""
import re
import sys
from pathlib import Path

if __name__ == "__main__":
    d = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Dell\Documents\Default Project\out\frames_proof_horizon")
    files = list(d.glob("element-*.png"))
    by_idx = {}
    for f in files:
        m = re.fullmatch(r"element-(\\d+)\\.png", f.name)
        if not m:
            continue
        i = int(m.group(1))
        # prefer the zero-padded variant over the unpadded duplicate
        if i not in by_idx or len(f.name) > len(by_idx[i].name):
            by_idx[i] = f

    if not by_idx:
        print("no frames found")
        sys.exit(1)

    # drop duplicates that are not the chosen file
    chosen = set(by_idx.values())
    for f in files:
        if f not in chosen:
            f.unlink()

    for i, f in sorted(by_idx.items()):
        target = d / f"element-{i:05d}.png"
        if f.name != target.name:
            f.rename(target)

    final = sorted(d.glob("element-*.png"))
    idx = [int(re.fullmatch(r"element-(\\d+)\\.png", p.name).group(1)) for p in final]
    missing = [i for i in range(0, max(idx) + 1) if i not in set(idx)]
    print(f"frames={len(final)} min={min(idx)} max={max(idx)} missing={len(missing)}")
    if missing:
        print("first missing:", missing[:10])
