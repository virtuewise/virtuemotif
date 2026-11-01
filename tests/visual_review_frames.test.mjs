import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  readPngDimensions,
  validateVisualReviewFrames,
  VISUAL_REVIEW_FRAMES,
} from "../tools/validate_visual_review_frames.mjs";

const makePngHeader = (width, height) => {
  const header = Buffer.alloc(24);
  Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]).copy(header, 0);
  header.write("IHDR", 12, "ascii");
  header.writeUInt32BE(width, 16);
  header.writeUInt32BE(height, 20);
  return header;
};

test("PNG dimension reader validates signature and IHDR", () => {
  const directory = mkdtempSync(join(tmpdir(), "virtuemotif-png-"));
  try {
    const validPath = join(directory, "valid.png");
    writeFileSync(validPath, makePngHeader(1920, 1080));
    assert.deepEqual(readPngDimensions(validPath), [1920, 1080]);
    const invalidPath = join(directory, "invalid.png");
    writeFileSync(invalidPath, Buffer.alloc(24));
    assert.throws(() => readPngDimensions(invalidPath), /Not a valid PNG header/);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("visual review validation requires every expected composition dimension", () => {
  const directory = mkdtempSync(join(tmpdir(), "virtuemotif-review-"));
  try {
    for (const [name, [width, height]] of Object.entries(VISUAL_REVIEW_FRAMES)) {
      writeFileSync(join(directory, name), makePngHeader(width, height));
    }
    const validated = validateVisualReviewFrames(directory);
    assert.equal(Object.keys(validated).length, Object.keys(VISUAL_REVIEW_FRAMES).length);
    assert.deepEqual(validated["smart-fur-4k.png"], [3840, 2160]);
    assert.deepEqual(validated["auto-lyrics-portrait.png"], [1080, 1920]);
    assert.deepEqual(validated["auto-lyrics-square.png"], [1024, 1024]);
    assert.deepEqual(validated["auto-lyrics-4k.png"], [3840, 2160]);

    writeFileSync(join(directory, "smart-fur-square.png"), makePngHeader(1920, 1080));
    assert.throws(() => validateVisualReviewFrames(directory), /Unexpected dimensions.*smart-fur-square/);
    rmSync(join(directory, "smart-fur-4k.png"));
    assert.throws(() => validateVisualReviewFrames(directory), /Missing visual review frame/);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
