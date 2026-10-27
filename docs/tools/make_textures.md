# make_textures.py

## Purpose
Regenerates grain, paper, and torn‑edge texture PNGs used by the Remotion renderer.

## Prerequisites
- Python 3.11+ with dependencies installed.
- `Pillow` (already in `requirements.txt`).

## Usage
```powershell
python tools/make_textures.py --output-dir out/textures
```

## Arguments
| Argument | Description |
|---|---|
| `--output-dir` | Directory where the generated textures will be saved. |
| `--size` | Base texture size (default `1920x1080`). |
| `--seed` | Random seed for reproducibility. |

## Output
A set of PNG files:
- `grain.png`
- `paper.png`
- `torn_edge.png`

## Notes
- Textures are deterministic when `--seed` is supplied, useful for CI reproducibility.
