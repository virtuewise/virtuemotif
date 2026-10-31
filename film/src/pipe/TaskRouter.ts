// src/pipe/TaskRouter.ts
// Simple task router with configurable concurrency limit.
// Jobs are enqueued as functions returning a Promise. The router ensures that at most
// `maxConcurrent` jobs run simultaneously; excess jobs are queued and started when a slot frees.

type Job<T = any> = {
  // A human‑readable identifier for debugging/logging.
  id: string;
  // The async function that performs the work.
  run: () => Promise<T>;
  // Resolve/reject callbacks attached by the caller.
  resolve: (value: T) => void;
  reject: (reason?: any) => void;
};

export class TaskRouter {
  private maxConcurrent: number;
  private running: number = 0;
  private queue: Job[] = [];

  constructor(maxConcurrent = 3) {
    this.maxConcurrent = maxConcurrent;
  }

  /** Enqueue a job and get a promise for its result. */
  enqueue<T>(id: string, run: () => Promise<T>): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      const job: Job<T> = { id, run, resolve, reject };
      this.queue.push(job);
      this.processQueue();
    });
  }

  private async processQueue() {
    if (this.running >= this.maxConcurrent) return;
    const job = this.queue.shift();
    if (!job) return;
    this.running++;
    try {
      const result = await job.run();
      job.resolve(result);
    } catch (e) {
      job.reject(e);
    } finally {
      this.running--;
      // Continue processing any remaining queued jobs.
      this.processQueue();
    }
  }
}

// Export a singleton used throughout the project.
export const router = new TaskRouter(3);
