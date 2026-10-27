# asr_words.py

## Purpose
Extracts word‑level timestamps from an audio file using an Automatic Speech Recognition (ASR) model and outputs a JSON mapping words to time offsets.

## Prerequisites
- Python 3.11+ with `torch` and `transformers` installed.
- A compatible ASR model checkpoint (default provided in the repo).

## Usage
```powershell
python tools/asr_words.py --audio path/to/audio.m4a --model davidsandberg/whisper-large-v2 --output timing/asr_words.json
```

## Arguments
| Argument | Description |
|---|---|
| `--audio` | Input audio file. |
| `--model` | Hugging Face model identifier (default: `openai/whisper-base`). |
| `--output` | Destination JSON file. |
| `--language` | Optional language code (e.g., `en`). |

## Output
A JSON array where each entry contains `{ "word": "...", "start": <sec>, "end": <sec> }`.

## Notes
- The script runs on CPU by default; set `CUDA_VISIBLE_DEVICES` to enable GPU.
- Post‑process the output with `tools/align_lyrics.py` to merge with existing lyric timing.
