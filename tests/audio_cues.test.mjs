import test from "node:test";
import assert from "node:assert/strict";
import { evaluateAudioCues, frameToTime, parseAudioIntelligence, snapEntranceTime } from "../film/src/fur3d/audioCues.ts";

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
