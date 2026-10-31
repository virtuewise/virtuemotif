import React, { useCallback } from "react";
import { AbsoluteFill, Audio, staticFile } from "remotion";
import * as THREE from "three";
import { FurryLyricView, FurryLyricViewProps } from "./FurryLyricView";
import { Song } from "../HorizonFilm";
import horizon from "../data/horizon.json";

/**
 * Fur Fog Depth Cue – adds exponential depth‑based fog to the fur shader.
 * The fog density uniform is set on the mesh uniform block.
 */
export const FurFogDepthCue: React.FC = () => {
  const HORIZON = horizon as unknown as Song;

  const handleMeshReady = useCallback((mesh: any) => {
    // Set a moderate fog density; tweak as needed.
    if (mesh.uniforms && mesh.uniforms.uFogDensity) {
      mesh.uniforms.uFogDensity.value = 0.4;
    }
  }, []);

  return (
    <AbsoluteFill>
      <Audio src={staticFile(HORIZON.audio)} />
      <FurryLyricView
        song={HORIZON}
        presetName="goldenHorizon"
        presetBg={true}
        onMeshReady={handleMeshReady}
      />
    </AbsoluteFill>
  );
};
