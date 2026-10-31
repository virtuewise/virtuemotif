// src/lyrics/SongBuilder.ts
// Validates, formats, and outputs standard Song JSON files
// ready for Remotion 2D and 3D compositions.

import type { SongMetadata } from './types';

/**
 * Validates and sanitizes a SongMetadata object to ensure strict chronological ordering,
 * non-overlapping boundaries, and valid timestamps for rendering.
 */
export function sanitizeSong(song: SongMetadata): SongMetadata {
  const sanitized = JSON.parse(JSON.stringify(song)) as SongMetadata;

  // Ensure sections are chronologically ordered
  sanitized.sections.sort((a, b) => a.start - b.start);

  for (let s = 0; s < sanitized.sections.length; s++) {
    const sec = sanitized.sections[s];

    // Ensure section boundaries do not invert
    if (sec.end < sec.start) {
      sec.end = sec.start + 1.0;
    }

    // Sort lines inside section
    sec.lines.sort((a, b) => a.from - b.from);

    for (let l = 0; l < sec.lines.length; l++) {
      const line = sec.lines[l];
      if (line.to < line.from) {
        line.to = line.from + 0.8;
      }

      // Sort and clamp word timestamps within line boundaries
      if (Array.isArray(line.words) && line.words.length > 0) {
        line.words.sort((a, b) => a.from - b.from);
        for (const w of line.words) {
          w.from = Math.max(line.from, w.from);
          w.to = Math.min(line.to + 0.5, Math.max(w.from + 0.05, w.to));
        }
      }
    }
  }

  return sanitized;
}

/**
 * Converts a SongMetadata object into a formatted JSON string matching horizon.json format.
 */
export function formatSongJson(song: SongMetadata): string {
  const cleanSong = sanitizeSong(song);
  return JSON.stringify(cleanSong, null, 1);
}
