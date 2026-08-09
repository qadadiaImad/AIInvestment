# Render episode 3 (full + short) and the CRF-27 chat previews.
#
# Two renders writing the same file was a real incident here, so this script
# is the only thing that writes bubbles_*_v6.mp4 - run it, don't hand-roll
# the command.
$ErrorActionPreference = "Stop"
$repo = "C:\Users\imadq\AIInvestment"
$out  = "$repo\content\probe"
Set-Location "$repo\remotion"

npx remotion render src/index.ts Bubbles "$out\bubbles_full_v6.mp4" `
  --crf 19 --log=info
if ($LASTEXITCODE -ne 0) { throw "full render failed" }

npx remotion render src/index.ts BubblesShort "$out\bubbles_short_v6.mp4" `
  --crf 19 --log=info
if ($LASTEXITCODE -ne 0) { throw "short render failed" }

$ff = "$repo\remotion\node_modules\@remotion\compositor-win32-x64-msvc\ffmpeg.exe"
& $ff -v error -i "$out\bubbles_full_v6.mp4" -c:v libx264 -crf 27 -preset veryfast `
  -c:a aac -b:a 96k "$out\bubbles_full_v6_preview.mp4" -y
& $ff -v error -i "$out\bubbles_short_v6.mp4" -c:v libx264 -crf 27 -preset veryfast `
  -c:a aac -b:a 96k "$out\bubbles_short_v6_preview.mp4" -y

Get-ChildItem "$out\bubbles_*_v6*.mp4" | Select-Object Name, Length
"RENDER_V6_DONE"
