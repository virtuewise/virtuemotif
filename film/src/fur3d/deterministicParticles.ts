import { rnd } from "../theme";

export interface RainfallParticleData {
  positions: Float32Array;
  speeds: Float32Array;
}

/**
 * Build a stable particle field for repeatable Remotion renders.
 * The same count and seed always produce identical positions and speeds.
 */
export function createRainfallParticleData(
  particleCount = 2000,
  seed = 1,
): RainfallParticleData {
  if (!Number.isInteger(particleCount) || particleCount < 0) {
    throw new RangeError("particleCount must be a non-negative integer");
  }
  if (!Number.isFinite(seed)) {
    throw new RangeError("seed must be finite");
  }

  const positions = new Float32Array(particleCount * 3);
  const speeds = new Float32Array(particleCount);
  for (let i = 0; i < particleCount; i += 1) {
    const offset = seed + i * 4;
    positions[i * 3] = (rnd(offset) - 0.5) * 12;
    positions[i * 3 + 1] = rnd(offset + 1) * 6 + 2;
    positions[i * 3 + 2] = (rnd(offset + 2) - 0.5) * 12;
    speeds[i] = 0.02 + rnd(offset + 3) * 0.03;
  }
  return { positions, speeds };
}
