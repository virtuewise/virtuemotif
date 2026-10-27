# Resumable chunked renderer (direct node CLI - no npx hang).
# Usage: powershell -File tools\render_chunks.ps1 -Comp Proof -OutName proof_horizon -AudioOffset 43.5
param(
  [string]$Comp = "Proof",
  [string]$OutName = "proof_horizon",
  [int]$Chunk = 150,
  [int]$Concurrency = 8,
  [double]$AudioOffset = 0,
  [string]$Audio = "",
  [int]$ChunkTimeoutSec = 900
)

$root = "C:\Users\Dell\Documents\Default Project"
$film = Join-Path $root "film"
$cli = Join-Path $film "node_modules\@remotion\cli\remotion-cli.js"
$framesDir = Join-Path $root "out\frames_$OutName"
$log = Join-Path $root "out\render_$OutName.log"
New-Item -ItemType Directory -Force -Path $framesDir | Out-Null

function Log($m) { $line = "[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $m; $line | Tee-Object -FilePath $log -Append }
function Chunk-Count($s, $e) {
  (Get-ChildItem $framesDir -Filter 'element-*.png' -ErrorAction SilentlyContinue |
    Where-Object { $n = [int]($_.BaseName -replace 'element-', ''); $n -ge $s -and $n -le $e }).Count
}

$total = switch ($Comp) { "Proof" { 1950 } "Horizon" { 7789 } "Rise" { 6445 } default { 0 } }
if ($total -eq 0) { Log "unknown composition $Comp"; exit 1 }
Log "$Comp : $total frames -> $framesDir"

for ($start = 0; $start -lt $total; $start += $Chunk) {
  $end = [Math]::Min($start + $Chunk - 1, $total - 1)
  $expected = $end - $start + 1
  if ((Chunk-Count $start $end) -ge $expected) { continue }

  for ($attempt = 1; $attempt -le 3; $attempt++) {
    Log "chunk $start-$end attempt $attempt ($(Chunk-Count $start $end)/$expected)"
    $p = Start-Process -FilePath "node.exe" -WorkingDirectory $film -PassThru -WindowStyle Hidden `
      -ArgumentList @("`"$cli`"", "render", "src/index.ts", $Comp, "`"$framesDir`"", "--sequence",
                      "--frames=$start-$end", "--concurrency=$Concurrency", "--log=error")
    Wait-Process -Id $p.Id -Timeout $ChunkTimeoutSec -ErrorAction SilentlyContinue
    if (-not $p.HasExited) {
      Log "chunk $start-$end timeout -> killing (finished frames kept)"
      & taskkill /PID $p.Id /T /F | Out-Null
    }
    Get-Process chrome-headless-shell -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    $got = Chunk-Count $start $end
    if ($got -ge $expected) { break }
    Log "  incomplete ($got/$expected)"
  }
}

$count = (Get-ChildItem $framesDir -Filter 'element-*.png').Count
Log "frames on disk: $count/$total"

if ($count -ge $total) {
  $mp4 = Join-Path $root "out\$OutName`_1080p.mp4"
  if ($Audio -eq "") {
    $audioFile = if ($Comp -eq "Rise") { "rise.m4a" } else { "horizon.m4a" }
    $Audio = Join-Path $film "public\audio\$audioFile"
  }
  $ss = if ($AudioOffset -gt 0) { @("-ss", "$AudioOffset") } else { @() }
  Log "normalising frame names"
  python (Join-Path $root "tools\normalize_frames.py") $framesDir | ForEach-Object { Log "  $_" }
  Log "muxing -> $mp4"
  & ffmpeg -v error -y -framerate 30 -i (Join-Path $framesDir 'element-%05d.png') @ss -i $Audio `
    -map 0:v -map 1:a -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -c:a aac -b:a 256k -shortest -movflags +faststart $mp4
  Get-Item $mp4 | ForEach-Object { Log ("DONE {0} {1} MB" -f $_.Name, [math]::Round($_.Length/1MB,2)) }
} else {
  Log "INCOMPLETE - rerun to resume"
}
