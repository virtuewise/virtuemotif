// src/pipe/miniIdb.ts
// Lightweight zero-dependency IndexedDB wrapper (idb-compatible subset)

export interface SimpleDB {
  get: (storeName: string, key: string) => Promise<any>;
  put: (storeName: string, value: any, key: string) => Promise<void>;
  close?: () => void;
}

export async function openDB(
  name: string,
  version: number = 1,
  options?: { upgrade?: (db: any) => void }
): Promise<SimpleDB> {
  if (typeof indexedDB === "undefined") {
    // In-memory fallback for non-browser / headless SSR contexts
    const memStore: Record<string, Record<string, any>> = {
      cache: {},
      ratings: {},
    };
    return {
      get: async (storeName: string, key: string) => memStore[storeName]?.[key],
      put: async (storeName: string, value: any, key: string) => {
        if (!memStore[storeName]) memStore[storeName] = {};
        memStore[storeName][key] = value;
      },
    };
  }

  return new Promise<SimpleDB>((resolve, reject) => {
    const request = indexedDB.open(name, version);
    request.onupgradeneeded = (e: any) => {
      const db = e.target.result;
      if (options?.upgrade) {
        options.upgrade(db);
      }
    };
    request.onsuccess = (e: any) => {
      const db = e.target.result as IDBDatabase;
      resolve({
        get: (storeName: string, key: string) =>
          new Promise((res, rej) => {
            try {
              const tx = db.transaction(storeName, "readonly");
              const store = tx.objectStore(storeName);
              const req = store.get(key);
              req.onsuccess = () => res(req.result);
              req.onerror = () => rej(req.error);
            } catch (err) {
              res(undefined);
            }
          }),
        put: (storeName: string, value: any, key: string) =>
          new Promise((res, rej) => {
            try {
              const tx = db.transaction(storeName, "readwrite");
              const store = tx.objectStore(storeName);
              const req = store.put(value, key);
              req.onsuccess = () => res();
              req.onerror = () => rej(req.error);
            } catch (err) {
              res();
            }
          }),
        close: () => db.close(),
      });
    };
    request.onerror = () => reject(request.error);
  });
}
