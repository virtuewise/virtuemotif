// scripts/generate_lyrics.ts
// Command-line Smart Auto Lyrics Generator
// Run with: node --experimental-strip-types scripts/generate_lyrics.ts [options]

import fs from 'node:fs';
import path from 'node:path';
import { generateAutoLyrics } from '../src/lyrics/WhisperEngine';
import { formatSongJson } from '../src/lyrics/SongBuilder';

function parseArgs(): Record<string, string> {
  const args = process.argv.slice(2);
  const result: Record<string, string> = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith('--')) {
      const key = arg.replace(/^--/, '');
      const next = args[i + 1];
      if (next && !next.startsWith('--')) {
        result[key] = next;
        i++;
      } else {
        result[key] = 'true';
      }
    }
  }

  return result;
}

async function main() {
  const options = parseArgs();
  const audioInput = options.audio || 'public/audio/horizon.m4a';
  const title = options.title || path.basename(audioInput, path.extname(audioInput)).replace(/[-_]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  const subtitle = options.subtitle || 'Smart Auto Lyrics';
  const artist = options.artist || 'virtuemotif';
  const language = options.language || 'auto';
  const outFile = options.out || `src/data/${path.basename(audioInput, path.extname(audioInput))}.json`;

  console.log('='.repeat(65));
  console.log('  VIRTUEMOTIF SMART AUTO LYRICS GENERATOR');
  console.log('='.repeat(65));
  console.log(`🎵 Audio file : ${audioInput}`);
  console.log(`🏷️  Title      : ${title}`);
  console.log(`👤 Artist     : ${artist}`);
  console.log(`🌐 Language   : ${language} (auto-detect all languages & accents)`);
  console.log(`💾 Output     : ${outFile}`);
  console.log('-'.repeat(65));

  const resolvedAudioPath = path.resolve(audioInput);
  if (!fs.existsSync(resolvedAudioPath)) {
    console.error(`❌ Error: Audio file not found at: ${resolvedAudioPath}`);
    process.exit(1);
  }

  console.log('⏳ Processing audio & running multilingual speech recognition...');

  try {
    const song = await generateAutoLyrics({
      audioPath: audioInput,
      title,
      subtitle,
      artist,
      language,
      translateToEnglish: true,
      apiKey: options.apiKey,
      endpointUrl: options.endpoint,
    });

    console.log(`✅ Transcription complete!`);
    console.log(`   - Detected language : ${song.detectedLanguage || 'English'}`);
    console.log(`   - Total duration    : ${song.duration}s`);
    console.log(`   - Musical sections  : ${song.sections.length} sections (${song.sections.map((s) => s.id).join(', ')})`);
    const totalLines = song.sections.reduce((acc, s) => acc + s.lines.length, 0);
    console.log(`   - Total lyric lines : ${totalLines}`);

    const jsonString = formatSongJson(song);
    const resolvedOut = path.resolve(outFile);
    fs.mkdirSync(path.dirname(resolvedOut), { recursive: true });
    fs.writeFileSync(resolvedOut, jsonString, 'utf-8');

    console.log('-'.repeat(65));
    console.log(`🎉 Saved song JSON to: ${resolvedOut}`);
    console.log('='.repeat(65));
  } catch (err: any) {
    console.error('❌ Failed to generate lyrics:', err.message || err);
    process.exit(1);
  }
}

main().catch(console.error);
