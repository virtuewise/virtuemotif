import numpy as np
from PIL import Image


def main() -> None:
    for p in ["out/v_21.png", "out/v_47.png"]:
        try:
            im = np.asarray(Image.open(p).convert("RGB")).astype(np.int16)
        except Exception:
            continue
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        cream = ((r > 205) & (g > 185) & (b > 140)).mean() * 100
        print(
            p,
            f"mean={im.mean():.0f} cream={cream:.2f}% dark={(im.mean(2)<20).mean()*100:.0f}%",
        )


if __name__ == "__main__":
    main()
