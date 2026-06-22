# AI STACK STUDIO
Local content cockpit (Electron). Gallery of reels/posts (by day→stock) + live data viewer + embedded PowerShell/Claude terminal.

## Run
    cd studio
    npm install          # node-pty ships NAPI prebuilds — no native rebuild needed
    npm run dev

## Build a distributable
    npm run dist         # builds the NSIS installer (electron-builder.yml)

## What it reads (never writes)
- Media: ../higgs/*  and ../content/carousel_*/<TK>/
- Data:  ../web/public/data/{site,quantum,congress}.json
Pipelines run from the embedded terminal (or quick-action buttons). See ../higgs/README_reels.md.
