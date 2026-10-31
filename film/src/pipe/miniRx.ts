// src/pipe/miniRx.ts
// Lightweight zero-dependency Subject implementation (RxJS-compatible subset)

export class Subject<T = any> {
  private observers: Array<(value: T) => void> = [];

  next(value: T): void {
    for (const observer of [...this.observers]) {
      try {
        observer(value);
      } catch (err) {
        console.error("Subject observer error:", err);
      }
    }
  }

  subscribe(observer: (value: T) => void): { unsubscribe: () => void } {
    this.observers.push(observer);
    return {
      unsubscribe: () => {
        this.observers = this.observers.filter((fn) => fn !== observer);
      },
    };
  }
}
