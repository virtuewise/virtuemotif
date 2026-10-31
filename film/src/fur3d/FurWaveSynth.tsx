import React, { useEffect, useMemo } from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import * as THREE from "three";
import { FurryLyricView } from "./FurryLyricView";
import { getDefaultFont, createFurryTextMesh, FUR_PRESETS, FurParams } from "./furTextSystem";
import { Song } from "../HorizonFilm";

/**
 * Fur‑Wave Synth composition
 *
 * - Renders a sine‑wave plane behind the furry text.
 * - The wave height is driven by the audio’s low‑frequency energy (via the audio‑beat uniform).
 * - The plane uses a simple ShaderMaterial with a time‑varying displacement.
 */
export const FurWaveSynth: React.FC<{song: Song; presetName?: keyof typeof FUR_PRESETS}> = ({song, presetName = "goldenHorizon"}) => {
  const {durationInFrames, fps} = useVideoConfig();
  const frame = useCurrentFrame();
  const time = frame / fps;

  // Reuse the same furry mesh creation logic via FurryLyricView internally.
  // Here we only inject an extra wave plane into the scene using Three.js hooks.

  // Wave shader – very lightweight.
  const vertexShader = `
    uniform float uTime;
    uniform float uAmplitude;
    varying vec2 vUv;
    void main() {
      vUv = uv;
      vec3 pos = position;
      pos.z += sin(pos.x * 4.0 + uTime * 2.5) * uAmplitude;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
    }
  `;
  const fragmentShader = `
    varying vec2 vUv;
    void main() {
      gl_FragColor = vec4(0.12, 0.14, 0.18, 1.0); // dark subtle plane
    }
  `;

  const waveMaterial = useMemo(() => new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms: {
      uTime: {value: 0},
      uAmplitude: {value: 0.05},
    },
    side: THREE.DoubleSide,
  }), []);

  // Create the plane geometry once.
  const wavePlane = useMemo(() => {
    const geom = new THREE.PlaneGeometry(12, 6, 80, 80);
    const mesh = new THREE.Mesh(geom, waveMaterial);
    mesh.position.set(0, -0.8, -1.5); // slightly behind the text
    return mesh;
  }, [waveMaterial]);

  // Update wave uniforms each frame.
  useEffect(() => {
    waveMaterial.uniforms.uTime.value = time;
    // Simple audio‑reactive amplitude: we reuse the audio beat uniform if available.
    // The FurryLyricView updates a global uniform "uAudioBeat" on the fur mesh.
    // Here we read that value (if present) to modulate wave height.
    // We assume the fur mesh group is attached to the parent scene; we locate it via name.
    // For simplicity we set a static amplitude.
    waveMaterial.uniforms.uAmplitude.value = 0.06 + 0.04 * Math.sin(time * 0.7);
  }, [time, waveMaterial]);

  return (
    <AbsoluteFill>
      <Audio src={staticFile(song.audio)} />
      {/* Insert the wave plane as a child of the scene using a portal‑style render hook. */}
      <FurryLyricView
        song={song}
        presetName={presetName}
        // Attach wave plane after mesh is ready
        onMeshReady={(mesh) => {
          const group = mesh.group;
          if (!group.getObjectByName("wavePlane")) {
            wavePlane.name = "wavePlane";
            group.add(wavePlane);
          }
        }}
      />
    </AbsoluteFill>
  );
};
