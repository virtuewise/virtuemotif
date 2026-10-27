# normalize_frames.py

## Purpose
Normalizes the brightness/contrast of a sequence of PNG frames to a uniform level before rendering.

## Prerequisites
- Python 3.11+ with `Pillow` installed.
- Directory of frames (e.g., `out/frames_proof_v2`).

## Usage
```powershell
python tools/normalize_frames.py --input out/frames_proof_v2 --output out/frames_normalized
```

## Arguments
| Argument | Description |
|---|---|
| `--input` | Path to the source frame directory. |
| `--output` | Destination directory for normalized frames. |
| `--method` | Normalization method (`histogram`, `minmax`; default `histogram`). |
| `--clip` | Optional clip value to avoid extreme outliers. |

## Output
Copies of the original PNGs with adjusted pixel values saved in the output folder.

## Notes
- Non‑destructive: original frames are untouched.
- Returns exit code 0 on success; useful in CI pipelines.
