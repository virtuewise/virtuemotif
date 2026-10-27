import numpy as np
from PIL import Image


def main() -> None:
    for p in ["out/t_700.png", "out/t_1380.png"]:
        try:
            im = np.asarray(Image.open(p).convert("RGB")).astype(np.int16)
        except Exception:
            continue
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        m = (r > 205) & (g > 185) & (b > 140)
        ys, xs = np.nonzero(m)
        if len(xs) == 0:
            print(p, "NO CREAM")
            continue
        print(
            f"{p} cream={m.mean()*100:.2f}% bbox x[{xs.min()},{xs.max()}] y[{ys.min()},{ys.max()}] "
            f"cx={(xs.min()+xs.max())/2:.0f} cy={(ys.min()+ys.max())/2:.0f}"
        )


if __name__ == "__main__":
    main()
