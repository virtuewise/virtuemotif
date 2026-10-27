# make_youtube.py

## Purpose
Generates YouTube description, tags, and chapter files from lyric and timing data, ready for upload.

## Prerequisites
- Python 3.11+ and project dependencies installed.
- Existing timing JSON (e.g., `timing/horizon.json`).
- Corresponding lyric JSON in `lyrics/`.

## Usage
```powershell
python tools/make_youtube.py --timing timing/horizon.json --lyrics lyrics/horizon.json --out-dir out/youtube
```

## Arguments
| Argument | Description |
|---|---|
| `--timing` | Path to the timing JSON file. |
| `--lyrics` | Path to the lyric JSON file. |
| `--out-dir` | Directory where `*-description.txt` and `*-tags.txt` will be written. |
| `--title` | Optional custom video title (default derived from song name). |

## Output Files
- `<song>-description.txt` – full description including lyrics, translations, and chapter timestamps.
- `<song>-tags.txt` – a newline‑separated list of tags for YouTube.

## Notes
- The script extracts chapter timestamps from the timing JSON and formats them as `mm:ss` entries.
- Tags are generated from song metadata, genre keywords, and common YouTube SEO terms.
- You can edit the generated description before uploading.
