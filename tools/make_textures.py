"""Generate film-grain, paper-fibre and dust textures for the lyrical film."""

import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def value_noise(size, cells, rng):
    g = rng.random((cells + 1, cells + 1)).astype(np.float32)
    img = Image.fromarray((g * 255).astype(np.uint8), "L").resize(
        (size, size), Image.BICUBIC
    )
    return np.asarray(img, dtype=np.float32) / 255.0


def fbm(size, octaves, rng, base=4):
    out = np.zeros((size, size), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        out += value_noise(size, base * (2**o), rng) * amp
        tot += amp
        amp *= 0.5
    return out / tot


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "film" / "public" / "tex"
    os.makedirs(out_dir, exist_ok=True)
    rng = np.random.default_rng(7)

    # ---------- film grain (removable, tiled, neutral) ----------
    s = 1024
    grain = rng.normal(0.5, 0.16, (s, s)).astype(np.float32)
    grain = np.clip(grain, 0, 1)
    clump = fbm(s, 5, rng, 8)
    grain = np.clip(grain * 0.72 + 0.28 * (clump * 0.6 + 0.4 * grain), 0, 1)
    Image.fromarray((grain * 255).astype(np.uint8), "L").save(out_dir / "grain.png")

    # ---------- paper / canvas fibre ----------
    p = 1024
    fibre = fbm(p, 6, rng, 6)
    streak = value_noise(p, 64, rng).mean(axis=0)  # vertical drag
    streak = np.tile(streak, (p, 1)).astype(np.float32)
    streak = (
        np.asarray(
            Image.fromarray((streak * 255).astype(np.uint8)).filter(
                ImageFilter.GaussianBlur(1.2)
            ),
            dtype=np.float32,
        )
        / 255.0
    )
    paper = 0.55 * fibre + 0.25 * streak + 0.20 * rng.normal(0.5, 0.05, (p, p))
    paper = np.clip((paper - paper.min()) / (paper.max() - paper.min()), 0, 1)
    paper = 0.5 + (paper - 0.5) * 0.55  # keep it subtle
    Image.fromarray((paper * 255).astype(np.uint8), "L").save(out_dir / "paper.png")

    # ---------- fibrous edge / torn paper alpha ----------
    e = 512
    edge = fbm(e, 5, rng, 10)
    edge = np.clip((edge - 0.35) * 2.2, 0, 1)
    Image.fromarray((edge * 255).astype(np.uint8), "L").save(out_dir / "torn.png")

    print("textures written to", out_dir)
    for n in ("grain.png", "paper.png", "torn.png"):
        im = Image.open(out_dir / n)
        print(n, im.size, im.mode)


if __name__ == "__main__":
    main()
