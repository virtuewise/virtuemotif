// src/workers/mockOrt.ts
// Lightweight zero-dependency ONNX Runtime Web mock for local execution and bundling

export class Tensor {
  data: any;
  dims: number[];
  constructor(public type: string, data: any, dims: number[] = []) {
    this.data = data;
    this.dims = dims;
  }
}

export class InferenceSession {
  static async create(_pathOrBuffer: string | ArrayBuffer, _options?: any): Promise<InferenceSession> {
    return new InferenceSession();
  }

  async run(feeds: Record<string, Tensor>): Promise<Record<string, Tensor>> {
    // If input tensor looks like an image with dims [1, 3, height, width]
    const input = feeds['input'];
    if (input && input.dims && input.dims.length === 4) {
      const h = input.dims[2];
      const w = input.dims[3];
      // Generate a pleasant dark gradient texture
      const floatData = new Float32Array(h * w * 3);
      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          const idx = y * w + x;
          floatData[idx] = 0.15 + (x / w) * 0.2; // R
          floatData[idx + h * w] = 0.1 + (y / h) * 0.15; // G
          floatData[idx + 2 * h * w] = 0.25; // B
        }
      }
      return {
        output: new Tensor('float32', floatData, [1, 3, h, w]),
      };
    }

    // Default landmark payload (33 joints * 3 coordinates)
    const landmarks = new Float32Array(33 * 3).fill(0.5);
    return {
      output: new Tensor('float32', landmarks, [1, 33, 3]),
    };
  }
}
