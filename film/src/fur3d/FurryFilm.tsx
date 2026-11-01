import React from "react";
import { AbsoluteFill, Audio, staticFile } from "remotion";
import { Song } from "../HorizonFilm";
import { FurryLyricView } from "./FurryLyricView";
import { FUR_PRESETS } from "./furTextSystem";
import { AutoLyricsPanel } from "../ui/AutoLyricsPanel";

export interface FurryFilmProps {
  song: Song;
  presetName?: keyof typeof FUR_PRESETS;
}

export const FurryFilm: React.FC<FurryFilmProps> = ({ song, presetName = "goldenHorizon" }) => {
  const hasSubtitles = song.sections.some((section) => section.lines.some((line) => Boolean(line.translation?.trim())));

  return (
    <AbsoluteFill>
      <Audio src={staticFile(song.audio)} />
      <FurryLyricView song={song} presetName={presetName} presetBg={true} />
      {song.detectedLanguage ? (
        <AutoLyricsPanel
          song={song}
          detectedLanguage={song.detectedLanguage}
          confidence={song.languageConfidence ?? 0}
          isTranslating={hasSubtitles}
          reviewRequired={song.reviewRequired ?? false}
        />
      ) : null}
    </AbsoluteFill>
  );
};
