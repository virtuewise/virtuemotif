import * as THREE from "three";
import { Font, FontLoader } from "three/examples/jsm/loaders/FontLoader.js";
import { TextGeometry } from "three/examples/jsm/geometries/TextGeometry.js";
import * as BufferGeometryUtils from "three/examples/jsm/utils/BufferGeometryUtils.js";
import { SHELL_VERTEX_SHADER, SHELL_FRAGMENT_SHADER } from "./furShaders";
import { estimateLyricCharacterEquivalent, wrapWideScriptText } from "../typography";
import helvetikerBoldJson from "../../public/fonts/helvetiker_bold.typeface.json";

export interface FurParams {
  furLength: number;
  furDensity: number;
  clumping: number;
  curliness: number;
  baseColor: string;
  tipColor: string;
  roughness: number;
  specular: number;
  shellCount: number;
  windStrength: number;
  keyLightColor?: string;
  keyLightIntensity?: number;
  rimLightColor?: string;
  rimIntensity?: number;
  ambientIntensity?: number;
}

export const FUR_PRESETS: Record<string, FurParams> = {
  goldenHorizon: {
    furLength: 0.22,
    furDensity: 0.88,
    clumping: 0.42,
    curliness: 0.26,
    baseColor: "#d97706", // Rich amber gold
    tipColor: "#fffbeb", // Glowing warm cream
    roughness: 0.38,
    specular: 1.35,
    shellCount: 42,
    windStrength: 0.85,
    keyLightColor: "#fff7ed",
    keyLightIntensity: 1.5,
    rimLightColor: "#fde68a",
    rimIntensity: 1.35,
    ambientIntensity: 0.65,
  },
  sakuraMochi: {
    furLength: 0.26,
    furDensity: 0.9,
    clumping: 0.5,
    curliness: 0.32,
    baseColor: "#f472b6", // Soft rose pink
    tipColor: "#fff1f2", // Ivory tip
    roughness: 0.42,
    specular: 1.15,
    shellCount: 42,
    windStrength: 0.75,
    keyLightColor: "#ffffff",
    keyLightIntensity: 1.35,
    rimLightColor: "#c084fc",
    rimIntensity: 1.25,
    ambientIntensity: 0.7,
  },
  electricCyan: {
    furLength: 0.24,
    furDensity: 0.92,
    clumping: 0.35,
    curliness: 0.22,
    baseColor: "#0284c7", // Vivid cyan
    tipColor: "#e0f2fe", // Ice tip
    roughness: 0.32,
    specular: 1.45,
    shellCount: 42,
    windStrength: 1.1,
    keyLightColor: "#e0f2fe",
    keyLightIntensity: 1.55,
    rimLightColor: "#f43f5e",
    rimIntensity: 1.55,
    ambientIntensity: 0.6,
  },
  emeraldGlow: {
    furLength: 0.23,
    furDensity: 0.88,
    clumping: 0.44,
    curliness: 0.28,
    baseColor: "#059669", // Rich emerald
    tipColor: "#fef08a", // Golden tip
    roughness: 0.36,
    specular: 1.3,
    shellCount: 42,
    windStrength: 0.9,
    keyLightColor: "#ecfdf5",
    keyLightIntensity: 1.4,
    rimLightColor: "#f59e0b",
    rimIntensity: 1.4,
    ambientIntensity: 0.65,
  },
  midnightShadow: {
    furLength: 0.3,
    furDensity: 0.85,
    clumping: 0.5,
    curliness: 0.3,
    baseColor: "#0f172a", // Dark slate
    tipColor: "#64748b", // Muted blue‑gray
    roughness: 0.5,
    specular: 0.9,
    shellCount: 38,
    windStrength: 0.7,
    keyLightColor: "#1e293b",
    keyLightIntensity: 1.2,
    rimLightColor: "#334155",
    rimIntensity: 1.2,
    ambientIntensity: 0.6,
  },
};

/**
 * Automatically wraps phrases into aesthetically balanced multi-line blocks for 3D typography.
 * Avoids single-word dangling orphans (e.g., "THE HORIZON" / "OF LIGHT") by balancing line lengths.
 */
export function balanceWrapText(str: string, maxCharsPerLine = 18): string[] {
  const trimmed = str.trim();
  if (trimmed.includes("\n")) {
    return trimmed.split("\n").map((s) => s.trim()).filter(Boolean);
  }

  const words = trimmed.split(/\s+/).filter(Boolean);
  const measure = (value: string) => estimateLyricCharacterEquivalent(value);

  // CJK text commonly has no spaces; wrap it at character boundaries when needed.
  const wideScriptLines = words.length === 1 ? wrapWideScriptText(trimmed, maxCharsPerLine) : null;
  if (wideScriptLines) return wideScriptLines;

  if (words.length <= 1 || measure(trimmed) <= maxCharsPerLine) {
    return [trimmed];
  }

  // If text has 2, 3, or 4 words and length exceeds maxCharsPerLine (e.g. "THE HORIZON OF LIGHT"):
  // Find the split point that minimizes difference between line lengths
  if (words.length <= 4) {
    let bestSplit = 1;
    let minDiff = Infinity;
    for (let i = 1; i < words.length; i++) {
      const line1 = words.slice(0, i).join(" ");
      const line2 = words.slice(i).join(" ");
      const diff = Math.abs(measure(line1) - measure(line2));
      const penalty = Math.max(0, measure(line1) - maxCharsPerLine) + Math.max(0, measure(line2) - maxCharsPerLine);
      const score = diff + penalty * 3;
      if (score < minDiff) {
        minDiff = score;
        bestSplit = i;
      }
    }
    return [words.slice(0, bestSplit).join(" "), words.slice(bestSplit).join(" ")];
  }

  // For longer phrases: balance across lines
  const totalChars = measure(trimmed);
  const numLines = Math.max(2, Math.ceil(totalChars / maxCharsPerLine));
  const targetChars = totalChars / numLines;

  const lines: string[] = [];
  let currentWords: string[] = [];
  let currentLen = 0;

  for (let i = 0; i < words.length; i++) {
    const word = words[i];
    const wordLen = measure(word);
    const testLen = currentLen === 0 ? wordLen : currentLen + 1 + wordLen;

    const remainingWords = words.length - i;
    const remainingLines = numLines - lines.length;

    if (
      currentWords.length > 0 &&
      (testLen > maxCharsPerLine || (testLen > targetChars * 1.15 && remainingWords >= remainingLines))
    ) {
      lines.push(currentWords.join(" "));
      currentWords = [word];
      currentLen = wordLen;
    } else {
      currentWords.push(word);
      currentLen = testLen;
    }
  }

  if (currentWords.length > 0) {
    // Avoid orphan single word on last line if previous line can donate
    if (currentWords.length === 1 && lines.length > 0) {
      const prevLineWords = lines[lines.length - 1].split(" ");
      if (prevLineWords.length > 2) {
        const moved = prevLineWords.pop()!;
        lines[lines.length - 1] = prevLineWords.join(" ");
        currentWords.unshift(moved);
      }
    }
    lines.push(currentWords.join(" "));
  }

  return lines;
}

export function wrapText(str: string, maxCharsPerLine = 18): string {
  return balanceWrapText(str, maxCharsPerLine).join("\n");
}

/**
 * Augments text geometry with grooming tangents and follicle masks
 */
export function prepareTextGeometryForFur(geometry: THREE.BufferGeometry): THREE.BufferGeometry {
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();

  const pos = geometry.attributes.position;
  const norm = geometry.attributes.normal;
  const count = pos.count;
  const tangents = new Float32Array(count * 3);
  const follicleMask = new Float32Array(count);
  const uvs = new Float32Array(count * 2);

  const bb = geometry.boundingBox!;
  const sizeX = bb.max.x - bb.min.x || 1.0;
  const sizeY = bb.max.y - bb.min.y || 1.0;

  for (let i = 0; i < count; i++) {
    const x = pos.getX(i);
    const y = pos.getY(i);

    uvs[i * 2] = (x - bb.min.x) / sizeX;
    uvs[i * 2 + 1] = (y - bb.min.y) / sizeY;

    const nx = norm.getX(i);
    const ny = norm.getY(i);
    const nz = norm.getZ(i);
    const normal = new THREE.Vector3(nx, ny, nz).normalize();

    // Natural downward grooming flow with slight lateral flair
    const down = new THREE.Vector3(0.08 * (x > 0 ? 1 : -1), -1, 0).normalize();
    let tangent = down.clone().sub(normal.clone().multiplyScalar(down.dot(normal))).normalize();
    if (tangent.lengthSq() < 0.001) {
      tangent = new THREE.Vector3(1, 0, 0);
    }

    tangents[i * 3] = tangent.x;
    tangents[i * 3 + 1] = tangent.y;
    tangents[i * 3 + 2] = tangent.z;

    // Full follicle coverage on font faces & bevels
    follicleMask[i] = 1.0;
  }

  geometry.setAttribute("uv", new THREE.BufferAttribute(uvs, 2));
  geometry.setAttribute("aFollicleMask", new THREE.BufferAttribute(follicleMask, 1));
  geometry.setAttribute("aGroomTangent", new THREE.BufferAttribute(tangents, 3));

  return geometry;
}

export interface FurMeshGroup {
  group: THREE.Group;
  uniforms: Record<string, THREE.IUniform>;
  update: (time: number, audioBeat?: THREE.Vector3) => void;
  dispose: () => void;
}

/**
 * Creates a complete 3D furry text mesh group with volumetric GPU fur shells.
 * Ensures every individual line is horizontally and vertically centered,
 * balanced, and constrained to safe screen dimensions to prevent overlap.
 */
export function createFurryTextMesh(
  rawText: string,
  font: Font,
  params: FurParams = FUR_PRESETS.goldenHorizon,
  options: {
    size?: number;
    depth?: number;
    curveSegments?: number;
    bevelEnabled?: boolean;
    bevelThickness?: number;
    bevelSize?: number;
    maxFitWidth?: number;
    maxFitHeight?: number;
    maxCharsPerLine?: number;
  } = {}
): FurMeshGroup {
  const lines = balanceWrapText(rawText, Math.round(options.maxCharsPerLine ?? 18));
  const size = options.size ?? 1.35;
  const depth = options.depth ?? 0.32;
  const curveSegments = options.curveSegments ?? 8;
  const bevelEnabled = options.bevelEnabled ?? true;
  const bevelThickness = options.bevelThickness ?? 0.06;
  const bevelSize = options.bevelSize ?? 0.04;

  const lineSpacing = size * 1.38; // Ample vertical separation preventing fur shell collision
  const totalYHeight = (lines.length - 1) * lineSpacing;

  const lineGeometries: THREE.BufferGeometry[] = [];

  for (let i = 0; i < lines.length; i++) {
    const lineText = lines[i];
    if (!lineText) continue;

    const lineGeo = new TextGeometry(lineText, {
      font,
      size,
      depth,
      curveSegments,
      bevelEnabled,
      bevelThickness,
      bevelSize,
      bevelSegments: 4,
    });

    // Center this line horizontally and vertically at (0, 0, 0)
    lineGeo.center();

    // Position vertically so the multi-line block as a whole is centered at Y = 0
    const lineY = totalYHeight / 2 - i * lineSpacing;
    lineGeo.translate(0, lineY, 0);

    lineGeometries.push(lineGeo);
  }

  let baseGeometry: THREE.BufferGeometry;
  if (lineGeometries.length === 0) {
    baseGeometry = new THREE.BufferGeometry();
  } else if (lineGeometries.length === 1) {
    baseGeometry = lineGeometries[0];
  } else {
    baseGeometry = BufferGeometryUtils.mergeGeometries(lineGeometries, false);
    lineGeometries.forEach((g) => g.dispose());
  }

  baseGeometry.computeBoundingBox();
  prepareTextGeometryForFur(baseGeometry);

  const bb = baseGeometry.boundingBox!;
  const geoWidth = bb.max.x - bb.min.x || 1.0;
  const geoHeight = bb.max.y - bb.min.y || 1.0;

  // Maximum allowed width and height in world units within screen view volume
  // Leaves safe margins from camera view edges and bottom subtitle / top badge overlays
  const maxW = options.maxFitWidth ?? 7.8;
  const maxH = options.maxFitHeight ?? 3.6;

  const furExtra = (params.furLength ?? 0.25) * 2;
  const effectiveW = geoWidth + furExtra;
  const effectiveH = geoHeight + furExtra;

  let autoScale = 1.0;
  if (effectiveW > maxW) {
    autoScale = Math.min(autoScale, maxW / effectiveW);
  }
  if (effectiveH > maxH) {
    autoScale = Math.min(autoScale, maxH / effectiveH);
  }

  const shellCount = params.shellCount || 42;

  // Instanced shell geometry
  const shellGeometry = new THREE.InstancedBufferGeometry();
  shellGeometry.index = baseGeometry.index;
  shellGeometry.attributes.position = baseGeometry.attributes.position;
  shellGeometry.attributes.normal = baseGeometry.attributes.normal;
  shellGeometry.attributes.uv = baseGeometry.attributes.uv;
  shellGeometry.attributes.aFollicleMask = baseGeometry.attributes.aFollicleMask;
  shellGeometry.attributes.aGroomTangent = baseGeometry.attributes.aGroomTangent;

  const shellIndices = new Float32Array(shellCount);
  for (let i = 0; i < shellCount; i++) {
    shellIndices[i] = (i + 1) / shellCount;
  }
  shellGeometry.setAttribute(
    "aShellIndex",
    new THREE.InstancedBufferAttribute(shellIndices, 1)
  );
  shellGeometry.instanceCount = shellCount;

  const uniforms: Record<string, THREE.IUniform> = {
    uFurLength: { value: params.furLength },
    uFurDensity: { value: params.furDensity },
    uClumping: { value: params.clumping },
    uCurliness: { value: params.curliness },
    uBaseColor: { value: new THREE.Color(params.baseColor) },
    uTipColor: { value: new THREE.Color(params.tipColor) },
    uRoughness: { value: params.roughness },
    uSpecular: { value: params.specular },
    uKeyLightDir: { value: new THREE.Vector3(0.5, 0.8, 0.7).normalize() },
    uKeyLightColor: { value: new THREE.Color(params.keyLightColor ?? "#fff7ed") },
    uKeyLightIntensity: { value: params.keyLightIntensity ?? 1.5 },
    uRimLightDir: { value: new THREE.Vector3(-0.6, 0.4, -0.85).normalize() },
    uRimLightColor: { value: new THREE.Color(params.rimLightColor ?? "#fed7aa") },
    uRimIntensity: { value: params.rimIntensity ?? 1.35 },
    uAmbientIntensity: { value: params.ambientIntensity ?? 0.65 },
    uEnvSkyColor: { value: new THREE.Color("#fef3c7") },
    uEnvGroundColor: { value: new THREE.Color("#1e1b4b") },
    uTime: { value: 0.0 },
    uWindStrength: { value: params.windStrength },
    uAudioBeat: { value: new THREE.Vector3(0, 0, 0) },
    uFogDensity: { value: 0.5 },
  };

  const shellMaterial = new THREE.ShaderMaterial({
    vertexShader: SHELL_VERTEX_SHADER,
    fragmentShader: SHELL_FRAGMENT_SHADER,
    uniforms,
    transparent: true,
    depthWrite: true,
    side: THREE.DoubleSide,
  });

  const shellMesh = new THREE.Mesh(shellGeometry, shellMaterial);

  // Core base mesh for solid inner foundation
  const coreMaterial = new THREE.MeshStandardMaterial({
    color: params.baseColor,
    roughness: 0.85,
    metalness: 0.05,
  });
  const coreMesh = new THREE.Mesh(baseGeometry, coreMaterial);

  const group = new THREE.Group();
  group.add(coreMesh);
  group.add(shellMesh);
  group.scale.set(autoScale, autoScale, autoScale);

  return {
    group,
    uniforms,
    update: (time: number, audioBeat?: THREE.Vector3) => {
      uniforms.uTime.value = time;
      if (audioBeat) {
        uniforms.uAudioBeat.value.copy(audioBeat);
      }
    },
    dispose: () => {
      baseGeometry.dispose();
      shellGeometry.dispose();
      shellMaterial.dispose();
      coreMaterial.dispose();
    },
  };
}

let cachedFont: Font | null = null;

export function getDefaultFont(): Font {
  if (cachedFont) {
    return cachedFont;
  }
  const loader = new FontLoader();
  cachedFont = loader.parse(helvetikerBoldJson);
  return cachedFont;
}
