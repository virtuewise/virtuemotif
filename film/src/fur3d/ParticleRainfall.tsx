import React, { useCallback, useMemo } from "react";
import * as THREE from "three";
import { FurryLyricView, FurryLyricViewProps } from "./FurryLyricView";
import { audioReactiveParticleFallRate, type AudioCueFrame } from "./audioCues";
import { createRainfallParticleData } from "./deterministicParticles";

/**
 * Particle‑Rainfall Refraction scene.
 * Seeded particle geometry plus frame-synchronous audio uniforms keep still and
 * full renders consistent while letting the energy envelope shape the motion.
 */
export const ParticleRainfall: React.FC<FurryLyricViewProps> = (props) => {
  const material = useMemo(() => new THREE.ShaderMaterial({
    vertexShader: `
      attribute float aSpeed;
      uniform float uTime;
      uniform float uFallRate;
      void main() {
        vec3 pos = position;
        pos.y -= aSpeed * uTime * 60.0 * uFallRate;
        // Wrap particles in a stable time-derived cycle.
        float span = 10.0;
        pos.y = mod(pos.y + 2.0, span) - 2.0;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        gl_PointSize = 2.0;
      }
    `,
    fragmentShader: `
      void main() {
        gl_FragColor = vec4(0.9, 0.95, 1.0, 0.75);
      }
    `,
    uniforms: {
      uTime: { value: 0 },
      uFallRate: { value: 1 },
    },
    transparent: true,
    depthWrite: false,
  }), []);

  const handleSceneReady = useCallback((scene: THREE.Scene) => {
    if (scene.getObjectByName("RainPoints")) return;
    const { positions, speeds } = createRainfallParticleData(2000, 1);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("aSpeed", new THREE.BufferAttribute(speeds, 1));
    const points = new THREE.Points(geometry, material);
    points.name = "RainPoints";
    scene.add(points);
  }, [material]);

  const handleAudioCueFrame = useCallback((cueFrame: AudioCueFrame) => {
    material.uniforms.uTime.value = cueFrame.time;
    material.uniforms.uFallRate.value = audioReactiveParticleFallRate(cueFrame);
  }, [material]);

  return (
    <FurryLyricView
      {...props}
      onSceneReady={handleSceneReady}
      onAudioCueFrame={handleAudioCueFrame}
    />
  );
};
