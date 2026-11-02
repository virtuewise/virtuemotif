import * as THREE from "three";
import type { AudioCueFrame } from "./audioCues";

export type HorizonShot = "establishing" | "journey" | "memory" | "revelation" | "intimate";

export interface HorizonCameraPose {
  shot: HorizonShot;
  position: THREE.Vector3;
  target: THREE.Vector3;
  fov: number;
}

/**
 * Lyric- and music-directed camera blocking for The Horizon of Light.
 * The shot vocabulary is intentionally explicit and deterministic: a given
 * frame, lyric, section and cue frame always produces the same camera pose.
 * Replace/extend these authored beats as the final song storyboard is approved.
 */
const STORY_CUES: Record<Exclude<HorizonShot, "establishing">, readonly string[]> = {
  journey: ["walk", "journey", "travel", "road", "run", "famba", "hamba", "siyahamba", "uhambo"],
  memory: ["remember", "memory", "memories", "ancestor", "ancestors", "khumbula", "khumbulani", "nhoroondo"],
  revelation: ["hope", "light", "future", "morning", "rise", "freedom", "tariro", "chiedza", "ithemba", "ukukhanya"],
  intimate: ["heart", "love", "tears", "home", "family", "together", "rudo", "ikhaya", "umndeni"],
};

const tokens = (value: string) => new Set(
  value.normalize("NFKC").toLocaleLowerCase().split(/[^\p{L}\p{N}]+/u).filter(Boolean),
);

function hasAny(words: Set<string>, candidates: readonly string[]) {
  return candidates.some((candidate) => words.has(candidate));
}

export function directHorizonCamera(
  time: number,
  lyric: string,
  section: string,
  cue: AudioCueFrame,
  aspect: number,
): HorizonCameraPose {
  const words = tokens(`${lyric} ${section}`);
  const shot: HorizonShot = hasAny(words, STORY_CUES.revelation) || /chorus|outro|final/i.test(section)
    ? "revelation"
    : hasAny(words, STORY_CUES.journey)
      ? "journey"
      : hasAny(words, STORY_CUES.memory)
        ? "memory"
        : hasAny(words, STORY_CUES.intimate)
          ? "intimate"
          : "establishing";

  const energy = THREE.MathUtils.clamp(Number.isFinite(cue.energy) ? cue.energy : 0, 0, 1);
  const pulse = THREE.MathUtils.clamp(Number.isFinite(cue.beatPulse) ? cue.beatPulse : 0, 0, 1);
  const t = Math.max(0, Number.isFinite(time) ? time : 0);
  const portrait = aspect < 1;
  const sway = Math.sin(t * 0.17) * (0.035 + energy * 0.035);
  const breath = Math.sin(t * 0.31) * 0.018;
  const push = energy * 0.18 + pulse * 0.055;

  const presets: Record<HorizonShot, { x: number; y: number; z: number; tx: number; ty: number; tz: number; fov: number }> = {
    establishing: { x: 0, y: 0.12, z: 7.0, tx: 0, ty: -0.35, tz: -8.5, fov: 42 },
    journey: { x: -1.15, y: 0.18, z: 6.45, tx: 0.35, ty: -0.55, tz: -7.8, fov: 39 },
    memory: { x: 1.05, y: 0.48, z: 7.25, tx: 0.15, ty: -0.15, tz: -11.5, fov: 40 },
    revelation: { x: 0.15, y: 0.72, z: 6.15, tx: 0.45, ty: -0.35, tz: -12.2, fov: 37 },
    intimate: { x: 0.05, y: 0.05, z: 5.65, tx: 0, ty: -0.15, tz: -6.5, fov: 35 },
  };
  const preset = presets[shot];
  const portraitScale = portrait ? 0.72 : 1;
  const position = new THREE.Vector3(
    preset.x * portraitScale + sway,
    preset.y + breath + pulse * 0.025,
    preset.z - push,
  );
  const target = new THREE.Vector3(preset.tx, preset.ty, preset.tz);
  return { shot, position, target, fov: preset.fov + (portrait ? 2 : 0) - energy * 0.6 };
}
