// src/optimiser/QBandit.ts
// Q‑learning bandit that optimizes shader uniforms (fog density, beat sensitivity)
// based on user rating feedback stored in IndexedDB.

import { openDB } from '../pipe/miniIdb';

export interface BanditAction {
  fogDensity: number;
  beatSensitivity: number;
}

const DB_NAME = 'VirtueMotifCache';
const STORE_NAME = 'bandit';

export class QBandit {
  private dbPromise = openDB(DB_NAME, 1, {
    upgrade(db: any) {
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    },
  });

  private alpha = 0.2; // learning rate
  private epsilon = 0.15; // exploration rate

  // Discrete action space for fog density and audio-beat reactivity
  private actions: BanditAction[] = [
    { fogDensity: 0.15, beatSensitivity: 1.2 }, // Subtle depth fog, snappy beat
    { fogDensity: 0.35, beatSensitivity: 1.5 }, // Medium atmospheric fog, balanced beat
    { fogDensity: 0.55, beatSensitivity: 1.8 }, // Moody dense fog, energetic beat
    { fogDensity: 0.25, beatSensitivity: 2.2 }, // Clear fog, high glitch/audio sensitivity
  ];

  /**
   * Selects an action using an epsilon-greedy policy over stored Q-values.
   */
  async selectAction(): Promise<BanditAction> {
    try {
      const db = await this.dbPromise;

      // Exploration: pick random action
      if (Math.random() < this.epsilon) {
        const randomIndex = Math.floor(Math.random() * this.actions.length);
        return this.actions[randomIndex];
      }

      // Exploitation: pick action with highest stored Q-value
      let bestAction = this.actions[1];
      let maxQ = -Infinity;

      for (let i = 0; i < this.actions.length; i++) {
        const key = `action_${i}`;
        const qVal = (await db.get(STORE_NAME, key)) ?? 0;
        if (qVal > maxQ) {
          maxQ = qVal;
          bestAction = this.actions[i];
        }
      }

      return bestAction;
    } catch {
      return this.actions[1]; // Safe fallback default
    }
  }

  /**
   * Updates the Q-value for the selected action given a user star rating (1-5).
   */
  async updateQ(rating: number, action: BanditAction): Promise<void> {
    try {
      const db = await this.dbPromise;
      const index = this.actions.findIndex(
        (a) => a.fogDensity === action.fogDensity && a.beatSensitivity === action.beatSensitivity
      );
      const actionIdx = index >= 0 ? index : 1;
      const key = `action_${actionIdx}`;
      const currentQ = (await db.get(STORE_NAME, key)) ?? 0;

      // Normalize 1..5 star rating to reward in [-1.0, 1.0]
      const reward = (rating - 3) / 2;
      const newQ = currentQ + this.alpha * (reward - currentQ);
      await db.put(STORE_NAME, newQ, key);
    } catch (err) {
      console.warn('Failed to update Q-value in bandit store:', err);
    }
  }
}

export const qBandit = new QBandit();
