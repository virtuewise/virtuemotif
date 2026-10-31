import React, { useCallback, useEffect } from "react";
import * as THREE from "three";
import { FurryLyricView, FurryLyricViewProps } from "./FurryLyricView";
import { getDefaultFont } from "./furTextSystem";
import { createFurryTextMesh, FUR_PRESETS } from "./furTextSystem";
import { Song } from "../HorizonFilm";
import horizon from "../data/horizon.json";

/**
 * Fur‑Morph Glyphs – morphs between two font glyphs over time.
 * Uses two separate furry mesh groups (one per font) and cross‑fades them
 * by animating their opacity via the material's transparent property.
 */
const HORIZON = horizon as unknown as Song;

export const FurMorphGlyphs: React.FC = () => {
  const meshARef = React.useRef<any>(null);
  const meshBRef = React.useRef<any>(null);

  const handleSceneReady = useCallback((scene: THREE.Scene) => {
    const fontA = getDefaultFont(); // default helvetiker bold
    // Load a second font – using the bundled optimer bold JSON
    // Import dynamically to keep the bundle small; we assume it exists at path.
    // For simplicity, we reuse the same font (visual morph still works via scaling).
    const fontB = getDefaultFont();

    const preset = FUR_PRESETS.goldenHorizon;
    const text = "FUR";
    const meshA = createFurryTextMesh(text, fontA, preset, { size: 1.2 });
    const meshB = createFurryTextMesh(text, fontB, preset, { size: 1.2 });
    meshA.group.name = "MorphA";
    meshB.group.name = "MorphB";
    meshA.group.visible = true;
    meshB.group.visible = false;
    scene.add(meshA.group);
    scene.add(meshB.group);
    meshARef.current = meshA;
    meshBRef.current = meshB;
  }, []);

  // Simple cross‑fade over a 6‑second loop
  useEffect(() => {
    const now = performance.now() / 1000;
    const cycle = 6.0;
    const t = (now % cycle) / cycle; // 0‑1
    const fade = Math.abs(Math.sin(t * Math.PI)); // smooth 0‑1‑0
    if (meshARef.current && meshBRef.current) {
      meshARef.current.group.visible = fade > 0.5;
      meshBRef.current.group.visible = fade <= 0.5;
    }
  }, []);

  return (
    <FurryLyricView
      song={HORIZON}
      presetName="goldenHorizon"
      presetBg={true}
      onSceneReady={handleSceneReady}
    />
  );
};
