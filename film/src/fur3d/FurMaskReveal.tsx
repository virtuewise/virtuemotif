import React, { useCallback, useEffect } from "react";
import * as THREE from "three";
import { FurryLyricView, FurryLyricViewProps } from "./FurryLyricView";

/**
 * Fur‑Mask Reveal – a rotating circular mask that reveals the fur only inside the shape.
 * Implemented by adding a full‑screen quad with a custom fragment shader that
 * draws a semi‑transparent dark overlay outside the rotating circle.
 */
export const FurMaskReveal: React.FC<FurryLyricViewProps> = (props) => {
  const handleSceneReady = useCallback((scene: THREE.Scene) => {
    // Full‑screen plane (covers NDC space -1 to 1)
    const geometry = new THREE.PlaneGeometry(2, 2);
    const material = new THREE.ShaderMaterial({
      fragmentShader: `
        uniform float uTime;
        void main(){
          vec2 uv = gl_FragCoord.xy / vec2(1920.0, 1080.0);
          float angle = uTime * 0.5;
          vec2 center = vec2(0.5) + 0.2 * vec2(cos(angle), sin(angle));
          float radius = 0.3;
          float dist = distance(uv, center);
          // Outside the circle -> dark overlay with opacity 0.85
          if(dist > radius){
            gl_FragColor = vec4(0.0, 0.0, 0.0, 0.85);
          } else {
            discard; // inside: keep what was already rendered (the fur)
          }
        }
      `,
      uniforms: { uTime: { value: 0 } },
      transparent: true,
      depthTest: false,
      depthWrite: false,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.renderOrder = 999;
    scene.add(mesh);
    // Update the time uniform each frame
    scene.onBeforeRender = () => {
      material.uniforms.uTime.value = performance.now() / 1000;
    };
  }, []);

  return <FurryLyricView {...props} onSceneReady={handleSceneReady} />;
};
