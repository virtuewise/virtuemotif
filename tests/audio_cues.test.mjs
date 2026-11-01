import test from "node:test";
import assert from "node:assert/strict";
import {
  audioReactiveGlitchIntensity,
  audioReactiveParticleFallRate,
  audioReactiveWaveAmplitude,
  evaluateAudioCues,
  frameToTime,
  parseAudioIntelligence,
  snapEntranceTime,
} from "../film/src/fur3d/audioCues.ts";
import { createRainfallParticleData } from "../film/src/fur3d/deterministicParticles.ts";

const valid = {
  schema_version: 1,
  duration: 4,
  sample_rate: 16000,
  tempo: { bpm: 120, confidence: 0.8 },
  beats: [0, 0.5, 1, 1.5, 2],
  downbeats: [0, 2],
  energy_curve: [{ time: 0, rms: 0.2 }, { time: 2, rms: 0.8 }, { time: 4, rms: 0.4 }],
  events: [{ time: 1, type: "energy-rise", strength: 0.9 }],
};

test("validates schema version and malformed cue data", () => {
  assert.equal(parseAudioIntelligence(valid)?.schema_version, 1);
  assert.equal(parseAudioIntelligence({ ...valid, schema_version: 2 }), null);
  assert.equal(parseAudioIntelligence({ ...valid, beats: [1, 0] }), null);
  assert.equal(parseAudioIntelligence({ ...valid, beats: [4.1] }), null);
  assert.equal(parseAudioIntelligence({ ...valid, events: [{ time: -1, type: "onset", strength: 1 }] }), null);
  assert.equal(parseAudioIntelligence({ ...valid, tempo: { bpm: 120, confidence: 1.1 } }), null);
  assert.equal(parseAudioIntelligence({ ...valid, energy_curve: [{ time: 0, rms: 1.1 }] }), null);
  assert.equal(parseAudioIntelligence({ ...valid, events: [{ time: 1, type: "onset", strength: 1.1 }] }), null);
});

test("frame-to-time conversion is zero-based and clamps duration", () => {
  assert.equal(frameToTime(0, 30, 4), 0);
  assert.equal(frameToTime(45, 30, 4), 1.5);
  assert.equal(frameToTime(999, 30, 4), 4);
  assert.equal(frameToTime(10, 0, 4), 0);
});

test("entrance timing snaps only inside the configured tolerance", () => {
  assert.equal(snapEntranceTime(1.08, valid.beats), 1);
  assert.equal(snapEntranceTime(1.24, valid.beats), 1.24);
  assert.equal(snapEntranceTime(1.08, []), 1.08);
});

test("real cues drive beat pulse, energy interpolation and event intensity", () => {
  const cues = parseAudioIntelligence(valid);
  assert.ok(cues);
  const atBeat = evaluateAudioCues(30, 30, cues);
  assert.equal(atBeat.beatPulse, 1);
  assert.equal(atBeat.hasAudioCues, true);
  assert.ok(atBeat.transitionIntensity > 0.7);
  assert.equal(evaluateAudioCues(60, 30, cues).energy, 0.8);
});

test("missing or invalid cue data uses deterministic fallback", () => {
  const missing = evaluateAudioCues(15, 30, null);
  assert.equal(missing.hasAudioCues, false);
  assert.deepEqual(evaluateAudioCues(15, 30, undefined), missing);
  assert.equal(missing.time, 0.5);
  assert.notEqual(evaluateAudioCues(0, 30, null).beatPulse, missing.beatPulse);
  assert.equal(parseAudioIntelligence(null), null);
});

test("audio-reactive wave amplitude responds deterministically to beat and energy cues", () => {
  const quiet = audioReactiveWaveAmplitude({ energy: 0, beatPulse: 0, transitionIntensity: 0 });
  const energetic = audioReactiveWaveAmplitude({ energy: 0.8, beatPulse: 1, transitionIntensity: 0.9 });
  assert.equal(quiet, 0.025);
  assert.ok(energetic > quiet);
  assert.ok(energetic <= 0.3);
  assert.equal(
    audioReactiveWaveAmplitude({ energy: 0.8, beatPulse: 1, transitionIntensity: 0.9 }),
    energetic,
  );
  assert.ok(Math.abs(audioReactiveWaveAmplitude({ energy: Number.NaN, beatPulse: -1, transitionIntensity: 2 }) - 0.105) < 1e-12);
});

test("glitch intensity is bounded and reacts to beats and transitions", () => {
  assert.equal(audioReactiveGlitchIntensity({ energy: 0, beatPulse: 0, transitionIntensity: 0 }), 0);
  assert.ok(audioReactiveGlitchIntensity({ energy: 0.1, beatPulse: 1, transitionIntensity: 0 }) >
    audioReactiveGlitchIntensity({ energy: 0.1, beatPulse: 0, transitionIntensity: 0 }));
  assert.equal(audioReactiveGlitchIntensity({ energy: 1, beatPulse: 1, transitionIntensity: 1 }), 1);
  assert.equal(audioReactiveGlitchIntensity({ energy: Number.NaN, beatPulse: -1, transitionIntensity: 2 }), 0.45);
});

test("particle fall rate is deterministic and responds to audio energy and beats", () => {
  const quiet = audioReactiveParticleFallRate({ energy: 0, beatPulse: 0 });
  const energetic = audioReactiveParticleFallRate({ energy: 1, beatPulse: 1 });
  assert.equal(quiet, 0.8);
  assert.equal(energetic, 1.4);
  assert.equal(audioReactiveParticleFallRate({ energy: Number.NaN, beatPulse: -1 }), 0.8);
});

test("rainfall particle fields are reproducible for the same seed", () => {
  const first = createRainfallParticleData(128, 7);
  const second = createRainfallParticleData(128, 7);
  assert.deepEqual(first.positions, second.positions);
  assert.deepEqual(first.speeds, second.speeds);
  assert.notDeepEqual(first.positions, createRainfallParticleData(128, 8).positions);
  assert.equal(first.positions.length, 128 * 3);
  assert.equal(first.speeds.length, 128);
  assert.ok(first.positions.every(Number.isFinite));
  assert.ok(first.speeds.every((speed) => speed >= 0.02 && speed < 0.05));
});

test("rainfall particle generator validates size and seed", () => {
  assert.throws(() => createRainfallParticleData(-1), /non-negative integer/);
  assert.throws(() => createRainfallParticleData(1.5), /non-negative integer/);
  assert.throws(() => createRainfallParticleData(1, Number.NaN), /seed must be finite/);
});
