// Marschner Hair BSDF and Hybrid GPU Volumetric Fur Shaders
// Adapted for 3D Motion Typography in Remotion / Three.js

export const COMMON_HAIR_BSDF_GLSL = /* glsl */ `
  uniform vec3 uBaseColor;
  uniform vec3 uTipColor;
  uniform float uRoughness;
  uniform float uSpecular;
  uniform float uFurDensity;
  uniform vec3 uKeyLightDir;
  uniform vec3 uKeyLightColor;
  uniform float uKeyLightIntensity;
  uniform vec3 uRimLightDir;
  uniform vec3 uRimLightColor;
  uniform float uRimIntensity;
  uniform float uAmbientIntensity;
  uniform vec3 uEnvSkyColor;
  uniform vec3 uEnvGroundColor;

  // Shift hair tangent along normal to simulate tilted cuticle scales (Marschner 2003)
  vec3 shiftTangent(vec3 T, vec3 N, float shift) {
    return normalize(T + N * shift);
  }

  // Anisotropic Kajiya-Kay / Marschner specular lobe
  float hairSpecularLobe(vec3 T, vec3 N, vec3 V, vec3 L, float roughness) {
    vec3 H = normalize(L + V + vec3(1e-6));
    float dotTH = clamp(dot(T, H), -1.0, 1.0);
    float sinTH = sqrt(max(1e-5, 1.0 - dotTH * dotTH));
    float hemiVis = smoothstep(-0.25, 0.15, dot(N, L));
    float exponent = mix(220.0, 10.0, clamp(roughness * roughness, 0.0, 1.0));
    float normFactor = (exponent + 2.0) / 8.0;
    return hemiVis * pow(sinTH, exponent) * normFactor * 0.12;
  }

  vec3 evaluatePhysicalHairShading(
    vec3 worldPos,
    vec3 surfNormal,
    vec3 hairTangent,
    float h,
    float strandSeed
  ) {
    vec3 N = normalize(surfNormal);
    vec3 T = normalize(hairTangent);
    vec3 V = normalize(cameraPosition - worldPos);
    vec3 L = normalize(uKeyLightDir);
    vec3 Lrim = normalize(uRimLightDir);

    // 1. Root-to-Tip Color Gradient with per-strand micro-variation
    float rootTipMix = smoothstep(0.04, 0.94, pow(h, 0.85));
    vec3 strandTint = mix(vec3(0.92), vec3(1.08), fract(strandSeed * 17.37));
    vec3 albedo = mix(uBaseColor, uTipColor, rootTipMix) * strandTint;

    // 2. Follicle Ambient Occlusion (darker at roots)
    float follicleAO = mix(0.24, 1.0, pow(clamp(h, 0.0, 1.0), 0.72));

    // 3. Beer-Lambert Volumetric Hair Self-Shadowing
    float NdotL = dot(N, L);
    float opticalDepth = (1.0 - h) * (0.45 + 0.55 * uFurDensity) / max(0.22, NdotL * 0.5 + 0.55);
    float deepShadow = exp(-opticalDepth * 1.4);
    float wrapDiffuse = clamp((NdotL + 0.45) / 1.45, 0.0, 1.0);

    // 4. Primary Specular Lobe (R): shifted toward root
    vec3 tPrimary = shiftTangent(T, N, -0.16);
    float specR = hairSpecularLobe(tPrimary, N, V, L, uRoughness) * uSpecular;

    // 5. Secondary Specular Lobe (TRT): colored glint shifted toward tip
    vec3 tSecondary = shiftTangent(T, N, 0.22);
    float specTRT = hairSpecularLobe(tSecondary, N, V, L, uRoughness * 1.5) * (uSpecular * 0.65);
    vec3 trtColor = mix(vec3(1.0), uTipColor, 0.55);

    // Direct illumination terms
    vec3 directDiffuse = albedo * uKeyLightColor * (wrapDiffuse * deepShadow * uKeyLightIntensity);
    vec3 directSpec = (vec3(specR) + trtColor * specTRT) * uKeyLightColor * (uKeyLightIntensity * deepShadow);

    // Rim lighting (backlight glint)
    float rimNdotL = smoothstep(-0.3, 0.6, dot(N, Lrim));
    float rimSpec = hairSpecularLobe(shiftTangent(T, N, 0.1), N, V, Lrim, uRoughness) * uRimIntensity;
    directSpec += (uRimLightColor * rimSpec * rimNdotL);

    // Ambient / Environment fill
    float hemiFactor = clamp(N.y * 0.5 + 0.5, 0.0, 1.0);
    vec3 hemiFill = mix(uEnvGroundColor, uEnvSkyColor, hemiFactor) * uAmbientIntensity;
    vec3 ambientTerm = albedo * hemiFill * follicleAO;

    return directDiffuse + directSpec + ambientTerm;
  }
`;

export const SHELL_VERTEX_SHADER = /* glsl */ `
  attribute float aFollicleMask;
  attribute vec3 aGroomTangent;
  attribute float aShellIndex;

  uniform float uFurLength;
  uniform float uClumping;
  uniform float uCurliness;
  uniform float uTime;
  uniform float uWindStrength;
  uniform vec3 uAudioBeat; // Audio reactivity: bass/rms displacement

  varying float vLayerHeight;
  varying float vFollicleMask;
  varying vec3 vLocalPos;
  varying vec3 vWorldPos;
  varying vec3 vSurfNormal;
  varying vec3 vHairTangent;

  void main() {
    float h = clamp(aShellIndex, 0.0, 1.0);
    vLayerHeight = h;
    vFollicleMask = aFollicleMask;
    vLocalPos = position;

    vec3 localNormal = normalize(normal);
    vec3 groomDir = normalize(aGroomTangent);
    vec3 sideDir = normalize(cross(localNormal, groomDir) + vec3(1e-4, 0.0, 0.0));

    // Bend curve along shell layer
    float bendFactor = pow(h, 1.55);

    // Procedural wind + audio reactive vibration
    vec3 windWave = vec3(
      sin(position.y * 3.5 + uTime * 3.2) * 0.08,
      cos(position.x * 3.2 + uTime * 2.8) * 0.05,
      cos(position.z * 3.5 - uTime * 3.0) * 0.08
    ) * uWindStrength;

    vec3 audioPush = uAudioBeat * bendFactor * 0.25;

    float effectiveLen = uFurLength * aFollicleMask;

    // Curliness & strand wave
    float lockPhase = dot(position, vec3(4.2, 5.1, 4.0));
    float curlFreq = mix(3.0, 8.0, uCurliness);
    float wavePhase = h * curlFreq + lockPhase;
    float smoothEnv = h * h * (3.0 - 2.0 * h);
    float waveAmp = uCurliness * effectiveLen * 0.25 * smoothEnv;
    vec3 waveOffset = (sideDir * sin(wavePhase) + groomDir * (cos(wavePhase) - 1.0) * 0.5) * waveAmp;
    vec3 waveTangent = (sideDir * cos(wavePhase) - groomDir * sin(wavePhase) * 0.5) * (waveAmp * curlFreq);

    vec3 totalOffset =
      localNormal * (h * effectiveLen) +
      groomDir * (bendFactor * effectiveLen * (0.28 + 0.18 * uClumping)) +
      waveOffset +
      (windWave + audioPush) * bendFactor * effectiveLen;

    vec3 displacedLocal = position + totalOffset;
    vec4 worldPosition = modelMatrix * vec4(displacedLocal, 1.0);
    vWorldPos = worldPosition.xyz;

    vSurfNormal = normalize(mat3(modelMatrix) * localNormal);

    vec3 localHairDir = normalize(
      localNormal * effectiveLen +
      groomDir * (1.5 * pow(max(0.05, h), 0.55) * effectiveLen * 0.35) +
      waveTangent +
      (windWave + audioPush) * 1.5 * pow(max(0.05, h), 0.55)
    );
    vHairTangent = normalize(mat3(modelMatrix) * localHairDir);

    gl_Position = projectionMatrix * viewMatrix * worldPosition;
  }
`;

export const SHELL_FRAGMENT_SHADER = /* glsl */ `
  ${COMMON_HAIR_BSDF_GLSL}

  uniform float uClumping;
  uniform float uCurliness;
  uniform float uFogDensity;

  varying float vLayerHeight;
  varying float vFollicleMask;
  varying vec3 vLocalPos;
  varying vec3 vWorldPos;
  varying vec3 vSurfNormal;
  varying vec3 vHairTangent;

  // Planar / Triplanar surface coordinates for 3D typography
  vec2 textSurfaceUV(vec3 pos, vec3 norm) {
    vec3 n = abs(norm);
    if (n.z > n.x && n.z > n.y) {
      return pos.xy;
    } else if (n.x > n.y) {
      return pos.yz;
    } else {
      return pos.xz;
    }
  }

  vec3 hash23(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * vec3(443.897, 441.423, 437.195));
    p3 += dot(p3, p3.yzx + 19.19);
    return fract((p3.xxz + p3.yxx) * p3.zyx);
  }

  void main() {
    if (vFollicleMask < 0.05) {
      discard;
    }

    float gridScale = mix(38.0, 75.0, clamp(uFurDensity, 0.0, 1.0));
    vec2 baseUV = textSurfaceUV(vLocalPos, vSurfNormal);
    vec2 sampleUV = baseUV * gridScale;

    // Macro-tuft clumping
    vec2 clumpGrid = baseUV * (gridScale * 0.25);
    vec2 clumpFract = fract(clumpGrid) - 0.5;
    sampleUV -= clumpFract * (vLayerHeight * uClumping * 1.5);

    vec2 cellId = floor(sampleUV);
    vec2 cellLocal = fract(sampleUV) - 0.5;
    vec3 rand = hash23(cellId);

    // Height taper test
    float densityFactor = clamp(uFurDensity * 1.1, 0.2, 1.0);
    float fiberMaxH = mix(0.35, 1.0, rand.z) * densityFactor;
    if (vLayerHeight > fiberMaxH) {
      discard;
    }

    // Strand center & curl inside cell
    float curlFreq = mix(3.0, 8.0, uCurliness);
    float curlAngle = vLayerHeight * curlFreq + rand.x * 6.28318;
    float smoothEnv = vLayerHeight * vLayerHeight * (3.0 - 2.0 * vLayerHeight);
    float curlRadius = (0.03 * uClumping + 0.12 * uCurliness) * smoothEnv;
    vec2 strandCenter = (rand.xy - 0.5) * 0.25 + vec2(cos(curlAngle), sin(curlAngle)) * curlRadius;
    float distToAxis = length(cellLocal - strandCenter);

    // Conical hair strand radius tapering to tip
    float normH = clamp(vLayerHeight / max(0.15, fiberMaxH), 0.0, 1.0);
    float maxRadius = 0.65 * (1.0 - pow(normH, 1.25));
    if (distToAxis > maxRadius) {
      discard;
    }

    vec3 color = evaluatePhysicalHairShading(
      vWorldPos,
      vSurfNormal,
      vHairTangent,
      vLayerHeight,
      rand.x
    );

    gl_FragColor = vec4(color, 1.0);
  // Depth‑based exponential fog
  float depth = length(vWorldPos - cameraPosition);
  gl_FragColor.a *= exp(-depth * uFogDensity);
  }
`;
