import React, { useCallback } from "react";
import { AbsoluteFill, Audio, staticFile } from "remotion";
import * as THREE from "three";
import { FurryLyricView, FurryLyricViewProps } from "./FurryLyricView";
import { Song } from "../HorizonFilm";
import horizon from "../data/horizon.json";

/**
 * GlitchDistortionOverlay – fullscreen glitch effect driven by audio beat.
 * The effect is implemented as a full‑screen quad with a custom fragment shader.
 * The shader intensity is modulated by the `uAudioBeat` uniform (bass amplitude).
 */
export const GlitchDistortionOverlay: React.FC = () => {
  const HORIZON = horizon as unknown as Song;

  const handleMeshReady = useCallback((mesh: any) => {
    const group = mesh.group;
    // Avoid duplicate overlay.
    if (group.getObjectByName("glitchOverlay")) return;

    const geometry = new THREE.PlaneGeometry(2, 2);
    const material = new THREE.ShaderMaterial({
      fragmentShader: `
        uniform float uTime;
        uniform float uIntensity;
        void main(){
          vec2 uv = gl_FragCoord.xy / vec2(1920.0,1080.0);
          // Simple noise based on time & uv
          float noise = fract(sin(dot(uv*10.0 + uTime, vec2(12.9898,78.233))) * 43758.5453);
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
    });
    const quad = new THREE.Mesh(geometry, material);
    quad.name = "glitchOverlay";
    quad.renderOrder = 1000;
    group.add(quad);

    // Update per frame based on audio beat.
    const update = () => {
      const now = performance.now() / 1000;
      material.uniforms.uTime.value = now;
      const furMesh: any = group.children.find((c: any) => (c as any).material?.uniforms?.uAudioBeat);
      if (furMesh && furMesh.material?.uniforms?.uAudioBeat) {
        const beat = furMesh.material.uniforms.uAudioBeat.value;
        material.uniforms.uIntensity.value = beat.length() * 1.5;
      } else {
        material.uniforms.uIntensity.value = 0.0;
      }
    };
    const scene = group.parent as THREE.Scene;
    if (scene) {
      const original = scene.onBeforeRender;
      scene.onBeforeRender = function (renderer: any, scn: any, cam: any, geometry: any, material: any, grp: any) {
        if (original) (original as any).call(this, renderer, scn, cam, geometry, material, grp);
        update();
      };
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
