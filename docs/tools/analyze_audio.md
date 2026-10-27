# analyze_audio.py

## Purpose
Performs spectral analysis on an audio file and produces visualizations (spectrogram, waveform) as PNGs.

## Prerequisites
- Python 3.11+, `requirements.txt` installed.
- `ffmpeg` available in `PATH`.

## Usage
```powershell
python tools/analyze_audio.py --audio path/to/audio.m4a --output-dir out/analysis
```

## Arguments
| Argument | Description |
|---|---|
| `--audio` | Input audio file (m4a, wav, etc.). |
| `--output-dir` | Directory where PNGs will be saved. |
| `--window` | FFT window size (default: 1024). |
| `--hop` | Hop length (default: 512). |

## Output
- `spectrogram.png` – magnitude spectrogram (log‑scale).
- `waveform.png` – waveform image.
- `segments.json` – optional JSON with detected segments (silence, speech).

## Notes
- Uses `librosa` for audio loading and `matplotlib` for plotting.
- For large files, consider down‑sampling to 22 kHz to speed up processing.
