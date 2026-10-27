# decode_phones.py

## Purpose
Converts phoneme label files into a format suitable for the video renderer, optionally applying a phone‑to‑viseme mapping.

## Prerequisites
- Python 3.11+ with repository dependencies installed.

## Usage
```powershell
python tools/decode_phones.py --input path/to/phones.txt --output path/to/visemes.json
```

## Arguments
| Argument | Description |
|---|---|
| `--input` | Path to a plain‑text phone label file (one phone per line). |
| `--output` | Destination JSON containing the mapped visemes. |
| `--mapping` | Optional JSON file defining custom phone‑to‑viseme mapping. |

## Output
A JSON array of objects `{ "phone": "...", "viseme": "...", "start": <sec>, "end": <sec> }`.

## Notes
- If no mapping is supplied, the script uses an internal default mapping suitable for the Remotion renderer.
- Useful as a preprocessing step before `make_tapsync.py`.
