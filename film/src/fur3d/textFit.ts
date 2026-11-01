/** Pure scale composition used by deterministic 3D text motion. */
export function combineTextFitAndMotionScale(fitScale: number, motionScale: number): number {
  if (!Number.isFinite(fitScale) || fitScale <= 0 ||
      !Number.isFinite(motionScale) || motionScale <= 0) return 0;
  // Fit is never enlarged beyond the computed safe geometry scale; motion remains subtle.
  return Math.min(1, fitScale) * Math.min(1.1, motionScale);
}
