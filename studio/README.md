# AI STACK STUDIO
Local content cockpit (Electron). Gallery of reels/posts (by day→stock) + live data viewer + embedded PowerShell/Claude terminal.

## Run
    cd studio
    npm install          # rebuilds node-pty for Electron (postinstall)
    npm run dev

## Build a distributable
    npm run build        # see electron-builder config in package.json

## What it reads (never writes)
- Media: ../higgs/*  and ../content/carousel_*/<TK>/
- Data:  ../web/public/data/{site,quantum,congress}.json
Pipelines run from the embedded terminal (or quick-action buttons). See ../higgs/README_reels.md.
