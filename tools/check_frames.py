import glob
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> None:
    for p in sorted(glob.glob("out/p_*.png")):
        try:
            im = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
        except Exception:
            continue
        h, w, _ = im.shape
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        cream = ((r > 215) & (g > 195) & (b > 150)).mean() * 100
        bright = (im.mean(2) > 180).mean() * 100
        dark = (im.mean(2) < 25).mean() * 100
        # type band = central 40% vertically
        band = im[int(h * 0.30) : int(h * 0.72)]
        rb, gb, bb = band[..., 0], band[..., 1], band[..., 2]
        bandcream = ((rb > 215) & (gb > 195) & (bb > 150)).mean() * 100
        # warm sun region
        sun = im[int(h * 0.45) : int(h * 0.75), int(w * 0.30) : int(w * 0.70)]
        fname = Path(p).name
        print(
            f"{fname:12s} meanRGB=({r.mean():.0f},{g.mean():.0f},{b.mean():.0f}) "
            f"cream%={cream:.2f} bandcream%={bandcream:.2f} bright%={bright:.2f} "
            f"dark%={dark:.1f} sunMean={sun.mean():.0f}"
        )


if __name__ == "__main__":
    main()
