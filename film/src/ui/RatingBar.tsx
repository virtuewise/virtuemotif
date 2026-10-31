// src/ui/RatingBar.tsx
// Simple 5‑star rating overlay used in SmartFurScene.
// Stores rating per composition ID in IndexedDB via the `ratings` store.

import React, { useState, useEffect } from 'react';
import { openDB } from '../pipe/miniIdb';

interface RatingBarProps {
  compositionId: string;
  onRate?: (value: number) => void;
}

const DB_NAME = 'VirtueMotifCache';
const STORE_NAME = 'ratings';

async function getDb() {
  return openDB(DB_NAME, 1, {
    upgrade(db: any) {
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    },
  });
}

export const RatingBar: React.FC<RatingBarProps> = ({ compositionId, onRate }) => {
  const [rating, setRating] = useState<number>(0);

  useEffect(() => {
    (async () => {
      const db = await getDb();
      const saved = await db.get(STORE_NAME, compositionId);
      if (typeof saved === 'number') setRating(saved);
    })();
  }, [compositionId]);

  const handleClick = async (value: number) => {
    setRating(value);
    const db = await getDb();
    await db.put(STORE_NAME, value, compositionId);
    onRate?.(value);
  };

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 20,
        left: '50%',
        transform: 'translateX(-50%)',
        display: 'flex',
        gap: 8,
        background: 'rgba(0,0,0,0.5)',
        padding: '4px 8px',
        borderRadius: 8,
        zIndex: 1000,
      }}
    >
      {[1, 2, 3, 4, 5].map((star) => (
        <svg
          key={star}
          onClick={() => handleClick(star)}
          width={24}
          height={24}
          viewBox="0 0 24 24"
          fill={star <= rating ? '#ffdd00' : '#555'}
          style={{ cursor: 'pointer' }}
        >
          <path d="M12 .587l3.668 7.571L24 9.748l-6 5.851L19.335 24 12 19.897 4.665 24 6 15.599 0 9.748l8.332-1.59z" />
        </svg>
      ))}
    </div>
  );
};
