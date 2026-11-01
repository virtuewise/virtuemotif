# Audio intelligence engine

`tools/audio_intelligence.py` extracts a lightweight, deterministic audio cue
track for use by lyric-video composition and effects:

- estimated tempo and a confidence score from spectral-flux autocorrelation
- a beat grid and a conventional four-beat downbeat grid for visual cueing
- a normalized per-second energy contour
- timestamped onset, energy-rise, and energy-drop events

## Usage

```bash
python -m tools.audio_intelligence path/to/song.wav
python -m tools.audio_intelligence path/to/song.wav --output timing/song.audio-intelligence.json
```

The output is versioned JSON designed to become a shared input for typography,
camera motion, transitions, and effect intensity. It uses NumPy and SoundFile;
it does not require a heavyweight music-analysis model.

### Export cues for Remotion

From the repository root, run:

```bash
python -m tools.export_audio_cues
```

This normalizes the bundled Horizon and Rise audio with FFmpeg, then writes
`film/public/audio-cues/horizon.audio-intelligence.json` and
`film/public/audio-cues/rise.audio-intelligence.json`. Remotion loads the
matching file by song ID and evaluates it at each zero-based frame timestamp.
The files are generated assets and should be regenerated whenever their source
audio changes.

The furry lyric director uses the real beat grid to snap lyric entrances when a
beat is within 180 ms, the energy curve to shape displacement, and onset/energy
events to raise transition and typography intensity. The wave and glitch
compositions map these same frame-synchronous cues into bounded shader
parameters. Procedural rainfall particle positions and speeds use a stable seed.
Avoid wall-clock time, unseeded randomness, or browser-persisted learning state
as inputs to production-rendered frames: the same input and frame should produce
the same visual state on every render worker.

Invalid or missing cue files use deterministic frame-derived motion instead of
failing a render.

Cue loading and frame-time utilities are covered by
`node --experimental-strip-types --test tests/audio_cues.test.mjs`; the CI
workflow also generates the Remotion cue assets before composition validation.

## Limitations

Tempo estimation is an estimate and can select half-time/double-time on ambiguous
material. The downbeat list assumes a four-beat grouping for convenience; it is
not a true time-signature detector. The current engine does not separate vocals
from instruments, identify chords, or infer emotion. Review cues before using
them as authoritative musical annotations. Deterministic animation makes renders
repeatable; it does not by itself prove that motion is musically well synchronized.
