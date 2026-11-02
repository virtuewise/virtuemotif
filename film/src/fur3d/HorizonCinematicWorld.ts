import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import type { AudioCueFrame } from "./audioCues";

export interface HorizonWorld {
  group: THREE.Group;
  ready: Promise<void>;
  update: (time: number, cue: AudioCueFrame, lyric: string, section: string) => void;
  dispose: () => void;
}

const tracked = <T extends THREE.BufferGeometry | THREE.Material | THREE.Texture>(items: Array<THREE.BufferGeometry | THREE.Material | THREE.Texture>, item: T): T => {
  items.push(item);
  return item;
};

const standard = (
  resources: Array<THREE.BufferGeometry | THREE.Material | THREE.Texture>,
  color: THREE.ColorRepresentation,
  options: THREE.MeshStandardMaterialParameters = {},
) => tracked(resources, new THREE.MeshStandardMaterial({
  color,
  roughness: 0.86,
  metalness: 0.02,
  ...options,
}));

const seeded = (n: number) => {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453123;
  return x - Math.floor(x);
};

function makeGroundTexture(
  resources: Array<THREE.BufferGeometry | THREE.Material | THREE.Texture>,
  seed: number,
  detailOnly = false,
) {
  const size = 128;
  const data = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const broad = Math.sin(x * 0.17 + seed) * Math.cos(y * 0.13 - seed * 0.7);
      const fine = Math.sin(x * 0.91 + y * 0.67 + seed * 1.9) * 0.32;
      const grain = Math.cos(x * 2.3 - y * 1.7 + seed * 2.7) * 0.12;
      const value = THREE.MathUtils.clamp(224 + (broad * 0.5 + fine + grain) * 34, 160, 255);
      const index = (y * size + x) * 4;
      data[index] = detailOnly ? value : Math.min(255, value + 4);
      data[index + 1] = value;
      data[index + 2] = detailOnly ? value : Math.max(0, value - 8);
      data[index + 3] = 255;
    }
  }
  const texture = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(8, 5);
  texture.generateMipmaps = true;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  if (!detailOnly) texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;
  return tracked(resources, texture);
}

const hasLyricCue = (text: string, terms: readonly string[]) => {
  const words = new Set(text.split(/[^\p{L}\p{N}]+/u).filter(Boolean));
  return terms.some((term) => words.has(term));
};

const LYRIC_CUES = {
  night: ["night", "star", "stars", "moon", "dark", "shadow", "dream", "usiku", "ebusuku", "ubusuku"],
  water: ["river", "water", "sea", "ocean", "rain", "flow", "tears", "mvura", "amanzi"],
  land: ["earth", "land", "mountain", "root", "roots", "home", "ancestor", "ancestors", "nyika", "umhlaba", "ikhaya"],
  hope: ["hope", "light", "future", "morning", "rise", "healing", "peace", "freedom", "together", "tariro", "chiedza", "ithemba", "ukukhanya", "ekuseni"],
} as const;

const smoothNoise = (x: number, z: number, seed: number) => {
  const a = Math.sin(x * 0.31 + seed) * Math.cos(z * 0.23 - seed * 0.7);
  const b = Math.sin(x * 0.83 - z * 0.51 + seed * 1.3) * 0.34;
  const c = Math.cos(x * 0.13 + z * 0.41 + seed) * 0.52;
  return a * 0.72 + b + c;
};

function makeTerrain(
  resources: Array<THREE.BufferGeometry | THREE.Material | THREE.Texture>,
  options: { width: number; depth: number; segmentsX: number; segmentsY: number; base: number; amplitude: number; seed: number },
) {
  const geometry = tracked(resources, new THREE.PlaneGeometry(
    options.width, options.depth, options.segmentsX, options.segmentsY,
  ));
  const position = geometry.getAttribute("position") as THREE.BufferAttribute;
  for (let i = 0; i < position.count; i += 1) {
    const x = position.getX(i);
    const z = position.getY(i);
    const edge = Math.min(1, Math.max(0, (z + options.depth * 0.5) / options.depth));
    const ridge = smoothNoise(x, z, options.seed);
    const peaks = Math.pow(Math.max(0, Math.sin(x * 0.19 + options.seed) * 0.5 + 0.5), 2.2);
    position.setY(i, options.base + ridge * options.amplitude + peaks * options.amplitude * 0.42 + edge * 0.08);
  }
  geometry.computeVertexNormals();
  return geometry;
}

const skyVertex = `
varying vec3 vDirection;
void main() {
  vDirection = normalize(position);
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}`;

const skyFragment = `
uniform vec3 uHorizon;
uniform vec3 uZenith;
uniform float uNight;
varying vec3 vDirection;
void main() {
  float h = clamp(vDirection.y * 0.5 + 0.48, 0.0, 1.0);
  h = smoothstep(0.0, 1.0, h);
  vec3 day = mix(uHorizon, uZenith, pow(h, 0.82));
  vec3 night = mix(vec3(0.025, 0.045, 0.105), vec3(0.004, 0.012, 0.035), h);
  gl_FragColor = vec4(mix(day, night, uNight), 1.0);
}`;

const waterVertex = `
varying vec2 vUv;
varying vec3 vWorld;
uniform float uTime;
uniform float uEnergy;
void main() {
  vUv = uv;
  vec3 p = position;
  float wave = sin(p.x * 2.4 + uTime * 1.2) * 0.025
    + sin(p.x * 5.7 - uTime * 0.8) * 0.012;
  p.z += wave * (0.35 + uEnergy);
  vec4 world = modelMatrix * vec4(p, 1.0);
  vWorld = world.xyz;
  gl_Position = projectionMatrix * viewMatrix * world;
}`;

const waterFragment = `
uniform float uTime;
uniform float uEnergy;
uniform float uFocus;
varying vec2 vUv;
varying vec3 vWorld;
void main() {
  vec2 p = vUv * vec2(18.0, 5.0);
  float rippleA = sin(p.x * 1.7 + uTime * 1.8 + sin(p.y * 2.0)) * 0.5 + 0.5;
  float rippleB = sin(p.x * 3.8 - uTime * 1.1 + p.y * 4.0) * 0.5 + 0.5;
  float glint = pow(max(0.0, rippleA * rippleB), 5.0);
  float fresnel = pow(1.0 - abs(normalize(cameraPosition - vWorld).z), 2.0);
  vec3 deep = vec3(0.018, 0.12, 0.17);
  vec3 reflectedSky = mix(vec3(0.08, 0.25, 0.31), vec3(0.48, 0.34, 0.25), uFocus);
  vec3 color = mix(deep, reflectedSky, 0.22 + fresnel * 0.48);
  color += vec3(0.24, 0.62, 0.68) * glint * (0.22 + uEnergy * 0.55);
  float alpha = 0.76 + glint * 0.18;
  gl_FragColor = vec4(color, alpha);
}`;

/** A deterministic procedural environment. Every animated value is a pure function of Remotion time/cues. */
export function createHorizonWorld(): HorizonWorld {
  const group = new THREE.Group();
  group.name = "HorizonCinematicWorld";
  // Lift the landscape into the camera frustum while preserving the lyric title at world origin.
  group.position.y = 3.3;
  const resources: Array<THREE.BufferGeometry | THREE.Material | THREE.Texture> = [];
  const add = <T extends THREE.Object3D>(object: T, name: string): T => {
    object.name = name;
    group.add(object);
    return object;
  };

  const skyMaterial = tracked(resources, new THREE.ShaderMaterial({
    vertexShader: skyVertex,
    fragmentShader: skyFragment,
    side: THREE.BackSide,
    depthWrite: false,
    uniforms: {
      uHorizon: { value: new THREE.Color("#e7a66f") },
      uZenith: { value: new THREE.Color("#354e72") },
      uNight: { value: 0 },
    },
  }));
  add(new THREE.Mesh(tracked(resources, new THREE.SphereGeometry(42, 48, 32)), skyMaterial), "cinematic-sky");

  const sunGroup = add(new THREE.Group(), "horizon-sun");
  sunGroup.position.set(0.7, -2.05, -14);
  const sunMaterial = new THREE.MeshBasicMaterial({ color: "#ffe0a2", toneMapped: false });
  tracked(resources, sunMaterial);
  const sun = new THREE.Mesh(tracked(resources, new THREE.SphereGeometry(0.82, 48, 32)), sunMaterial);
  sunGroup.add(sun);
  const haloMaterial = new THREE.SpriteMaterial({
    map: (() => {
      const data = new Uint8Array(64 * 64 * 4);
      for (let y = 0; y < 64; y += 1) for (let x = 0; x < 64; x += 1) {
        const d = Math.hypot((x - 31.5) / 31.5, (y - 31.5) / 31.5);
        const i = (y * 64 + x) * 4;
        data[i] = 255; data[i + 1] = 194; data[i + 2] = 125;
        data[i + 3] = Math.round(Math.pow(Math.max(0, 1 - d), 2.8) * 190);
      }
      const texture = new THREE.DataTexture(data, 64, 64, THREE.RGBAFormat);
      texture.needsUpdate = true;
      return texture;
    })(),
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    toneMapped: false,
  });
  tracked(resources, haloMaterial);
  if (haloMaterial.map) tracked(resources, haloMaterial.map);
  const halo = new THREE.Sprite(haloMaterial);
  halo.scale.set(7.5, 7.5, 1);
  sunGroup.add(halo);

  const farGeometry = makeTerrain(resources, { width: 44, depth: 13, segmentsX: 120, segmentsY: 38, base: -2.2, amplitude: 0.85, seed: 2.1 });
  const midGeometry = makeTerrain(resources, { width: 42, depth: 12, segmentsX: 120, segmentsY: 38, base: -3.1, amplitude: 0.72, seed: 8.4 });
  const nearGeometry = makeTerrain(resources, { width: 40, depth: 11, segmentsX: 120, segmentsY: 38, base: -4.1, amplitude: 0.56, seed: 15.2 });
  const farMaterial = standard(resources, "#718096", { roughness: 1, flatShading: false });
  const midMaterial = standard(resources, "#435b58", { roughness: 0.98 });
  const nearMaterial = standard(resources, "#263b32", { roughness: 0.96 });
  const far = add(new THREE.Mesh(farGeometry, farMaterial), "far-mountains");
  const mid = add(new THREE.Mesh(midGeometry, midMaterial), "middle-mountains");
  const near = add(new THREE.Mesh(nearGeometry, nearMaterial), "near-ridge");
  far.position.set(0, -1.0, -16);
  mid.position.set(0, -1.0, -11.5);
  near.position.set(0, -1.0, -8.2);


  const groundGeometry = tracked(resources, new THREE.PlaneGeometry(48, 24, 96, 48));
  const groundPosition = groundGeometry.getAttribute("position") as THREE.BufferAttribute;
  const colors: number[] = [];
  for (let i = 0; i < groundPosition.count; i += 1) {
    const x = groundPosition.getX(i);
    const y = groundPosition.getY(i);
    const n = smoothNoise(x, y, 5.7);
    groundPosition.setZ(i, n * 0.12 + Math.sin(x * 0.7 + y * 0.3) * 0.035);
    const shade = THREE.MathUtils.clamp(0.52 + n * 0.11 + seeded(i) * 0.09, 0.25, 0.78);
    colors.push(0.31 * shade, 0.19 * shade, 0.13 * shade);
  }
  groundGeometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  groundGeometry.computeVertexNormals();
  const earthAlbedo = makeGroundTexture(resources, 5.7);
  const earthDetail = makeGroundTexture(resources, 9.3, true);
  const groundMaterial = standard(resources, "#ffffff", {
    vertexColors: true,
    map: earthAlbedo,
    roughnessMap: earthDetail,
    bumpMap: earthDetail,
    bumpScale: 0.075,
    roughness: 1,
  });
  const ground = add(new THREE.Mesh(groundGeometry, groundMaterial), "red-earth");
  ground.position.set(0, -6.2, -7.2);
  ground.rotation.x = -0.04;

  const waterMaterial = tracked(resources, new THREE.ShaderMaterial({
    vertexShader: waterVertex,
    fragmentShader: waterFragment,
    transparent: true,
    depthWrite: false,
    uniforms: {
      uTime: { value: 0 },
      uEnergy: { value: 0 },
      uFocus: { value: 0 },
    },
  }));
  const water = add(new THREE.Mesh(tracked(resources, new THREE.PlaneGeometry(15, 3.2, 96, 24)), waterMaterial), "river-of-light");
  water.position.set(0.1, -4.85, -6.65);
  water.rotation.x = -0.11;

  const portal = add(new THREE.Group(), "journey-portal");
  portal.position.set(0.7, -2.5, -12.4);
  const gold = standard(resources, "#d9ae70", {
    metalness: 0.72, roughness: 0.24,
    emissive: "#70401d", emissiveIntensity: 0.42,
  });
  const ring = new THREE.Mesh(tracked(resources, new THREE.TorusGeometry(1.18, 0.055, 20, 112)), gold);
  ring.scale.y = 1.35;
  portal.add(ring);
  const pillarGeometry = tracked(resources, new THREE.CylinderGeometry(0.075, 0.12, 1.65, 16, 1));
  for (const x of [-1.17, 1.17]) {
    const pillar = new THREE.Mesh(pillarGeometry, gold);
    pillar.position.set(x, -1.05, 0);
    portal.add(pillar);
    const cap = new THREE.Mesh(tracked(resources, new THREE.SphereGeometry(0.15, 16, 12)), gold);
    cap.position.set(x, -0.22, 0);
    portal.add(cap);
  }

  // CC0 real-world scale assets from 3DAssets.dev. Loaded once per composition;
  // the URLs are immutable and every GLB is self-contained (no runtime API lookup).
  const importedAssets = add(new THREE.Group(), "licensed-world-assets");
  const assetLoader = new GLTFLoader();
  const importedResources = new Set<THREE.BufferGeometry | THREE.Material | THREE.Texture>();
  const importedNodes: Array<{ root: THREE.Group; kind: "tree" | "vehicle" }> = [];
  let disposed = false;
  const assetDefinitions = [
    { name: "baobab-tree", url: "https://cdn.3dassets.dev/assets/37714/v1/model.glb", kind: "tree" as const, position: [-6.2, -5.9, -9.2] as const, scale: 0.62 },
    { name: "large-acacia-tree", url: "https://cdn.3dassets.dev/assets/37713/v1/model.glb", kind: "tree" as const, position: [6.2, -5.9, -10.0] as const, scale: 0.58 },
    { name: "small-acacia-tree", url: "https://cdn.3dassets.dev/assets/37712/v1/model.glb", kind: "tree" as const, position: [-8.0, -5.8, -6.8] as const, scale: 0.72 },
    { name: "grand-touring-coupe", url: "https://cdn.3dassets.dev/assets/18681/v1/model.glb", kind: "vehicle" as const, position: [4.3, -5.8, -5.8] as const, scale: 0.48 },
  ];
  const ready = Promise.allSettled(assetDefinitions.map(async (definition) => {
    const gltf = await assetLoader.loadAsync(definition.url);
    const root = gltf.scene;
    root.name = definition.name;
    root.position.set(definition.position[0], definition.position[1], definition.position[2]);
    root.scale.setScalar(definition.scale);
    root.traverse((node) => {
      if (!(node instanceof THREE.Mesh)) return;
      node.castShadow = true;
      node.receiveShadow = true;
      importedResources.add(node.geometry);
      const materials = Array.isArray(node.material) ? node.material : [node.material];
      for (const material of materials) {
        importedResources.add(material);
        for (const value of Object.values(material)) {
          if (value instanceof THREE.Texture) importedResources.add(value);
        }
      }
    });
    if (disposed) {
      root.traverse((node) => {
        if (node instanceof THREE.Mesh) {
          node.geometry.dispose();
          const materials = Array.isArray(node.material) ? node.material : [node.material];
          for (const material of materials) {
            for (const value of Object.values(material)) if (value instanceof THREE.Texture) value.dispose();
            material.dispose();
          }
        }
      });
      return;
    }
    importedAssets.add(root);
    importedNodes.push({ root, kind: definition.kind });
  })).then(() => undefined);

  const vegetation = add(new THREE.Group(), "native-vegetation");
  const trunkGeometry = tracked(resources, new THREE.CylinderGeometry(0.035, 0.075, 0.9, 7));
  const crownGeometry = tracked(resources, new THREE.IcosahedronGeometry(0.42, 1));
  const trunkMaterial = standard(resources, "#493326", { roughness: 1 });
  const leafMaterials = [
    standard(resources, "#263b2c", { roughness: 1 }),
    standard(resources, "#40503a", { roughness: 1 }),
    standard(resources, "#596044", { roughness: 1 }),
  ];
  for (let i = 0; i < 58; i += 1) {
    const x = -15 + seeded(i + 20) * 30;
    const scale = 0.45 + seeded(i + 80) * 1.0;
    const z = -6.0 - seeded(i + 140) * 1.8;
    const tree = new THREE.Group();
    tree.position.set(x, -5.25 + seeded(i + 190) * 0.5, z);
    tree.scale.setScalar(scale);
    tree.rotation.z = (seeded(i + 240) - 0.5) * 0.18;
    const trunk = new THREE.Mesh(trunkGeometry, trunkMaterial);
    trunk.position.y = 0.4;
    tree.add(trunk);
    const crown = new THREE.Mesh(crownGeometry, leafMaterials[i % leafMaterials.length]);
    crown.position.y = 1.05;
    crown.scale.set(1.0 + seeded(i + 290) * 0.4, 0.85 + seeded(i + 340) * 0.55, 0.9);
    tree.add(crown);
    vegetation.add(tree);
  }

  const starPositions = new Float32Array(520 * 3);
  for (let i = 0; i < 520; i += 1) {
    const a = i * 2.399963;
    const radius = 3.2 + seeded(i + 400) * 17;
    starPositions[i * 3] = Math.cos(a) * radius;
    starPositions[i * 3 + 1] = -2.3 + Math.sin(a) * radius * 0.54;
    starPositions[i * 3 + 2] = -18 - seeded(i + 500) * 2;
  }
  const starsGeometry = tracked(resources, new THREE.BufferGeometry());
  starsGeometry.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
  const starsMaterial = tracked(resources, new THREE.PointsMaterial({
    color: "#fff0d2", size: 0.045, transparent: true, opacity: 0.02,
    sizeAttenuation: true, depthWrite: false,
  }));
  const stars = add(new THREE.Points(starsGeometry, starsMaterial), "ancestral-stars");

  const particleCount = 220;
  const particlePositions = new Float32Array(particleCount * 3);
  for (let i = 0; i < particleCount; i += 1) {
    const a = i * 2.399963;
    const r = 1.8 + seeded(i + 600) * 7.5;
    particlePositions[i * 3] = Math.cos(a) * r;
    particlePositions[i * 3 + 1] = -3.6 + Math.sin(a) * 2.2;
    particlePositions[i * 3 + 2] = -5.2 - seeded(i + 700) * 7;
  }
  const particleGeometry = tracked(resources, new THREE.BufferGeometry());
  particleGeometry.setAttribute("position", new THREE.BufferAttribute(particlePositions, 3));
  const particleMaterial = tracked(resources, new THREE.PointsMaterial({
    color: "#ffd18a", size: 0.055, transparent: true, opacity: 0.58,
    blending: THREE.AdditiveBlending, depthWrite: false,
  }));
  const particles = add(new THREE.Points(particleGeometry, particleMaterial), "golden-journey-particles");

  const hazeMaterial = new THREE.MeshBasicMaterial({
    color: "#e5b59a", transparent: true, opacity: 0.12, depthWrite: false,
    blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
  });
  tracked(resources, hazeMaterial);
  const haze = add(new THREE.Mesh(tracked(resources, new THREE.PlaneGeometry(38, 5)), hazeMaterial), "atmospheric-haze");
  haze.position.set(0, -5.2, -9.8);

  const ambient = add(new THREE.HemisphereLight("#d9e5ff", "#36241c", 1.05), "environment-hemisphere");
  const sunLight = add(new THREE.DirectionalLight("#ffd2a0", 2.0), "cinematic-key-light");
  sunLight.position.set(-4, 7, 5);
  const rimLight = add(new THREE.DirectionalLight("#91b7d0", 0.75), "cool-rim-light");
  rimLight.position.set(5, 2, -8);

  const update = (time: number, cue: AudioCueFrame, lyric: string, section: string) => {
    const normalized = `${lyric} ${section}`.normalize("NFKC").toLowerCase();
    const night = hasLyricCue(normalized, LYRIC_CUES.night);
    const waterFocus = hasLyricCue(normalized, LYRIC_CUES.water);
    const landFocus = hasLyricCue(normalized, LYRIC_CUES.land);
    const hopeFocus = hasLyricCue(normalized, LYRIC_CUES.hope)
      || /chorus|outro|final/i.test(section);
    const energy = THREE.MathUtils.clamp(cue.energy, 0, 1);
    const pulse = THREE.MathUtils.clamp(cue.beatPulse * 0.55 + cue.transitionIntensity * 0.28 + energy * 0.17, 0, 1);

    skyMaterial.uniforms.uNight.value = night ? 1 : 0;
    (skyMaterial.uniforms.uHorizon.value as THREE.Color).set(night ? "#34415f" : hopeFocus ? "#f2b77e" : "#c58b72");
    (skyMaterial.uniforms.uZenith.value as THREE.Color).set(night ? "#111b3b" : "#526b8c");
    sunGroup.scale.setScalar(0.96 + pulse * 0.1 + (hopeFocus ? 0.08 : 0));
    sunGroup.position.y = -2.15 + Math.sin(time * 0.035) * 0.12 + (hopeFocus ? 0.24 : 0);
    sunMaterial.color.set(night ? "#c6d9ff" : "#ffe0a2");
    (waterMaterial.uniforms.uTime.value as number) = time;
    (waterMaterial.uniforms.uEnergy.value as number) = energy;
    (waterMaterial.uniforms.uFocus.value as number) = waterFocus ? 1 : 0.25;
    water.visible = waterFocus || !landFocus;
    water.scale.y = 1 + pulse * 0.08;
    portal.visible = hopeFocus || landFocus;
    importedAssets.visible = true;
    // Keep imported scene dressing available independently of lyric language.
    for (const asset of importedNodes) asset.root.visible = true;
    portal.scale.setScalar(0.96 + pulse * 0.1);
    portal.rotation.y = Math.sin(time * 0.08) * 0.035;
    stars.visible = night;
    starsMaterial.opacity = night ? 0.86 : 0.02;
    particles.rotation.y = time * (0.008 + energy * 0.012);
    particles.rotation.z = Math.sin(time * 0.13) * 0.025;
    vegetation.rotation.z = Math.sin(time * 0.55) * (0.006 + energy * 0.009);
    far.position.x = Math.sin(time * 0.012) * 0.12;
    mid.position.x = Math.sin(time * 0.019 + 1.1) * 0.2;
    near.position.x = Math.sin(time * 0.027 + 2.2) * 0.28;
    hazeMaterial.opacity = 0.07 + energy * 0.035 + (night ? 0.025 : 0);
    sunLight.intensity = (night ? 0.45 : 1.8) + energy * 0.55 + pulse * 0.3;
    sunLight.color.set(night ? "#9bb7e8" : hopeFocus ? "#ffe0b2" : "#f1b88c");
    ambient.intensity = night ? 0.52 : 1.05;
    rimLight.intensity = night ? 1.05 : 0.65;
    group.rotation.y = Math.sin(time * 0.018) * 0.012;
  };

  return {
    group,
    ready,
    update,
    dispose: () => {
      disposed = true;
      for (const resource of resources) resource.dispose();
      for (const resource of importedResources) resource.dispose();
      group.clear();
    },
  };
}
