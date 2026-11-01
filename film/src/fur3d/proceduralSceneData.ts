/** Deterministic geometry inputs for procedural scene layouts. */
export interface CityBuildingSpec {
  x: number;
  width: number;
  depth: number;
  height: number;
}

const seededUnit = (seed: number): number => {
  const value = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return value - Math.floor(value);
};

/**
 * Create repeatable city-building dimensions and positions for Remotion renders.
 * The same count and seed always produce the same ordered geometry.
 */
export function createCityBuildingSpecs(count = 12, seed = 1): CityBuildingSpec[] {
  if (!Number.isInteger(count) || count < 0) {
    throw new RangeError("count must be a non-negative integer");
  }
  if (!Number.isFinite(seed)) {
    throw new RangeError("seed must be finite");
  }

  return Array.from({ length: count }, (_, index) => {
    const offset = seed + index * 4;
    return {
      x: count <= 1 ? 0 : -5 + index * (10 / (count - 1)),
      width: 0.8 + seededUnit(offset) * 0.4,
      depth: 0.8 + seededUnit(offset + 1) * 0.4,
      height: 1.5 + seededUnit(offset + 2) * 3,
    };
  });
}
