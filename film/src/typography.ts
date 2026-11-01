/**
 * Deterministic layout helpers for lyric typography.
 *
 * These estimates intentionally avoid browser measurement so Remotion renders
 * are reproducible in CI, Studio, and headless render workers.
 */

export type LyricWordTime = { w: string; from: number; to: number };

const glyphWidth = (glyph: string): number => {
  if (/^\p{Mark}$/u.test(glyph)) return 0;
  if (/^\s$/u.test(glyph)) return 0.32;
  if (/^[\p{P}\p{S}]$/u.test(glyph)) return 0.34;

  const codePoint = glyph.codePointAt(0) ?? 0;
  // CJK ideographs, kana, Hangul, and full-width forms occupy roughly one em.
  if (
    (codePoint >= 0x2e80 && codePoint <= 0x9fff) ||
    (codePoint >= 0xac00 && codePoint <= 0xd7af) ||
    (codePoint >= 0xf900 && codePoint <= 0xfaff) ||
    (codePoint >= 0xff01 && codePoint <= 0xff60)
  ) {
    return 1;
  }
  if (/^[A-Z]$/u.test(glyph)) return 0.64;
  if (/^[0-9]$/u.test(glyph)) return 0.56;
  return 0.54;
};

/** Estimate rendered em-width, accounting for scripts with wide glyphs. */
export const estimateLyricWidthUnits = (text: string): number => {
  const normalized = text.normalize("NFC").trim();
  if (!normalized) return 0;
  const glyphUnits = Array.from(normalized).reduce((sum, glyph) => sum + glyphWidth(glyph), 0);
  const wordCount = normalized.split(/\s+/u).filter(Boolean).length;
  // LyricLine uses a small flex gap between independently animated words.
  return glyphUnits + Math.max(0, wordCount - 1) * 0.26;
};

/** Convert estimated glyph width to Latin-character-equivalent units for line wrapping. */
export const estimateLyricCharacterEquivalent = (text: string): number => {
  const normalized = text.normalize("NFC").trim();
  if (!normalized) return 0;
  const wordCount = normalized.split(/\s+/u).filter(Boolean).length;
  const glyphUnits = estimateLyricWidthUnits(normalized) - Math.max(0, wordCount - 1) * 0.26;
  return Math.max(0, glyphUnits / 0.54);
};

/**
 * Calculate a deterministic font size for landscape, portrait, square, and 4K.
 * baseSize is the design size at the composition's reference resolution.
 */
export const calculateLyricFontSize = (
  text: string,
  width: number,
  height: number,
  baseSize = 104,
): number => {
  const safeWidth = Number.isFinite(width) && width > 0 ? width : 1920;
  const safeHeight = Number.isFinite(height) && height > 0 ? height : 1080;
  const safeBase = Number.isFinite(baseSize) && baseSize > 0 ? baseSize : 104;
  const referenceWidth = safeWidth < safeHeight ? 1080 : safeWidth === safeHeight ? 1024 : 1920;
  const scale = safeWidth / referenceWidth;
  const maxSize = Math.min(safeBase, safeWidth < safeHeight ? 84 : 116) * scale;
  const minSize = 18 * scale;
  const availableWidth = safeWidth * 0.84;
  const units = estimateLyricWidthUnits(text);

  if (units <= 0) return maxSize;
  return Math.max(minSize, Math.min(maxSize, (availableWidth / units) * 1.04));
};

/**
 * Return word start times only when every supplied timestamp aligns with the
 * visible lyric token in order. Invalid/mismatched ASR timings fall back to
 * deterministic staggered animation rather than animating the wrong word.
 */
export const resolveWordTimings = (
  text: string,
  wordTimes?: LyricWordTime[],
): number[] | null => {
  const words = text.trim().split(/\s+/u).filter(Boolean);
  if (!wordTimes || wordTimes.length !== words.length || words.length === 0) return null;

  const normalizeWord = (word: string): string =>
    word.normalize("NFC").toLowerCase().replace(/[\p{P}\p{S}]/gu, "");

  let previousFrom = -Infinity;
  for (let index = 0; index < words.length; index += 1) {
    const timing = wordTimes[index];
    if (
      normalizeWord(words[index]) !== normalizeWord(timing.w) ||
      !Number.isFinite(timing.from) ||
      !Number.isFinite(timing.to) ||
      timing.from < 0 ||
      timing.to < timing.from ||
      timing.from < previousFrom
    ) {
      return null;
    }
    previousFrom = timing.from;
  }
  return wordTimes.map(({ from }) => from);
};
