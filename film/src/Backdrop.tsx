import React, { useMemo } from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { PALETTE as P, clamp, lerp, mix, noise1, rnd } from "./theme";

const W = 1920;
const H = 1080;
const HORIZON = 690;

/* ------------------------------------------------------------------ sky */
export const Sky: React.FC<{ t: number; sunY: number; warmth: number; night?: number }> = ({
  t,
  sunY,
  warmth,
  night = 0,
}) => {
  const top = mix(mix(P.night, "#101A38", 1 - night), P.dusk, warmth * 0.35);
  const mid = mix(mix("#0C2030", P.teal, 0.55), P.rust, warmth * 0.5);
  const glow = sunY; // 0 high, 1 at horizon
  const cold = night > 0.5;
  const stopA = cold ? "#0A2230" : mix(P.rust, P.ochre, 0.35 + glow * 0.3);
  const stopB = cold ? "#123B44" : mix(P.amber, P.cream, 0.25 + glow * 0.25);
  const stopC = cold ? "#06111A" : P.tealDark;
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `linear-gradient(180deg, ${top} 0%, ${mid} 46%, ${stopA} 64%, ${stopB} 70%, ${stopC} 72%, ${P.night} 100%)`,
        }}
      />
      {/* sun halo */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: HORIZON - 40,
          width: 1900,
          height: 1200,
          transform: `translate(-50%, ${lerp(-260, -40, glow)}px)`,
          background: cold
            ? `radial-gradient(closest-side, #9FB6C855 0%, #2C5A642E 40%, transparent 72%)`
            : `radial-gradient(closest-side, ${P.amber}55 0%, ${P.ember}2E 38%, transparent 72%)`,
          filter: "blur(6px)",
        }}
      />
      {/* drifting paper cloud bands */}
      {new Array(7).fill(0).map((_, i) => {
        const y = 120 + i * 62 + rnd(i + 3) * 40;
        const w = 520 + rnd(i + 9) * 760;
        const speed = 6 + i * 2.5;
        const x = ((t * speed + rnd(i) * 2400) % 2600) - 340;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: w,
              height: 12 + (i % 3) * 7,
              borderRadius: 60,
              background: `linear-gradient(90deg, transparent, ${mix(P.teal, P.night, 0.25 + i * 0.06)}AA 18%, ${
                P.dusk
              }66 60%, transparent)`,
              opacity: 0.55 - i * 0.04,
              filter: "blur(1.2px)",
            }}
          />
        );
      })}
      {/* stars, fading out with warmth */}
      {new Array(70).fill(0).map((_, i) => {
        const x = rnd(i * 2.7) * W;
        const y = rnd(i * 5.1) * 420;
        const tw = 0.35 + 0.65 * Math.abs(Math.sin(t * (0.6 + rnd(i) * 1.4) + i));
        return (
          <div
            key={`s${i}`}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: 2 + rnd(i + 1) * 2.4,
              height: 2 + rnd(i + 1) * 2.4,
              borderRadius: 4,
              background: P.bone,
              opacity: tw * (1 - warmth) * (0.35 + night * 0.65) * 0.95,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ sun */
export const Sun: React.FC<{
  x: number;
  y: number;
  r: number;
  rising: number;
  core?: string;
  mid?: string;
  edge?: string;
}> = ({ x, y, r, rising, core = "#FFF4D2", mid = P.amber, edge = P.ember }) => {
  const bands = new Array(6).fill(0).map((_, i) => ({
    y: r * 0.08 + i * (r * 0.13),
    h: 3 + i * 1.9,
  }));
  return (
    <g>
      <defs>
        <radialGradient id="sunG" cx="50%" cy="42%" r="62%">
          <stop offset="0%" stopColor={core} />
          <stop offset="45%" stopColor={mid} />
          <stop offset="82%" stopColor={edge} />
          <stop offset="100%" stopColor={P.clay} />
        </radialGradient>
        <clipPath id="sunClip">
          <circle cx={x} cy={y} r={r * rising} />
        </clipPath>
      </defs>
      <circle cx={x} cy={y} r={r * rising} fill="url(#sunG)" opacity={0.98} />
      <g clipPath="url(#sunClip)">
        {r >= 100
          ? bands.map((b, i) => (
              <rect
                key={i}
                x={x - r}
                y={y + b.y * rising}
                width={r * 2}
                height={b.h * rising}
                fill={P.dusk}
                opacity={0.75}
              />
            ))
          : null}
      </g>
      <circle cx={x} cy={y} r={r * rising} fill="none" stroke={P.amber} strokeWidth={1.2} opacity={0.5} />
    </g>
  );
};

/* --------------------------------------------------------------- ridges */
const ridgePoints = (baseY: number, amp: number, freq: number, seed: number, phase: number) => {
  const pts: [number, number][] = [];
  for (let x = -40; x <= W + 40; x += 24) {
    const n =
      noise1(x * freq + phase, seed) * 0.6 +
      noise1(x * freq * 2.7 + phase * 1.7, seed + 3) * 0.28 +
      noise1(x * freq * 6.1 + phase * 2.3, seed + 9) * 0.12;
    pts.push([x, baseY - (n - 0.45) * amp]);
  }
  return pts;
};

export const Ridge: React.FC<{
  baseY: number;
  amp: number;
  freq: number;
  seed: number;
  phase: number;
  fill: string;
  opacity?: number;
  edge?: string;
  shadow?: boolean;
}> = ({ baseY, amp, freq, seed, phase, fill, opacity = 1, edge, shadow = true }) => {
  const pts = useMemo(() => ridgePoints(baseY, amp, freq, seed, phase), [baseY, amp, freq, seed, phase]);
  const d =
    `M ${pts[0][0]},${H} L ${pts[0][0]},${pts[0][1]} ` +
    pts.map(([x, y]) => `L ${x},${y.toFixed(1)}`).join(" ") +
    ` L ${W + 40},${H} Z`;
  return (
    <path
      d={d}
      fill={fill}
      opacity={opacity}
      stroke={edge}
      strokeWidth={edge ? 2 : 0}
      style={shadow ? { filter: "drop-shadow(0 -7px 14px rgba(4,8,14,0.45))" } : undefined}
    />
  );
};

/* ---------------------------------------------------------------- trees */
const Acacia: React.FC<{ x: number; y: number; s: number; fill: string; sway?: number }> = ({
  x,
  y,
  s,
  fill,
  sway = 0,
}) => (
  <g transform={`translate(${x} ${y}) scale(${s}) rotate(${sway} 0 -40)`}>
    <path
      d="M -6,0 L -2,-96 L 2,-96 L 6,0 Z M -2,-58 L -22,-76 L -18,-80 L 2,-64 Z M 2,-64 L 20,-82 L 24,-78 L 4,-60 Z"
      fill={fill}
    />
    {[
      [-34, -104, 40, 9],
      [0, -116, 56, 11],
      [38, -104, 36, 8],
      [-14, -96, 30, 7],
      [16, -96, 30, 7],
    ].map(([cx, cy, rx, ry], i) => (
      <ellipse key={i} cx={cx} cy={cy} rx={rx} ry={ry} fill={fill} />
    ))}
  </g>
);

export const Treeline: React.FC<{ y: number; fill: string; t: number; density?: number }> = ({
  y,
  fill,
  t,
  density = 6,
}) => (
  <g>
    {new Array(density).fill(0).map((_, i) => {
      const x = (i + 0.35) * (W / density) + rnd(i + 21) * 120 - 60;
      const s = 0.55 + rnd(i + 4) * 0.55;
      return (
        <Acacia key={i} x={x} y={y} s={s} fill={fill} sway={Math.sin(t * 0.5 + i) * 0.8} />
      );
    })}
  </g>
);

/* -------------------------------------------------------------- figures */
type Pose = "stand" | "walk" | "raise" | "mbira" | "child" | "pair";

export const Figure: React.FC<{
  x: number;
  y: number;
  s?: number;
  pose?: Pose;
  fill?: string;
  t?: number;
  flip?: boolean;
}> = ({ x, y, s = 1, pose = "stand", fill = "#050C12", t = 0, flip }) => {
  const bob = Math.sin(t * 1.2) * 1.2;
  const arm = pose === "raise" ? -155 + Math.sin(t * 0.8) * 4 : 0;
  return (
    <g transform={`translate(${x} ${y + bob}) scale(${flip ? -s : s} ${s})`}>
      {/* head */}
      <circle cx={0} cy={-126} r={13} fill={fill} />
      {/* neck + torso */}
      <path d="M -11,-112 L 11,-112 L 16,-62 L -16,-62 Z" fill={fill} />
      {/* legs */}
      {pose === "walk" ? (
        <>
          <path d="M -14,-64 L -30,-2 L -18,-2 L -6,-58 Z" fill={fill} />
          <path d="M 8,-62 L 16,0 L 28,-2 L 10,-64 Z" fill={fill} />
        </>
      ) : (
        <>
          <path d="M -15,-64 L -18,0 L -6,0 L -2,-60 Z" fill={fill} />
          <path d="M 2,-62 L 7,0 L 19,0 L 13,-64 Z" fill={fill} />
        </>
      )}
      {/* arms */}
      {pose === "raise" ? (
        <>
          <path d="M -12,-108 L -34,-162" stroke={fill} strokeWidth={9} strokeLinecap="round" />
          <path d="M 12,-108 L 34,-158" stroke={fill} strokeWidth={9} strokeLinecap="round" />
          <circle cx={-36} cy={-166} r={5.5} fill={fill} />
          <circle cx={36} cy={-162} r={5.5} fill={fill} />
        </>
      ) : pose === "mbira" ? (
        <>
          <path d="M -12,-108 L -26,-74 L -6,-70" stroke={fill} strokeWidth={8} fill="none" strokeLinecap="round" />
          <path d="M 12,-108 L 26,-76 L 6,-70" stroke={fill} strokeWidth={8} fill="none" strokeLinecap="round" />
          <rect x={-20} y={-78} width={40} height={16} rx={3} fill={fill} transform="rotate(-8 -0 -70)" />
        </>
      ) : (
        <>
          <path d={`M -12,-108 L -22,-72`} stroke={fill} strokeWidth={9} strokeLinecap="round" transform={`rotate(${arm} -12 -108)`} />
          <path d="M 12,-108 L 22,-70" stroke={fill} strokeWidth={9} strokeLinecap="round" />
        </>
      )}
      {/* ground contact shadow */}
      <ellipse cx={0} cy={4} rx={26} ry={4} fill="#000" opacity={0.25} />
    </g>
  );
};

/* ---------------------------------------------------------------- birds */
export const Birds: React.FC<{ t: number }> = ({ t }) => (
  <g opacity={0.55}>
    {new Array(9).fill(0).map((_, i) => {
      const sp = 26 + rnd(i) * 16;
      const x = ((t * sp + rnd(i + 5) * 2400) % 2500) - 200;
      const y = 150 + rnd(i + 2) * 260 + Math.sin(t * 0.9 + i) * 12;
      const sz = 0.7 + rnd(i + 8) * 0.8;
      const flap = Math.sin(t * 6 + i * 1.7);
      return (
        <g key={i} transform={`translate(${x} ${y}) scale(${sz})`}>
          <path
            d={`M -12,0 Q -6,${-6 * flap - 2} 0,0 Q 6,${-6 * flap - 2} 12,0`}
            stroke="#0A1420"
            strokeWidth={2.2}
            fill="none"
            strokeLinecap="round"
          />
        </g>
      );
    })}
  </g>
);

/* ------------------------------------------------------- paper + film FX */
export const FilmGrain: React.FC<{ frame: number; opacity?: number }> = ({ frame, opacity = 0.17 }) => {
  const ox = Math.floor(rnd(frame * 1.7) * 980);
  const oy = Math.floor(rnd(frame * 3.1 + 5) * 980);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "overlay", opacity }}>
      <Img
        src={staticFile("tex/grain.png")}
        style={{ position: "absolute", width: 2048, height: 2048, left: -ox, top: -oy }}
      />
    </AbsoluteFill>
  );
};

export const PaperTexture: React.FC<{ opacity?: number }> = ({ opacity = 0.14 }) => (
  <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "multiply", opacity }}>
    <Img
      src={staticFile("tex/paper.png")}
      style={{ position: "absolute", width: 2400, height: 1350, left: -240, top: -135 }}
    />
  </AbsoluteFill>
);

export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.82 }) => (
  <AbsoluteFill
    style={{
      pointerEvents: "none",
      background: `radial-gradient(120% 100% at 50% 46%, transparent 38%, rgba(4,6,12,${strength * 0.55}) 74%, rgba(3,5,10,${strength}) 100%)`,
    }}
  />
);

export const Dust: React.FC<{ t: number; count?: number }> = ({ t, count = 70 }) => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    {new Array(count).fill(0).map((_, i) => {
      const bx = rnd(i * 1.3) * W;
      const sp = 6 + rnd(i + 2) * 16;
      const y = H - ((t * sp + rnd(i + 4) * H * 1.4) % (H * 1.3));
      const x = bx + Math.sin(t * 0.35 + i) * 40;
      const r = 1 + rnd(i + 7) * 2.6;
      const a = (0.12 + rnd(i + 11) * 0.35) * (0.5 + 0.5 * Math.sin(t * 0.8 + i));
      return (
        <div
          key={i}
          style={{
            position: "absolute",
            left: x,
            top: y,
            width: r,
            height: r,
            borderRadius: r,
            background: P.cream,
            opacity: clamp(a, 0, 0.6),
            boxShadow: `0 0 ${r * 3}px ${P.amber}66`,
          }}
        />
      );
    })}
  </AbsoluteFill>
);

/** horizon glow that sits under the ridges */
export const HorizonGlow: React.FC<{ intensity: number }> = ({ intensity }) => (
  <div
    style={{
      position: "absolute",
      left: 0,
      right: 0,
      top: HORIZON - 220,
      height: 340,
      background: `linear-gradient(180deg, transparent, ${P.amber}${Math.round(
        clamp(intensity) * 90,
      )
        .toString(16)
        .padStart(2, "0")} 70%, ${P.ember}44 100%)`,
      filter: "blur(24px)",
    }}
  />
);
