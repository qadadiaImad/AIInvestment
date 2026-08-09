# Render "The Machine" (full and/or the Shorts cut) plus the CRF-27 previews.
#
# Two renders writing the same file was a real incident here, so this script
# is the only thing that writes bubbles_*_v<N>.mp4 - run it, don't hand-roll
# the command.
#
#   powershell -File scripts\bubbles\render_episode.ps1 -Version v9
#   powershell -File scripts\bubbles\render_episode.ps1 -Version v9 -Only full
param(
  [string]$Version = "v9",
  [ValidateSet("both", "full", "short")]
  [string]$Only = "both"
)

$ErrorActionPreference = "Stop"
$repo = "C:\Users\imadq\AIInvestment"
$out  = "$repo\content\probe"
$ff   = "$repo\remotion\node_modules\@remotion\compositor-win32-x64-msvc\ffmpeg.exe"
Set-Location "$repo\remotion"

if ($Only -ne "short") {
  npx remotion render src/index.ts Bubbles "$out\bubbles_full_$Version.mp4" `
    --crf 19 --log=info
  if ($LASTEXITCODE -ne 0) { throw "full render failed" }
  & $ff -v error -i "$out\bubbles_full_$Version.mp4" -c:v libx264 -crf 27 -preset veryfast `
    -c:a aac -b:a 96k "$out\bubbles_full_${Version}_preview.mp4" -y
}

if ($Only -ne "full") {
  npx remotion render src/index.ts BubblesShort "$out\bubbles_short_$Version.mp4" `
    --crf 19 --log=info
  if ($LASTEXITCODE -ne 0) { throw "short render failed" }
  & $ff -v error -i "$out\bubbles_short_$Version.mp4" -c:v libx264 -crf 27 -preset veryfast `
    -c:a aac -b:a 96k "$out\bubbles_short_${Version}_preview.mp4" -y
}

Get-ChildItem "$out\bubbles_*_$Version*.mp4" | Select-Object Name, Length
"RENDER_DONE $Version $Only"
