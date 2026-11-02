import test from "node:test";
import assert from "node:assert/strict";
import * as THREE from "three";
import { createHorizonCharacterPerformance } from "../film/src/fur3d/HorizonCharacterPerformance.ts";

function clips() {
  return [
    new THREE.AnimationClip("idle", 1, [new THREE.VectorKeyframeTrack(".position", [0, 1], [0, 0, 0, 0, 0.1, 0])]),
    new THREE.AnimationClip("walk", 1, [new THREE.VectorKeyframeTrack(".position", [0, 1], [0, 0, 0, 0, 0, 1])]),
    new THREE.AnimationClip("turn", 1, [new THREE.VectorKeyframeTrack(".rotation[y]", [0, 1], [0, 1])]),
    new THREE.AnimationClip("look_to_horizon", 1, [new THREE.VectorKeyframeTrack(".rotation[x]", [0, 1], [0, 0.2])]),
  ];
}

test("character performance requires authored story clips", () => {
  const root = new THREE.Group();
  assert.throws(
    () => createHorizonCharacterPerformance(root, [clips()[0]]),
    /missing authored clips: walk, turn, look_to_horizon/,
  );
});

test("character performance is frame-seekable and responds to story cues", () => {
  const root = new THREE.Group();
  const performance = createHorizonCharacterPerformance(root, clips());
  performance.update(0.5, "We walk into the morning", "Verse", 0.7);
  const first = root.position.toArray();
  performance.update(0.5, "We walk into the morning", "Verse", 0.7);
  assert.deepEqual(root.position.toArray(), first);
  performance.update(0.5, "I remember the road", "Verse", 0.3);
  assert.ok(Number.isFinite(root.rotation.y));
  performance.update(0.5, "A light for the future", "Chorus", 0.9);
  assert.ok(Number.isFinite(root.rotation.x));
  performance.dispose();
});
