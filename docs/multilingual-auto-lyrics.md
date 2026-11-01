# Multilingual auto-lyrics engine

VirtueMotif's first multilingual lyric engine is in `tools/lyrics_engine.py`.
It generates timestamped lyric segments and word timestamps using an optional
multilingual speech-recognition backend. As the decoder yields segments, the CLI
can emit JSON Lines events immediately; `--output` saves a complete versioned
JSON document instead.

## Install and run

Install ASR separately so the video renderer stays lightweight:

```bash
python -m pip install "faster-whisper>=1.1" sounddevice
python -m tools.lyrics_engine path/to/song.wav --model small
python -m tools.lyrics_engine path/to/song.wav --output lyrics/song.auto.json
python -m tools.lyrics_engine --live --model small --chunk-seconds 5
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

## Browser worker versus real transcription

The browser worker in `film/src/workers/whisper.worker.ts` currently performs **voice-activity detection only**. It reports vocal-energy intervals and deliberately returns `detectedLanguage: "und"`, zero language confidence, and `transcriptionAvailable: false`. It does not contain an ASR model; it must not invent placeholder lyric phrases or a language label.

For actual audio-to-text transcription, use the optional `faster-whisper` engine documented above. In `--live` mode it captures microphone windows, runs the ASR model per window, and streams timestamped JSONL lyric segments with the model's language probability. Latency depends on chunk size, hardware, and model. Five-second windows are a starting point, not a real-time guarantee.

Language identification is best-effort, not universal. Whisper-family models vary in support for Shona, isiNdebele, isiZulu, and code-switched singing. Short windows, instrumental bleed, backing vocals, and sung pronunciation can lower accuracy. Keep human review enabled and evaluate representative native-speaker audio before claiming production coverage.

## Export generated lyrics for Remotion

Generate a versioned ASR document, then convert it into the exact Song JSON shape used by the film compositions:

```bash
python -m tools.lyrics_engine path/to/song.wav --output timing/song.auto.json --model small
python -m tools.export_lyrics_song timing/song.auto.json --audio audio/song.m4a --output film/src/data/song.auto.json --title "My Song" --artist "Artist"
```

The `--audio` value is a path relative to `film/public/`. You can pass `--duration` when you know the full audio duration, including an instrumental outro; otherwise the exporter uses the final recognized lyric end time or the input document's duration. Import the generated JSON into `film/src/Root.tsx` and register a composition to render it. Choose a new output path when you want to preserve an existing song file; the converter writes to the exact path you specify.

The exported document preserves per-segment language and confidence, word timings when the ASR backend supplied them, and sets `reviewRequired: true` unless the input explicitly says otherwise. Generated lyric films show the detected language/confidence and a visible human-review warning. The exporter never invents word timings or translated subtitles.
