# Multilingual auto-lyrics engine

VirtueMotif's first multilingual lyric engine is in `tools/lyrics_engine.py`.
It generates timestamped lyric segments and word timestamps using an optional
multilingual speech-recognition backend. As the decoder yields segments, the CLI
can emit JSON Lines events immediately; `--output` saves a complete versioned
JSON document instead.

## Install and run

Install ASR separately so the video renderer stays lightweight:

```bash
python -m pip install "faster-whisper>=1.1"
python -m tools.lyrics_engine path/to/song.wav --model small
python -m tools.lyrics_engine path/to/song.wav --output lyrics/song.auto.json
```

Omit `--language` to let the backend detect the dominant audio language. The
engine attaches timestamps, word timestamps when available, language metadata,
and a confidence/method field.

## Language coverage and limits

Initial lexical hints include English, Shona, isiNdebele, isiZulu, isiXhosa,
Afrikaans, and Swahili, plus script-based hints for several non-Latin writing
systems. The hints are intentionally conservative. Nguni languages overlap,
short phrases and code-switching can be ambiguous, and the engine falls back to
the ASR language when text evidence is insufficient.

This is a foundation, **not a promise of correct detection for every language**.
Whisper-family model support for Shona, isiNdebele, isiZulu, and other
under-resourced languages varies. Reliable production quality needs a
representative audio test set, native-speaker review, and potentially
language-specific model adaptation.

The output sets `review_required: true`; machine transcriptions are not
canonical lyrics until reviewed. The current CLI streams decoded segments from
an audio file; live microphone capture and strict low-latency streaming are a
separate adapter and are not claimed by this implementation.
