import test from "node:test";
import assert from "node:assert/strict";
import {
  audioReactiveLightBoost,
  audioReactiveSceneScale,
  audioReactiveTypographyScale,
} from "../film/src/fur3d/audioCues.ts";

test("audio-reactive typography scale is subtle, deterministic, and bounded", () => {
  const quiet = { energy: 0, beatPulse: 0, transitionIntensity: 0 };
  const peak = { energy: 1, beatPulse: 1, transitionIntensity: 1 };
  assert.equal(audioReactiveTypographyScale(quiet), 1);
  assert.equal(audioReactiveTypographyScale(peak), 1.036);
  assert.equal(audioReactiveTypographyScale(peak), audioReactiveTypographyScale({ ...peak }));
  assert.ok(audioReactiveTypographyScale({ energy: Number.NaN, beatPulse: -1, transitionIntensity: 2 }) <= 1.012);
});

test("audio-reactive scene and lighting changes remain restrained", () => {
  const quiet = { energy: 0, beatPulse: 0, transitionIntensity: 0 };
  const peak = { energy: 1, beatPulse: 1, transitionIntensity: 1 };
  assert.equal(audioReactiveSceneScale(quiet), 1);
  assert.equal(audioReactiveSceneScale(peak), 1.014);
  assert.equal(audioReactiveLightBoost(quiet), 0);
  assert.equal(audioReactiveLightBoost(peak), 0.3);
  assert.ok(audioReactiveSceneScale({ energy: Number.NaN, beatPulse: -1, transitionIntensity: 2 }) <= 1.007);
});
