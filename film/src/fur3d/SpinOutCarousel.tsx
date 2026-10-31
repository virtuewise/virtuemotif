import React, { useCallback } from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import * as THREE from "three";
import { FurryLyricView, FurryLyricViewProps } from "./FurryLyricView";
import { Song } from "../HorizonFilm";
import horizon from "../data/horizon.json";

/**
 * SpinOutCarousel – camera circles around the fur text while the fur group spins.
 * The camera follows a circular trajectory based on the current frame.
 */
export const SpinOutCarousel: React.FC = () => {
  const HORIZON = horizon as unknown as Song;

// No separate scene handler needed; camera animation handled via onMeshReady.

  const handleMeshReady = useCallback((mesh: any) => {
    const group = mesh.group;
    const onBeforeRender = (renderer: THREE.WebGLRenderer, scene: THREE.Scene, camera: THREE.Camera) => {
      const { fps } = (window as any).remotion?.videoConfig || { fps: 30 };
      const frame = (window as any).remotion?.currentFrame || 0;
      const time = frame / fps;
      const radius = 6.5;
      const angle = time * 0.5; // rotate speed
      const cam = camera as THREE.PerspectiveCamera;
      cam.position.set(Math.cos(angle) * radius, Math.sin(angle) * 0.5, Math.sin(angle) * radius);
      cam.lookAt(0, 0, 0);
      // Spin the fur group itself
      group.rotation.y = time * 0.7;
    };
    const scene = group.parent as THREE.Scene;
    if (scene) {
      scene.onBeforeRender = onBeforeRender;
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
