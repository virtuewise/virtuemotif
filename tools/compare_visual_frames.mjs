#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { readPngDimensions } from "./validate_visual_review_frames.mjs";

export const COMPARABLE_VISUAL_FRAMES = {
  "smart-fur-landscape.png": [1920, 1080],
  "smart-fur-4k.png": [3840, 2160],
  "smart-fur-portrait.png": [1080, 1920],
  "smart-fur-square.png": [1024, 1024],
};

/** Compare RGBA buffers and report changed pixels plus mean channel error. */
export function comparePixelBuffers(expected, actual, channelThreshold = 8) {
  if (expected.length !== actual.length || expected.length % 4 !== 0) {
    throw new Error("RGBA buffers must have the same length divisible by four");
  }
  if (!Number.isFinite(channelThreshold) || channelThreshold < 0 || channelThreshold > 255) {
    throw new Error("channelThreshold must be between 0 and 255");
  }

  let changedPixels = 0;
  let absoluteError = 0;
  const totalPixels = expected.length / 4;
  for (let offset = 0; offset < expected.length; offset += 4) {
    let maxChannelDelta = 0;
    for (let channel = 0; channel < 4; channel += 1) {
      const delta = Math.abs(expected[offset + channel] - actual[offset + channel]);
      absoluteError += delta;
      maxChannelDelta = Math.max(maxChannelDelta, delta);
    }
    if (maxChannelDelta > channelThreshold) changedPixels += 1;
  }
  return {
    totalPixels,
    changedPixels,
    changedPixelRatio: totalPixels === 0 ? 0 : changedPixels / totalPixels,
    meanAbsoluteError: expected.length === 0 ? 0 : absoluteError / expected.length,
  };
}

/** Decode a PNG to raw RGBA with the repository's FFmpeg runtime dependency. */
export function decodePngToRgba(filePath) {
  return execFileSync(
    "ffmpeg",
    ["-v", "error", "-i", filePath, "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
    { maxBuffer: 512 * 1024 * 1024 },
  );
}

/**
 * Compare generated frames against an explicitly approved reference directory.
 * The caller must supply the baseline; this tool never creates or approves one.
 */
export function compareVisualFrames(referenceDirectory, actualDirectory, options = {}) {
  const referenceRoot = resolve(referenceDirectory);
  const actualRoot = resolve(actualDirectory);
  const channelThreshold = options.channelThreshold ?? 8;
  const maxChangedPixelRatio = options.maxChangedPixelRatio ?? 0.01;
  if (!Number.isFinite(maxChangedPixelRatio) || maxChangedPixelRatio < 0 || maxChangedPixelRatio > 1) {
    throw new Error("maxChangedPixelRatio must be between 0 and 1");
  }

  const results = {};
  for (const [name, expectedDimensions] of Object.entries(COMPARABLE_VISUAL_FRAMES)) {
    const referencePath = resolve(referenceRoot, name);
    const actualPath = resolve(actualRoot, name);
    if (!existsSync(referencePath)) throw new Error(`Missing approved reference frame: ${referencePath}`);
    if (!existsSync(actualPath)) throw new Error(`Missing actual review frame: ${actualPath}`);

    const referenceDimensions = readPngDimensions(referencePath);
    const actualDimensions = readPngDimensions(actualPath);
    if (
      referenceDimensions[0] !== expectedDimensions[0] ||
      referenceDimensions[1] !== expectedDimensions[1] ||
      actualDimensions[0] !== expectedDimensions[0] ||
      actualDimensions[1] !== expectedDimensions[1]
    ) {
      throw new Error(`Frame dimensions do not match the approved contract for ${name}`);
    }

    const expectedPixels = decodePngToRgba(referencePath);
    const actualPixels = decodePngToRgba(actualPath);
    const metrics = comparePixelBuffers(expectedPixels, actualPixels, channelThreshold);
    results[name] = { ...metrics, passed: metrics.changedPixelRatio <= maxChangedPixelRatio };
  }
  return results;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [referenceDirectory, actualDirectory, ratioArgument] = process.argv.slice(2);
  if (!referenceDirectory || !actualDirectory) {
    process.stderr.write(
      "Usage: node tools/compare_visual_frames.mjs <approved-reference-dir> <actual-frame-dir> [max-changed-pixel-ratio]\n",
    );
    process.exitCode = 2;
  } else {
    const maxChangedPixelRatio = ratioArgument === undefined ? 0.01 : Number(ratioArgument);
    const results = compareVisualFrames(referenceDirectory, actualDirectory, { maxChangedPixelRatio });
    process.stdout.write(`${JSON.stringify(results, null, 2)}\n`);
    if (Object.values(results).some((result) => !result.passed)) process.exitCode = 1;
  }
}
