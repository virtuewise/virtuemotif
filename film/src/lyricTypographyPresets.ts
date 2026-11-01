// Kept self-contained so Node's type-stripping test runner can import the preset contract.
const P = {
  tealLight: "#2C7A74",
  ochre: "#E8A33D",
  amber: "#F2B24A",
  cream: "#F6E7C8",
  bone: "#FFF6E3",
} as const;
const FONT_DISPLAY = "'Anton', 'Arial Narrow', sans-serif";
const FONT_SERIF = "'Instrument Serif', Georgia, serif";
const FONT_MONO = "'Space Grotesk', 'Segoe UI', sans-serif";

export type LyricTypographyPresetName = "display" | "whisper" | "neon" | "editorial";

export interface LyricTypographyPreset {
  fontFamily: string;
  fontStyle: "normal" | "italic";
  textTransform: "uppercase" | "none";
  color: string;
  highlightColor: string;
  letterSpacing: string;
  textShadow: string;
  wordGap: string;
  ruleColor: string;
  ruleAccent: string;
  translationFontFamily: string;
  translationFontStyle: "normal" | "italic";
  translationColor: string;
  translationScale: number;
}

/**
 * Declarative motion-typography treatments. Add or tune a named preset here;
 * LyricLine consumes these tokens without requiring per-style render branches.
 */
export const LYRIC_TYPOGRAPHY_PRESETS: Record<LyricTypographyPresetName, LyricTypographyPreset> = {
  display: {
    fontFamily: FONT_DISPLAY,
    fontStyle: "normal",
    textTransform: "uppercase",
    color: P.bone,
    highlightColor: P.amber,
    letterSpacing: "-0.005em",
    textShadow: "0 3px 0 #2A140F, 0 20px 44px rgba(0,0,0,0.55)",
    wordGap: "0 0.26em",
    ruleColor: P.ochre,
    ruleAccent: P.amber,
    translationFontFamily: FONT_SERIF,
    translationFontStyle: "italic",
    translationColor: P.ochre,
    translationScale: 1,
  },
  whisper: {
    fontFamily: FONT_SERIF,
    fontStyle: "italic",
    textTransform: "none",
    color: P.bone,
    highlightColor: P.cream,
    letterSpacing: "0.01em",
    textShadow: "0 6px 26px rgba(0,0,0,0.75)",
    wordGap: "0 0.18em",
    ruleColor: P.tealLight,
    ruleAccent: P.cream,
    translationFontFamily: FONT_SERIF,
    translationFontStyle: "italic",
    translationColor: P.cream,
    translationScale: 0.78,
  },
  neon: {
    fontFamily: FONT_MONO,
    fontStyle: "normal",
    textTransform: "uppercase",
    color: "#C8FFF6",
    highlightColor: "#FFFFFF",
    letterSpacing: "0.035em",
    textShadow: "0 0 10px rgba(45,212,191,0.8), 0 4px 24px rgba(0,0,0,0.8)",
    wordGap: "0 0.2em",
    ruleColor: P.tealLight,
    ruleAccent: "#A7F3D0",
    translationFontFamily: FONT_MONO,
    translationFontStyle: "normal",
    translationColor: "#A7F3D0",
    translationScale: 0.72,
  },
  editorial: {
    fontFamily: FONT_SERIF,
    fontStyle: "normal",
    textTransform: "none",
    color: P.cream,
    highlightColor: P.ochre,
    letterSpacing: "0.01em",
    textShadow: "0 6px 28px rgba(0,0,0,0.72)",
    wordGap: "0 0.2em",
    ruleColor: P.ochre,
    ruleAccent: P.cream,
    translationFontFamily: FONT_SERIF,
    translationFontStyle: "italic",
    translationColor: P.ochre,
    translationScale: 0.82,
  },
};

export const isLyricTypographyPreset = (value: string): value is LyricTypographyPresetName =>
  Object.prototype.hasOwnProperty.call(LYRIC_TYPOGRAPHY_PRESETS, value);

export const resolveLyricTypographyPreset = (
  value?: string,
  fallback: LyricTypographyPresetName = "display",
): LyricTypographyPresetName =>
  value && isLyricTypographyPreset(value) ? value : fallback;
