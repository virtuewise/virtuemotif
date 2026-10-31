// src/ui/AutoLyricsPanel.tsx
// Interactive HUD panel displaying live auto-detected language,
// accent confidence, and synchronized word-timing lyrics status.

import React from 'react';
import { Song } from '../HorizonFilm';

interface AutoLyricsPanelProps {
  song: Song;
  detectedLanguage?: string;
  confidence?: number;
  audioFormat?: string;
  isTranslating?: boolean;
}

export const AutoLyricsPanel: React.FC<AutoLyricsPanelProps> = ({
  song,
  detectedLanguage = 'Multilingual (Auto-Detect)',
  confidence = 0.96,
  audioFormat = 'M4A / AAC / MP3 / WAV',
  isTranslating = true,
}) => {
  const totalLines = song.sections.reduce((acc, s) => acc + s.lines.length, 0);

  return (
    <div
      style={{
        position: 'absolute',
        top: 24,
        left: 28,
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        padding: '10px 16px',
        borderRadius: 12,
        background: 'rgba(15, 23, 42, 0.72)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(245, 158, 11, 0.25)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.45)',
        color: '#f8fafc',
        fontFamily: 'Space Grotesk, sans-serif',
        fontSize: 13,
        letterSpacing: '0.04em',
        zIndex: 50,
        pointerEvents: 'none',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: '#10b981',
            boxShadow: '0 0 10px #10b981',
          }}
        />
        <span style={{ fontWeight: 700, textTransform: 'uppercase', color: '#fbbf24', letterSpacing: '0.08em' }}>
          Smart Auto Lyrics Engine
        </span>
      </div>

      <div style={{ display: 'flex', gap: 14, color: '#94a3b8', fontSize: 11 }}>
        <div>
          Format: <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{audioFormat}</span>
        </div>
        <div>
          Language: <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{detectedLanguage}</span>
        </div>
        <div>
          Confidence: <span style={{ color: '#34d399', fontWeight: 600 }}>{Math.round(confidence * 100)}%</span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 14, color: '#94a3b8', fontSize: 11 }}>
        <div>
          Sections: <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{song.sections.length}</span>
        </div>
        <div>
          Aligned Lines: <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{totalLines}</span>
        </div>
        {isTranslating ? (
          <div>
            Subtitles: <span style={{ color: '#60a5fa', fontWeight: 600 }}>Active</span>
          </div>
        ) : null}
      </div>
    </div>
  );
};
