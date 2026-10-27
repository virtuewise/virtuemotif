# build_timeline.py

## Purpose
Combines lyric timing JSON with audio analysis results to produce a final timeline JSON consumed by the Remotion video renderer.

## Prerequisites
- Python 3.11+ with repo dependencies installed.
- A timing JSON (`timing/horizon.json` or `timing/rise.json`).
- Optional lyric JSON for metadata.

## Usage
```powershell
python tools/build_timeline.py --timing timing/horizon.json --output timing/horizon_final.json
```

## Arguments
| Argument | Description |
|---|---|
| `--timing` | Input timing JSON (raw or partially aligned). |
| `--lyrics` | Optional lyric JSON to enrich the output with section titles. |
| `--output` | Destination file for the merged timeline. |
| `--fps` | Frames per second for the video (default 30). |

## Output
A JSON file conforming to the schema used by `tools/make_tapsync.py` and the Remotion renderer. It contains an array of scenes, each with start/end times, lyric lines, and optional visual effects.

## Notes
- The script interpolates missing timestamps linearly between known anchors.
- Use `--fps` to adjust the granularity of frame‑based timing.
