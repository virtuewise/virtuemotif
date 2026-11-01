import React from "react";
import { AbsoluteFill, Audio, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE as P, clamp, rnd } from "./theme";
import {
  Birds,
  Dust,
  FilmGrain,
  Figure,
  HorizonGlow,
  PaperTexture,
  Ridge,
  Sky,
  Sun,
  Treeline,
  Vignette,
} from "./Backdrop";
import { CornerLabel, LyricLine, PaperWipe, TitleCard, useFilmFonts } from "./Type";

export type Pose = "stand" | "walk" | "raise" | "mbira" | "child";

export type Look = {
  variant: "dusk" | "sunrise" | "night" | "giant";
  sunX: number;
  sunY: number;
  sunR: number;
  warmth: number;
  night: number;
  camStart: number;
  camEnd: number;
  panX?: number;
  treeDensity: number;
  figures: { x: number; y: number; pose: Pose; s: number; flip?: boolean }[];
  haze?: number;
};

export type WordTime = { w: string; from: number; to: number };
export type Line = {
  text: string;
  translation: string;
  style: string;
  from: number;
  to: number;
  words?: WordTime[];
  language?: string;
  languageConfidence?: number;
};
export type Section = { id: string; label: string; look: string; start: number; end: number; lines: Line[] };
export type Song = {
  id: string;
  title: string;
  subtitle: string;
  artist: string;
  audio: string;
  duration: number;
  sections: Section[];
  detectedLanguage?: string;
  detectedLanguageCode?: string;
  languageConfidence?: number;
  reviewRequired?: boolean;
};

/* --------------------------------------------------------------- scenery */
export const Scenery: React.FC<{ t: number; st: number; look: Look; fade?: number }> = ({
  t,
  st,
  look,
  fade = 1,
}) => {
  const push = interpolate(clamp(st / 28), [0, 1], [look.camStart, look.camEnd]);
  const drift = (look.panX ?? 0) * Math.sin(st * 0.09);
  const night = look.variant === "night";
  return (
    <AbsoluteFill style={{ opacity: fade, background: P.night, overflow: "hidden" }}>
      <AbsoluteFill style={{ transform: `scale(${push}) translateX(${drift}px)` }}>
        <Sky t={t} sunY={clamp(1 - (look.sunY - 220) / 470)} warmth={look.warmth} night={night ? 1 : look.night} />
        {night ? null : <HorizonGlow intensity={0.55 + look.warmth * 0.45} />}
        <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>
          {look.variant === "giant" ? (
            <>
              <Sun x={look.sunX} y={look.sunY} r={look.sunR} rising={1} />
              <Ridge baseY={1010} amp={30} freq={0.0042} seed={17} phase={t * 2} fill="#071018" opacity={0.65} />
            </>
          ) : night ? (
            <>
              <Sun x={1380} y={250} r={64} rising={1} core="#FFF9E8" mid="#E9E2C8" edge="#B9C4B0" />
            </>
          ) : (
            <Sun x={look.sunX} y={look.sunY} r={look.sunR} rising={1} />
          )}
          <Birds t={t} />
          {look.variant === "giant" ? null : (
            <>
              <Ridge baseY={792} amp={116} freq={0.0022} seed={11} phase={t * 2} fill="#16424A" opacity={0.5} />
              <Ridge baseY={830} amp={82} freq={0.0034} seed={4} phase={t * 3} fill="#0F3239" opacity={0.92} />
              <Treeline y={884} fill="#0A2228" t={t} density={look.treeDensity} />
              <Ridge baseY={946} amp={72} freq={0.0052} seed={27} phase={t * 4} fill="#071820" />
            </>
          )}
          {look.figures.map((f, i) => (
            <g key={i} style={{ filter: "drop-shadow(0 0 7px rgba(232,163,61,0.45))" }}>
              <Figure x={f.x} y={f.y} s={f.s} pose={f.pose} t={t + i * 1.7} flip={f.flip} fill="#050C12" />
            </g>
          ))}
          <Ridge baseY={1052} amp={38} freq={0.009} seed={33} phase={t * 6} fill="#030A0F" shadow={false} />
          {new Array(26).fill(0).map((_, i) => {
            const x = i * 78 + 20;
            const h = 60 + rnd(i) * 90;
            const sway = Math.sin(t * 1.1 + i) * 7;
            return (
              <path
                key={`g${i}`}
                d={`M ${x},1080 Q ${x + sway},${1080 - h * 0.6} ${x + sway * 1.8},${1080 - h}`}
                stroke="#030A0F"
                strokeWidth={7 + rnd(i + 3) * 5}
                fill="none"
                strokeLinecap="round"
              />
            );
          })}
        </svg>
        <Dust t={t} count={night ? 40 : 80} />
      </AbsoluteFill>
      <PaperTexture opacity={0.13} />
      <Vignette strength={night ? 0.95 : 0.82} />
      <FilmGrain frame={Math.round(t * 30)} opacity={0.19} />
    </AbsoluteFill>
  );
};

/* ----------------------------------------------------------------- looks */
const LOOKS: Record<string, Look> = {
  wide: {
    variant: "dusk",
    sunX: 960,
    sunY: 566,
    sunR: 292,
    warmth: 0.62,
    night: 0.1,
    camStart: 1.0,
    camEnd: 1.07,
    panX: 12,
    treeDensity: 5,
    figures: [
      { x: 452, y: 1006, pose: "stand", s: 0.95 },
      { x: 1462, y: 1002, pose: "mbira", s: 1.05, flip: true },
    ],
  },
  walkers: {
    variant: "sunrise",
    sunX: 1210,
    sunY: 520,
    sunR: 316,
    warmth: 0.9,
    night: 0,
    camStart: 1.08,
    camEnd: 1.0,
    panX: -18,
    treeDensity: 4,
    figures: [
      { x: 372, y: 1018, pose: "walk", s: 1.35 },
      { x: 566, y: 1024, pose: "child", s: 0.95 },
      { x: 786, y: 1020, pose: "walk", s: 1.3, flip: true },
      { x: 1368, y: 1014, pose: "raise", s: 1.45 },
    ],
  },
  raise: {
    variant: "dusk",
    sunX: 700,
    sunY: 600,
    sunR: 330,
    warmth: 0.78,
    night: 0,
    camStart: 1.1,
    camEnd: 1.02,
    panX: 10,
    treeDensity: 3,
    figures: [
      { x: 360, y: 1020, pose: "raise", s: 1.5 },
      { x: 620, y: 1026, pose: "raise", s: 1.35 },
      { x: 900, y: 1022, pose: "stand", s: 1.4 },
      { x: 1180, y: 1026, pose: "raise", s: 1.55, flip: true },
      { x: 1470, y: 1020, pose: "mbira", s: 1.3, flip: true },
    ],
  },
  mbira: {
    variant: "dusk",
    sunX: 1480,
    sunY: 600,
    sunR: 280,
    warmth: 0.7,
    night: 0.05,
    camStart: 1.16,
    camEnd: 1.06,
    panX: -8,
    treeDensity: 6,
    figures: [
      { x: 1180, y: 1042, pose: "mbira", s: 1.9, flip: true },
      { x: 470, y: 1010, pose: "stand", s: 1.0 },
    ],
  },
  giant: {
    variant: "giant",
    sunX: 960,
    sunY: 700,
    sunR: 620,
    warmth: 1,
    night: 0,
    camStart: 1.04,
    camEnd: 1.14,
    panX: 6,
    treeDensity: 0,
    figures: [
      { x: 420, y: 1058, pose: "raise", s: 1.35 },
      { x: 760, y: 1062, pose: "stand", s: 1.3 },
      { x: 1180, y: 1060, pose: "raise", s: 1.32, flip: true },
      { x: 1520, y: 1058, pose: "walk", s: 1.28, flip: true },
    ],
  },
  night: {
    variant: "night",
    sunX: 1380,
    sunY: 250,
    sunR: 64,
    warmth: 0,
    night: 1,
    camStart: 1.0,
    camEnd: 1.09,
    panX: 14,
    treeDensity: 5,
    figures: [
      { x: 700, y: 1008, pose: "stand", s: 1.0 },
      { x: 1280, y: 1012, pose: "mbira", s: 1.1, flip: true },
    ],
  },
};

/* ------------------------------------------------------------------ film */
export const Film: React.FC<{ song: Song }> = ({ song }) => {
  useFilmFonts();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const secs = song.sections;
  let active = secs[0];
  for (const s of secs) if (t >= s.start && t < s.end) active = s;
  const prev = secs[Math.max(0, secs.indexOf(active) - 1)];
  const look = LOOKS[active.look] ?? LOOKS.wide;

  // crossfade the outgoing look for 1.1s after a section change
  const since = t - active.start;
  const showPrev = prev !== active && since < 1.1;
  const wipeAt = secs.filter((s) => s.start > 0 && s.start < song.duration).map((s) => s.start);
  const wipe = wipeAt.find((w) => t >= w - 0.08 && t <= w + 1.0);

  return (
    <AbsoluteFill style={{ background: P.night }}>
      <Audio src={staticFile(song.audio)} />

      {showPrev ? (
        <Scenery
          t={t}
          st={t - prev.start}
          look={LOOKS[prev.look] ?? LOOKS.wide}
          fade={1 - clamp(since / 1.1)}
        />
      ) : null}
      <Scenery t={t} st={since} look={look} />

      {/* opening: fade up from black */}
      <div style={{ position: "absolute", inset: 0, background: P.night, opacity: clamp(1 - t / 2.2) }} />
      {/* closing: fade to black */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: P.night,
          opacity: clamp((t - (song.duration - 6)) / 5.5),
        }}
      />

      {wipe !== undefined ? <PaperWipe at={wipe} duration={0.9} color="#08111E" /> : null}

      <TitleCard
        title={`${song.title}`}
        subtitle={song.subtitle}
        kicker="A lyrical film"
        artist={song.artist}
        from={1.2}
        to={Math.max(4.6, Math.min(7.5, (secs[0]?.lines[0]?.from ?? 9) - 1.2))}
      />

      {active.lines.map((ln, i) => (
        <LyricLine
          key={`${active.id}-${i}`}
          text={ln.text}
          translation={ln.translation || undefined}
          from={ln.from}
          to={ln.to}
          whisper={ln.style === "whisper"}
          size={ln.style === "whisper" ? 104 : 104}
          words={ln.words}
          y={-18}
        />
      ))}

      <CornerLabel text={`${song.title}${song.subtitle ? " / " + song.subtitle : ""}`} from={2.5} to={song.duration} />
      <CornerLabel text={`${song.artist} Â· suno`} from={song.duration - 8} to={song.duration} />
    </AbsoluteFill>
  );
};


/* ------------------------------------------------------------------ proof */
/* The proof is simply the real film, rendered for its first ~65 seconds.  */
export const Proof: React.FC<{ song: Song }> = ({ song }) => <Film song={song} />;
