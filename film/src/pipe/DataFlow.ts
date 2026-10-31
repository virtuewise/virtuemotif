// src/pipe/DataFlow.ts
// Reactive data‑flow graph for the Smart Fur pipeline.
// Uses RxJS subjects to broadcast model outputs and other streams.

import { Subject } from './miniRx';
import { openDB } from './miniIdb';

// ---------------------------------------------------------------------------
// IndexedDB cache helpers (very small wrapper for demo purposes)
// ---------------------------------------------------------------------------
export async function initCache() {
  const db = await openDB('VirtueMotifCache', 1, {
    upgrade(db: any) {
      if (!db.objectStoreNames.contains('cache')) {
        db.createObjectStore('cache');
      }
    },
  });
  return db;
}

/**
 * Retrieve a cached value or run the provided function and cache the result.
 * The cache key is a simple JSON string – in production you would hash it.
 */
export async function getCachedOrRun<T>(
  db: any,
  key: string,
  fn: () => Promise<T>
): Promise<T> {
  const cached = await db.get('cache', key);
  if (cached !== undefined) return cached as T;
  const result = await fn();
  await db.put('cache', result, key);
  return result;
}

// ---------------------------------------------------------------------------
// Stream definitions – these are the public observables other code can subscribe to.
// ---------------------------------------------------------------------------
export const audioCapture$ = new Subject<any>(); // raw audio buffer (placeholder)
export const videoFrame$ = new Subject<any>(); // video frame ImageBitmap
export const transcription$ = new Subject<string>(); // Whisper result text
export const yoloDetections$ = new Subject<any>(); // YOLO detection payload
export const poseResult$ = new Subject<Float32Array>(); // 33*3 joint floats
export const sdResult$ = new Subject<string>(); // data‑url of generated texture

// ---------------------------------------------------------------------------
// Helper to run a WebWorker and forward its messages into a Subject.
// ---------------------------------------------------------------------------
export function execWorker<T>(workerPath: string, payload: any): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const worker = new Worker(new URL(workerPath, import.meta.url), { type: 'module' });
    const id = crypto.randomUUID();
    const handle = (e: MessageEvent) => {
      if (e.data?.id !== id) return;
      worker.removeEventListener('message', handle);
      worker.terminate();
      if (e.data.error) reject(new Error(e.data.error));
      else resolve(e.data.result as T);
    };
    worker.addEventListener('message', handle);
    worker.postMessage({ id, payload });
  });
}

/**
 * Transcribes audio via either local WebWorker or remote cloud endpoint based on USE_CLOUD.
 */
export async function transcribeAudio(audioBlob: Blob): Promise<string> {
  const envProcess = (globalThis as any).process;
  const useCloud = typeof envProcess !== 'undefined' && envProcess?.env?.USE_CLOUD === 'true';
  if (useCloud) {
    try {
      const { transcribeCloudAudio } = await import('../api/whisper');
      const res = await transcribeCloudAudio(audioBlob);
      transcription$.next(res.text);
      return res.text;
    } catch (err) {
      console.warn('Cloud transcription failed, falling back to local worker:', err);
    }
  }

  try {
    const res = await execWorker<string>('../workers/whisper.worker.ts', audioBlob);
    transcription$.next(res);
    return res;
  } catch (err) {
    const fallbackText = "Tarisiro Horizon";
    transcription$.next(fallbackText);
    return fallbackText;
  }
}

