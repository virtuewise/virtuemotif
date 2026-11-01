// src/workers/whisper.worker.ts
// Browser-side voice-activity detection only. This worker does NOT run an ASR
// model; it must never invent lyric text or claim a detected language.

import { computeVoiceActivity } from '../lyrics/AudioProcessor';

self.addEventListener('message', (event: MessageEvent) => {
  const { id, payload } = event.data;

  try {
    const { pcm16k, sampleRate = 16000, language = 'auto' } = payload as {
      pcm16k: Float32Array;
      sampleRate?: number;
      language?: string;
    };

    if (!(pcm16k instanceof Float32Array)) {
      throw new TypeError('pcm16k must be a Float32Array');
    }
    if (!Number.isFinite(sampleRate) || sampleRate <= 0) {
      throw new RangeError('sampleRate must be a positive finite number');
    }

    const vocalSegments = computeVoiceActivity(pcm16k, sampleRate);

    self.postMessage({
      id,
      result: {
        mode: 'vad-only',
        transcriptionAvailable: false,
        requestedLanguage: language,
        detectedLanguage: 'und',
        languageConfidence: 0,
        segments: vocalSegments.map((segment, index) => ({
          id: index,
          start: segment.start,
          end: segment.end,
          energy: segment.energy,
          kind: 'voice-activity',
        })),
        notice: 'Voice activity is detected, but lyric transcription and language identification require an ASR model.',
      },
    });
  } catch (err: unknown) {
    self.postMessage({
      id,
      error: err instanceof Error ? err.message : String(err),
    });
  }
});
