# check_frames.py

## Purpose
Validates that the generated PNG frame sequence matches expected dimensions and detects missing or corrupted frames.

## Prerequisites
- Python 3.11+ with dependencies installed.
- Directory of frames (e.g., `out/frames_proof_v2`).

## Usage
```powershell
python tools/check_frames.py --input out/frames_proof_v2 --expected-width 1920 --expected-height 1080
```

## Arguments
| Argument | Description |
|---|---|
| `--input` | Path to the directory containing PNG frames. |
| `--expected-width` | Expected image width in pixels. |
| `--expected-height` | Expected image height in pixels. |
| `--tolerance` | Allowed pixel variation (default 0). |

## Output
Prints a summary: total frames, mismatched dimensions, missing indices, and any IO errors.

## Notes
- Returns exit code 0 on success, 1 on any failure, enabling CI usage.
- Can be combined with `python -m pytest` for automated testing.
