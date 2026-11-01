import test from "node:test";
import assert from "node:assert/strict";
import {
  calculateLyricFontSize,
  estimateLyricWidthUnits,
  resolveWordTimings,
} from "../film/src/typography.ts";

test("long lyrics shrink while short lyrics retain the configured design size", () => {
  const short = calculateLyricFontSize("Vuka!", 1920, 1080, 104);
  const long = calculateLyricFontSize(
    "Where the red soil remembers the strength of the past and carries us forward",
    1920,
    1080,
    104,
  );
  assert.equal(short, 104);
  assert.ok(long < short);
  assert.ok(long >= 18);
});

test("font sizing scales with the composition resolution", () => {
  const fullHd = calculateLyricFontSize("Horizon of Light", 1920, 1080, 104);
  const fourK = calculateLyricFontSize("Horizon of Light", 3840, 2160, 104);
  const portrait = calculateLyricFontSize("Horizon of Light", 1080, 1920, 104);
  const square = calculateLyricFontSize("Horizon of Light", 1024, 1024, 104);
  assert.equal(fourK, fullHd * 2);
  assert.ok(portrait > 0 && portrait <= 84);
  assert.ok(square > 0 && square <= 104);
});

test("width estimates account for CJK glyphs, spaces, and empty input", () => {
  assert.equal(estimateLyricWidthUnits(""), 0);
  assert.ok(estimateLyricWidthUnits("你好世界") > estimateLyricWidthUnits("abcd"));
  assert.ok(estimateLyricWidthUnits("one two") > estimateLyricWidthUnits("onetwo"));
});

test("word timings are accepted only when token text and chronology align", () => {
  const valid = [
    { w: "Hello,", from: 0.1, to: 0.4 },
    { w: "world!", from: 0.5, to: 0.9 },
  ];
  assert.deepEqual(resolveWordTimings("Hello, world!", valid), [0.1, 0.5]);
  assert.equal(resolveWordTimings("Hello, world!", [{ ...valid[0], w: "Wrong" }, valid[1]]), null);
  assert.equal(resolveWordTimings("Hello, world!", [valid[1], valid[0]]), null);
  assert.equal(resolveWordTimings("Hello, world!", [{ ...valid[0], from: Number.NaN }, valid[1]]), null);
  assert.equal(resolveWordTimings("Hello, world!", [valid[0]]), null);
});
