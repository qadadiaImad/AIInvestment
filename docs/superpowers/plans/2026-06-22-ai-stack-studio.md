# AI STACK STUDIO Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local Electron desktop "content cockpit" that galleries the produced reels/posts (by day→stock), shows the live terminal data behind each, and embeds a real PowerShell terminal where the owner runs `claude`.

**Architecture:** Electron two-process app in a new `studio/` dir (scaffolded with electron-vite). Main process owns a `node-pty` PowerShell, a `media://` protocol serving local `higgs/`+`content/` files, and reads `web/public/data/*.json`. Renderer is React+Tailwind (gallery-first, terminal docked). A secure `contextBridge` preload is the only privileged surface. Pure logic (media indexer, caption parser, data join) is TDD'd with Vitest.

**Tech Stack:** electron@42, electron-vite@5, react@19, tailwindcss@4, @xterm/xterm@6 + @xterm/addon-fit@0.11, node-pty@1.1, @electron/rebuild@4, electron-builder@26, vitest@3, typescript@5.

**Spec:** `docs/superpowers/specs/2026-06-22-ai-stack-studio-design.md`

**Repo paths referenced (read-only consumers):** `web/public/data/{site,quantum,congress,congress_stocks,news}.json`, `higgs/`, `content/`. The studio app NEVER writes to those; it only reads + serves them. All studio code lives under `studio/`. Run all commands from repo root `C:/Users/imadq/AIInvestment` unless noted.

---

## Task 0: Scaffold the `studio/` Electron app

**Files:**
- Create: `studio/package.json`
- Create: `studio/electron.vite.config.ts`
- Create: `studio/tsconfig.json`
- Create: `studio/.gitignore`
- Create: `studio/src/main/index.ts`
- Create: `studio/src/preload/index.ts`
- Create: `studio/src/renderer/index.html`
- Create: `studio/src/renderer/src/main.tsx`
- Create: `studio/src/renderer/src/App.tsx`

- [ ] **Step 1: Create `studio/package.json`**

```json
{
  "name": "ai-stack-studio",
  "version": "0.1.0",
  "description": "Local content cockpit for AI STACK reels/posts",
  "main": "./out/main/index.js",
  "scripts": {
    "dev": "electron-vite dev",
    "build": "electron-vite build",
    "start": "electron-vite preview",
    "test": "vitest run",
    "rebuild": "electron-rebuild -f -w node-pty",
    "postinstall": "electron-rebuild -f -w node-pty"
  },
  "dependencies": {
    "@xterm/addon-fit": "0.11.0",
    "@xterm/xterm": "6.0.0",
    "node-pty": "1.1.0"
  },
  "devDependencies": {
    "@electron/rebuild": "4.0.4",
    "@types/react": "19.2.4",
    "@types/react-dom": "19.2.4",
    "@vitejs/plugin-react": "5.0.4",
    "electron": "42.4.1",
    "electron-builder": "26.15.3",
    "electron-vite": "5.0.0",
    "react": "19.2.4",
    "react-dom": "19.2.4",
    "tailwindcss": "4.1.18",
    "@tailwindcss/vite": "4.1.18",
    "typescript": "5.9.3",
    "vitest": "3.2.6"
  }
}
```

- [ ] **Step 2: Create `studio/electron.vite.config.ts`**

```ts
import { resolve } from 'path'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import react from '@vitejs/plugin-react'
import tailwind from '@tailwindcss/vite'

export default defineConfig({
  main: { plugins: [externalizeDepsPlugin()] },
  preload: { plugins: [externalizeDepsPlugin()] },
  renderer: {
    root: 'src/renderer',
    resolve: { alias: { '@': resolve('src/renderer/src') } },
    plugins: [react(), tailwind()],
    build: { rollupOptions: { input: resolve('src/renderer/index.html') } }
  }
})
```

- [ ] **Step 3: Create `studio/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "baseUrl": ".",
    "paths": { "@/*": ["src/renderer/src/*"] },
    "types": ["vite/client"]
  },
  "include": ["src", "test"]
}
```

- [ ] **Step 4: Create `studio/.gitignore`**

```
node_modules/
out/
dist/
*.log
```

- [ ] **Step 5: Create `studio/src/main/index.ts` (minimal secure window)**

```ts
import { app, BrowserWindow } from 'electron'
import { join } from 'path'

function createWindow(): void {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    backgroundColor: '#0A0D12',
    show: false,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false // required: preload uses node-pty bridge
    }
  })
  win.once('ready-to-show', () => win.show())
  if (process.env.ELECTRON_RENDERER_URL) {
    win.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    win.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  createWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
```

- [ ] **Step 6: Create `studio/src/preload/index.ts` (placeholder bridge — expanded later)**

```ts
import { contextBridge } from 'electron'

// Expanded in later tasks (terminal, posts, stock, caption).
contextBridge.exposeInMainWorld('studio', {
  ping: () => 'pong'
})
```

- [ ] **Step 7: Create `studio/src/renderer/index.html`**

```html
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="Content-Security-Policy"
      content="default-src 'self'; img-src 'self' media: data:; media-src 'self' media:; style-src 'self' 'unsafe-inline'; script-src 'self'" />
    <title>AI STACK STUDIO</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 8: Create `studio/src/renderer/src/main.tsx`**

```tsx
import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

createRoot(document.getElementById('root')!).render(<App />)
```

- [ ] **Step 9: Create `studio/src/renderer/src/index.css`**

```css
@import "tailwindcss";
:root { color-scheme: dark; }
body { margin: 0; background: #0A0D12; color: #E8EDF2; font-family: Inter, system-ui, sans-serif; }
```

- [ ] **Step 10: Create `studio/src/renderer/src/App.tsx` (blank 3-zone shell)**

```tsx
export default function App() {
  return (
    <div className="h-screen flex flex-col">
      <header className="h-14 px-5 flex items-center border-b border-white/10 font-mono tracking-widest text-emerald-400">
        AI STACK STUDIO
      </header>
      <main className="flex-1 overflow-auto p-4 text-white/40">gallery (todo)</main>
      <footer className="h-48 border-t border-white/10 p-2 text-white/40 font-mono text-sm">terminal (todo)</footer>
    </div>
  )
}
```

- [ ] **Step 11: Install deps**

Run: `cd studio && npm install`
Expected: installs; `postinstall` runs `electron-rebuild` for `node-pty` (may take 1–3 min compiling). If electron-rebuild fails here because node-pty isn't imported yet, that's fine — it still rebuilds the module.

- [ ] **Step 12: Smoke test — window opens**

Run: `cd studio && npm run dev`
Expected: an Electron window opens, dark background, header "AI STACK STUDIO", "gallery (todo)" / "terminal (todo)" zones. Close it.

- [ ] **Step 13: Commit**

```bash
git add studio/package.json studio/electron.vite.config.ts studio/tsconfig.json studio/.gitignore studio/src
git commit -m "feat(studio): scaffold electron-vite + react shell"
```

---

## Task 1: PowerShell PTY ↔ xterm terminal (de-risk the hard part first)

**Files:**
- Modify: `studio/src/main/index.ts`
- Create: `studio/src/main/terminal.ts`
- Modify: `studio/src/preload/index.ts`
- Create: `studio/src/renderer/src/components/Terminal.tsx`
- Create: `studio/src/renderer/src/global.d.ts`
- Modify: `studio/src/renderer/src/App.tsx`

- [ ] **Step 1: Create `studio/src/main/terminal.ts`**

```ts
import { ipcMain, WebContents } from 'electron'
import * as pty from 'node-pty'
import { join } from 'path'

const REPO_ROOT = join(__dirname, '..', '..', '..') // studio/out/main -> repo root
const SHELL = process.platform === 'win32' ? 'powershell.exe' : (process.env.SHELL || 'bash')

export function registerTerminal(): void {
  let term: pty.IPty | null = null

  ipcMain.on('term:start', (e, cols: number, rows: number) => {
    if (term) return
    term = pty.spawn(SHELL, [], {
      name: 'xterm-color',
      cols: cols || 100,
      rows: rows || 24,
      cwd: REPO_ROOT,
      env: process.env as { [k: string]: string }
    })
    const wc: WebContents = e.sender
    term.onData((d) => { if (!wc.isDestroyed()) wc.send('term:data', d) })
    term.onExit(() => { term = null })
  })

  ipcMain.on('term:input', (_e, data: string) => term?.write(data))
  ipcMain.on('term:resize', (_e, cols: number, rows: number) => { try { term?.resize(cols, rows) } catch {} })
}
```

- [ ] **Step 2: Wire terminal into `studio/src/main/index.ts`**

Add the import near the top:
```ts
import { registerTerminal } from './terminal'
```
And inside `app.whenReady().then(() => { ... })`, before `createWindow()`:
```ts
  registerTerminal()
```

- [ ] **Step 3: Expand `studio/src/preload/index.ts`**

```ts
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('studio', {
  term: {
    start: (cols: number, rows: number) => ipcRenderer.send('term:start', cols, rows),
    input: (data: string) => ipcRenderer.send('term:input', data),
    resize: (cols: number, rows: number) => ipcRenderer.send('term:resize', cols, rows),
    onData: (cb: (d: string) => void) => {
      const h = (_: unknown, d: string) => cb(d)
      ipcRenderer.on('term:data', h)
      return () => ipcRenderer.removeListener('term:data', h)
    }
  }
})
```

- [ ] **Step 4: Create `studio/src/renderer/src/global.d.ts`**

```ts
export {}
declare global {
  interface Window {
    studio: {
      term: {
        start(cols: number, rows: number): void
        input(data: string): void
        resize(cols: number, rows: number): void
        onData(cb: (d: string) => void): () => void
      }
    }
  }
}
```

- [ ] **Step 5: Create `studio/src/renderer/src/components/Terminal.tsx`**

```tsx
import { useEffect, useRef } from 'react'
import { Terminal as Xterm } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

export default function Terminal() {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current) return
    const term = new Xterm({
      fontFamily: 'JetBrains Mono, monospace', fontSize: 13,
      theme: { background: '#0A0D12', foreground: '#E8EDF2', cursor: '#34D399' },
      cursorBlink: true
    })
    const fit = new FitAddon()
    term.loadAddon(fit)
    term.open(ref.current)
    fit.fit()
    window.studio.term.start(term.cols, term.rows)
    const off = window.studio.term.onData((d) => term.write(d))
    term.onData((d) => window.studio.term.input(d))
    const onResize = () => { fit.fit(); window.studio.term.resize(term.cols, term.rows) }
    window.addEventListener('resize', onResize)
    return () => { off(); window.removeEventListener('resize', onResize); term.dispose() }
  }, [])
  return <div ref={ref} className="h-full w-full" />
}
```

- [ ] **Step 6: Mount Terminal in `App.tsx` footer**

Replace the `<footer>...</footer>` line with:
```tsx
      <footer className="h-56 border-t border-white/10 bg-[#0A0D12]">
        <Terminal />
      </footer>
```
And add at the top of `App.tsx`:
```tsx
import Terminal from './components/Terminal'
```

- [ ] **Step 7: Smoke test — real shell**

Run: `cd studio && npm run dev`
Expected: the footer shows a live PowerShell prompt. Type `echo hi` → prints `hi`. Type `claude --version` → prints the Claude Code version. Type `claude` → Claude Code launches inside the pane. This proves the riskiest piece.

- [ ] **Step 8: Commit**

```bash
git add studio/src
git commit -m "feat(studio): embedded PowerShell terminal (node-pty + xterm)"
```

---

## Task 2: `media://` protocol + repo path resolver

**Files:**
- Create: `studio/src/main/paths.ts`
- Create: `studio/src/main/media.ts`
- Modify: `studio/src/main/index.ts`

- [ ] **Step 1: Create `studio/src/main/paths.ts`**

```ts
import { join } from 'path'
// studio/out/main -> repo root is three levels up.
export const REPO_ROOT = join(__dirname, '..', '..', '..')
export const HIGGS = join(REPO_ROOT, 'higgs')
export const CONTENT = join(REPO_ROOT, 'content')
export const DATA = join(REPO_ROOT, 'web', 'public', 'data')
```

- [ ] **Step 2: Create `studio/src/main/media.ts`**

```ts
import { protocol, net } from 'electron'
import { pathToFileURL, fileURLToPath } from 'url'
import { join, normalize } from 'path'
import { REPO_ROOT } from './paths'

// media://higgs/reel_nvda_2026-06-22.mp4  ->  <repo>/higgs/reel_...mp4
export function registerMediaProtocol(): void {
  protocol.handle('media', (req) => {
    const rel = decodeURIComponent(new URL(req.url).href.replace(/^media:\/\//, ''))
    const abs = normalize(join(REPO_ROOT, rel))
    if (!abs.startsWith(normalize(REPO_ROOT))) {
      return new Response('forbidden', { status: 403 })
    }
    return net.fetch(pathToFileURL(abs).toString()) // handles range requests for video
  })
}
export const PRIVILEGED = [{ scheme: 'media', privileges: { standard: true, secure: true, stream: true, supportFetchAPI: true } }]
export { fileURLToPath } // (kept for tests if needed)
```

- [ ] **Step 3: Register protocol scheme + handler in `studio/src/main/index.ts`**

Add imports:
```ts
import { protocol } from 'electron'
import { registerMediaProtocol, PRIVILEGED } from './media'
```
BEFORE `app.whenReady()` (protocol schemes must be registered before ready):
```ts
protocol.registerSchemesAsPrivileged(PRIVILEGED)
```
Inside `app.whenReady().then(() => { ... })`, add (before `createWindow()`):
```ts
  registerMediaProtocol()
```

- [ ] **Step 4: Smoke test — serve a real reel**

Run: `cd studio && npm run dev`, open DevTools console (View menu), run:
```js
fetch('media://higgs/reel_nvda_2026-06-22.mp4').then(r => console.log(r.status))
```
Expected: logs `200`. (Confirms the protocol resolves repo media.)

- [ ] **Step 5: Commit**

```bash
git add studio/src/main
git commit -m "feat(studio): media:// protocol for local reels/posts"
```

---

## Task 3: Media indexer (pure, TDD)

**Files:**
- Create: `studio/src/main/indexer.ts`
- Create: `studio/test/indexer.test.ts`
- Create: `studio/vitest.config.ts`

- [ ] **Step 1: Create `studio/vitest.config.ts`**

```ts
import { defineConfig } from 'vitest/config'
export default defineConfig({ test: { environment: 'node', include: ['test/**/*.test.ts'] } })
```

- [ ] **Step 2: Write the failing test `studio/test/indexer.test.ts`**

```ts
import { describe, it, expect } from 'vitest'
import { buildIndex, type Post } from '../src/main/indexer'

describe('buildIndex', () => {
  it('groups a reel + its slides + caption under one bundle by date+ticker', () => {
    const files = {
      higgs: [
        'reel_nvda_2026-06-22.mp4',
        'reel_nvda_data.png', 'reel_nvda_hook.png', 'reel_nvda_takeaway.png',
        'v4_nvda_1_hook.png', 'v4_nvda_2_data.png', 'v4_nvda_3_takeaway.png',
        'reels_2026-06-22.txt',
        'hero_nvda_2026-06-22.png', 'logo_NVDA.png', '_check_anim.png' // excluded
      ],
      content: ['carousel_2026-06-03/CRM/slide_1.html', 'carousel_2026-06-03/CRM/brief.md']
    }
    const out: Post[] = buildIndex(files)
    const nvda = out.find(p => p.ticker === 'NVDA' && p.date === '2026-06-22')!
    expect(nvda.kind).toBe('reel')
    expect(nvda.media.some(m => m.endsWith('reel_nvda_2026-06-22.mp4'))).toBe(true)
    expect(nvda.media.some(m => m.includes('v4_nvda_1_hook'))).toBe(true)
    // intermediates excluded
    expect(nvda.media.some(m => m.includes('hero_') || m.includes('logo_') || m.includes('_check'))).toBe(false)
    // content carousel becomes its own bundle
    expect(out.some(p => p.ticker === 'CRM' && p.date === '2026-06-03' && p.kind === 'carousel')).toBe(true)
  })

  it('sorts newest day first', () => {
    const out = buildIndex({ higgs: ['reel_ionq_2026-06-21.mp4', 'reel_nvda_2026-06-22.mp4'], content: [] })
    expect(out[0].date >= out[out.length - 1].date).toBe(true)
  })
})
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd studio && npx vitest run test/indexer.test.ts`
Expected: FAIL — `buildIndex` not exported / not defined.

- [ ] **Step 4: Implement `studio/src/main/indexer.ts`**

```ts
export type Post = {
  date: string
  ticker: string
  kind: 'reel' | 'carousel' | 'post'
  media: string[]      // media:// URLs
  poster?: string
  captionFile?: string
}
export type FileSets = { higgs: string[]; content: string[] }

const M = (rel: string) => `media://${rel}`
const EXCLUDE = /^(hero_|logo_|maya_|_)|\.json$/i

export function buildIndex(files: FileSets): Post[] {
  const byKey = new Map<string, Post>()
  const key = (d: string, t: string) => `${d}|${t}`

  const ensure = (date: string, ticker: string, kind: Post['kind']): Post => {
    const k = key(date, ticker)
    if (!byKey.has(k)) byKey.set(k, { date, ticker, kind, media: [] })
    return byKey.get(k)!
  }

  // captions by date (sectioned files) — attached to every bundle of that date
  const captionByDate = new Map<string, string>()

  for (const f of files.higgs) {
    if (EXCLUDE.test(f)) continue
    let m: RegExpMatchArray | null
    if ((m = f.match(/^reel_([a-z]+)_(\d{4}-\d{2}-\d{2})\.mp4$/i))) {
      const p = ensure(m[2], m[1].toUpperCase(), 'reel'); p.kind = 'reel'; p.media.unshift(M(`higgs/${f}`))
    } else if ((m = f.match(/^v4_([a-z]+)_\d_[a-z]+\.png$/i))) {
      // carousel slide; ticker known, date unknown here -> attach to that ticker's newest bundle later; store under a synthetic 'v4' map
      v4slides.push([m[1].toUpperCase(), f])
    } else if ((m = f.match(/^reels?_(\d{4}-\d{2}-\d{2})\.txt$/i)) || (m = f.match(/^posts?_(\d{4}-\d{2}-\d{2})\.txt$/i))) {
      captionByDate.set(m[1], `media://higgs/${f}`)
    }
  }

  // content/carousel_<date>/<TK>/...
  const contentSeen = new Set<string>()
  for (const f of files.content) {
    const m = f.match(/^carousel_(\d{4}-\d{2}-\d{2})\/([A-Z]+)\//)
    if (!m) continue
    const ck = key(m[1], m[2])
    if (contentSeen.has(ck)) continue
    contentSeen.add(ck)
    const p = ensure(m[1], m[2], 'carousel'); if (p.kind !== 'reel') p.kind = 'carousel'
    p.media.push(M(`content/carousel_${m[1]}/${m[2]}/slide_1.html`))
  }

  // attach v4 slides to that ticker's bundle (any date for that ticker; prefer reel bundle)
  for (const [ticker, file] of v4slides) {
    const target = [...byKey.values()].filter(p => p.ticker === ticker).sort((a, b) => b.date.localeCompare(a.date))[0]
    if (target) target.media.push(M(`higgs/${file}`))
  }

  const out = [...byKey.values()]
  for (const p of out) { const c = captionByDate.get(p.date); if (c) p.captionFile = c }
  return out.sort((a, b) => b.date.localeCompare(a.date) || a.ticker.localeCompare(b.ticker))
}

const v4slides: [string, string][] = []
```

> Note: move `const v4slides` to the top of `buildIndex` as a local (not module-level) to stay pure across calls. Final form:
> ```ts
> export function buildIndex(files: FileSets): Post[] {
>   const v4slides: [string, string][] = []
>   // ...rest unchanged...
> }
> ```
> Delete the trailing module-level `const v4slides`.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd studio && npx vitest run test/indexer.test.ts`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add studio/src/main/indexer.ts studio/test/indexer.test.ts studio/vitest.config.ts
git commit -m "feat(studio): media indexer (filenames -> post bundles), TDD"
```

---

## Task 4: Caption-section parser (pure, TDD)

**Files:**
- Create: `studio/src/main/captions.ts`
- Create: `studio/test/captions.test.ts`

- [ ] **Step 1: Write failing test `studio/test/captions.test.ts`**

```ts
import { describe, it, expect } from 'vitest'
import { parseCaptions } from '../src/main/captions'

const SAMPLE = `AI STACK — NARRATED REEL KIT (2026-06-22)
=============== REEL 1 — NVDA (AI CHIPS) ===============
File: reel_nvda_2026-06-22.mp4
Caption:
Every AI chip stock looks expensive except the biggest one.
Hashtags: #nvidia #nvda
=============== REEL 2 — IONQ (QUANTUM) ===============
Caption:
Quantum gets traded like one bet.
Hashtags: #ionq`

describe('parseCaptions', () => {
  it('returns caption text per ticker', () => {
    const c = parseCaptions(SAMPLE)
    expect(c.NVDA).toContain('biggest one')
    expect(c.NVDA).toContain('#nvidia')
    expect(c.IONQ).toContain('one bet')
  })
  it('returns {} for empty input', () => {
    expect(parseCaptions('')).toEqual({})
  })
})
```

- [ ] **Step 2: Run to verify fail**

Run: `cd studio && npx vitest run test/captions.test.ts`
Expected: FAIL — `parseCaptions` not defined.

- [ ] **Step 3: Implement `studio/src/main/captions.ts`**

```ts
// Parses the reel/post caption sheets: sections headed "=== ... — TICKER (..) ===",
// returns { TICKER: "caption + hashtags block" }.
export function parseCaptions(text: string): Record<string, string> {
  const out: Record<string, string> = {}
  if (!text.trim()) return out
  const blocks = text.split(/^={3,}.*$/m)
  const heads = text.match(/^={3,}.*$/gm) || []
  for (let i = 0; i < heads.length; i++) {
    const tk = heads[i].match(/—\s*([A-Z]{1,6})\b/)?.[1]
    if (!tk) continue
    const body = (blocks[i + 1] || '').trim()
    if (body) out[tk] = body
  }
  return out
}
```

- [ ] **Step 4: Run to verify pass**

Run: `cd studio && npx vitest run test/captions.test.ts`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add studio/src/main/captions.ts studio/test/captions.test.ts
git commit -m "feat(studio): caption-sheet section parser, TDD"
```

---

## Task 5: Data join (pure, TDD)

**Files:**
- Create: `studio/src/main/datajoin.ts`
- Create: `studio/test/datajoin.test.ts`

- [ ] **Step 1: Write failing test `studio/test/datajoin.test.ts`**

```ts
import { describe, it, expect } from 'vitest'
import { joinStock, type Bundles } from '../src/main/datajoin'

const B: Bundles = {
  site: { stocks: { NVDA: { layer: 'L1-chips', valuation: { price: 210, fundamental_value: 345, fundamental_discount_pct: 39, fundamental_valuation: 'Undervalued' } } } },
  quantum: { stocks: { IONQ: { valuation: { price: 56, fundamental_value: 86, fundamental_discount_pct: 35 } } } },
  congress: { trades: [{ ticker: 'NVDA', politician: 'Jane Doe', txn_type: 'S', txn_date: '06/16/2026', amount_range_low: 1001, amount_range_high: 15000 }] }
}

describe('joinStock', () => {
  it('finds an AI-stack name in site and attaches congress trades', () => {
    const r = joinStock('NVDA', B)
    expect(r.found).toBe(true)
    expect(r.source).toBe('site')
    expect(r.valuation?.fundamental_discount_pct).toBe(39)
    expect(r.congress_trades.length).toBe(1)
  })
  it('falls back to quantum', () => {
    expect(joinStock('IONQ', B).source).toBe('quantum')
  })
  it('reports not found cleanly', () => {
    expect(joinStock('ZZZZ', B).found).toBe(false)
  })
})
```

- [ ] **Step 2: Run to verify fail**

Run: `cd studio && npx vitest run test/datajoin.test.ts`
Expected: FAIL — `joinStock` not defined.

- [ ] **Step 3: Implement `studio/src/main/datajoin.ts`**

```ts
export type Bundles = { site?: any; quantum?: any; congress?: any }
export type StockView = {
  found: boolean
  source?: 'site' | 'quantum'
  layer?: string
  valuation?: any
  congress_trades: any[]
}

export function joinStock(ticker: string, b: Bundles): StockView {
  const t = ticker.toUpperCase()
  let rec: any, source: 'site' | 'quantum' | undefined
  if (b.site?.stocks?.[t]) { rec = b.site.stocks[t]; source = 'site' }
  else if (b.quantum?.stocks?.[t]) { rec = b.quantum.stocks[t]; source = 'quantum' }
  const trades = (b.congress?.trades || []).filter((x: any) => x.ticker === t)
  if (!rec) return { found: false, congress_trades: trades }
  return { found: true, source, layer: rec.layer, valuation: rec.valuation, congress_trades: trades }
}
```

- [ ] **Step 4: Run to verify pass**

Run: `cd studio && npx vitest run test/datajoin.test.ts`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add studio/src/main/datajoin.ts studio/test/datajoin.test.ts
git commit -m "feat(studio): ticker->data join across site/quantum/congress, TDD"
```

---

## Task 6: Wire IPC — posts.list / stock.get / caption.get

**Files:**
- Create: `studio/src/main/api.ts`
- Modify: `studio/src/main/index.ts`
- Modify: `studio/src/preload/index.ts`
- Modify: `studio/src/renderer/src/global.d.ts`

- [ ] **Step 1: Create `studio/src/main/api.ts`**

```ts
import { ipcMain } from 'electron'
import { readFileSync, readdirSync, existsSync } from 'fs'
import { join } from 'path'
import { HIGGS, CONTENT, DATA } from './paths'
import { buildIndex } from './indexer'
import { parseCaptions } from './captions'
import { joinStock, type Bundles } from './datajoin'

function walk(dir: string, base = ''): string[] {
  if (!existsSync(dir)) return []
  const out: string[] = []
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const rel = base ? `${base}/${e.name}` : e.name
    if (e.isDirectory()) out.push(...walk(join(dir, e.name), rel))
    else out.push(rel)
  }
  return out
}
const readJson = (f: string) => { try { return JSON.parse(readFileSync(join(DATA, f), 'utf-8')) } catch { return undefined } }

export function registerApi(): void {
  ipcMain.handle('posts:list', () => {
    const higgs = existsSync(HIGGS) ? readdirSync(HIGGS) : []
    const content = walk(CONTENT)
    return buildIndex({ higgs, content })
  })
  ipcMain.handle('stock:get', (_e, ticker: string) => {
    const b: Bundles = { site: readJson('site.json'), quantum: readJson('quantum.json'), congress: readJson('congress.json') }
    return joinStock(ticker, b)
  })
  ipcMain.handle('caption:get', (_e, date: string, ticker: string) => {
    for (const name of [`reels_${date}.txt`, `posts_${date}.txt`]) {
      const p = join(HIGGS, name)
      if (existsSync(p)) {
        const c = parseCaptions(readFileSync(p, 'utf-8'))
        if (c[ticker.toUpperCase()]) return c[ticker.toUpperCase()]
      }
    }
    return ''
  })
}
```

- [ ] **Step 2: Register in `studio/src/main/index.ts`**

Add import:
```ts
import { registerApi } from './api'
```
Inside `app.whenReady().then(...)`, add (before `createWindow()`):
```ts
  registerApi()
```

- [ ] **Step 3: Expand `studio/src/preload/index.ts`** (add to the `studio` object)

```ts
  posts: { list: () => ipcRenderer.invoke('posts:list') },
  stock: { get: (ticker: string) => ipcRenderer.invoke('stock:get', ticker) },
  caption: { get: (date: string, ticker: string) => ipcRenderer.invoke('caption:get', date, ticker) },
  reveal: (rel: string) => ipcRenderer.send('reveal', rel),
  copy: (text: string) => ipcRenderer.send('copy', text),
  quickAction: (name: string) => ipcRenderer.send('quick', name)
```

- [ ] **Step 4: Add reveal/copy/quick handlers in `studio/src/main/api.ts`** (append inside `registerApi`)

```ts
  // appended inside registerApi():
  const { shell, clipboard } = require('electron')
  ipcMain.on('reveal', (_e, rel: string) => shell.showItemInFolder(join(HIGGS, '..', rel)))
  ipcMain.on('copy', (_e, text: string) => clipboard.writeText(text))
  const QUICK: Record<string, string> = {
    'refresh-data': 'cd scripts; python refresh_daily.py; cd ..',
    'make-reels': 'python higgs/make_reel.py NVDA <hero_url> <voice_url>  # edit args / see README_reels.md',
    'build-carousel': 'python higgs/_build_v4.py'
  }
  ipcMain.on('quick', (e, name: string) => {
    const cmd = QUICK[name]
    if (cmd) e.sender.send('term:data', '') // no-op; renderer injects via term:input
  })
```

> Note: the quick-action actually injects into the PTY from the renderer (Task 9) via `term.input(cmd + "\r")`; the main `QUICK` map is the source of command strings, exposed by adding to preload: `quickCmd: (name: string) => ipcRenderer.sendSync('quick:cmd', name)` and in api.ts `ipcMain.on('quick:cmd', (e,n)=>{ e.returnValue = QUICK[n] || '' })`. Implement that sendSync pair now:

Add to `api.ts` registerApi:
```ts
  ipcMain.on('quick:cmd', (e, name: string) => { e.returnValue = QUICK[name] || '' })
```
Add to preload `studio` object:
```ts
  quickCmd: (name: string) => ipcRenderer.sendSync('quick:cmd', name)
```

- [ ] **Step 5: Extend `studio/src/renderer/src/global.d.ts`** (add to the `studio` interface)

```ts
      posts: { list(): Promise<Array<{ date: string; ticker: string; kind: string; media: string[]; poster?: string; captionFile?: string }>> }
      stock: { get(ticker: string): Promise<{ found: boolean; source?: string; layer?: string; valuation?: any; congress_trades: any[] }> }
      caption: { get(date: string, ticker: string): Promise<string> }
      reveal(rel: string): void
      copy(text: string): void
      quickCmd(name: string): string
```

- [ ] **Step 6: Smoke test — data over IPC**

Run: `cd studio && npm run dev`, DevTools console:
```js
await window.studio.posts.list()        // -> array incl. {ticker:'NVDA', date:'2026-06-22', kind:'reel', ...}
await window.studio.stock.get('NVDA')    // -> {found:true, valuation:{fundamental_discount_pct:39,...}}
await window.studio.caption.get('2026-06-22','NVDA') // -> caption text
```
Expected: each returns real data.

- [ ] **Step 7: Commit**

```bash
git add studio/src
git commit -m "feat(studio): IPC api — posts.list, stock.get, caption.get, reveal/copy/quick"
```

---

## Task 7: Gallery UI (grouped tiles + filters)

**Files:**
- Create: `studio/src/renderer/src/components/Gallery.tsx`
- Create: `studio/src/renderer/src/store.ts`
- Modify: `studio/src/renderer/src/App.tsx`

- [ ] **Step 1: Create `studio/src/renderer/src/store.ts`**

```tsx
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
type Post = Awaited<ReturnType<typeof window.studio.posts.list>>[number]
type Ctx = { posts: Post[]; refresh: () => void; selected: Post | null; select: (p: Post | null) => void }
const C = createContext<Ctx>(null as any)
export const useStudio = () => useContext(C)
export function StudioProvider({ children }: { children: ReactNode }) {
  const [posts, setPosts] = useState<Post[]>([])
  const [selected, select] = useState<Post | null>(null)
  const refresh = () => window.studio.posts.list().then(setPosts)
  useEffect(() => { refresh() }, [])
  return <C.Provider value={{ posts, refresh, selected, select }}>{children}</C.Provider>
}
```

- [ ] **Step 2: Create `studio/src/renderer/src/components/Gallery.tsx`**

```tsx
import { useMemo, useState } from 'react'
import { useStudio } from '../store'

export default function Gallery() {
  const { posts, select } = useStudio()
  const [day, setDay] = useState('all'); const [tk, setTk] = useState('all')
  const days = useMemo(() => ['all', ...Array.from(new Set(posts.map(p => p.date)))], [posts])
  const tks = useMemo(() => ['all', ...Array.from(new Set(posts.map(p => p.ticker)))], [posts])
  const shown = posts.filter(p => (day === 'all' || p.date === day) && (tk === 'all' || p.ticker === tk))
  const grouped = useMemo(() => {
    const m = new Map<string, typeof shown>()
    for (const p of shown) { (m.get(p.date) ?? m.set(p.date, []).get(p.date)!).push(p) }
    return [...m.entries()]
  }, [shown])

  return (
    <div className="flex-1 overflow-auto p-5">
      <div className="flex gap-3 mb-5 font-mono text-sm">
        <select value={day} onChange={e => setDay(e.target.value)} className="bg-white/5 px-3 py-1 rounded">{days.map(d => <option key={d}>{d}</option>)}</select>
        <select value={tk} onChange={e => setTk(e.target.value)} className="bg-white/5 px-3 py-1 rounded">{tks.map(t => <option key={t}>{t}</option>)}</select>
      </div>
      {grouped.map(([date, items]) => (
        <div key={date} className="mb-7">
          <div className="font-mono text-xs tracking-widest text-emerald-400 mb-3">{date}</div>
          <div className="grid grid-cols-4 gap-4">
            {items.map((p, i) => {
              const mp4 = p.media.find(m => m.endsWith('.mp4'))
              const img = p.media.find(m => m.endsWith('.png'))
              return (
                <button key={i} onClick={() => select(p)} className="text-left rounded-xl overflow-hidden border border-white/10 hover:border-emerald-400/60 bg-white/5">
                  <div className="aspect-[4/5] bg-black/40 flex items-center justify-center">
                    {mp4 ? <video src={mp4} muted className="h-full w-full object-cover" /> :
                     img ? <img src={img} className="h-full w-full object-cover" /> :
                     <span className="text-white/30 text-xs">{p.kind}</span>}
                  </div>
                  <div className="px-3 py-2 font-mono text-sm flex justify-between">
                    <span className="font-bold">{p.ticker}</span><span className="text-white/40">{p.kind}</span>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 3: Wire into `App.tsx`**

Replace `<main>...</main>` with `<Gallery />` and wrap the whole return in `<StudioProvider>`. New `App.tsx`:
```tsx
import Terminal from './components/Terminal'
import Gallery from './components/Gallery'
import Detail from './components/Detail'
import { StudioProvider, useStudio } from './store'

function Shell() {
  const { refresh } = useStudio()
  return (
    <div className="h-screen flex flex-col">
      <header className="h-14 px-5 flex items-center justify-between border-b border-white/10">
        <span className="font-mono tracking-widest text-emerald-400">AI STACK STUDIO</span>
        <button onClick={refresh} className="font-mono text-xs bg-white/5 hover:bg-white/10 px-3 py-1 rounded">Refresh</button>
      </header>
      <div className="flex-1 flex overflow-hidden">
        <Gallery />
        <Detail />
      </div>
      <footer className="h-56 border-t border-white/10 bg-[#0A0D12]"><Terminal /></footer>
    </div>
  )
}
export default function App() { return <StudioProvider><Shell /></StudioProvider> }
```

- [ ] **Step 4: Create a stub `studio/src/renderer/src/components/Detail.tsx`** (filled in Task 8)

```tsx
export default function Detail() { return null }
```

- [ ] **Step 5: Smoke test — gallery renders**

Run: `cd studio && npm run dev`
Expected: gallery shows tiles grouped by date (newest first); NVDA/IONQ/ADBE/congress reels show video thumbnails; day/stock filters work.

- [ ] **Step 6: Commit**

```bash
git add studio/src/renderer
git commit -m "feat(studio): gallery — post bundles grouped by day/stock with filters"
```

---

## Task 8: Detail panel (player/slides + data + caption + copy/reveal)

**Files:**
- Modify: `studio/src/renderer/src/components/Detail.tsx`

- [ ] **Step 1: Implement `studio/src/renderer/src/components/Detail.tsx`**

```tsx
import { useEffect, useState } from 'react'
import { useStudio } from '../store'

export default function Detail() {
  const { selected, select } = useStudio()
  const [data, setData] = useState<any>(null)
  const [caption, setCaption] = useState('')
  useEffect(() => {
    if (!selected) return
    window.studio.stock.get(selected.ticker).then(setData)
    window.studio.caption.get(selected.date, selected.ticker).then(setCaption)
  }, [selected])
  if (!selected) return null
  const mp4 = selected.media.find(m => m.endsWith('.mp4'))
  const imgs = selected.media.filter(m => m.endsWith('.png'))
  const v = data?.valuation
  return (
    <aside className="w-[420px] border-l border-white/10 overflow-auto p-5 bg-[#0B0E14]">
      <div className="flex justify-between items-center mb-4">
        <span className="font-mono text-lg font-bold">{selected.ticker} <span className="text-white/40 text-sm">{selected.date}</span></span>
        <button onClick={() => select(null)} className="text-white/40 hover:text-white">✕</button>
      </div>
      {mp4 ? <video src={mp4} controls className="w-full rounded-lg mb-4" /> :
        <div className="grid grid-cols-3 gap-2 mb-4">{imgs.map((s, i) => <img key={i} src={s} className="rounded" />)}</div>}
      {v && (
        <div className="font-mono text-sm bg-white/5 rounded-lg p-4 mb-4 space-y-1">
          <div className="text-emerald-400 tracking-widest text-xs mb-2">DATA · {data.source}</div>
          <Row k="Price" val={`$${v.price}`} /><Row k="Fundamental value" val={`$${v.fundamental_value}`} />
          <Row k="Discount" val={`${v.fundamental_discount_pct}%`} /><Row k="Tag" val={v.fundamental_valuation ?? '—'} />
          {data.layer && <Row k="Layer" val={data.layer} />}
          {data.congress_trades?.length > 0 && <Row k="Congress trades" val={String(data.congress_trades.length)} />}
        </div>
      )}
      {caption && (
        <div className="mb-3">
          <div className="text-emerald-400 tracking-widest text-xs font-mono mb-2">CAPTION</div>
          <textarea defaultValue={caption} className="w-full h-40 bg-white/5 rounded p-3 text-sm" />
        </div>
      )}
      <div className="flex gap-2 font-mono text-xs">
        <button onClick={() => window.studio.copy(caption)} className="bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 px-3 py-2 rounded">Copy caption</button>
        {mp4 && <button onClick={() => window.studio.reveal(mp4.replace('media://', ''))} className="bg-white/5 hover:bg-white/10 px-3 py-2 rounded">Reveal file</button>}
      </div>
    </aside>
  )
}
function Row({ k, val }: { k: string; val: string }) {
  return <div className="flex justify-between"><span className="text-white/40">{k}</span><span>{val}</span></div>
}
```

- [ ] **Step 2: Smoke test — detail panel**

Run: `cd studio && npm run dev`
Expected: click NVDA reel → panel shows the playable video, DATA block (Price $210, Discount 39%, Tag Undervalued), the caption in an editable box; "Copy caption" copies; "Reveal file" opens the OS folder with the mp4 selected.

- [ ] **Step 3: Commit**

```bash
git add studio/src/renderer/src/components/Detail.tsx
git commit -m "feat(studio): detail panel — player/slides + live data + caption + copy/reveal"
```

---

## Task 9: Quick-actions row (inject commands into the terminal)

**Files:**
- Modify: `studio/src/renderer/src/components/Terminal.tsx`
- Create: `studio/src/renderer/src/components/QuickActions.tsx`
- Modify: `studio/src/renderer/src/App.tsx`

- [ ] **Step 1: Export a terminal-input helper from `Terminal.tsx`**

Add a module-level injector and register it on mount. At top of `Terminal.tsx` (module scope):
```tsx
export let injectToTerminal: (cmd: string) => void = () => {}
```
Inside the `useEffect`, after `term.onData(...)`, add:
```tsx
    injectToTerminal = (cmd: string) => { window.studio.term.input(cmd + '\r') }
```

- [ ] **Step 2: Create `studio/src/renderer/src/components/QuickActions.tsx`**

```tsx
import { injectToTerminal } from './Terminal'
const ACTIONS = [
  { name: 'refresh-data', label: 'Refresh data' },
  { name: 'build-carousel', label: 'Build carousel' },
  { name: 'make-reels', label: 'Make reels' }
]
export default function QuickActions() {
  return (
    <div className="flex gap-2 px-3 py-2 border-b border-white/10 font-mono text-xs">
      {ACTIONS.map(a => (
        <button key={a.name} onClick={() => injectToTerminal(window.studio.quickCmd(a.name))}
          className="bg-white/5 hover:bg-emerald-500/20 px-3 py-1 rounded">{a.label}</button>
      ))}
      <span className="ml-auto text-white/30 self-center">type <b>claude</b> to chat ↓</span>
    </div>
  )
}
```

- [ ] **Step 3: Add QuickActions above the terminal in `App.tsx`**

Change the footer to:
```tsx
      <footer className="h-64 border-t border-white/10 bg-[#0A0D12] flex flex-col">
        <QuickActions />
        <div className="flex-1 overflow-hidden"><Terminal /></div>
      </footer>
```
And import:
```tsx
import QuickActions from './components/QuickActions'
```

- [ ] **Step 4: Smoke test**

Run: `cd studio && npm run dev`
Expected: clicking "Build carousel" types `python higgs/_build_v4.py` into the terminal and runs it; output appears; gallery "Refresh" then shows any new slides.

- [ ] **Step 5: Commit**

```bash
git add studio/src/renderer
git commit -m "feat(studio): quick-actions row injecting pipeline commands into the shell"
```

---

## Task 10: House styling polish + fonts

**Files:**
- Modify: `studio/src/renderer/index.html`
- Modify: `studio/src/renderer/src/index.css`

- [ ] **Step 1: Add fonts in `index.html`** (inside `<head>`)

```html
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet" />
```
> Note: extend the CSP `style-src`/`font-src` to allow Google Fonts: update the CSP meta to `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com;` (append to existing directives).

- [ ] **Step 2: Polish `index.css`**

```css
@import "tailwindcss";
:root { color-scheme: dark; }
body { margin: 0; background: #0A0D12; color: #E8EDF2; font-family: Inter, system-ui, sans-serif; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: #1d2530; border-radius: 6px; }
.font-display { font-family: 'Fraunces', serif; }
.font-mono { font-family: 'JetBrains Mono', monospace; }
```

- [ ] **Step 3: Smoke test** — Run `cd studio && npm run dev`; confirm fonts/scrollbars look like the house style. 

- [ ] **Step 4: Commit**

```bash
git add studio/src/renderer
git commit -m "style(studio): house dark-emerald theme + fonts"
```

---

## Task 11: `npm run studio` launcher + README + git artifact policy

**Files:**
- Modify: `package.json` (repo root — add a convenience script)
- Create: `studio/README.md`
- Create: `higgs/.gitignore`

- [ ] **Step 1: Check for a root `package.json`**

Run: `ls package.json` (repo root).
- If it exists, add to its `scripts`: `"studio": "cd studio && npm run dev"`.
- If it does NOT exist, create `studio/RUN.md` with the line `Run the studio: cd studio && npm install && npm run dev` and skip the root-script edit.

- [ ] **Step 2: Create `higgs/.gitignore` (commit deliverables, ignore intermediates)**

```
# Intermediates & source art — regenerable, keep out of git
hero_*
logo_*
maya_*
voice_*.mp3
_*.py
_*.sh
_*.js
_check*
*.json
# (Deliverables ARE committed: reel_*.mp4, v4_*.png, post*_*.png, posts_*.txt, reels_*.txt)
!reel_*.mp4
!v4_*.png
!post*_*.png
!posts_*.txt
!reels_*.txt
```

> Note: `make_reel.py`, `_build_*.py` etc. are matched by `_*.py`; but `make_reel.py` does NOT start with `_`. The pipeline scripts that should stay in git (`make_reel.py`, `_build_reel_stock.py`, `_build_v4.py`, `_workflow_make_reels.js`, `README_reels.md`, `reels_manifest.json`) — DECISION: keep the builder scripts tracked. So refine: do NOT ignore `_build_*`, `make_reel.py`, `_workflow_*`, `README_reels.md`, `reels_manifest.json`. Use this corrected `higgs/.gitignore` instead:

```
# Source art & scratch — regenerable, keep out of git
hero_*
logo_*
maya_*
voice_*.mp3
_check*
*_anim.mp4
# everything else under higgs/ (builder scripts, deliverables, manifests, README) is tracked
```

- [ ] **Step 3: Create `studio/README.md`**

```markdown
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
```

- [ ] **Step 4: Stage the deliverables + studio per the policy**

```bash
git add higgs/.gitignore studio/README.md
git add higgs/reel_*.mp4 higgs/v4_*.png higgs/post*_*.png higgs/posts_*.txt higgs/reels_*.txt
git add higgs/make_reel.py higgs/_build_reel_stock.py higgs/_build_v4.py higgs/_build_reel_congress.py higgs/_workflow_make_reels.js higgs/README_reels.md higgs/reels_manifest.json
git status   # verify: heroes/logos/voice mp3s NOT staged
```
Expected: staged = deliverables + builder scripts + studio; NOT staged = `hero_*`, `logo_*`, `voice_*.mp3`, `*_anim.mp4`.

- [ ] **Step 5: Commit**

```bash
git commit -m "chore(studio): launcher + README; commit reel/post deliverables to git"
```

---

## Task 12: electron-builder packaging config (Windows now; Mac/Linux ready)

**Files:**
- Modify: `studio/package.json` (add `build` block)
- Create: `studio/electron-builder.yml`

- [ ] **Step 1: Create `studio/electron-builder.yml`**

```yaml
appId: com.aistack.studio
productName: AI STACK Studio
directories: { output: dist }
files: [ "out/**/*", "package.json" ]
asarUnpack: [ "**/node_modules/node-pty/**" ]
win: { target: [ { target: nsis, arch: [x64] } ] }
mac: { target: [ dmg ], category: public.app-category.finance }
linux: { target: [ AppImage ] }
```

- [ ] **Step 2: Add the dist script to `studio/package.json` scripts**

```json
    "dist": "electron-vite build && electron-builder --config electron-builder.yml"
```

- [ ] **Step 3: Build test (Windows)**

Run: `cd studio && npm run dist`
Expected: produces `studio/dist/AI STACK Studio Setup 0.1.0.exe`. (Mac/Linux targets build on those OSes from the same config.) Launch the installer output to confirm the app runs standalone with the terminal + gallery.

- [ ] **Step 4: Commit**

```bash
git add studio/package.json studio/electron-builder.yml
git commit -m "build(studio): electron-builder packaging (win/mac/linux targets)"
```

---

## Self-Review

**Spec coverage:**
- §3 Architecture (Electron 2-proc, electron-vite, media://, node-pty) → Tasks 0,1,2.
- §4 Layout (gallery-first, terminal docked, header, detail) → Tasks 7,8,9.
- §5 data model + indexer/data-join (TDD) → Tasks 3,5; caption parser → Task 4.
- §6 IPC surface → Task 6.
- §7 data flow → Tasks 6–9.
- §8 git artifact policy → Task 11.
- §9 risks (node-pty rebuild first) → Task 1 (built first); media:// → Task 2.
- §10 build order → task order matches.
- §11 testing (vitest pure fns + manual smoke) → Tasks 3,4,5 unit; smoke steps in 1,2,6,7,8,9,12.
- §2 non-goals (no autopost, no mobile) → not built; copy/reveal in Task 8 stands in for "launch".

**Placeholder scan:** All code blocks are concrete. The two `> Note:` callouts in Tasks 3 and 11 are corrections to fold in (move `v4slides` local; corrected `higgs/.gitignore`) — the engineer must apply the corrected version, not the first draft. No TBD/TODO remain.

**Type consistency:** `Post` shape consistent across indexer.ts, global.d.ts, store.ts, Gallery, Detail. `studio` bridge methods (`term`, `posts`, `stock`, `caption`, `reveal`, `copy`, `quickCmd`) declared in preload AND global.d.ts AND used in components — all match. `joinStock`/`StockView` consistent between datajoin.ts and Detail's `data.valuation`/`data.source`/`data.congress_trades`.

**Known follow-ups (acceptable):** `make-reels` quick-action command is a reminder string (needs hero/voice URLs from Phase-1 MCP) — intentional, documented inline. Mac/Linux dist builds require those OSes.
