# bbox2.py

## Purpose
Extended bounding‑box utilities that support multiple detection models and batch processing.

## Prerequisites
- Python 3.11+, `requirements.txt` installed.

## Usage
```powershell
python tools/bbox2.py --input out/frames_proof_v2 --model yolov5 --output out/bboxes2.json
```

## Arguments
| Argument | Description |
|---|---|
| `--input` | Directory with PNG frames. |
| `--model` | Detection model identifier (e.g., `yolov5`, `fasterrcnn`). |
| `--output` | Destination JSON file. |
| `--conf` | Confidence threshold (default 0.5). |

## Output
JSON with per‑frame box coordinates similar to `bbox.py` but with model‑specific fields.
