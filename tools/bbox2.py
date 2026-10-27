import numpy as np
from PIL import Image


def main() -> None:
    for p in ["out/h_5700.png", "out/r_1000.png"]:
        try:
            im = np.asarray(Image.open(p).convert("RGB")).astype(np.int16)
        except Exception:
            continue
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        m = (r > 205) & (g > 185) & (b > 140)
        ys, xs = np.nonzero(m)
        warm = ((r > 150) & (g > 90) & (g < 190) & (b < 110)).mean() * 100
        print(
            f"{p} mean=({r.mean():.0f},{g.mean():.0f},{b.mean():.0f}) "
            f"cream={m.mean()*100:.2f}% warmpix={warm:.1f}% dark={(im.mean(2)<25).mean()*100:.0f}%"
        )
        if len(xs):
            print(
                f"   type bbox x[{xs.min()},{xs.max()}] y[{ys.min()},{ys.max()}] "
                f"w={xs.max()-xs.min()} h={ys.max()-ys.min()}"
            )


if __name__ == "__main__":
    main()
