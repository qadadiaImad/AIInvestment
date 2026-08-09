# Render episode 3 (full + short) and the CRF-27 chat previews.
#
# Two renders writing the same file was a real incident here, so this script
# is the only thing that writes bubbles_*_v<N>.mp4 - run it, don't hand-roll
# the command.
#
#   powershell -File scripts\bubbles\render_v6.ps1 -Version v7
param([string]$Version = "v7")

$ErrorActionPreference = "Stop"
$repo = "C:\Users\imadq\AIInvestment"
$out  = "$repo\content\probe"
Set-Location "$repo\remotion"

npx remotion render src/index.ts Bubbles "$out\bubbles_full_$Version.mp4" `
  --crf 19 --log=info
if ($LASTEXITCODE -ne 0) { throw "full render failed" }

npx remotion render src/index.ts BubblesShort "$out\bubbles_short_$Version.mp4" `
  --crf 19 --log=info
if ($LASTEXITCODE -ne 0) { throw "short render failed" }

$ff = "$repo\remotion\node_modules\@remotion\compositor-win32-x64-msvc\ffmpeg.exe"
& $ff -v error -i "$out\bubbles_full_$Version.mp4" -c:v libx264 -crf 27 -preset veryfast `
  -c:a aac -b:a 96k "$out\bubbles_full_${Version}_preview.mp4" -y
& $ff -v error -i "$out\bubbles_short_$Version.mp4" -c:v libx264 -crf 27 -preset veryfast `
  -c:a aac -b:a 96k "$out\bubbles_short_${Version}_preview.mp4" -y

Get-ChildItem "$out\bubbles_*_$Version*.mp4" | Select-Object Name, Length
"RENDER_DONE $Version"
