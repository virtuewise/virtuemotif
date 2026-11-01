import React, { useCallback, useMemo } from "react";
import { AbsoluteFill, Audio, staticFile } from "remotion";
import * as THREE from "three";
import { FurryLyricView, FurryLyricViewProps } from "./FurryLyricView";
import { audioReactiveGlitchIntensity, type AudioCueFrame } from "./audioCues";
import { Song } from "../HorizonFilm";
import horizon from "../data/horizon.json";

/**
 * GlitchDistortionOverlay – frame-synchronous glitch treatment.
 * Shader time and intensity come from Remotion's analyzed audio cues, never
 * wall-clock time, so a still render matches the same frame in a full render.
 */
export const GlitchDistortionOverlay: React.FC = () => {
  const HORIZON = horizon as unknown as Song;
  const material = useMemo(() => new THREE.ShaderMaterial({
    vertexShader: `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      varying vec2 vUv;
      uniform float uTime;
      uniform float uIntensity;
      void main() {
        float noise = fract(sin(dot(vUv * 10.0 + uTime, vec2(12.9898, 78.233))) * 43758.5453);
        float glitch = step(0.8, noise) * uIntensity;
        gl_FragColor = vec4(vec3(glitch), glitch);
      }
    `,
    uniforms: {
      uTime: { value: 0 },
      uIntensity: { value: 0 },
    },
    transparent: true,
    depthTest: false,
    depthWrite: false,
  }), []);

  const handleMeshReady = useCallback((mesh: any) => {
    const group = mesh.group;
    if (group.getObjectByName("glitchOverlay")) return;

    const geometry = new THREE.PlaneGeometry(2, 2);
    const quad = new THREE.Mesh(geometry, material);
    quad.name = "glitchOverlay";
    quad.renderOrder = 1000;
    group.add(quad);
  }, [material]);

  const handleAudioCueFrame = useCallback((cueFrame: AudioCueFrame) => {
    material.uniforms.uTime.value = cueFrame.time;
    material.uniforms.uIntensity.value = audioReactiveGlitchIntensity(cueFrame);
  }, [material]);

  return (
    <AbsoluteFill>
      <Audio src={staticFile(HORIZON.audio)} />
      <FurryLyricView
        song={HORIZON}
        presetName="goldenHorizon"
        presetBg={true}
        onMeshReady={handleMeshReady}
        onAudioCueFrame={handleAudioCueFrame}
      />
    </AbsoluteFill>
  );
};
