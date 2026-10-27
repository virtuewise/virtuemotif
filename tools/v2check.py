import numpy as np
from PIL import Image


def main() -> None:
    for p in ["out/v2_20.png", "out/v2_45.png", "out/v2_57.png"]:
        try:
            im = np.asarray(Image.open(p).convert("RGB")).astype(np.int16)
        except Exception:
            continue
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        cream = ((r > 205) & (g > 185) & (b > 140)).mean() * 100
        ys, xs = np.nonzero((r > 205) & (g > 185) & (b > 140))
        bb = (
            f"bbox x[{xs.min()},{xs.max()}] y[{ys.min()},{ys.max()}]"
            if len(xs)
            else "no type"
        )
        print(f"{p} cream={cream:.2f}% dark={(im.mean(2)<20).mean()*100:.0f}% {bb}")


if __name__ == "__main__":
    main()
