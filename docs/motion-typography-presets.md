# Motion typography presets

VirtueMotif's classic Remotion lyric renderer supports named per-line typography
presets. Set the line's existing `style` field to one of the supported names:

- `display` — high-contrast cinematic display typography (default).
- `whisper` — softer serif italic treatment.
- `neon` — cool, luminous monospaced emphasis.
- `editorial` — restrained serif typography with editorial spacing.

Example Song JSON excerpt:

```json
{
  "text": "Ngiyavuka, ngiyakhanya",
  "translation": "I rise, I shine",
  "style": "neon",
  "from": 12.4,
  "to": 16.8
}
```

Unknown or legacy style names fall back to `display`; existing `whisper`
lines keep their prior appearance. Preset tokens live in
`film/src/lyricTypographyPresets.ts`: font family/style, text transform,
letter spacing, text shadow, word spacing, emphasis color, rule colors, and
translation treatment can be tuned independently.

The layout helper in `film/src/typography.ts` estimates glyph width
deterministically, accounting for full-width CJK characters and Unicode
punctuation, and scales typography to the composition's reference resolution.
This is an estimate rather than browser-measured font geometry, so CI tests
cover deterministic behavior while visual review remains required for approved
reference frames and production lyrics.

Presets are presentation choices only: they do not translate lyrics, infer
language, repair transcription, or change word timestamps. Human review of
machine-generated lyrics remains required.
