// src/lyrics/WhisperEngine.ts
// Multilingual & multi-accent speech-to-text, word-level alignment,
// translation generation, and musical section segmentation.

import type {
  LyricLineSegment,
  MusicalSection,
  SongMetadata,
  TranscriptionOptions,
  WordTiming,
} from './types';

// Map of common language codes to human-readable names
export const LANGUAGE_NAMES: Record<string, string> = {
  en: 'English',
  sn: 'Shona',
  nd: 'Ndebele',
  zu: 'Zulu',
  xh: 'Xhosa',
  sw: 'Swahili',
  es: 'Spanish',
  fr: 'French',
  pt: 'Portuguese',
  ar: 'Arabic',
  hi: 'Hindi',
  ja: 'Japanese',
  zh: 'Mandarin Chinese',
  de: 'German',
  it: 'Italian',
  ru: 'Russian',
  ko: 'Korean',
  yo: 'Yoruba',
  ig: 'Igbo',
};

const LANGUAGE_ALIASES: Record<string, string> = {
  english: 'en', shona: 'sn', ndebele: 'nd', 'north ndebele': 'nd',
  zulu: 'zu', 'isizulu': 'zu', xhosa: 'xh', 'isixhosa': 'xh',
  swahili: 'sw', afrikaans: 'af', spanish: 'es', french: 'fr',
  portuguese: 'pt', arabic: 'ar', hindi: 'hi', japanese: 'ja',
  chinese: 'zh', mandarin: 'zh', german: 'de', italian: 'it',
  russian: 'ru', korean: 'ko', yoruba: 'yo', igbo: 'ig',
};

/** Normalize API language names and codes to stable base language codes. */
export function normalizeLanguageCode(value: unknown): string {
  if (typeof value !== 'string' || !value.trim()) return 'und';
  const lower = value.trim().toLowerCase();
  return LANGUAGE_ALIASES[lower] || (LANGUAGE_NAMES[lower] ? lower : lower.split(/[-_]/)[0]);
}

/**
 * Intelligent section classifier that groups lyric lines into musical sections
 * (Intro, Verse 1, Chorus 1, Verse 2, Chorus 2, Bridge, Outro) based on
 * timing gaps, silence detection, and phrase repetition.
 */
export function groupIntoMusicalSections(
  lines: LyricLineSegment[],
  totalDuration: number
): MusicalSection[] {
  const sections: MusicalSection[] = [];
  if (lines.length === 0) {
    sections.push({
      id: 'full',
      label: 'Instrumental',
      look: 'wide',
      start: 0,
      end: totalDuration,
      lines: [],
    });
    return sections;
  }

  const firstVocalStart = lines[0].from;

  // 1. Intro section if there is instrumental music before vocals start (> 3.5s)
  if (firstVocalStart > 3.5) {
    sections.push({
      id: 'intro',
      label: 'Intro — Instrumental',
      look: 'wide',
      start: 0.0,
      end: parseFloat(firstVocalStart.toFixed(2)),
      lines: [],
    });
  }

  // 2. Identify repeat occurrences to detect Chorus sections
  const textFrequency: Record<string, number> = {};
  for (const line of lines) {
    const key = line.text.trim().toLowerCase();
    textFrequency[key] = (textFrequency[key] || 0) + 1;
  }

  // 3. Cluster lines into sections by detecting inter-line pauses (> 4.5s)
  const clusters: LyricLineSegment[][] = [];
  let currentCluster: LyricLineSegment[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (currentCluster.length === 0) {
      currentCluster.push(line);
    } else {
      const prevLine = currentCluster[currentCluster.length - 1];
      const gap = line.from - prevLine.to;

      // New section break if gap is larger than 4.5s or cluster exceeds 6 lines
      if (gap > 4.5 || currentCluster.length >= 6) {
        clusters.push(currentCluster);
        currentCluster = [line];
      } else {
        currentCluster.push(line);
      }
    }
  }
  if (currentCluster.length > 0) {
    clusters.push(currentCluster);
  }

  // 4. Assign semantic labels and cinematography looks to clusters
  let verseIndex = 1;
  let chorusIndex = 1;

  for (let c = 0; c < clusters.length; c++) {
    const cluster = clusters[c];
    const segStart = cluster[0].from;
    const nextStart = c < clusters.length - 1 ? clusters[c + 1][0].from : totalDuration;
    const segEnd = Math.min(totalDuration, Math.max(cluster[cluster.length - 1].to + 1.2, nextStart));

    // Check if lines in this cluster are repeated elsewhere (Chorus candidate)
    let repeatCount = 0;
    for (const l of cluster) {
      if ((textFrequency[l.text.trim().toLowerCase()] || 0) > 1) {
        repeatCount++;
      }
    }
    const isChorus = repeatCount >= Math.ceil(cluster.length * 0.45);

    let id: string;
    let label: string;
    let look: string;

    if (c === clusters.length - 1 && cluster.length <= 2 && segEnd >= totalDuration - 8) {
      id = 'outro';
      label = 'Outro';
      look = 'sunrise';
    } else if (isChorus) {
      id = `chorus${chorusIndex}`;
      label = `Chorus ${chorusIndex}`;
      look = 'giant';
      chorusIndex++;
    } else {
      id = `verse${verseIndex}`;
      label = `Verse ${verseIndex}`;
      look = verseIndex % 2 === 1 ? 'walkers' : 'dusk';
      verseIndex++;
    }

    sections.push({
      id,
      label,
      look,
      start: parseFloat(segStart.toFixed(2)),
      end: parseFloat(segEnd.toFixed(2)),
      lines: cluster,
    });
  }

  // 5. Final outro instrumental section if music continues after last vocal
  const lastSection = sections[sections.length - 1];
  if (lastSection && lastSection.end < totalDuration - 3.0) {
    sections.push({
      id: 'outro_inst',
      label: 'Outro — Fade',
      look: 'night',
      start: lastSection.end,
      end: parseFloat(totalDuration.toFixed(2)),
      lines: [],
    });
  }

  return sections;
}

/**
 * Main Auto-Lyrics generation engine.
 * Supports cloud API (Groq/OpenAI Whisper) and local heuristic alignment.
 */
export async function generateAutoLyrics(
  options: TranscriptionOptions
): Promise<SongMetadata> {
  const {
    audioPath,
    title = 'Automated Track',
    subtitle = 'Lyrics Generation',
    artist = 'virtuemotif',
    language = 'auto',
    translateToEnglish = true,
    apiKey,
    endpointUrl,
  } = options;

  let lines: LyricLineSegment[] = [];
  let detectedLang = language !== 'auto' ? language : 'und';
  // The transcription API does not expose a calibrated confidence value here.
  let langConfidence = 0;
  let audioDuration = 0;

  // 1. Check for Cloud Whisper API (Groq / OpenAI / Custom Serverless)
  const resolvedKey = apiKey || (typeof process !== 'undefined' ? process.env?.WHISPER_API_KEY || process.env?.GROQ_API_KEY || process.env?.OPENAI_API_KEY : '');
  const isCloudAvailable = Boolean(resolvedKey || endpointUrl);

  if (isCloudAvailable) {
    try {
      const url = endpointUrl || (resolvedKey?.startsWith('gsk_') ? 'https://api.groq.com/openai/v1/audio/transcriptions' : 'https://api.openai.com/v1/audio/transcriptions');
      const model = resolvedKey?.startsWith('gsk_') ? 'whisper-large-v3' : 'whisper-1';

      // Fetch audio data as blob
      const audioRes = await fetch(audioPath);
      const audioBlob = await audioRes.blob();

      const formData = new FormData();
      formData.append('file', audioBlob, 'track.m4a');
      formData.append('model', model);
      formData.append('response_format', 'verbose_json');
      formData.append('timestamp_granularities[]', 'word');
      formData.append('timestamp_granularities[]', 'segment');
      if (language && language !== 'auto') {
        formData.append('language', language);
      }

      const headers: Record<string, string> = {};
      if (resolvedKey) {
        headers['Authorization'] = `Bearer ${resolvedKey}`;
      }

      const apiRes = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });

      if (apiRes.ok) {
        const data = await apiRes.json();
        detectedLang = normalizeLanguageCode(data.language || detectedLang);
        audioDuration = data.duration || audioDuration;

        if (Array.isArray(data.segments)) {
          lines = data.segments.map((seg: any) => {
            const segWords: WordTiming[] = [];
            if (Array.isArray(data.words)) {
              for (const w of data.words) {
                if (w.start >= seg.start - 0.2 && w.end <= seg.end + 0.3) {
                  segWords.push({
                    w: w.word.trim(),
                    from: parseFloat(w.start.toFixed(2)),
                    to: parseFloat(w.end.toFixed(2)),
                  });
                }
              }
            }

            return {
              text: seg.text.trim(),
              translation: '',
              style: 'display',
              from: parseFloat(seg.start.toFixed(2)),
              to: parseFloat(seg.end.toFixed(2)),
              words: segWords.length > 0 ? segWords : undefined,
            };
          });
          if (audioDuration <= 0 && lines.length > 0) {
            audioDuration = lines[lines.length - 1].to;
          }
        }
      }
    } catch (cloudErr) {
      console.warn('Cloud Whisper API attempt failed, proceeding with audio processor:', cloudErr);
    }
  }

  // Do not manufacture placeholder lyric text from vocal activity. VAD can find
  // sound, but it cannot identify the words being sung. Fail clearly so the UI
  // can ask the user to configure a transcription provider instead of publishing
  // fabricated lyrics or placeholder translations.
  if (lines.length === 0) {
    throw new Error(
      'No lyric transcription was returned. Configure a valid Whisper-compatible API key/endpoint, check the audio URL, and try again. Local voice-activity detection cannot recover lyric words.'
    );
  }

  // Whisper transcription is not translation. Do not display a fake translated
  // subtitle; a translation provider must be added before this option can be
  // advertised as supported.
  if (translateToEnglish && detectedLang !== 'en') {
    for (const line of lines) {
      line.translation = '';
    }
  }

  // 4. Cluster lines into musical sections
  const sections = groupIntoMusicalSections(lines, audioDuration);

  const songId = title.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'song';

  return {
    id: songId,
    title,
    subtitle: subtitle || (detectedLang !== 'en' ? `${LANGUAGE_NAMES[detectedLang] || detectedLang} Lyric Film` : 'Horizon'),
    artist,
    audio: audioPath.replace(/^public\//, ''),
    duration: parseFloat(audioDuration.toFixed(2)),
    palette: 'dusk',
    detectedLanguage: LANGUAGE_NAMES[detectedLang] || detectedLang,
    languageConfidence: langConfidence,
    sections,
  };
}
