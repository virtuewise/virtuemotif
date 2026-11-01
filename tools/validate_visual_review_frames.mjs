#!/usr/bin/env node
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

export const VISUAL_REVIEW_FRAMES = {
  "furry-horizon-smoke.png": [1920, 1080],
  "furry-rise-smoke.png": [1920, 1080],
  "smart-fur-landscape.png": [1920, 1080],
  "smart-fur-4k.png": [3840, 2160],
  "smart-fur-portrait.png": [1080, 1920],
  "smart-fur-square.png": [1024, 1024],
  "auto-lyrics-landscape.png": [1920, 1080],
  "auto-lyrics-portrait.png": [1080, 1920],
  "auto-lyrics-square.png": [1024, 1024],
  "auto-lyrics-4k.png": [3840, 2160],
  "particle-rainfall-smoke.png": [1920, 1080],
  "glitch-distortion-smoke.png": [1920, 1080],
};

/** Read PNG dimensions from the signature and IHDR header without decoding image pixels. */
export function readPngDimensions(filePath) {
  const data = readFileSync(filePath);
  if (data.length < 24 || !data.subarray(0, 8).equals(PNG_SIGNATURE) || data.toString("ascii", 12, 16) !== "IHDR") {
    throw new Error(`Not a valid PNG header: ${filePath}`);
  }
  return [data.readUInt32BE(16), data.readUInt32BE(20)];
}

/** Fail CI if any visual-review capture is missing or has the wrong composition dimensions. */
export function validateVisualReviewFrames(directory) {
  const root = resolve(directory);
  const actual = {};
  for (const [name, expected] of Object.entries(VISUAL_REVIEW_FRAMES)) {
    const filePath = resolve(root, name);
    if (!existsSync(filePath)) throw new Error(`Missing visual review frame: ${filePath}`);
    const dimensions = readPngDimensions(filePath);
    if (dimensions[0] !== expected[0] || dimensions[1] !== expected[1]) {
      throw new Error(`Unexpected dimensions for ${name}: ${dimensions.join("x")}; expected ${expected.join("x")}`);
    }
    actual[name] = dimensions;
  }
  return actual;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const directory = process.argv[2] ?? "build/visual-review";
  const frames = validateVisualReviewFrames(directory);
  for (const [name, dimensions] of Object.entries(frames)) {
    process.stdout.write(`Validated ${name}: ${dimensions.join("x")}\n`);
  }
}
