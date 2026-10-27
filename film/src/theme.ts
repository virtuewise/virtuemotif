export const PALETTE = {
  night: "#070C18",
  deep: "#0B1226",
  tealDark: "#0E2A33",
  teal: "#134A4E",
  tealLight: "#2C7A74",
  ochre: "#E8A33D",
  amber: "#F2B24A",
  ember: "#E0662B",
  rust: "#B4402A",
  clay: "#8C2F23",
  cream: "#F6E7C8",
  bone: "#FFF6E3",
  ink: "#2A140F",
  dusk: "#6E3A2A",
} as const;

export const FONT_DISPLAY = "'Anton', 'Arial Narrow', sans-serif";
export const FONT_SERIF = "'Instrument Serif', Georgia, serif";
export const FONT_MONO = "'Space Grotesk', 'Segoe UI', sans-serif";

export const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const smooth = (t: number) => t * t * (3 - 2 * t);
export const easeInOut = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
export const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);
export const easeIn = (t: number) => t * t * t;

/** deterministic pseudo random in [0,1) */
export const rnd = (seed: number) => {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

/** smooth 1-D value noise, deterministic */
export const noise1 = (x: number, seed = 0) => {
  const i = Math.floor(x);
  const f = x - i;
  const a = rnd(i + seed * 57.3);
  const b = rnd(i + 1 + seed * 57.3);
  return lerp(a, b, smooth(f));
};

export type Rgb = [number, number, number];
export const hexToRgb = (hex: string): Rgb => {
  const h = hex.replace("#", "");
  return [
    parseInt(h.slice(0, 2), 16),
    parseInt(h.slice(2, 4), 16),
    parseInt(h.slice(4, 6), 16),
  ];
};
export const mix = (a: string, b: string, t: number) => {
  const A = hexToRgb(a);
  const B = hexToRgb(b);
  const c = A.map((v, i) => Math.round(lerp(v, B[i], clamp(t))));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
};
