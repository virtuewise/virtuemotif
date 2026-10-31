import React, { useEffect, useMemo, useRef } from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import * as THREE from "three";
import { FurryLyricView, FurryLyricViewProps } from "./FurryLyricView";
import { Song } from "../HorizonFilm";
import { FUR_PRESETS } from "./furTextSystem";

/**
 * Neon‑Pulse Cityscape composition
 *
 * - Adds a low‑poly skyline (boxes) behind the furry text.
 * - Each building uses an emissive material whose intensity follows the audio beat (via the fur mesh uniform `uAudioBeat`).
 * - The skyline is static in position but glows rhythmically.
 */
export const NeonPulseCityscape: React.FC<{song: Song; presetName?: keyof typeof FUR_PRESETS}> = ({
  song,
  presetName = "goldenHorizon",
}) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const time = frame / fps;

  // References to objects that need per‑frame updates
  const cityGroupRef = useRef<THREE.Group | null>(null);
  const furMeshRef = useRef<any>(null); // we only need uniforms.uAudioBeat

  // Build the skyline once
  const buildCity = useMemo(() => {
    const group = new THREE.Group();
    const buildingMaterial = new THREE.MeshStandardMaterial({
      color: new THREE.Color("#111827"), // dark base color
      emissive: new THREE.Color("#0ff"), // neon cyan base emissive
      emissiveIntensity: 0.0,
      roughness: 0.8,
    });

    // Simple procedural skyline – 12 buildings spaced across X
    const count = 12;
    for (let i = 0; i < count; i++) {
      const width = 0.8 + Math.random() * 0.4;
      const depth = 0.8 + Math.random() * 0.4;
      const height = 1.5 + Math.random() * 3.0;
      const geometry = new THREE.BoxGeometry(width, height, depth);
      const mesh = new THREE.Mesh(geometry, buildingMaterial.clone());
      mesh.position.set(-5 + i * (10 / (count - 1)), height / 2 - 0.2, -2.5);
      group.add(mesh);
    }
    group.name = "NeonCityGroup";
    return group;
  }, []);

  // Callback when three‑js scene is ready – attach the skyline
  const handleSceneReady = (scene: THREE.Scene) => {
    if (!cityGroupRef.current) {
      scene.add(buildCity);
      cityGroupRef.current = buildCity;
    }
  };

  // Callback when the fur mesh is ready – keep a reference to its uniforms
  const handleMeshReady = (mesh: any) => {
    furMeshRef.current = mesh;
  };

  // Per‑frame update – drive neon emissive intensity from the audio beat uniform
  useEffect(() => {
    if (!cityGroupRef.current || !furMeshRef.current) return;
    // The fur shader provides a Vector3 `uAudioBeat` where length corresponds to beat strength.
    const audioBeat = furMeshRef.current.uniforms?.uAudioBeat?.value as THREE.Vector3 | undefined;
    const beatStrength = audioBeat ? audioBeat.length() : 0;
    // Map beat strength (0‑~1) to emissive intensity (0‑2)
    const intensity = THREE.MathUtils.lerp(0.2, 1.8, Math.min(1, beatStrength));
    // Update emissive intensity on each building material
    cityGroupRef.current.traverse((obj) => {
      if ((obj as THREE.Mesh).isMesh) {
        const mat = (obj as THREE.Mesh).material as THREE.MeshStandardMaterial;
        mat.emissiveIntensity = intensity;
      }
    });
  }, [time]);

  return (
    <AbsoluteFill>
      <Audio src={staticFile(song.audio)} />
      <FurryLyricView
        song={song}
        presetName={presetName}
        onSceneReady={handleSceneReady}
        onMeshReady={handleMeshReady}
        presetBg={true}
      />
    </AbsoluteFill>
  );
};
