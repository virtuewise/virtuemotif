import React from "react";
import { Composition } from "remotion";
import { Film, Proof, Song } from "./HorizonFilm";
import { Thumb } from "./Thumb";
import { FurryFilm } from "./fur3d/FurryFilm";
import horizon from "./data/horizon.json";
import rise from "./data/rise.json";
// New 3D scene imports
import { FurWaveSynth } from "./fur3d/FurWaveSynth";
import { NeonPulseCityscape } from "./fur3d/NeonPulseCityscape";
import { DynamicLightRim } from "./fur3d/DynamicLightRim";
import { FurMaskReveal } from "./fur3d/FurMaskReveal";
import { ParticleRainfall } from "./fur3d/ParticleRainfall";
import { FurMorphGlyphs } from "./fur3d/FurMorphGlyphs";
import { KaleidoscopicMirrors } from "./fur3d/KaleidoscopicMirrors";
import { FurFogDepthCue } from "./fur3d/FurFogDepthCue";
import { SpinOutCarousel } from "./fur3d/SpinOutCarousel";
import { GlitchDistortionOverlay } from "./fur3d/GlitchDistortionOverlay";
import { SmartFurScene } from "./fur3d/SmartFurScene";

const HORIZON = horizon as unknown as Song;
const RISE = rise as unknown as Song;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* 3D GPU Fur Motion Typography Compositions */}
      <Composition
        id="FurryHorizon"
        component={FurryFilm as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="FurryRise"
        component={FurryFilm as React.FC}
        defaultProps={{ song: RISE, presetName: "sakuraMochi" }}
        durationInFrames={Math.ceil(RISE.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="FurryProof"
        component={FurryFilm as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={30 * 30} // 30 seconds preview
        fps={30}
        width={1920}
        height={1080}
      />
      {/* 3D GPU Fur Motion Additional Scenes */}
      <Composition
        id="FurWaveSynth"
        component={FurWaveSynth as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="NeonPulseCityscape"
        component={NeonPulseCityscape as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="DynamicLightRim"
        component={DynamicLightRim as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="FurMaskReveal"
        component={FurMaskReveal as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="ParticleRainfall"
        component={ParticleRainfall as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="FurMorphGlyphs"
        component={FurMorphGlyphs as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="KaleidoscopicMirrors"
        component={KaleidoscopicMirrors as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="FurFogDepthCue"
        component={FurFogDepthCue as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="SpinOutCarousel"
        component={SpinOutCarousel as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="GlitchDistortionOverlay"
        component={GlitchDistortionOverlay as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="SmartFurScene"
        component={SmartFurScene as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="SmartFurScene4K"
        component={SmartFurScene as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={3840}
        height={2160}
      />
      <Composition
        id="SmartFurSceneVertical"
        component={SmartFurScene as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="SmartFurSceneSquare"
        component={SmartFurScene as React.FC}
        defaultProps={{ song: HORIZON, presetName: "goldenHorizon" }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        fps={30}
        width={1024}
        height={1024}
      />

      {/* Classic 2D Silhouette & Paper Typography Compositions */}
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
      {/* Generic composition for any Song JSON exported by the auto-lyrics engine. */}
      <Composition
        id="AutoLyrics"
        component={Film}
        defaultProps={{ song: HORIZON }}
        durationInFrames={Math.ceil(HORIZON.duration * 30)}
        calculateMetadata={({ props }) => ({
          durationInFrames: Math.max(1, Math.ceil(props.song.duration * 30)),
        })}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
