// src/lyrics/types.ts
// Universal data models for the Smart Auto Lyrics Generator

export interface WordTiming {
  w: string;
  from: number;
  to: number;
  confidence?: number;
}

export interface LyricLineSegment {
  text: string;
  translation?: string;
  style?: "display" | "whisper" | "title" | "chorus";
  from: number;
  to: number;
  words?: WordTiming[];
}

export interface MusicalSection {
  id: string;
  label: string;
  look: string; // "wide" | "walkers" | "giant" | "dusk" | "sunrise" | "night"
  start: number;
  end: number;
  lines: LyricLineSegment[];
}

export interface SongMetadata {
  id: string;
  title: string;
  subtitle: string;
  artist: string;
  audio: string;
  duration: number;
  palette?: string;
  detectedLanguage?: string;
  languageConfidence?: number;
  sections: MusicalSection[];
}

export interface AudioProcessingResult {
  duration: number;
  sampleRate: number;
  channels: number;
  pcm16k: Float32Array;
  vocalSegments: Array<{ start: number; end: number; energy: number }>;
}

export interface TranscriptionOptions {
  audioPath: string; // Path or URL to .mp3, .m4a, .wav, .aac
  title?: string;
  subtitle?: string;
  artist?: string;
  language?: string; // e.g. "auto", "en", "sn" (Shona), "nd" (Ndebele), "es", "ja", "fr"
  translateToEnglish?: boolean; // Generate secondary English subtitle for foreign lyrics
  provider?: "cloud" | "worker" | "heuristic";
  apiKey?: string; // Optional OpenAI / Groq / custom endpoint API key
  endpointUrl?: string; // Custom Whisper endpoint (e.g. localhost:8000/v1 or api.groq.com)
}
