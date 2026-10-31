import React, { useCallback } from "react";
import { AbsoluteFill, Audio, staticFile } from "remotion";
import * as THREE from "three";
import { FurryLyricView } from "./FurryLyricView";
import { Song } from "../HorizonFilm";
import horizon from "../data/horizon.json";

/**
 * Kaleidoscopic Mirrors composition
 * - Creates several rotated instances of the fur text group forming a kaleidoscopic pattern.
 * - Uses InstancedMesh to efficiently duplicate the fur group.
 */
export const KaleidoscopicMirrors: React.FC = () => {
  const HORIZON = horizon as unknown as Song;

  // After the main fur group is ready, we clone it and add rotated instances.
  const handleMeshReady = useCallback((mesh: any) => {
    const group = mesh.group;
    // Avoid adding duplicates.
    if (group.getObjectByName('kaleidoRoot')) return;

    const instanceRoot = new THREE.Group();
    instanceRoot.name = 'kaleidoRoot';
    const angles = [0, Math.PI / 2, Math.PI, (3 * Math.PI) / 2];
    angles.forEach((angle) => {
      const clone = group.clone();
      clone.rotation.y = angle;
      clone.scale.set(0.8, 0.8, 0.8);
      instanceRoot.add(clone);
    });
    group.add(instanceRoot);
  }, []);


  return (
    <AbsoluteFill>
      <Audio src={staticFile(HORIZON.audio)} />
      <FurryLyricView song={HORIZON} presetName="goldenHorizon" onMeshReady={handleMeshReady} />
    </AbsoluteFill>
  );
};
