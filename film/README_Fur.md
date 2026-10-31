# GPU‑Fur Text Components Documentation

This document describes the new 3‑D fur‑shaded text components added to the **virtuemotif** Remotion project. The components live in the `film/src/fur3d/` folder and can be used to create animated, audio‑reactive fur typography for lyric videos.

---

## Overview
- **Fur Shaders** – Implemented in `furShaders.ts`, providing a Marschner‑style BSDF and audio‑reactive wind uniforms.
- **Fur Text System** – Utility functions in `furTextSystem.ts` for creating instanced fur meshes from a Three.js `Font`. Includes several preset parameter sets.
- **FurryLyricView** – A Remotion React component that drives the fur mesh based on lyric timing and audio analysis.
- **FurryFilm** – Simple wrapper composition that loads the audio track and renders `FurryLyricView`.

The new compositions are registered in `Root.tsx`:
```tsx
export const FurryHorizon = () => <FurryFilm preset="goldenHorizon" />;
export const FurryRise = () => <FurryFilm preset="electricCyan" />;
export const FurryProof = () => <FurryFilm preset="emeraldGlow" />;
```

---

## Installing Dependencies
The fur system relies on **three** and the TypeScript typings for React:
```bash
cd film
npm install three @types/react @types/react-dom
```

---

## Core API
### `FurParams`
```ts
export type FurParams = {
  length: number;          // Fur strand length (world units)
  density: number;         // Number of strands per cm²
  width: number;           // Base strand thickness
  color: THREE.Color;      // Base color of the fur
  hairColor?: THREE.Color; // Optional tip color for gradient effect
  windStrength?: number;   // Amplitude of the audio‑reactive wind
  windFrequency?: number;  // Frequency of wind oscillation
};
```

### Presets (exported from `furTextSystem.ts`)
| Preset | Description |
|--------|-------------|
| `goldenHorizon` | Warm gold hue, moderate length, subtle wind – good for sunrise‑style titles. |
| `sakuraMochi`   | Soft pink‑purple, short dense fur, gentle wind – suited for delicate lyric sections. |
| `electricCyan`  | Vibrant cyan with longer strands and stronger wind – creates a dynamic, cyber‑punk feel. |
| `emeraldGlow`   | Deep green with a hint of gold tip, medium length – works well for nature‑themed videos. |

You can import a preset and pass it to the film component:
```tsx
import { FurryFilm } from "./FurryFilm";
import { goldenHorizon } from "./fur3d/furTextSystem";

export const MyFurTitle = () => <FurryFilm preset="goldenHorizon" />;
```

---

## Using the Components
### 1. Add the composition to `Root.tsx`
```tsx
import { FurryFilm } from "./fur3d/FurryFilm";

export const MyFurComposition = () => (
  <FurryFilm preset="electricCyan" audioFile="/audio/mytrack.mp3" />
);
```
> **Note**: `audioFile` defaults to `public/audio/default.mp3` if omitted.

### 2. Provide lyric timing (optional)
`FurryLyricView` expects a `lyrics` prop of the form:
```ts
type LyricLine = { text: string; start: number; end: number };
const lyrics: LyricLine[] = [
  { text: "Hello", start: 0, end: 2 },
  { text: "World", start: 2, end: 4 },
];
```
If omitted, the component will display the preset text "Fur Typography".

### 3. Render frames or a full video
```bash
# Render a single frame (for a showcase image)
npx remotion render src/index.ts FurryProof out/furry_showcase.png --still-frame 60

# Render the full video (default 30 fps, 10 s duration in this example)
npx remotion render src/index.ts FurryHorizon out/furry_video.mp4
```
The CLI respects the audio length and will stop when the track ends.

---

## File Structure
```
film/
├─ public/
│  └─ fonts/
│     ├─ helvetiker_bold.typeface.json   # bundled default font
│     └─ optimer_bold.typeface.json       # optional alternative
├─ src/
│  ├─ fur3d/
│  │  ├─ furShaders.ts          # GLSL shaders for fur rendering
│  │  ├─ furTextSystem.ts       # Geometry creation, presets, helpers
│  │  ├─ FurryLyricView.tsx     # Main React component handling animation
│  │  └─ FurryFilm.tsx          # Wrapper composition
│  └─ Root.tsx                  # Registers the new compositions
└─ tsconfig.json               # Project‑specific TypeScript config
```

---

## Tips & Gotchas
- **Synchronous Font Loading** – The font is loaded synchronously via `FontLoader.parse` on the bundled JSON. Do **not** replace it with an async loader unless you also handle Remotion’s `continueRender` flow.
- **Performance** – High `density` values increase strand count exponentially. For 1080p renders, `density ≤ 30` gives a good balance between quality and render time.
- **Audio Reactive Wind** – The `windStrength` uniform is driven by the audio’s average amplitude per frame. Adjust the `windFrequency` preset to change the visual jitter.
- **Export Settings** – When exporting a video, you may want to increase the `--quality` flag for smoother fur edges:
  ```bash
  npx remotion render src/index.ts FurryProof out/video.mp4 --quality high
  ```

---

## License
The fur‑shader code is adapted from the original **3D‑GPU‑Fur‑Simulation** project (MIT License). The surrounding wrapper and TypeScript utilities are released under the same MIT license as the rest of the `virtuemotif` repository.

## Template Scenes

| Composition ID | Description |
|---|---|
| FurWaveSynth | Fur‑Wave Synth – audio‑reactive fur strands moving in a wave pattern. |
| NeonPulseCityscape | Neon‑Pulse Cityscape – glowing neon outlines with pulse‑driven intensity. |
| DynamicLightRim | Dynamic Light‑Rim – rim lighting that reacts to audio beats. |
| FurMaskReveal | Fur‑Mask Reveal – mask shader reveals fur inside rotating shape. |
| ParticleRainfall | Particle‑Rainfall Refraction – rain particles refracting over fur. |
| FurMorphGlyphs | Fur‑Morph Glyphs – glyph morphing between two fonts. |
| KaleidoscopicMirrors | Kaleidoscopic Mirrors – multiple rotated fur groups forming a kaleidoscope. |
| FurFogDepthCue | Fur‑Fog Depth Cue – exponential depth‑based fog applied to fur. |
| SpinOutCarousel | Spin‑Out Carousel – camera circles around fur text while it spins. |
| GlitchDistortionOverlay | Glitch Distortion Overlay – full‑screen glitch effect driven by audio beat. |
| SmartFurScene | Smart Fur (16:9 Landscape 1080p) – integrated pipeline with pose estimation, full-res diffusion background, rating UI, and Q-learning bandit. |
| SmartFurScene4K | Smart Fur (16:9 Landscape 4K UHD 3840×2160) – Ultra HD composition. |
| SmartFurSceneVertical | Smart Fur (9:16 Vertical 1080×1920) – Mobile-first layout optimized for TikTok, Instagram Reels, and YouTube Shorts. |
| SmartFurSceneSquare | Smart Fur (1:1 Square 1024×1024) – Square format for Instagram feed / cover art. |

> **Note**: The `FurFogDepthCue` composition introduces a new shader uniform `uFogDensity` (default `0.4`) to control fog intensity.

---

## Smart Multi-Aspect Pipeline & AI Optimization

The `SmartFurScene` family dynamically adapts typography scale, camera position, and background geometry to different aspect ratios:
- **16:9 Landscape (`1920×1080` & `3840×2160`)**: Full horizontal width, cinematic letterboxing, standard camera drift.
- **9:16 Vertical/Portrait (`1080×1920`)**: Mobile-first vertical framing for TikTok & Instagram Reels. The camera distance and typography scales adapt so fur text never clips on mobile screens, and UI kickers avoid bottom navigation and right-hand action zones.
- **1:1 Square (`1024×1024`)**: Centered framing ideal for social posts and album art.

### Background Generation & Task Router
Background generation occurs via the Stable Diffusion worker (`sd.worker.ts`) or procedural renderer managed by `TaskRouter.ts`. The background plane in Three.js is automatically dimensioned to $7.5 \times aspect$ at $Z = -2.0$, ensuring zero distortion or texture stretching across any aspect ratio.

### Q-Learning Bandit (`QBandit.ts`)
A lightweight reinforcement learning bandit selects and updates visual parameters based on user 5-star ratings persisted to IndexedDB:
- `fogDensity`: Visual depth cue intensity.
- `beatSensitivity`: Audio bass reactivity multiplier for fur strand flutter.

