import React, { useCallback } from "react";
import * as THREE from "three";
import { FurryLyricView, FurryLyricViewProps } from "./FurryLyricView";
import { createRainfallParticleData } from "./deterministicParticles";

/**
 * Particle‑Rainfall Refraction scene.
 * Adds a point cloud that falls like rain. The particle field is seeded so
 * Remotion still renders are identical across runs and render workers.
 */
export const ParticleRainfall: React.FC<FurryLyricViewProps> = (props) => {
  const handleSceneReady = useCallback((scene: THREE.Scene) => {
    const { positions, speeds } = createRainfallParticleData(2000, 1);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("aSpeed", new THREE.BufferAttribute(speeds, 1));

    const material = new THREE.ShaderMaterial({
      vertexShader: `
        attribute float aSpeed;
        uniform float uTime;
        void main(){
          vec3 pos = position;
          pos.y -= aSpeed * uTime * 60.0; // fall speed
          // Reset below-ground particles in a stable, frame-derived cycle.
          if(pos.y < -2.0) pos.y = 6.0;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
          gl_PointSize = 2.0;
        }
      `,
      fragmentShader: `
        void main(){
          gl_FragColor = vec4(0.9, 0.95, 1.0, 0.75);
        }
      `,
      transparent: true,
      depthWrite: false,
    });

    const points = new THREE.Points(geometry, material);
    points.name = "RainPoints";
    scene.add(points);
  }, []);

  return <FurryLyricView {...props} onSceneReady={handleSceneReady} />;
};
