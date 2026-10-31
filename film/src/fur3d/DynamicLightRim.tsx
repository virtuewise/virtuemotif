import React, { useCallback, useEffect } from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import * as THREE from "three";
import { FurryLyricView, FurryLyricViewProps } from "./FurryLyricView";
import { Song } from "../HorizonFilm";
import horizon from "../data/horizon.json";
import { FUR_PRESETS } from "./furTextSystem";

/**
 * Dynamic Light‑Rim composition
 * -------------------------------------------------
 * This scene animates the rim‑light direction and intensity on the fur mesh
 * using the `onMeshReady` callback to gain access to the mesh uniforms.
 * The animation is driven by the current Remotion frame.
 */
const HORIZON = horizon as unknown as Song;

export const DynamicLightRim: React.FC = () => {
  // Hold a mutable reference to the mesh group so the per‑frame effect can access it.
  const meshRef = React.useRef<any>(null);

  // Called when the three‑js scene is ready – we don’t need to add extra objects.
  const handleSceneReady = useCallback((scene: THREE.Scene) => {
    // No custom scene objects for this demo.
  }, []);

  // Called when the furry mesh is created – store the reference.
  const handleMeshReady = useCallback((mesh: any) => {
    meshRef.current = mesh;
  }, []);

  // Per‑frame rim‑light animation.
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const time = frame / fps;

  useEffect(() => {
    const mesh = meshRef.current;
    if (!mesh) return;
    // Animate rim‑light direction in a circular path.
    const angle = time * 0.4; // slower rotation
    const dir = new THREE.Vector3(Math.cos(angle), Math.sin(angle), 0.5).normalize();
    mesh.uniforms.uRimLightDir.value.copy(dir);

    // Pulse rim intensity with a simple sine wave.
    const intensity = 1.2 + Math.abs(Math.sin(time * Math.PI * 1.5)) * 0.4;
    mesh.uniforms.uRimIntensity.value = intensity;
  }, [time]);

  return (
    <AbsoluteFill>
      <Audio src={staticFile(HORIZON.audio)} />
      <FurryLyricView
        song={HORIZON}
        presetName="goldenHorizon"
        presetBg={true}
        onSceneReady={handleSceneReady}
        onMeshReady={handleMeshReady}
      />
    </AbsoluteFill>
  );
};
