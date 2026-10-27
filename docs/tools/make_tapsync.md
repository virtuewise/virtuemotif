# make_tapsync.py

## Purpose
Regenerates the tap‑sync HTML pages from lyric JSON files, allowing manual timing adjustments.

## Prerequisites
- Python 3.11+ with repository dependencies installed.
- Lyric JSON files in `lyrics/`.

## Usage
```powershell
python tools/make_tapsync.py --lyrics-dir lyrics --out-dir out/frames_syntaxcheck
```

## Arguments
| Argument | Description |
|---|---|
| `--lyrics-dir` | Directory containing lyric JSON files. |
| `--out-dir` | Destination directory for generated HTML pages. |
| `--template` | Optional path to a custom HTML template. |

## Output
HTML files (`element-0.html`, `element-1.html`, …) that display the waveform and allow the user to press **SPACE** to mark line start times.

## Notes
- The generated pages are consumed by `check_frames.py` for visual verification.
- After editing, export the timing JSON with the **Export** button; the file will be saved alongside the HTML page.
