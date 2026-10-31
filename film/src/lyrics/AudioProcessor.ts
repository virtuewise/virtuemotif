// src/lyrics/AudioProcessor.ts
// Handles universal audio decoding (.mp3, .m4a, .wav, .aac),
// channel downmixing, 16kHz resampling, and Voice Activity Detection (VAD).

import type { AudioProcessingResult } from './types';

/**
 * Resamples an input Float32Array audio buffer to 16,000 Hz mono.
 */
export function resampleTo16k(
  inputData: Float32Array,
  sourceSampleRate: number
): Float32Array {
  if (sourceSampleRate === 16000) return inputData;

  const targetSampleRate = 16000;
  const ratio = sourceSampleRate / targetSampleRate;
  const targetLength = Math.round(inputData.length / ratio);
  const output = new Float32Array(targetLength);

  for (let i = 0; i < targetLength; i++) {
    const srcIndex = i * ratio;
    const indexLow = Math.floor(srcIndex);
    const indexHigh = Math.min(indexLow + 1, inputData.length - 1);
    const frac = srcIndex - indexLow;
    // Linear interpolation between adjacent samples
    output[i] = inputData[indexLow] * (1 - frac) + inputData[indexHigh] * frac;
  }

  return output;
}

/**
 * Downmixes multi-channel audio buffers into a single mono channel.
 */
export function downmixToMono(channels: Float32Array[]): Float32Array {
  if (channels.length === 0) return new Float32Array(0);
  if (channels.length === 1) return channels[0];

  const length = channels[0].length;
  const mono = new Float32Array(length);
  const numChannels = channels.length;

  for (let i = 0; i < length; i++) {
    let sum = 0;
    for (let c = 0; c < numChannels; c++) {
      sum += channels[c][i];
    }
    mono[i] = sum / numChannels;
  }

  return mono;
}

/**
 * Computes root-mean-square (RMS) energy across sliding frames to detect vocal energy & silences.
 */
export function computeVoiceActivity(
  pcm16k: Float32Array,
  sampleRate: number = 16000,
  frameDurationMs: number = 25,
  hopDurationMs: number = 10
): Array<{ start: number; end: number; energy: number }> {
  const frameSize = Math.floor((sampleRate * frameDurationMs) / 1000);
  const hopSize = Math.floor((sampleRate * hopDurationMs) / 1000);
  const numFrames = Math.floor((pcm16k.length - frameSize) / hopSize);

  if (numFrames <= 0) return [];

  const energies = new Float32Array(numFrames);
  let totalEnergy = 0;

  for (let i = 0; i < numFrames; i++) {
    const offset = i * hopSize;
    let sumSq = 0;
    for (let j = 0; j < frameSize; j++) {
      const sample = pcm16k[offset + j];
      sumSq += sample * sample;
    }
    const rms = Math.sqrt(sumSq / frameSize);
    energies[i] = rms;
    totalEnergy += rms;
  }

  const avgEnergy = totalEnergy / numFrames;
  const threshold = Math.max(0.008, avgEnergy * 0.45);

  // Group continuous frames above threshold into vocal segments
  const segments: Array<{ start: number; end: number; energy: number }> = [];
  let inVocal = false;
  let segStart = 0;
  let segSumEnergy = 0;
  let segCount = 0;

  for (let i = 0; i < numFrames; i++) {
    const time = (i * hopSize) / sampleRate;
    const isAbove = energies[i] >= threshold;

    if (isAbove) {
      if (!inVocal) {
        inVocal = true;
        segStart = time;
        segSumEnergy = energies[i];
        segCount = 1;
      } else {
        segSumEnergy += energies[i];
        segCount++;
      }
    } else {
      if (inVocal) {
        inVocal = false;
        const segEnd = time + frameDurationMs / 1000;
        // Keep vocal bursts longer than 0.35 seconds
        if (segEnd - segStart >= 0.35) {
          segments.push({
            start: parseFloat(segStart.toFixed(2)),
            end: parseFloat(segEnd.toFixed(2)),
            energy: parseFloat((segSumEnergy / Math.max(1, segCount)).toFixed(4)),
          });
        }
      }
    }
  }

  if (inVocal) {
    const finalEnd = (numFrames * hopSize) / sampleRate;
    segments.push({
      start: parseFloat(segStart.toFixed(2)),
      end: parseFloat(finalEnd.toFixed(2)),
      energy: parseFloat((segSumEnergy / Math.max(1, segCount)).toFixed(4)),
    });
  }

  return segments;
}

/**
 * Universal browser-side audio decoder for .mp3, .m4a, .wav, and .aac.
 */
export async function decodeAudioInBrowser(
  audioSource: string | Blob | ArrayBuffer
): Promise<AudioProcessingResult> {
  let arrayBuffer: ArrayBuffer;

  if (typeof audioSource === 'string') {
    const res = await fetch(audioSource);
    arrayBuffer = await res.arrayBuffer();
  } else if (audioSource instanceof Blob) {
    arrayBuffer = await audioSource.arrayBuffer();
  } else {
    arrayBuffer = audioSource;
  }

  const AudioContextClass =
    typeof window !== 'undefined'
      ? window.AudioContext || (window as any).webkitAudioContext
      : null;

  if (!AudioContextClass) {
    throw new Error('Web Audio API (AudioContext) is not available in current environment.');
  }

  const ctx = new AudioContextClass();
  try {
    const decodedBuffer = await ctx.decodeAudioData(arrayBuffer.slice(0));
    const channels: Float32Array[] = [];
    for (let c = 0; c < decodedBuffer.numberOfChannels; c++) {
      channels.push(decodedBuffer.getChannelData(c));
    }

    const mono = downmixToMono(channels);
    const pcm16k = resampleTo16k(mono, decodedBuffer.sampleRate);
    const vocalSegments = computeVoiceActivity(pcm16k, 16000);

    return {
      duration: decodedBuffer.duration,
      sampleRate: decodedBuffer.sampleRate,
      channels: decodedBuffer.numberOfChannels,
      pcm16k,
      vocalSegments,
    };
  } finally {
    await ctx.close().catch(() => {});
  }
}
