import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { evaluateAudioCues, parseAudioIntelligence, snapEntranceTime, type AudioCueFrame, type AudioIntelligence } from "./audioCues";
import * as THREE from "three";
import {
  createFurryTextMesh,
  FurMeshGroup,
  FUR_PRESETS,
  FurParams,
  getDefaultFont,
} from "./furTextSystem";
import { Song, Line } from "../HorizonFilm";
import { FilmGrain, Vignette } from "../Backdrop";
import { estimateLyricCharacterEquivalent } from "../typography";

/**
 * Props for the furry lyric view.
 * Added callbacks `onSceneReady` and `onMeshReady` to allow external scenes (e.g., wave plane, extra lights) to hook into the three‑js scene.
 */
export interface FurryLyricViewProps {
  song: Song;
  preset?: FurParams;
  presetName?: keyof typeof FUR_PRESETS;
  presetBg?: boolean;
  /** Called after the Three.js scene has been created. */
  onSceneReady?: (scene: THREE.Scene) => void;
  /** Called after the furry mesh group has been created. */
  onMeshReady?: (mesh: FurMeshGroup) => void;
  /** Supplies the frame-synchronous audio cues to effects hosted in the same composition. */
  onAudioCueFrame?: (cueFrame: AudioCueFrame) => void;
}

export const FurryLyricView: React.FC<FurryLyricViewProps> = ({
  song,
  presetName = "goldenHorizon",
  presetBg = true,
  onSceneReady,
  onMeshReady,
  onAudioCueFrame,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [audioCues, setAudioCues] = useState<AudioIntelligence | null>(null);
  const cueRenderHandle = useMemo(() => delayRender("Loading versioned audio intelligence cues"), [song.id]);

  // Cue files are generated from the same audio engine used by the Python pipeline.
  // Missing, stale, or invalid data deliberately falls back to deterministic motion.
  useEffect(() => {
    let cancelled = false;
    let released = false;
    const releaseRender = () => {
      if (!released) {
        released = true;
        continueRender(cueRenderHandle);
      }
    };
    setAudioCues(null);
    fetch(staticFile(`audio-cues/${song.id}.audio-intelligence.json`))
      .then((response) => response.ok ? response.json() : null)
      .then((payload: unknown) => {
        if (!cancelled) setAudioCues(parseAudioIntelligence(payload));
      })
      .catch(() => {
        if (!cancelled) setAudioCues(null);
      })
      .finally(() => {
        if (!cancelled) releaseRender();
      });
    return () => {
      cancelled = true;
      releaseRender();
    };
  }, [song.id, cueRenderHandle]);

  // Synchronously load bundled typeface font
  const font = useMemo(() => getDefaultFont(), []);

  // Three.js scene graph references
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const currentMeshRef = useRef<FurMeshGroup | null>(null);
  const currentTextRef = useRef<string>("");

  const currentTime = frame / fps;
  const cueFrame = evaluateAudioCues(frame, fps, audioCues);

  // Identify active lyric line
  let activeLine: Line | null = null;
  let activeSectionLabel = "";
  for (const section of song.sections) {
    if (currentTime >= section.start && currentTime <= section.end) {
      activeSectionLabel = section.label;
      for (const line of section.lines) {
        if (currentTime >= line.from && currentTime <= line.to) {
          activeLine = line;
          break;
        }
      }
    }
  }

  const displayText = activeLine
    ? activeLine.text
    : currentTime < 40
    ? song.title.toUpperCase()
    : song.subtitle.toUpperCase();

  const snappedEntranceTime = activeLine && audioCues
    ? snapEntranceTime(activeLine.from, audioCues.beats)
    : activeLine?.from ?? 0;
  // A beat before the lyric starts must not make the entrance animation partially complete.
  const lineEntranceTime = activeLine
    ? Math.max(activeLine.from, snappedEntranceTime)
    : snappedEntranceTime;
  const activePreset = FUR_PRESETS[presetName] || FUR_PRESETS.goldenHorizon;

  // Main three.js setup – runs once per frame to stay in sync with Remotion
  useLayoutEffect(() => {
    if (!canvasRef.current || !font) return;
    const canvas = canvasRef.current;

    // Initialise renderer / scene / camera once
    if (!rendererRef.current) {
      const renderer = new THREE.WebGLRenderer({
        canvas,
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      });
      renderer.setPixelRatio(1.0);
      renderer.setSize(width, height);
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.15;
      rendererRef.current = renderer;

      const scene = new THREE.Scene();
      sceneRef.current = scene;

      const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100);
      camera.position.set(0, 0, 6.8);
      cameraRef.current = camera;

      // 3‑point lighting
      const keyLight = new THREE.DirectionalLight("#fff7ed", 1.6);
      keyLight.position.set(3.5, 4.5, 4.0);
      scene.add(keyLight);

      const rimLight = new THREE.DirectionalLight("#fed7aa", 1.4);
      rimLight.position.set(-3.5, 2.5, -4.0);
      scene.add(rimLight);

      const fillLight = new THREE.DirectionalLight("#c4b5fd", 0.6);
      fillLight.position.set(0, -3.0, 2.0);
      scene.add(fillLight);

      const hemiLight = new THREE.HemisphereLight("#fffbeb", "#1e1b4b", 0.75);
      scene.add(hemiLight);

      // Invoke external scene callback if provided
      if (onSceneReady) {
        onSceneReady(scene);
      }
    }

    const scene = sceneRef.current!;
    const camera = cameraRef.current!;
    const renderer = rendererRef.current!;

    // Re‑create fur mesh when the displayed text changes
    if (currentTextRef.current !== displayText) {
      if (currentMeshRef.current) {
        scene.remove(currentMeshRef.current.group);
        currentMeshRef.current.dispose();
        currentMeshRef.current = null;
      }
      const aspect = width / height;
      const isPortrait = aspect < 1.0;
      const baseZ = isPortrait ? 6.8 / Math.max(0.48, aspect * 1.3) : 6.8;
      const frustumH = 2 * baseZ * Math.tan((42 * Math.PI) / 360);
      const frustumW = frustumH * aspect;
      // Proportional safe bounds preventing text from overflowing viewport or colliding with UI
      const maxFitWidth = frustumW * (isPortrait ? 0.80 : 0.82);
      const maxFitHeight = frustumH * (isPortrait ? 0.48 : 0.58);

      const textLen = estimateLyricCharacterEquivalent(displayText);
      const sizeMultiplier = isPortrait ? Math.min(1.0, aspect * 1.35) : 1.0;
      const targetSize =
        (textLen > 36
          ? 0.7
          : textLen > 24
          ? 0.88
          : textLen > 14
          ? 1.15
          : 1.55) * sizeMultiplier;

      const furMesh = createFurryTextMesh(displayText, font, activePreset, {
        size: targetSize,
        depth: 0.28,
        bevelThickness: 0.06,
        bevelSize: 0.04,
        maxFitWidth,
        maxFitHeight,
        maxCharsPerLine: isPortrait ? 12 : 18,
      });
      scene.add(furMesh.group);
      currentMeshRef.current = furMesh;

      // Notify external code about the mesh (e.g., to attach uniforms)
      if (onMeshReady) {
        onMeshReady(furMesh);
      }
    }

    // Camera setup with responsive base distance
    const aspect = width / height;
    const isPortrait = aspect < 1.0;
    const baseZ = isPortrait ? 6.8 / Math.max(0.48, aspect * 1.3) : 6.8;
    const camX = Math.sin(currentTime * 0.35) * 0.35;
    const camY = Math.cos(currentTime * 0.25) * 0.18;
    camera.position.set(camX, camY, baseZ);
    camera.lookAt(0, 0, 0);

    // Audio‑reactive wind and floating motion
    const beatPulse = cueFrame.beatPulse;
    const audioDisplacement = new THREE.Vector3(
      Math.sin(currentTime * 2.8) * (0.12 + cueFrame.energy * 0.12),
      0.04 + cueFrame.energy * 0.12 + beatPulse * 0.22 + cueFrame.transitionIntensity * 0.12,
      Math.cos(currentTime * 2.4) * (0.1 + cueFrame.energy * 0.08),
    );

    // Entrance and positioning animation ("fall on the screen not overlapping" unless motion zoom is applied)
    const isZoomMotion = activeLine?.style === "zoom";
    let enterProgress = 1.0;
    if (activeLine) {
      const lineDuration = Math.max(0.1, activeLine.to - activeLine.from);
      const enterDur = Math.min(0.9, lineDuration * 0.35);
      enterProgress = Math.min(1.0, Math.max(0.0, (currentTime - lineEntranceTime) / enterDur));
    } else {
      // Intro title: "THE HORIZON OF LIGHT"
      enterProgress = Math.min(1.0, Math.max(0.0, currentTime / 1.5));
    }

    // Easing for falling into center
    const easeOutCubic = (val: number) => 1 - Math.pow(1 - val, 3);
    const eased = easeOutCubic(enterProgress);

    const mesh = currentMeshRef.current;
    if (mesh) {
      // If motion zoom is explicitly requested, zoom in from scale 0.35 to 1.0;
      // otherwise text falls into place from above (+1.45 world units down to 0)
      if (isZoomMotion) {
        const zoomScale = (0.35 + 0.65 * eased) * (1 + beatPulse * 0.025 + cueFrame.transitionIntensity * 0.04);
        const scale = mesh.fitScale * zoomScale;
        mesh.group.scale.set(scale, scale, scale);
        mesh.group.position.y = Math.sin(currentTime * 1.1) * 0.08;
      } else {
        const fallY = (1.0 - eased) * 1.45; // Smoothly drops and settles into screen center
        mesh.group.position.y = fallY + Math.sin(currentTime * 1.1) * 0.08;
        const beatScale = 1 + beatPulse * 0.025 + cueFrame.transitionIntensity * 0.04;
        const scale = mesh.fitScale * beatScale;
        mesh.group.scale.set(scale, scale, scale);
      }

      mesh.group.rotation.y = Math.sin(currentTime * 0.5) * 0.09;
      mesh.group.rotation.x = Math.cos(currentTime * 0.35) * 0.04;
      mesh.update(currentTime, audioDisplacement);
    }

    // Publish the exact same frame cues used for the typography and scene motion.
    // Consumers can update their own shader uniforms before this frame is rendered.
    onAudioCueFrame?.(cueFrame);

    // Render the frame
    renderer.render(scene, camera);
  }, [font, displayText, activePreset, currentTime, width, height, onSceneReady, onMeshReady, onAudioCueFrame, cueFrame.time, cueFrame.beatPulse, cueFrame.energy, cueFrame.transitionIntensity]);

  // Fade in/out based on lyric line progress or title entrance
  const lineProgress = activeLine
    ? (currentTime - lineEntranceTime) / Math.max(0.1, activeLine.to - lineEntranceTime)
    : Math.min(1.0, currentTime / 1.5);
  const opacity = activeLine
    ? interpolate(lineProgress, [0, 0.08, 0.9, 1], [0, 1, 1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : interpolate(currentTime, [0, 0.4, 38, 40], [0, 1, 1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });

  return (
    <AbsoluteFill
      style={{
        background: presetBg
          ? "radial-gradient(110% 90% at 50% 20%, #1c1917 0%, #0c0a09 70%, #050505 100%)"
          : "transparent",
      }}
    >
      <AbsoluteFill style={{ opacity }}>
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          style={{
            width: "100%",
            height: "100%",
            display: "block",
          }}
        />
      </AbsoluteFill>

      {/* Translation or subtitle kicker */}
      {activeLine && activeLine.translation ? (
        <div
          style={{
            position: "absolute",
            bottom: width < height ? "180px" : "80px",
            width: "100%",
            textAlign: "center",
            padding: width < height ? "0 32px" : "0",
            boxSizing: "border-box",
            color: "#f6e7c8",
            opacity: 0.88,
            fontSize: width < height ? "20px" : "26px",
            fontFamily: "Space Grotesk, sans-serif",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            textShadow: "0 2px 14px rgba(0,0,0,0.85)",
          }}
        >
          {activeLine.translation}
        </div>
      ) : !activeLine ? (
        <div
          style={{
            position: "absolute",
            bottom: width < height ? "180px" : "80px",
            width: "100%",
            textAlign: "center",
            padding: width < height ? "0 32px" : "0",
            boxSizing: "border-box",
            color: "#e8a33d",
            opacity: 0.8,
            fontSize: width < height ? "18px" : "22px",
            fontFamily: "Space Grotesk, sans-serif",
            letterSpacing: "0.22em",
            textTransform: "uppercase",
            textShadow: "0 2px 12px rgba(0,0,0,0.8)",
          }}
        >
          {song.subtitle} · {song.artist}
        </div>
      ) : null}

      {/* Corner badge */}
      <div
        style={{
          position: "absolute",
          top: width < height ? "64px" : "36px",
          right: width < height ? "24px" : "42px",
          color: "#e8a33d",
          opacity: 0.7,
          fontSize: width < height ? "12px" : "14px",
          fontFamily: "Space Grotesk, sans-serif",
          letterSpacing: "0.15em",
          textTransform: "uppercase",
        }}
      >
        GPU Fur Motion 3D · {activeSectionLabel || "Intro"}
      </div>

      {presetBg ? (
        <>
          <FilmGrain frame={frame} />
          <Vignette />
        </>
      ) : null}
    </AbsoluteFill>
  );
};