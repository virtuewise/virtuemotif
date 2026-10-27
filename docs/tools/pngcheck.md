# pngcheck.py

## Purpose
Validates PNG files for corruption and ensures they meet required dimensions and bit depth.

## Prerequisites
- Python 3.11+ with `Pillow` installed.

## Usage
```powershell
python tools/pngcheck.py --input out/frames_proof_v2 --max-size 5MB
```

## Arguments
| Argument | Description |
|---|---|
| `--input` | Directory containing PNG files to check. |
| `--max-size` | Optional maximum file size (e.g., `5MB`). |
| `--strict` | Fail on any warning (exit code 1). |

## Output
A summary report printed to stdout; exit code 0 on success, 1 on failures.

## Notes
- Useful in CI to catch broken frame exports before rendering.
