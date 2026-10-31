# scripts/generate_lyrics.ps1
# PowerShell wrapper to run the Smart Auto Lyrics Generator
param(
    [string]$Audio = "public/audio/horizon.m4a",
    [string]$Title = "",
    [string]$Subtitle = "",
    [string]$Artist = "virtuemotif",
    [string]$Language = "auto",
    [string]$Out = "",
    [string]$ApiKey = ""
)

$argsList = @("scripts/generate_lyrics.mjs", "--audio", $Audio)

if ($Title) { $argsList += @("--title", $Title) }
if ($Subtitle) { $argsList += @("--subtitle", $Subtitle) }
if ($Artist) { $argsList += @("--artist", $Artist) }
if ($Language) { $argsList += @("--language", $Language) }
if ($Out) { $argsList += @("--out", $Out) }
if ($ApiKey) { $argsList += @("--apiKey", $ApiKey) }

Write-Host "Running Smart Auto Lyrics Generator..." -ForegroundColor Cyan
& node $argsList
