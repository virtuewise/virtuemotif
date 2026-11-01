import test from "node:test";
import assert from "node:assert/strict";
import {
  COMPARABLE_VISUAL_FRAMES,
  comparePixelBuffers,
} from "../tools/compare_visual_frames.mjs";
import { VISUAL_REVIEW_FRAMES } from "../tools/validate_visual_review_frames.mjs";

test("visual comparator covers every required CI review capture", () => {
  assert.deepEqual(COMPARABLE_VISUAL_FRAMES, VISUAL_REVIEW_FRAMES);
  assert.equal(Object.keys(COMPARABLE_VISUAL_FRAMES).length, 12);
});

test("identical RGBA frames have zero changed pixels and zero channel error", () => {
  const frame = Buffer.from([10, 20, 30, 255, 40, 50, 60, 255]);
  assert.deepEqual(comparePixelBuffers(frame, Buffer.from(frame)), {
    totalPixels: 2,
    changedPixels: 0,
    changedPixelRatio: 0,
    meanAbsoluteError: 0,
  });
});

test("pixel diff applies channel tolerance and reports measurable regression", () => {
  const expected = Buffer.from([10, 20, 30, 255, 40, 50, 60, 255]);
  const actual = Buffer.from([30, 20, 30, 255, 40, 55, 60, 255]);
  const result = comparePixelBuffers(expected, actual, 8);
  assert.equal(result.totalPixels, 2);
  assert.equal(result.changedPixels, 1);
  assert.equal(result.changedPixelRatio, 0.5);
  assert.equal(result.meanAbsoluteError, 25 / 8);
});

test("pixel diff rejects incompatible buffers and invalid tolerances", () => {
  assert.throws(() => comparePixelBuffers(Buffer.from([0, 0, 0, 255]), Buffer.alloc(8)), /same length/);
  assert.throws(() => comparePixelBuffers(Buffer.alloc(3), Buffer.alloc(3)), /divisible by four/);
  assert.throws(() => comparePixelBuffers(Buffer.alloc(4), Buffer.alloc(4), 300), /between 0 and 255/);
});
