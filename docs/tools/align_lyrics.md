# align_lyrics.py

## Purpose
Align lyric timestamps with the audio waveform. Produces JSON files that map each lyric line to a precise time offset.

## Prerequisites
- Python 3.11+ with dependencies installed (`requirements.txt`).
- An audio file (e.g., `timing/horizon.wav`).
- Corresponding lyric JSON in `lyrics/`.

## Usage
```powershell
python tools/align_lyrics.py --audio path/to/audio.m4a --lyrics path/to/lyrics.json --output timing/horizon_aligned.json
```

## Arguments
| Argument | Description |
|---|---|
| `--audio` | Path to the source audio file.
| `--lyrics` | Path to the lyric JSON file.
| `--output` | Destination for the aligned timing JSON.
| `--threshold` | Optional confidence threshold (default: 0.6).

## Example
```powershell
python tools/align_lyrics.py --audio timing/horizon.wav --lyrics lyrics/horizon.json --output timing/horizon_aligned.json
```

## Notes
- The script uses a pre‑trained ASR model; ensure `torch` with CUDA is available for best performance.
- Output JSON follows the schema defined in `docs/data_flow.md`.
