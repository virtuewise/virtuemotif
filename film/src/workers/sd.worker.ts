// src/workers/sd.worker.ts
// Stable‑Diffusion WebWorker using ONNX Runtime Web.
// Accepts payload: { id: string, prompt: string, width?: number, height?: number, aspectRatio?: string }.
// Default full resolution is 1024x1024 (1:1), 1920x1080 / 3840x2160 (16:9), or 1080x1920 (9:16 mobile-first).
// Returns: { id: string, dataUrl: string } where dataUrl is a PNG data URL.

import * as ort from './mockOrt';

let session: ort.InferenceSession | null = null;

async function loadModel() {
  if (!session) {
    // Adjust the path if your model is stored elsewhere.
    const modelUrl = new URL('../../models/sd.onnx', import.meta.url).href;
    session = await ort.InferenceSession.create(modelUrl, {
      executionProviders: ['wasm'],
    });
  }
  return session;
}

function tensorFromPrompt(prompt: string, width: number, height: number): ort.Tensor {
  // Very naive placeholder: encode prompt length into a constant tensor.
  // Real implementation would use a text‑tokenizer and a diffusion scheduler.
  const size = width * height * 3;
  const data = new Float32Array(size).fill(0.5);
  return new ort.Tensor('float32', data, [1, 3, height, width]);
}

self.addEventListener('message', async (event: MessageEvent) => {
  const { id, payload } = event.data;
  try {
    const { prompt, width = 1024, height = 1024 } = payload as {
      prompt: string;
      width?: number;
      height?: number;
      aspectRatio?: string;
    };
    const session = await loadModel();
    const inputTensor = tensorFromPrompt(prompt, width, height);
    const feeds: Record<string, ort.Tensor> = { input: inputTensor };
    const results = await session.run(feeds);
    const output = results['output'] as ort.Tensor;
    // Convert tensor (NCHW) to ImageData.
    const [n, c, h, w] = output.dims as number[];
    const floatData = output.data as Float32Array;
    const canvas = new OffscreenCanvas(w, h);
    const ctx = canvas.getContext('2d')!;
    const imageData = ctx.createImageData(w, h);
    const data = imageData.data;
    // Simple conversion assuming range [0,1].
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const i = y * w + x;
        const r = floatData[i] * 255;
        const g = floatData[i + h * w] * 255;
        const b = floatData[i + 2 * h * w] * 255;
        const di = i * 4;
        data[di] = r;
        data[di + 1] = g;
        data[di + 2] = b;
        data[di + 3] = 255;
      }
    }
    ctx.putImageData(imageData, 0, 0);
    const blob = await canvas.convertToBlob({ type: 'image/png' });
    const dataUrl = await new Promise<string>((res) => {
      const reader = new FileReader();
      reader.onload = () => res(reader.result as string);
      reader.readAsDataURL(blob);
    });
    self.postMessage({ id, result: { dataUrl } });
  } catch (e: any) {
    self.postMessage({ id, error: e.message ?? String(e) });
  }
});
