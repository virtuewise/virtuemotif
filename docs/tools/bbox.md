# bbox.py

## Purpose
Provides utilities for generating bounding‑box annotations on frame PNGs.

## Prerequisites
- Python 3.11+, dependencies from `requirements.txt`.

## Usage
```powershell
python tools/bbox.py --input out/frames_proof_v2 --output out/bboxes.json
```

## Arguments
| Argument | Description |
|---|---|
| `--input` | Directory containing PNG frames. |
| `--output` | Destination JSON file with box coordinates. |
| `--threshold` | Confidence threshold for box detection (default: 0.5). |

## Output
A JSON array of objects `{ "frame": "element-01910.png", "boxes": [{"x":…, "y":…, "w":…, "h":…}] }`.
