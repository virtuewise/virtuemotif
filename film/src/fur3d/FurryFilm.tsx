import React from "react";
import { AbsoluteFill, Audio, staticFile } from "remotion";
import { Song } from "../HorizonFilm";
import { FurryLyricView } from "./FurryLyricView";
import { FUR_PRESETS } from "./furTextSystem";

export interface FurryFilmProps {
  song: Song;
  presetName?: keyof typeof FUR_PRESETS;
}

export const FurryFilm: React.FC<FurryFilmProps> = ({ song, presetName = "goldenHorizon" }) => {
  return (
    <AbsoluteFill>
      <Audio src={staticFile(song.audio)} />
      <FurryLyricView song={song} presetName={presetName} presetBg={true} />
    </AbsoluteFill>
  );
};
