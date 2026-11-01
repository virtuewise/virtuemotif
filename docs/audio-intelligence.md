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
camera motion, transitions, and effect intensity. It uses NumPy and the existing
SoundFile dependency; it does not require a heavyweight music-analysis model.

## Limitations

Tempo estimation is an estimate and can select half-time/double-time on ambiguous
material. The downbeat list assumes a four-beat grouping for convenience; it is
not a true time-signature detector. The current engine does not separate vocals
from instruments, identify chords, or infer emotion. Review cues before using
them as authoritative musical annotations.
