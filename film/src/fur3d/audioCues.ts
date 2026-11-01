/** Versioned audio-intelligence contract and deterministic frame-time evaluators. */
export type AudioEventType = "onset" | "energy-rise" | "energy-drop";

export interface AudioEventCue {
  time: number;
  type: AudioEventType;
  strength: number;
}

export interface EnergyPoint {
  time: number;
  rms: number;
}

export interface AudioIntelligence {
  schema_version: 1;
  duration: number;
  sample_rate: number;
  tempo: { bpm: number | null; confidence: number };
  beats: number[];
  downbeats: number[];
  energy_curve: EnergyPoint[];
  events: AudioEventCue[];
}

export interface AudioCueFrame {
  time: number;
  beatPulse: number;
  energy: number;
  transitionIntensity: number;
  hasAudioCues: boolean;
}

const isFiniteNumber = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value);

function isSortedTimes(values: unknown): values is number[] {
  return Array.isArray(values) && values.every(
    (value, index) => isFiniteNumber(value) && value >= 0 && (index === 0 || value >= values[index - 1]),
  );
}

/** Reject incompatible or malformed cue files rather than producing nondeterministic renders. */
export function parseAudioIntelligence(value: unknown): AudioIntelligence | null {
  if (!value || typeof value !== "object") return null;
  const data = value as Partial<AudioIntelligence>;
  if (
    data.schema_version !== 1 ||
    !isFiniteNumber(data.duration) || data.duration <= 0 ||
    !isFiniteNumber(data.sample_rate) || data.sample_rate <= 0 ||
    !data.tempo || !(data.tempo.bpm === null || (isFiniteNumber(data.tempo.bpm) && data.tempo.bpm > 0)) ||
    !isFiniteNumber(data.tempo.confidence) || data.tempo.confidence < 0 || data.tempo.confidence > 1 ||
    !isSortedTimes(data.beats) ||
    !isSortedTimes(data.downbeats) ||
    !Array.isArray(data.energy_curve) ||
    !data.energy_curve.every((point) => point && isFiniteNumber(point.time) && point.time >= 0 && isFiniteNumber(point.rms) && point.rms >= 0 && point.rms <= 1) ||
    !Array.isArray(data.events) ||
    !data.events.every((event) => event && isFiniteNumber(event.time) && event.time >= 0 &&
      (event.type === "onset" || event.type === "energy-rise" || event.type === "energy-drop") &&
      isFiniteNumber(event.strength) && event.strength >= 0 && event.strength <= 1)
  ) return null;

  const duration = data.duration;
  if (!isFiniteNumber(duration)) return null;
  if (
    data.beats.some((time) => time > duration) ||
    data.downbeats.some((time) => time > duration) ||
    data.energy_curve.some((point, index) => point.time > duration ||
      (index > 0 && point.time < data.energy_curve![index - 1].time)) ||
    data.events.some((event, index) => event.time > duration ||
      (index > 0 && event.time < data.events![index - 1].time))
  ) return null;

  return data as AudioIntelligence;
}

/** Remotion frame numbers are zero-based; clamp time to the cue's supported interval. */
export function frameToTime(frame: number, fps: number, duration: number): number {
  if (!isFiniteNumber(frame) || !isFiniteNumber(fps) || fps <= 0 || !isFiniteNumber(duration) || duration < 0) return 0;
  return Math.min(duration, Math.max(0, frame / fps));
}

function nearestBeatDistance(time: number, beats: number[]): number {
  if (beats.length === 0) return Number.POSITIVE_INFINITY;
  let low = 0;
  let high = beats.length - 1;
  while (low < high) {
    const mid = Math.floor((low + high) / 2);
    if (beats[mid] < time) low = mid + 1;
    else high = mid;
  }
  const after = Math.abs(beats[low] - time);
  const before = low > 0 ? Math.abs(beats[low - 1] - time) : Number.POSITIVE_INFINITY;
  return Math.min(after, before);
}

/** Return the closest beat time only when it falls inside the entrance snap window. */
export function snapEntranceTime(time: number, beats: number[], tolerance = 0.18): number {
  if (!isFiniteNumber(time) || !isFiniteNumber(tolerance) || tolerance < 0 || !isSortedTimes(beats) || beats.length === 0) return time;
  let low = 0;
  let high = beats.length - 1;
  while (low < high) {
    const mid = Math.floor((low + high) / 2);
    if (beats[mid] < time) low = mid + 1;
    else high = mid;
  }
  const candidates = [beats[low], ...(low > 0 ? [beats[low - 1]] : [])];
  const closest = candidates.reduce((best, candidate) =>
    Math.abs(candidate - time) < Math.abs(best - time) ? candidate : best, candidates[0]);
  return Math.abs(closest - time) <= tolerance ? closest : time;
}

function energyAt(time: number, curve: EnergyPoint[]): number {
  if (curve.length === 0) return 0.5;
  if (time <= curve[0].time) return curve[0].rms;
  for (let i = 1; i < curve.length; i++) {
    if (time <= curve[i].time) {
      const left = curve[i - 1];
      const right = curve[i];
      const span = right.time - left.time;
      if (span <= 0) return right.rms;
      const alpha = (time - left.time) / span;
      return left.rms + (right.rms - left.rms) * alpha;
    }
  }
  return curve[curve.length - 1].rms;
}

export function evaluateAudioCues(
  frame: number,
  fps: number,
  cues: AudioIntelligence | null | undefined,
): AudioCueFrame {
  const duration = cues?.duration ?? Number.MAX_SAFE_INTEGER;
  const time = frameToTime(frame, fps, duration);
  if (!cues) {
    const phase = time * Math.PI * 3.6;
    return {
      time,
      beatPulse: (Math.sin(phase) + 1) * 0.5,
      energy: 0.5 + 0.12 * Math.sin(time * 0.7),
      transitionIntensity: 0,
      hasAudioCues: false,
    };
  }

  const beatDistance = nearestBeatDistance(time, cues.beats);
  const beatPulse = Number.isFinite(beatDistance) && beatDistance < 0.16
    ? Math.max(0, 1 - beatDistance / 0.16)
    : 0;
  const transitionIntensity = cues.events.reduce((max, event) => {
    const distance = Math.abs(event.time - time);
    if (distance > 0.65) return max;
    const typeWeight = event.type === "energy-rise" ? 1 : event.type === "onset" ? 0.8 : 0.55;
    return Math.max(max, Math.min(1, event.strength) * typeWeight * (1 - distance / 0.65));
  }, 0);

  return {
    time,
    beatPulse,
    energy: Math.max(0, Math.min(1, energyAt(time, cues.energy_curve))),
    transitionIntensity,
    hasAudioCues: true,
  };
}

const unitInterval = (value: number): number =>
  Number.isFinite(value) ? Math.min(1, Math.max(0, value)) : 0;

/** Map normalized audio cues to a bounded wave displacement amplitude. */
export function audioReactiveWaveAmplitude(
  cue: Pick<AudioCueFrame, "energy" | "beatPulse" | "transitionIntensity">,
): number {
  return 0.025 +
    unitInterval(cue.energy) * 0.075 +
    unitInterval(cue.beatPulse) * 0.12 +
    unitInterval(cue.transitionIntensity) * 0.08;
}

/** Map beat, transition, and energy cues to a stable, bounded glitch intensity. */
export function audioReactiveGlitchIntensity(
  cue: Pick<AudioCueFrame, "energy" | "beatPulse" | "transitionIntensity">,
): number {
  return Math.min(
    1,
    unitInterval(cue.beatPulse) * 0.7 +
      unitInterval(cue.transitionIntensity) * 0.45 +
      unitInterval(cue.energy) * 0.08,
  );
}

/** Scale particle fall rate from the audio envelope without introducing randomness. */
export function audioReactiveParticleFallRate(
  cue: Pick<AudioCueFrame, "energy" | "beatPulse">,
): number {
  return 0.8 + unitInterval(cue.energy) * 0.4 + unitInterval(cue.beatPulse) * 0.2;
}
