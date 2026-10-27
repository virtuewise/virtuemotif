# check_timeline.py

## Purpose
Validates the generated timeline JSON against expected structure and checks for missing or overlapping scenes.

## Prerequisites
- Python 3.11+ with dependencies installed.
- A timeline JSON file (e.g., `timing/horizon.json`).

## Usage
```powershell
python tools/check_timeline.py --timeline timing/horizon.json
```

## Arguments
| Argument | Description |
|---|---|
| `--timeline` | Path to the timeline JSON to validate. |
| `--strict` | Exit with error on any warning (default `false`). |

## Output
 Prints a human‑readable report and returns exit code 0 if the file passes all checks.

## Notes
- The validator is used in CI to prevent malformed timelines from reaching the renderer.
- Use `--strict` in CI pipelines.
