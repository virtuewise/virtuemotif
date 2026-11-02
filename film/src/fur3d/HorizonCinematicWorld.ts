import * as THREE from "three";
import type { AudioCueFrame } from "./audioCues";

export interface HorizonWorld {
  group: THREE.Group;
  update: (time: number, cue: AudioCueFrame, lyric: string, section: string) => void;
  dispose: () => void;
}

const makeMaterial = (color: string, options: THREE.MeshStandardMaterialParameters = {}) =>
  new THREE.MeshStandardMaterial({ color, roughness: 0.82, metalness: 0.08, ...options });

function ridgeGeometry(seed: number, baseY: number, peak: number): THREE.BufferGeometry {
  const points: THREE.Vector2[] = [new THREE.Vector2(-18, -9)];
  for (let i = 0; i <= 48; i += 1) {
    const x = -18 + (36 * i) / 48;
    const wave = Math.sin(i * 0.57 + seed) * 0.55 + Math.sin(i * 0.19 + seed * 2) * 0.9;
    const summit = Math.max(0, 1 - Math.abs(x - (seed - 2) * 2.4) / 5) * peak;
    points.push(new THREE.Vector2(x, baseY + wave + summit));
  }
  points.push(new THREE.Vector2(18, -9));
  const shape = new THREE.Shape(points);
  return new THREE.ShapeGeometry(shape, 2);
}

/** Deterministic, lyric-led 3D world for the Horizon film. All motion is derived from Remotion time. */
export function createHorizonWorld(): HorizonWorld {
  const group = new THREE.Group();
  group.name = "HorizonCinematicWorld";
  const resources: Array<THREE.BufferGeometry | THREE.Material> = [];

  const addMesh = (geometry: THREE.BufferGeometry, material: THREE.Material, z: number, name: string) => {
    resources.push(geometry, material);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.z = z;
    mesh.name = name;
    group.add(mesh);
    return mesh;
  };

  const sky = addMesh(new THREE.SphereGeometry(38, 32, 20), new THREE.MeshBasicMaterial({
    color: "#111a35", side: THREE.BackSide,
  }), -18, "cinematic-sky");

  const sunMaterial = new THREE.MeshBasicMaterial({ color: "#ffd58a" });
  const sun = addMesh(new THREE.SphereGeometry(1.12, 40, 32), sunMaterial, -10.2, "horizon-sun");
  sun.position.set(0.1, 1.45, -10.2);
  const sunHalo = addMesh(new THREE.SphereGeometry(1.72, 32, 24), new THREE.MeshBasicMaterial({
    color: "#f7ad58", transparent: true, opacity: 0.16, side: THREE.BackSide,
  }), -10.1, "sun-halo");
  sunHalo.position.copy(sun.position);

  const far = addMesh(ridgeGeometry(2, -2.9, 2.5), makeMaterial("#34465f"), -12.5, "far-mountains");
  const mid = addMesh(ridgeGeometry(5, -3.6, 1.8), makeMaterial("#1b3944"), -9.4, "middle-mountains");
  const near = addMesh(ridgeGeometry(8, -4.35, 1.0), makeMaterial("#10272c"), -6.7, "near-ridge");
  far.material = far.material;
  mid.material = mid.material;
  near.material = near.material;

  const ground = addMesh(new THREE.PlaneGeometry(38, 18), makeMaterial("#241e28"), -5.9, "red-earth");
  ground.position.set(0, -7.2, -5.9);

  const riverCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-0.5, -7.0, -5.65),
    new THREE.Vector3(-1.5, -5.7, -7.2),
    new THREE.Vector3(0.8, -4.9, -8.8),
    new THREE.Vector3(0.2, -3.8, -10.4),
    new THREE.Vector3(1.0, -2.8, -12.2),
  ]);
  const river = addMesh(new THREE.TubeGeometry(riverCurve, 72, 0.105, 10, false), new THREE.MeshBasicMaterial({
    color: "#70c7cf", transparent: true, opacity: 0.72,
  }), 0, "river-of-light");

  const arch = new THREE.Group();
  arch.name = "journey-portal";
  const archMaterial = makeMaterial("#e9b96c", { emissive: "#8a4e22", emissiveIntensity: 0.75, metalness: 0.62, roughness: 0.28 });
  resources.push(archMaterial);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(1.45, 0.075, 14, 72), archMaterial);
  ring.scale.y = 1.32;
  arch.add(ring);
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.18, 0.65, 12), archMaterial);
  base.position.set(-1.42, -1.82, 0);
  arch.add(base);
  const base2 = base.clone();
  base2.position.x = 1.42;
  arch.add(base2);
  arch.position.set(0, -0.65, -8.3);
  group.add(arch);

  const treeMaterial = makeMaterial("#08191d");
  resources.push(treeMaterial);
  for (let i = 0; i < 26; i += 1) {
    const x = -12.5 + i * 1.0;
    const height = 0.55 + ((Math.sin(i * 7.13) + 1) * 0.5) * 1.25;
    const tree = new THREE.Mesh(new THREE.ConeGeometry(0.24 + height * 0.1, height, 6), treeMaterial);
    tree.position.set(x, -4.75 + height * 0.48, -6.1 - (i % 3) * 0.12);
    tree.rotation.z = Math.sin(i * 2.7) * 0.13;
    group.add(tree);
    resources.push(tree.geometry);
  }

  const starPositions = new Float32Array(420 * 3);
  for (let i = 0; i < 420; i += 1) {
    const angle = i * 2.399963;
    const radius = 3 + (i % 19) * 0.63;
    starPositions[i * 3] = Math.cos(angle) * radius;
    starPositions[i * 3 + 1] = 1.5 + Math.sin(angle) * radius * 0.54;
    starPositions[i * 3 + 2] = -13.8 - (i % 7) * 0.35;
  }
  const starGeometry = new THREE.BufferGeometry();
  starGeometry.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
  const starMaterial = new THREE.PointsMaterial({ color: "#fff0c7", size: 0.035, transparent: true, opacity: 0.8, sizeAttenuation: true });
  resources.push(starGeometry, starMaterial);
  const stars = new THREE.Points(starGeometry, starMaterial);
  stars.name = "ancestral-stars";
  group.add(stars);

  const dustPositions = new Float32Array(180 * 3);
  for (let i = 0; i < 180; i += 1) {
    const a = i * 2.399963;
    dustPositions[i * 3] = Math.cos(a) * (1.5 + (i % 13) * 0.22);
    dustPositions[i * 3 + 1] = -2.5 + Math.sin(a) * (1.0 + (i % 9) * 0.19);
    dustPositions[i * 3 + 2] = -4.8 - (i % 11) * 0.38;
  }
  const dustGeometry = new THREE.BufferGeometry();
  dustGeometry.setAttribute("position", new THREE.BufferAttribute(dustPositions, 3));
  const dustMaterial = new THREE.PointsMaterial({ color: "#f7c879", size: 0.045, transparent: true, opacity: 0.65 });
  resources.push(dustGeometry, dustMaterial);
  const dust = new THREE.Points(dustGeometry, dustMaterial);
  dust.name = "golden-journey-particles";
  group.add(dust);

  const ambient = new THREE.AmbientLight("#9cb4d0", 0.7);
  group.add(ambient);
  const sunLight = new THREE.PointLight("#ffc477", 2.2, 22);
  sunLight.position.set(0, 1.4, -7.5);
  group.add(sunLight);

  const update = (time: number, cue: AudioCueFrame, lyric: string, section: string) => {
    const words = `${lyric} ${section}`.toLowerCase();
    const night = /star|night|shadow|moon/.test(words);
    const riverFocus = /river|sea|water|flow|trace/.test(words);
    const mountainFocus = /mountain|mist|spirit|roots|past/.test(words);
    const hopeFocus = /hope|future|light|morning|healing|harmony|peace|sun/.test(words);
    const pulse = cue.beatPulse * 0.22 + cue.energy * 0.08 + cue.transitionIntensity * 0.12;

    sky.material = sky.material;
    (sky.material as THREE.MeshBasicMaterial).color.set(night ? "#071126" : hopeFocus ? "#382b42" : "#17243c");
    sun.scale.setScalar(0.88 + (hopeFocus ? 0.18 : 0) + pulse * 0.16);
    sun.position.y = 1.2 + Math.sin(time * 0.12) * 0.16 + (hopeFocus ? 0.32 : 0);
    sunMaterial.color.set(night ? "#d6ddff" : "#ffd58a");
    sunHalo.scale.setScalar(1 + pulse * 0.55);
    (sunHalo.material as THREE.MeshBasicMaterial).opacity = night ? 0.1 : 0.13 + pulse * 0.12;
    arch.visible = hopeFocus || /chorus|outro|final/.test(section.toLowerCase());
    arch.rotation.y = Math.sin(time * 0.12) * 0.045;
    arch.scale.setScalar(0.96 + pulse * 0.12);
    river.visible = riverFocus || !mountainFocus;
    (river.material as THREE.MeshBasicMaterial).opacity = riverFocus ? 0.9 : 0.48;
    stars.visible = night || time < 44;
    starMaterial.opacity = night ? 0.95 : 0.36;
    dust.rotation.y = time * 0.018;
    dust.rotation.z = Math.sin(time * 0.17) * 0.025;
    far.position.x = Math.sin(time * 0.025) * 0.18;
    mid.position.x = Math.sin(time * 0.04 + 1) * 0.28;
    near.position.x = Math.sin(time * 0.055 + 2) * 0.38;
    sunLight.intensity = 1.6 + pulse * 2.1 + (hopeFocus ? 0.5 : 0);
    sunLight.color.set(night ? "#9bb8ff" : mountainFocus ? "#d4a6ff" : "#ffc477");
    group.rotation.y = Math.sin(time * 0.035) * 0.018;
  };

  return {
    group,
    update,
    dispose: () => {
      for (const resource of resources) resource.dispose();
      group.clear();
    },
  };
}
