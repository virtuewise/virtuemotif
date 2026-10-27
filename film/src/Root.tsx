import React from "react";
import { Composition } from "remotion";
import { Film, Proof, Song } from "./HorizonFilm";
import { Thumb } from "./Thumb";
import horizon from "./data/horizon.json";
import rise from "./data/rise.json";

const HORIZON = horizon as unknown as Song;
const RISE = rise as unknown as Song;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Horizon"
        component={Film}
        defaultProps={{ song: HORIZON }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="Rise"
        component={Film}
        defaultProps={{ song: RISE }}
        durationInFrames={Math.ceil(RISE.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="Proof"
        component={Proof}
        defaultProps={{ song: HORIZON }}
        durationInFrames={65 * 30}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="ThumbHorizon"
        component={Thumb}
        defaultProps={{ title: "Horizon of Light", subtitle: "Tarisiro", artist: "virtuemotif" }}
        durationInFrames={1}
        fps={30}
        width={1280}
        height={720}
      />
      <Composition
        id="ThumbRise"
        component={Thumb}
        defaultProps={{ title: "Rise Together", subtitle: "Vuka Zimbabwe", artist: "virtuemotif" }}
        durationInFrames={1}
        fps={30}
        width={1280}
        height={720}
      />
    </>
  );
};
