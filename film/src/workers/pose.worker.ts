// src/workers/pose.worker.ts
// Pose‑estimation WebWorker using ONNX Runtime Web.
// Expects a payload of the form { id: string, imageBitmap: ImageBitmap }.
// Returns { id: string, landmarks: Float32Array } where landmarks are 33*3 floats.

import * as ort from './mockOrt';

let session: ort.InferenceSession | null = null;

async function loadModel() {
  if (!session) {
    // Adjust the path if your model is stored elsewhere.
    const modelUrl = new URL('../../models/pose.onnx', import.meta.url).href;
    session = await ort.InferenceSession.create(modelUrl, {
      executionProviders: ['wasm'],
    });
  }
  return session;
}

self.addEventListener('message', async (event: MessageEvent) => {
  const { id, payload } = event.data;
  try {
    const { imageBitmap } = payload as { imageBitmap: ImageBitmap };
    const session = await loadModel();
    // Convert ImageBitmap to tensor (NCHW, float32, normalized).
    const canvas = new OffscreenCanvas(imageBitmap.width, imageBitmap.height);
    const ctx = canvas.getContext('2d')!;
    ctx.drawImage(imageBitmap, 0, 0);
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const { data, width, height } = imageData;
    const floatData = new Float32Array(width * height * 3);
    for (let i = 0; i < width * height; i++) {
      const r = data[i * 4] / 255;
      const g = data[i * 4 + 1] / 255;
      const b = data[i * 4 + 2] / 255;
      floatData[i] = r;
      floatData[i + width * height] = g;
      floatData[i + 2 * width * height] = b;
    }
    const tensor = new ort.Tensor('float32', floatData, [1, 3, height, width]);
    const feeds: Record<string, ort.Tensor> = { input: tensor };
    const results = await session.run(feeds);
    // The model's output name may differ; adjust as needed.
    const output = results['output'] as ort.Tensor;
    const landmarks = new Float32Array(output.data);
    self.postMessage({ id, result: { landmarks } });
  } catch (e: any) {
    self.postMessage({ id, error: e.message ?? String(e) });
  }
});
