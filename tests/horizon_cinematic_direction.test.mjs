import test from "node:test";
import assert from "node:assert/strict";
import { directHorizonCamera } from "../film/src/fur3d/HorizonCinematicDirection.ts";

const cue = { time: 12, energy: 0.6, beatPulse: 0.8, transitionIntensity: 0.2 };

test("camera direction is deterministic for the same Remotion frame inputs", () => {
  const a = directHorizonCamera(12, "We walk toward the light", "Verse", cue, 16 / 9);
  const b = directHorizonCamera(12, "We walk toward the light", "Verse", cue, 16 / 9);
  assert.equal(a.shot, "journey");
  assert.deepEqual(a.position.toArray(), b.position.toArray());
  assert.deepEqual(a.target.toArray(), b.target.toArray());
  assert.equal(a.fov, b.fov);
});

test("chorus and multilingual hope cues stage a revelation shot", () => {
  assert.equal(directHorizonCamera(24, "Tariro nechiedza", "Chorus", cue, 16 / 9).shot, "revelation");
  assert.equal(directHorizonCamera(24, "ukukhanya", "Verse", cue, 16 / 9).shot, "revelation");
});

test("portrait direction narrows the composition without changing the story beat", () => {
  const landscape = directHorizonCamera(8, "I remember our home", "Verse", cue, 16 / 9);
  const portrait = directHorizonCamera(8, "I remember our home", "Verse", cue, 9 / 16);
  assert.equal(landscape.shot, "memory");
  assert.equal(portrait.shot, "memory");
  assert.ok(Math.abs(portrait.position.x) <= Math.abs(landscape.position.x));
  assert.ok(portrait.fov > landscape.fov);
});
