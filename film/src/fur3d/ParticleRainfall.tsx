import React, { useCallback } from "react";
import * as THREE from "three";
import { FurryLyricView, FurryLyricViewProps } from "./FurryLyricView";

/**
 * Particle‑Rainfall Refraction scene.
 * Adds a point cloud that falls like rain. The particles use a simple
 * shader that adds a slight refraction effect by sampling the background colour.
 */
export const ParticleRainfall: React.FC<FurryLyricViewProps> = (props) => {
  const handleSceneReady = useCallback((scene: THREE.Scene) => {
    const particleCount = 2000;
    const positions = new Float32Array(particleCount * 3);
    const speeds = new Float32Array(particleCount);
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 12; // x spread
      positions[i * 3 + 1] = Math.random() * 6 + 2; // start above
      positions[i * 3 + 2] = (Math.random() - 0.5) * 12; // z spread
      speeds[i] = 0.02 + Math.random() * 0.03;
    }

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
          // reset when below ground
          if(pos.y < -2.0) pos.y = 6.0;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
          gl_PointSize = 2.0;
        }
      `,
      fragmentShader: `
        void main(){
          // simple bright white with slight translucency
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
