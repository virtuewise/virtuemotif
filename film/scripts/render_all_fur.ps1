# PowerShell script to batch‑render all Fur compositions
# Place this file at `film/scripts/render_all_fur.ps1` and run from the `film` workspace

# List of composition names (registered in Root.tsx)
$compositions = @(
    "FurryHorizon",
    "FurryRise",
    "FurryProof",
    "FurWaveSynth",
    "NeonPulseCityscape",
    "DynamicLightRim",
    "FurMaskReveal",
    "ParticleRainfall",
    "FurMorphGlyphs",
    "KaleidoscopicMirrors",
    "FurFogDepthCue",
    "SpinOutCarousel",
    "GlitchDistortionOverlay",
    "SmartFurScene",
    "SmartFurScene4K",
    "SmartFurSceneVertical",
    "SmartFurSceneSquare"
)

# Output directory (relative to the film folder)
$outputDir = "out"

# Ensure output directory exists
if (-Not (Test-Path $outputDir)) { New-Item -ItemType Directory -Path $outputDir | Out-Null }

# Loop over each composition and render a full video
foreach ($comp in $compositions) {
    Write-Host "Rendering composition $comp..."
    npx remotion render src/index.ts $comp "$outputDir/${comp}.mp4" --quality high
    Write-Host "Finished $comp"
}

Write-Host "All renders complete. Files saved to $outputDir"
