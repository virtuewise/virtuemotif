import React, { useEffect, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT_DISPLAY, FONT_MONO, FONT_SERIF, PALETTE as P, clamp, easeOut, rnd } from "./theme";
import { calculateLyricFontSize, resolveWordTimings } from "./typography";
import { LYRIC_TYPOGRAPHY_PRESETS, resolveLyricTypographyPreset } from "./lyricTypographyPresets";
import { audioReactiveTypographyScale, type AudioCueFrame } from "./fur3d/audioCues";

/* ------------------------------------------------------------ font load */
const FACES = [
  { family: "Anton", file: "fonts/Anton-Regular.ttf", weight: "400" },
  { family: "Instrument Serif", file: "fonts/InstrumentSerif-Regular.ttf", weight: "400" },
  { family: "Instrument Serif", file: "fonts/InstrumentSerif-Italic.ttf", weight: "400", style: "italic" },
  { family: "Space Grotesk", file: "fonts/SpaceGrotesk.ttf", weight: "300 700" },
];

export const useFilmFonts = () => {
  const [handle] = useState(() => delayRender("fonts"));
  useEffect(() => {
    const css = FACES.map(
      (f) =>
        `@font-face{font-family:'${f.family}';src:url('${staticFile(f.file)}') format('truetype');font-weight:${f.weight};font-style:${f.style ?? "normal"};font-display:block;}`,
    ).join("\n");
    const style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);
    Promise.all(FACES.map((f) => document.fonts.load(`${f.style ?? "normal"} ${f.weight} 64px '${f.family}'`)))
      .then(() => document.fonts.ready)
      .then(() => continueRender(handle))
      .catch(() => continueRender(handle));
  }, [handle]);
};

/* ------------------------------------------------------------- fit size */
// Layout sizing lives in typography.ts so it can be tested without a browser.

/* ------------------------------------------------------------ lyric line */
export type WordTime = { w: string; from: number; to: number };

export const LyricLine: React.FC<{
  text: string;
  translation?: string;
  from: number;
  to: number;
  offset?: number;
  size?: number;
  whisper?: boolean;
  typographyPreset?: string;
  words?: WordTime[];
  audioCueFrame?: AudioCueFrame;
  y?: number;
}> = ({ text, translation, from, to, offset = 0, size = 104, whisper = false, typographyPreset, words: wordTimes, audioCueFrame, y = 0 }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps + offset;

  if (t < from - 0.2 || t > to + 0.6) return null;

  const words = text.trim().split(/\s+/u).filter(Boolean);
  const wordStarts = resolveWordTimings(text, wordTimes, from, to);
  const stagger = Math.min(0.14, 1.6 / Math.max(words.length, 1));
  const lastStart = wordStarts ? wordStarts[wordStarts.length - 1] : from + (words.length - 1) * stagger;
  const inEnd = wordStarts ? lastStart + 0.9 : from + 0.9 + words.length * stagger;
  const outStart = to - 0.75;
  const exit = clamp((t - outStart) / 0.75);

  const isPortrait = width < height;
  const activePresetName = resolveLyricTypographyPreset(typographyPreset, whisper ? "whisper" : "display");
  const preset = LYRIC_TYPOGRAPHY_PRESETS[activePresetName];
  const isWhisper = activePresetName === "whisper";
  const requestedSize = isWhisper && isPortrait ? size * 0.75 : size;
  const fs = calculateLyricFontSize(text, width, height, requestedSize);
  const audioScale = audioCueFrame ? audioReactiveTypographyScale(audioCueFrame) : 1;
  const lineOpacity = 1 - exit;
  const enterP = clamp((t - from) / 0.65);
  const fallY = (1 - easeOut(enterP)) * -32;
  const rise = interpolate(exit, [0, 1], [0, -26]);
  const blur = interpolate(exit, [0, 1], [0, 7]);
  const maxW = Math.min(1560, width * 0.88);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* legibility scrim — soft, no edges */}
      <div
        style={{
          position: "absolute",
          width: Math.min(1900, width * 0.98),
          height: Math.min(height * 0.62, 640 * (width < height ? width / 1080 : width === height ? width / 1024 : width / 1920)),
          top: "50%",
          marginTop: -Math.min(height * 0.62, 640 * (width < height ? width / 1080 : width === height ? width / 1024 : width / 1920)) / 2,
          background: "radial-gradient(closest-side, rgba(3,6,12,0.62), rgba(3,6,12,0.34) 55%, transparent 78%)",
          filter: "blur(14px)",
          opacity: 0.9 * lineOpacity,
        }}
      />
      <div
        style={{
          width: maxW,
          margin: "0 auto",
          transform: `translateY(${y + rise + fallY}px) scale(${audioScale})`,
          opacity: lineOpacity,
          filter: blur > 0.05 ? `blur(${blur}px)` : undefined,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily: preset.fontFamily,
            fontStyle: preset.fontStyle,
            fontSize: fs,
            lineHeight: 1.06,
            letterSpacing: preset.letterSpacing,
            textTransform: preset.textTransform,
            color: preset.color,
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: preset.wordGap,
            textShadow: preset.textShadow,
          }}
        >
          {words.map((w, i) => {
            const wordTiming = wordStarts ? wordTimes?.[i] : undefined;
            const start = wordTiming ? wordTiming.from - 0.06 : from + i * stagger;
            const pr = spring({
              frame: Math.round((t - start) * fps),
              fps,
              config: { damping: 200, mass: 0.6, stiffness: 90 },
            });
            const op = clamp(pr * 1.4);
            const dy = interpolate(pr, [0, 1], [46, 0]);
            const rot = interpolate(pr, [0, 1], [(rnd(i + text.length) - 0.5) * 3.2, 0]);
            const blurW = interpolate(pr, [0, 1], [10, 0]);
            const highlightStart = wordTiming?.from ?? start;
            const highlightEnd = wordTiming?.to ?? highlightStart + 0.45;
            const highlightDuration = Math.max(0.12, highlightEnd - highlightStart);
            const recent = clamp((t - highlightStart) / highlightDuration);
            const hot = 1 - Math.abs(recent * 2 - 1);
            const color = hot > 0.02
              ? activePresetName === "display" ? `rgb(${246 + hot * 9},${231 - hot * 20},${200 - hot * 120})` : preset.highlightColor
              : preset.color;
            return (
              <span
                key={i}
                style={{
                  display: "inline-block",
                  opacity: op,
                  transform: `translateY(${dy}px) rotate(${rot}deg)`,
                  filter: blurW > 0.1 ? `blur(${blurW}px)` : undefined,
                  color,
                  whiteSpace: "pre-wrap",
                  maxWidth: "100%",
                  overflowWrap: "anywhere",
                }}
              >
                {w}
              </span>
            );
          })}
        </div>

        {/* drawn rule */}
        <div
          style={{
            height: 3,
            margin: "26px auto 0",
            width: Math.min(width * 0.72, 1500 * (width < height ? width / 1080 : width === height ? width / 1024 : width / 1920)) * clamp((t - from - 0.25) / 0.9) * (1 - exit),
            background: `linear-gradient(90deg, transparent, ${preset.ruleColor} 12%, ${preset.ruleAccent} 50%, ${preset.ruleColor} 88%, transparent)`,
            opacity: 0.85 * (1 - exit),
            transform: `scaleY(${Math.max(1, 0.4 + Math.sin(t * 2) * 0.05)})`,
          }}
        />

        {translation ? (
          <div
            style={{
              marginTop: 22,
              fontFamily: preset.translationFontFamily,
              fontStyle: preset.translationFontStyle,
              fontSize: Math.min(isPortrait ? 34 : 44, width * 0.035) * preset.translationScale,
              maxWidth: width * 0.82,
              marginLeft: "auto",
              marginRight: "auto",
              overflowWrap: "anywhere",
              color: preset.translationColor,
              letterSpacing: preset.letterSpacing,
              opacity: clamp((t - inEnd) / 0.7) * (1 - exit),
              transform: `translateY(${interpolate(clamp((t - inEnd) / 0.7), [0, 1], [14, 0])}px)`,
              textShadow: "0 4px 18px rgba(0,0,0,0.7)",
            }}
          >
            {translation}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------ title card */
export const TitleCard: React.FC<{
  title: string;
  subtitle?: string;
  kicker?: string;
  artist?: string;
  from: number;
  to: number;
  offset?: number;
}> = ({ title, subtitle, kicker, artist, from, to, offset = 0 }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps + offset;
  if (t < from || t > to) return null;
  const p = clamp((t - from) / 1.4);
  const out = clamp((t - (to - 1.1)) / 1.1);
  const e = easeOut(p);
  const scale = interpolate(e, [0, 1], [1.045, 1]);
  const fallY = (1 - e) * -45; // Smoothly drops and settles into center without overlapping
  const isPortrait = width < height;
  const titleFontSize = isPortrait ? Math.min(84, width * 0.076) : Math.min(124, width * 0.064);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: 1 - out }}>
      <div
        style={{
          textAlign: "center",
          width: Math.min(1500, width * 0.88),
          margin: "0 auto",
          transform: `scale(${scale}) translateY(${fallY}px)`,
        }}
      >

        <div
          style={{
            fontFamily: FONT_MONO,
            fontWeight: 600,
            fontSize: isPortrait ? 15 : 19,
            letterSpacing: "0.52em",
            color: P.amber,
            textTransform: "uppercase",
            opacity: clamp((t - from) / 0.9),
            marginBottom: isPortrait ? 18 : 30,
          }}
        >
          {kicker ?? "A lyrical film"}
        </div>

        <div
          style={{
            fontFamily: FONT_DISPLAY,
            fontSize: titleFontSize,
            lineHeight: 1.04,
            letterSpacing: "-0.01em",
            color: P.bone,
            textTransform: "uppercase",
            textShadow: "0 4px 0 #2A140F, 0 26px 60px rgba(0,0,0,0.6)",
            opacity: e,
          }}
        >
          {title}
        </div>

        <div
          style={{
            width: Math.min(760, width * 0.6) * e,
            height: 2,
            margin: isPortrait ? "22px auto 18px" : "34px auto 26px",
            background: `linear-gradient(90deg, transparent, ${P.ochre}, transparent)`,
          }}
        />

        {subtitle ? (
          <div
            style={{
              fontFamily: FONT_SERIF,
              fontStyle: "italic",
              fontSize: isPortrait ? 46 : 72,
              color: P.cream,
              opacity: clamp((t - from - 0.5) / 0.8),
              textShadow: "0 6px 26px rgba(0,0,0,0.7)",
            }}
          >
            {subtitle}
          </div>
        ) : null}

        {artist ? (
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 18,
              letterSpacing: "0.42em",
              color: P.cream,
              opacity: 0.65 * clamp((t - from - 1.0) / 0.8),
              marginTop: 34,
              textTransform: "uppercase",
            }}
          >
            {artist}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

/* -------------------------------------------------------------- paper wipe */
export const PaperWipe: React.FC<{
  at: number;
  duration?: number;
  offset?: number;
  color?: string;
  reverse?: boolean;
}> = ({ at, duration = 0.9, offset = 0, color = P.night, reverse = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps + offset;
  if (t < at || t > at + duration) return null;
  const p = (t - at) / duration;
  const x = reverse ? interpolate(p, [0, 1], [-100, 100]) : interpolate(p, [0, 1], [100, -100]);
  // torn edge: jagged vertical seam
  const seam = new Array(26).fill(0).map((_, i) => `${i * 4},${i * 4}`).join(" ");
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          width: "130%",
          left: `${x}%`,
          background: color,
          boxShadow: "0 0 80px rgba(0,0,0,0.6)",
          clipPath: "polygon(0 0, 96% 0, 100% 8%, 97% 16%, 100% 24%, 97% 33%, 100% 41%, 96% 50%, 100% 58%, 97% 67%, 100% 75%, 96% 84%, 100% 92%, 97% 100%, 0 100%)",
          opacity: 0.985,
        }}
      >
        <span style={{ display: "none" }}>{seam}</span>
      </div>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------- lit label */
export const CornerLabel: React.FC<{ text: string; from: number; to: number; offset?: number }> = ({
  text,
  from,
  to,
  offset = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps + offset;
  if (t < from || t > to) return null;
  const a = Math.min(clamp((t - from) / 0.8), clamp((to - t) / 0.8));
  return (
    <div
      style={{
        position: "absolute",
        left: 92,
        bottom: 74,
        fontFamily: FONT_MONO,
        fontSize: 15,
        letterSpacing: "0.34em",
        color: P.cream,
        opacity: a * 0.55,
        textTransform: "uppercase",
      }}
    >
      {text}
    </div>
  );
};
