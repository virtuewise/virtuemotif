// src/fur3d/SmartFurScene.tsx
// Integrated smart pipeline composition with multi-aspect ratio and full-resolution support.
// Production renders use deterministic defaults; adaptive learning and live pose input are preview-only.

import React, { useEffect, useState, useCallback, useRef } from "react";
import { AbsoluteFill, Audio, staticFile, useVideoConfig } from "remotion";
import * as THREE from "three";
import { FurryLyricView } from "./FurryLyricView";
import horizon from "../data/horizon.json";
import { Song } from "../HorizonFilm";
import { router } from "../pipe/TaskRouter";
import { poseResult$, sdResult$ } from "../pipe/DataFlow";
import { RatingBar } from "../ui/RatingBar";
import { qBandit, BanditAction } from "../optimiser/QBandit";
import { resolveSmartFurRenderAction } from "./smartFurRenderMode";

const HORIZON: Song = horizon as unknown as Song;

export const SmartFurScene: React.FC<{
  song?: Song;
  presetName?: keyof typeof import("./furTextSystem").FUR_PRESETS;
  /** Enable browser-persisted Q-learning and live pose input for interactive previews only. */
  adaptivePreview?: boolean;
}> = ({
  song = HORIZON,
  presetName = "goldenHorizon",
  adaptivePreview = false,
}) => {
  const { width, height } = useVideoConfig();
  const aspect = width / height;

  const [bgTextureUrl, setBgTextureUrl] = useState<string | null>(null);
  const [rating, setRating] = useState<number>(0);
  const [banditAction, setBanditAction] = useState<BanditAction>(
    resolveSmartFurRenderAction(false),
  );

  const poseLandmarksRef = useRef<Float32Array | null>(null);

  // Learned actions depend on IndexedDB and random exploration, so production renders opt out.
  useEffect(() => {
    let cancelled = false;
    if (!adaptivePreview) {
      setBanditAction(resolveSmartFurRenderAction(false));
      return () => {
        cancelled = true;
      };
    }
    qBandit.selectAction().then((action) => {
      if (!cancelled) setBanditAction(resolveSmartFurRenderAction(true, action));
    });
    return () => {
      cancelled = true;
    };
  }, [adaptivePreview]);

  // Live pose streams are non-reproducible inputs and are preview-only.
  useEffect(() => {
    poseLandmarksRef.current = null;
    if (!adaptivePreview) return;
    const sub = poseResult$.subscribe((landmarks) => {
      poseLandmarksRef.current = landmarks;
    });
    return () => {
      sub.unsubscribe();
      poseLandmarksRef.current = null;
    };
  }, [adaptivePreview]);

  // Generate the procedural backdrop at the composition's target aspect ratio.
  useEffect(() => {
    const texWidth =
      width >= 3840 ? 3840 : width === 1080 && height === 1920 ? 1080 : width === height ? 1024 : 1920;
    const texHeight =
      height >= 2160 ? 2160 : width === 1080 && height === 1920 ? 1920 : width === height ? 1024 : 1080;

    router
      .enqueue("sd", async () => {
        const canvas = document.createElement("canvas");
        canvas.width = texWidth;
        canvas.height = texHeight;
        const ctx = canvas.getContext("2d")!;
        const gradient = ctx.createRadialGradient(
          texWidth / 2,
          texHeight * 0.3,
          texWidth * 0.1,
          texWidth / 2,
          texHeight / 2,
          texWidth * 0.8,
        );
        gradient.addColorStop(0, "#2e1c38");
        gradient.addColorStop(0.4, "#1b172a");
        gradient.addColorStop(0.8, "#0d0d18");
        gradient.addColorStop(1, "#05050a");
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, texWidth, texHeight);

        ctx.fillStyle = "rgba(235, 175, 85, 0.12)";
        for (let i = 0; i < 60; i += 1) {
          const px = ((Math.sin(i * 12.3) + 1) / 2) * texWidth;
          const py = ((Math.cos(i * 45.6) + 1) / 2) * texHeight;
          const radius = (Math.sin(i) + 1.5) * 1.8;
          ctx.beginPath();
          ctx.arc(px, py, radius, 0, Math.PI * 2);
          ctx.fill();
        }
        return { dataUrl: canvas.toDataURL("image/png") };
      })
      .then((res) => {
        sdResult$.next(res.dataUrl);
        setBgTextureUrl(res.dataUrl);
      })
      .catch(console.error);
  }, [width, height]);

  const handleSceneReady = useCallback(
    (scene: THREE.Scene) => {
      if (!bgTextureUrl) return;
      const existing = scene.getObjectByName("bgPlane");
      if (existing) scene.remove(existing);

      const tex = new THREE.TextureLoader().load(bgTextureUrl);
      tex.minFilter = THREE.LinearFilter;
      const material = new THREE.MeshBasicMaterial({ map: tex });
      const planeHeight = 7.5;
      const planeWidth = planeHeight * aspect;
      const geometry = new THREE.PlaneGeometry(planeWidth, planeHeight);
      const mesh = new THREE.Mesh(geometry, material);
      mesh.name = "bgPlane";
      mesh.position.set(0, 0, -2.0);
      scene.add(mesh);
    },
    [bgTextureUrl, aspect],
  );

  const handleMeshReady = useCallback(
    (furGroup: any) => {
      const group = furGroup.group;
      if (!group) return;

      const scene = group.parent as THREE.Scene;
      if (scene) {
        const original = scene.onBeforeRender;
        scene.onBeforeRender = function (
          renderer: any,
          scn: any,
          cam: any,
          geometry: any,
          material: any,
          grp: any,
        ) {
          if (original) (original as any).call(this, renderer, scn, cam, geometry, material, grp);

          if (adaptivePreview) {
            const furMesh: any = group.children?.find((child: any) => child.material?.uniforms?.uAudioBeat);
            if (furMesh?.material?.uniforms?.uAudioBeat) {
              furMesh.material.uniforms.uAudioBeat.value.multiplyScalar(banditAction.beatSensitivity / 1.5);
            }

            if (poseLandmarksRef.current) {
              const noseX = poseLandmarksRef.current[0] ?? 0.5;
              const noseY = poseLandmarksRef.current[1] ?? 0.5;
              group.rotation.z = (noseX - 0.5) * 0.1;
              group.position.x = (noseY - 0.5) * 0.15;
            }
          }
        };
      }
    },
    [adaptivePreview, banditAction],
  );

  const handleRate = useCallback(
    (val: number) => {
      setRating(val);
      if (adaptivePreview) qBandit.updateQ(val, banditAction);
    },
    [adaptivePreview, banditAction],
  );

  return (
    <AbsoluteFill>
      <Audio src={staticFile(song.audio)} />
      <FurryLyricView
        song={song}
        presetName={presetName}
        presetBg={false}
        onSceneReady={handleSceneReady}
        onMeshReady={handleMeshReady}
      />
      <RatingBar compositionId="SmartFurScene" onRate={handleRate} />
    </AbsoluteFill>
  );
};
