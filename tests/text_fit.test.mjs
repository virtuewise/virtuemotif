import test from "node:test";
import assert from "node:assert/strict";
import { combineTextFitAndMotionScale } from "../film/src/fur3d/textFit.ts";

test("motion scale preserves the base geometry fit scale", () => {
  assert.equal(combineTextFitAndMotionScale(0.72, 1), 0.72);
  assert.ok(Math.abs(combineTextFitAndMotionScale(0.72, 1.065) - 0.7668) < 1e-12);
  assert.equal(combineTextFitAndMotionScale(1, 1.065), 1.065);
});

test("text fit scale remains bounded and fails closed for invalid values", () => {
  assert.equal(combineTextFitAndMotionScale(1.5, 2), 1.1);
  assert.equal(combineTextFitAndMotionScale(Number.NaN, 1), 0);
  assert.equal(combineTextFitAndMotionScale(0.8, Number.POSITIVE_INFINITY), 0);
  assert.equal(combineTextFitAndMotionScale(-1, 1), 0);
});
