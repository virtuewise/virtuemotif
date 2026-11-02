import * as THREE from "three";

export type HorizonStoryBeat = "idle" | "walk" | "turn" | "look_to_horizon";
export interface HorizonCharacterPerformance {
  root: THREE.Object3D;
  update: (time: number, lyric: string, section: string, energy: number) => void;
  dispose: () => void;
}

const TOKENS = {
  walk: ["walk", "journey", "travel", "run", "siyahamba", "hamba", "famba", "เดิน"],
  turn: ["turn", "look", "remember", "remembering", "khumbula", "khumbulani"],
  hope: ["hope", "light", "future", "morning", "rise", "tariro", "chiedza", "ithemba", "ukukhanya"],
};

function hasToken(text: string, values: readonly string[]): boolean {
  const words = new Set(text.normalize("NFKC").toLocaleLowerCase().split(/[^\p{L}\p{N}]+/u).filter(Boolean));
  return values.some((value) => words.has(value));
}

/**
 * Deterministic story-performance adapter for an artist-authored, skinned GLB.
 * It consumes named clips and facial morph targets; it never synthesizes a
 * placeholder body or substitutes missing animation with random motion.
 */
export function createHorizonCharacterPerformance(
  root: THREE.Object3D,
  clips: THREE.AnimationClip[],
): HorizonCharacterPerformance {
  const mixer = new THREE.AnimationMixer(root);
  const clipByName = new Map(clips.map((clip) => [clip.name.toLowerCase().replace(/[\s-]+/g, "_"), clip]));
  const required: HorizonStoryBeat[] = ["idle", "walk", "turn", "look_to_horizon"];
  const missing = required.filter((name) => !clipByName.has(name));
  if (missing.length) {
    throw new Error(`Horizon protagonist is missing authored clips: ${missing.join(", ")}`);
  }
  const actions = new Map<HorizonStoryBeat, THREE.AnimationAction>();
  for (const name of required) {
    const action = mixer.clipAction(clipByName.get(name)!);
    action.reset();
    action.enabled = true;
    action.setLoop(THREE.LoopRepeat, Infinity);
    action.play();
    action.setEffectiveWeight(0);
    actions.set(name, action);
  }

  const morphTargets: Array<{ influences: number[]; index: number; name: string }> = [];
  root.traverse((object) => {
    if (!(object instanceof THREE.Mesh) || !object.morphTargetInfluences || !object.morphTargetDictionary) return;
    for (const [name, index] of Object.entries(object.morphTargetDictionary)) {
      morphTargets.push({ influences: object.morphTargetInfluences, index, name: name.toLowerCase() });
    }
  });

  let active: HorizonStoryBeat = "idle";
  const update = (time: number, lyric: string, section: string, energy: number) => {
    const normalized = `${lyric} ${section}`.normalize("NFKC").toLocaleLowerCase();
    const next: HorizonStoryBeat = hasToken(normalized, TOKENS.walk)
      ? "walk"
      : hasToken(normalized, TOKENS.turn)
        ? "turn"
        : hasToken(normalized, TOKENS.hope) || /chorus|outro|final/.test(normalized)
          ? "look_to_horizon"
          : "idle";
    if (next !== active) {
      actions.get(active)?.setEffectiveWeight(0);
      active = next;
      actions.get(active)?.setEffectiveWeight(1);
    }
    for (const [name, action] of actions) action.setEffectiveWeight(name === active ? 1 : 0);
    // setTime is absolute and frame-seekable; renders do not depend on update order.
    mixer.setTime(Math.max(0, Number.isFinite(time) ? time : 0));

    const intensity = THREE.MathUtils.clamp(Number.isFinite(energy) ? energy : 0, 0, 1);
    for (const target of morphTargets) {
      const key = target.name.replace(/[^a-z]/g, "");
      let value = 0;
      if (/smile|happy|joy/.test(key)) value = active === "look_to_horizon" ? 0.16 + intensity * 0.12 : 0.025;
      else if (/blink/.test(key)) value = 0;
      else if (/brow|surprise|wonder/.test(key)) value = active === "turn" ? 0.12 : 0.025;
      else if (/mouthopen|jawopen/.test(key)) value = intensity * 0.08;
      target.influences[target.index] = value;
    }
  };

  return {
    root,
    update,
    dispose: () => {
      mixer.stopAllAction();
      mixer.uncacheRoot(root);
    },
  };
}
