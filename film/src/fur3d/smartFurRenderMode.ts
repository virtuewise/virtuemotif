export interface SmartFurRenderAction {
  fogDensity: number;
  beatSensitivity: number;
}

export const DEFAULT_SMART_FUR_RENDER_ACTION: SmartFurRenderAction = Object.freeze({
  fogDensity: 0.35,
  beatSensitivity: 1.5,
});

/**
 * Keep production renders independent of browser storage and exploration.
 * Learned settings are honored only when an interactive preview explicitly opts in.
 */
export function resolveSmartFurRenderAction(
  adaptivePreview: boolean,
  learnedAction?: Partial<SmartFurRenderAction> | null,
): SmartFurRenderAction {
  if (
    !adaptivePreview ||
    !learnedAction ||
    !Number.isFinite(learnedAction.fogDensity) ||
    learnedAction.fogDensity! < 0 ||
    learnedAction.fogDensity! > 1 ||
    !Number.isFinite(learnedAction.beatSensitivity) ||
    learnedAction.beatSensitivity! <= 0 ||
    learnedAction.beatSensitivity! > 4
  ) {
    return { ...DEFAULT_SMART_FUR_RENDER_ACTION };
  }

  return {
    fogDensity: learnedAction.fogDensity!,
    beatSensitivity: learnedAction.beatSensitivity!,
  };
}
