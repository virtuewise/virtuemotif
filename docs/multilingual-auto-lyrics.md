# Multilingual auto-lyrics engine

VirtueMotif's multilingual lyric engine is in `tools/lyrics_engine.py`.
It generates timestamped lyric segments and word timestamps using an optional
multilingual speech-recognition backend. As the decoder yields segments, the CLI
emits JSON Lines events; `--output` saves a complete versioned JSON document
with a confidence-aware language timeline.

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
and a confidence/method field. Saved JSON records whether language detection was automatic
or a language was explicitly forced with `--language`, and includes `language_summary`
(segment counts by detected language, including `und` for unknown segments). The summary
is diagnostic rather than a claim that every word in a segment uses that language.

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

## Confidence-aware language timeline

When all segments have timestamps, `build_lyrics_document` includes a
`language_timeline` object in the saved JSON. It preserves segment times,
language labels, confidence signals, methods and text; summarizes label counts;
and exposes candidate transitions between adjacent language labels. Unknown or
mixed labels, short segments, missing confidence, and low confidence are flagged
for human review. Existing segment data is retained rather than smoothed or
rewritten.

In live mode, the JSONL stream also emits a `language_transition_candidate`
event whenever adjacent segments change language. Consumers should treat this
as a candidate boundary, not definitive proof of a code-switch. Confidence values
are model/heuristic signals, **not calibrated probabilities** unless separately
validated. Incomplete legacy segment records remain supported but do not receive
a fabricated timeline.

The output sets `review_required: true`; machine transcriptions are not
canonical lyrics until reviewed. The CLI streams decoded segments from audio
files or microphone windows; latency depends on chunk size, hardware, and model,
so the default five-second window is not a real-time guarantee.

## Browser worker versus real transcription

The browser worker in `film/src/workers/whisper.worker.ts` currently performs **voice-activity detection only**. It reports vocal-energy intervals and deliberately returns `detectedLanguage: "und"`, zero language confidence, and `transcriptionAvailable: false`. It does not contain an ASR model; it must not invent placeholder lyric phrases or a language label.

For actual audio-to-text transcription, use the optional `faster-whisper` engine documented above. In `--live` mode it captures microphone windows, runs the ASR model per window, and streams timestamped JSONL lyric segments with the model's language probability. Latency depends on chunk size, hardware, and model. Five-second windows are a starting point, not a real-time guarantee.

Language identification is best-effort, not universal. Whisper-family models vary in support for Shona, isiNdebele, isiZulu, and code-switched singing. Short windows, instrumental bleed, backing vocals, and sung pronunciation can lower accuracy. Keep human review enabled and evaluate representative native-speaker audio before claiming production coverage.

## Evaluate multilingual transcription quality

Use a manually reviewed schema-v1 reference JSON and the generated ASR JSON to
measure transcript word error rate (WER) and timestamp-overlap language accuracy:

```bash
python -m tools.lyrics_engine "path/to/rights-cleared-song.wav" \
  --output timing/song.auto.json --model small
python -m tools.evaluate_lyrics lyrics/reference.reviewed.json timing/song.auto.json \
  --output timing/song.evaluation.json
```

The report includes overall WER, language accuracy, per-language counts and
accuracy, and how many reference segments were excluded because their language
was marked `und`. Language scoring matches each hypothesis segment to the
reference segment with the greatest positive time overlap; WER compares the
concatenated normalized transcripts. Keep reference lyrics and timing reviewed
by fluent speakers, particularly for Shona, isiNdebele, isiZulu, code-switching,
and sung pronunciation. The repository does not bundle a rights-cleared
multilingual benchmark, and these metrics should not be reported as universal
language-coverage guarantees.

## One-command auto-lyrics video

After installing the optional ASR dependencies and the Node dependencies in
`film/`, the orchestration command runs transcription, converts the result to
Remotion Song JSON, writes the props wrapper, and renders the video:

```bash
python -m pip install "faster-whisper>=1.1"
cd film && npm ci && cd ..
python -m tools.make_auto_lyrics_video "path/to/song.m4a" \
  --output out/song.mp4 --title "My Song" --artist "Artist"
```

Use `--format landscape` (the default), `--format portrait`,
`--format square`, or `--format 4k` to choose the output size. These map to
1920×1080, 1080×1920, 1024×1024, and 3840×2160 at 30 fps respectively. Choose
a visual treatment with `--typography-preset display` (default),
`--typography-preset editorial`, `--typography-preset neon`, or
`--typography-preset whisper`. For example, render a vertical neon treatment:

```bash
python -m tools.make_auto_lyrics_video "path/to/song.m4a" \
  --format portrait --typography-preset neon --output out/song-portrait-neon.mp4
```

The presets change the font treatment, color, spacing, highlight, and translation
styling without requiring edits to the Remotion components. They are visual
treatments, not translations or claims about the language of the lyrics.

Omit `--language` to let the multilingual ASR model detect the language, or
supply a language code to force one. The command copies the source audio into
`film/public/audio/auto-lyrics/`, writes reviewable intermediate JSON under
`timing/` and `film/src/data/`, and selects the matching generic Remotion
composition. It probes the full media duration with `ffprobe` by default, so
instrumental intros and outros are retained; pass `--duration` to override the
probe when needed. It refuses to replace an existing output video unless
`--force` is supplied.

After rendering, the command probes the MP4 again and fails if the output is
missing or empty, lacks either an audio or video stream, does not match the
selected format's dimensions or 30 fps rate, differs from the source duration
by more than the configured tolerance, or has audio/video stream durations that
drift beyond the sync tolerance. This metadata gate catches structural output
failures; it does not replace listening to the result or reviewing lyric timing
and visuals.

Use only audio you have permission to process and redistribute; review
machine-generated lyrics before publishing.

## Export generated lyrics for Remotion

Generate a versioned ASR document, then convert it into the exact Song JSON shape used by the film compositions:

```bash
python -m tools.lyrics_engine path/to/song.wav --output timing/song.auto.json --model small
python -m tools.export_lyrics_song timing/song.auto.json --audio audio/song.m4a --output film/src/data/song.auto.json --props-output film/src/data/song.auto.props.json --title "My Song" --artist "Artist" --typography-preset neon
```

The `--audio` value is a path relative to `film/public/`. You can pass `--duration` when you know the full audio duration, including an instrumental outro; otherwise the exporter uses the final recognized lyric end time or the input document's duration. The optional `--typography-preset` applies the chosen preset to every lyric line; allowed values are `display`, `editorial`, `neon`, and `whisper`. Import the generated JSON into `film/src/Root.tsx` and register a composition to render it. Choose a new output path when you want to preserve an existing song file; the converter writes to the exact path you specify.

The exported document preserves per-segment language and confidence, word timings when the ASR backend supplied them, and sets `reviewRequired: true` unless the input explicitly says otherwise. Generated lyric films show the detected language/confidence and a visible human-review warning. The exporter never invents word timings or translated subtitles.

## Render generated lyrics without editing the React registry

The Remotion root provides four generic, duration-aware compositions for any
Song JSON exported by the auto-lyrics engine:

| Format | Composition | Output dimensions |
|---|---|---:|
| Landscape | `AutoLyrics` | 1920×1080 |
| Portrait | `AutoLyricsPortrait` | 1080×1920 |
| Square | `AutoLyricsSquare` | 1024×1024 |
| 4K | `AutoLyrics4K` | 3840×2160 |

The optional `--props-output` writes a wrapper JSON file with the exact
`{ "song": ... }` shape that these compositions expect, so a newly generated
song does not need a new import or a hand-edited `Root.tsx` entry.

1. Put the source audio at the path used by `--audio` under `film/public/`
   (for example, `film/public/audio/song.m4a` for `--audio audio/song.m4a`).
2. Generate the Song JSON and props wrapper with the command above.
3. From the `film/` directory, render a chosen format, for example:

   ```bash
   npx remotion render src/index.ts AutoLyricsPortrait out/song.auto.mp4 --props src/data/song.auto.props.json
   ```

The composition duration is derived from the supplied song's duration. Generated
lyrics still require human review; this automation does not create translations
or certify transcription accuracy.

## Repeatable language-identification smoke benchmark

Run the deterministic text-only smoke benchmark from the repository root:

```bash
python -m tools.benchmark_language_id
python -m tools.benchmark_language_id --output build/benchmark/multilingual-language-id.json
python -m pytest -q tests/test_benchmark_language_id.py tests/test_lyrics_engine.py
```

The starter fixture at `tests/fixtures/multilingual_language_smoke_v1.json` covers
Shona (`sn`), isiNdebele (`nd`), isiZulu (`zu`), English (`en`), mixed text
(`mul`), and uncertain text (`und`). The benchmark reports overall and
per-label accuracy, a confusion matrix, and example-level predictions. CI runs it
on every qualifying build and uploads the JSON report as an artifact.

**Important dataset status:** this first fixture is a synthetic regression smoke
set, not a native-speaker-reviewed benchmark and not an audio/ASR evaluation.
It exists to make changes repeatable and expose regressions, not to claim
real-world accuracy. Before publishing quality claims, replace or supplement it
with consented, rights-cleared lyrics reviewed by fluent speakers of Shona,
isiNdebele, and isiZulu; include naturally occurring code-switching, short and
ambiguous spans, spelling variants, dialects, and difficult sung audio. Keep
train/tuning examples separate from a held-out test set and report per-language
precision/recall as well as accuracy. Unknown or mixed predictions should remain
visible in the confusion report rather than being silently discarded.
