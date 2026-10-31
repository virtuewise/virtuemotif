// src/declarations.d.ts
// Ambient module declarations for external libraries without local type packages

declare module 'rxjs' {
  export class Subject<T = any> {
    next(value: T): void;
    subscribe(observer?: any): any;
  }
}

declare module 'idb' {
  export function openDB(name: string, version?: number, config?: any): Promise<any>;
}

declare module 'onnxruntime-web' {
  export class Tensor {
    constructor(type: string, data: any, dims?: number[]);
    data: any;
    dims: number[];
  }
  export class InferenceSession {
    static create(pathOrBuffer: string | ArrayBuffer, options?: any): Promise<InferenceSession>;
    run(feeds: Record<string, Tensor>): Promise<Record<string, Tensor>>;
  }
}
