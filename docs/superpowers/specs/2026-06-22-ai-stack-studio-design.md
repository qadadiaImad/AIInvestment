# AI STACK STUDIO — design spec

*Date: 2026-06-22 · Status: approved-for-planning · Educational/research tooling — not financial advice.*

## 1. Goal

A local **content command center** the owner opens when working on Instagram/TikTok posting. One window that:

1. **Shows the data** the posts are built from (valuations/discounts, congress trades, news) — "visualize the selected data from the console."
2. **Galleries the produced reels/posts**, grouped **by day → stock**, with video/slide preview + the caption.
3. Hosts a **live PowerShell terminal** where the owner runs `claude` and chats — the same shell that drives the pipelines, embedded in the UI.

It is a personal, single-user, local desktop app — a launchpad, not a publisher.

## 2. Non-goals (explicit cuts / YAGNI)

- **No auto-posting** to Instagram/TikTok (their post APIs are gated/painful). v1 = *review & launch*: copy caption to clipboard + reveal the mp4 in the OS file manager; the owner drops it into the native app.
- **No mobile/Android.** The core feature (a real local PowerShell running `claude`) needs an OS shell + filesystem + process spawning, which phones forbid. Cross-platform here = **Windows / macOS / Linux desktop** (Electron, one codebase). Decided 2026-06-22.
- **No in-app media editing**, no auth (local single-user), no remote/hosted mode.

## 3. Architecture

Electron, two processes + a secure preload bridge.

- **Main process (Node).** Owns the OS: spawns a **PowerShell PTY** via `node-pty`; scans `higgs/` + `content/` into a media index; reads `web/public/data/*.json`; registers a custom **`media://` protocol** to serve local mp4/png to the renderer safely. Working directory = repo root.
- **Renderer (React + Tailwind).** The cockpit UI in the house dark-emerald style (Fraunces / Inter / JetBrains Mono) to match the posts.
- **Preload bridge.** `contextIsolation: true`, `nodeIntegration: false`, `sandbox` where feasible. Exposes a minimal typed API via `contextBridge` — no raw Node in the renderer.

**Stack:** `electron-vite` (React HMR for the renderer; bundles main/preload) · `xterm.js` + `@xterm/addon-fit` · `node-pty` (rebuilt for Electron's ABI via `@electron/rebuild`; Windows uses the conpty backend, available on the owner's Win11) · Tailwind v4.

**Why not Next.js / the existing `web/` app:** the public site is a static Vercel deploy and can't host a PTY; and `web/AGENTS.md` warns Next 16 here is non-standard. The Studio is a **separate `studio/` app**, sidestepping both. It only *reads* `web/public/data/*.json` and the media dirs.

## 4. Layout (gallery-first, terminal docked)

```
┌───────────────────────────────────────────────┐
│ AI STACK STUDIO   [day▾] [stock▾] [Refresh] [⚙]│
├───────────────────────────────────────────────┤
│ GALLERY  (post bundles, grouped by day → stock)│
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐            │
│  │NVDA│ │IONQ│ │ADBE│ │CONG│ │ …  │            │
│  │▶mp4│ │▶mp4│ │post│ │▶mp4│ │    │            │
│  └────┘ └────┘ └────┘ └────┘ └────┘            │
│  click → DETAIL: player/slides + data + caption │
├───────────────────────────────────────────────┤
│ TERMINAL  PS> claude ____________   [▰ expand]  │
└───────────────────────────────────────────────┘
```

- **Header:** day filter, stock filter, Refresh (re-scan + optional pipeline run), settings.
- **Gallery:** tiles = *post bundles* (a reel + its 3 slides + caption, or a carousel). Reel tiles show a poster frame + ▶.
- **Detail panel (slide-in on click):** video player / slide carousel **+** that stock's live data (valuation, discount, congress trades, news) **+** the caption (read, copy-to-clipboard, reveal-in-explorer).
- **Terminal (docked bottom, expandable):** real PowerShell at repo root; type `claude` to chat. A **quick-actions row** (Refresh data · Make reels · Build carousel) injects the command into the shell so the owner stays in control rather than firing hidden jobs.

## 5. Data model & the testable core

**`Post` bundle** (normalized unit the gallery renders):
```
{ date: "2026-06-22", ticker: "NVDA", kind: "reel"|"carousel"|"post",
  media: ["media://higgs/reel_nvda_2026-06-22.mp4", ...slides],
  poster?: "media://...png", caption?: string, captionFile?: string }
```

**Media indexer (pure, TDD).** `filenames[] → Post[]` grouped by date→ticker. Parses the established naming:
- `higgs/reel_<tk>_<date>.mp4` → reel
- `higgs/v4_<tk>_{1_hook,2_data,3_takeaway}.png` → carousel slides for `<tk>`
- `higgs/posts_<date>.txt`, `higgs/reels_<date>.txt` → caption sheets (sectioned by ticker)
- `content/carousel_<date>/<TK>/slide_*.html` (+ `brief.md`) → HTML carousels
- (heroes/logos/scratch excluded from the gallery.)

**Data join (pure, TDD).** `ticker → stock record` across `site.json` / `quantum.json` / `congress_stocks.json`; congress member trades from `congress.json` `trades[]`.

Both are pure functions → **Vitest** unit tests (the project already uses vitest).

## 6. IPC surface (preload API)

Renderer ⇄ main, the only privileged calls:
- `terminal.start() / write(data) / onData(cb) / resize(cols,rows)` — PTY ↔ xterm.
- `posts.list()` → `Post[]` (from the indexer).
- `stock.get(ticker)` → merged data record.
- `caption.get(date, ticker)` → caption string.
- `revealInExplorer(path)` · `clipboard.write(text)` · `runQuickAction(name)` (types a known command into the PTY).
Media (mp4/png) loads via the `media://` protocol, not IPC.

## 7. Data flow

Launch → main scans media + reads JSON → renderer renders gallery (newest day first). Click tile → `stock.get` + `caption.get` → detail panel. Refresh → re-scan; quick-actions / typing `claude` drive pipelines in the PTY; new outputs appear on next Refresh. Terminal I/O streams over IPC to xterm; resize forwarded.

## 8. Git artifact policy (decided: commit posts/reels)

So a second laptop (git + Claude account) has the produced content:
- **Un-ignore & commit:** `higgs/reel_*.mp4`, `higgs/v4_*.png`, `higgs/posts_*.txt`, `higgs/reels_*.txt`, and `content/**` (the deliverables).
- **Stay ignored:** `higgs/hero_*`, `higgs/logo_*`, `_check*`, `maya_*`, other scratch (regenerable intermediates), and the bulky raw `data/` retrieval tree (the second laptop regenerates it via the pipelines). `web/public/data/*.json` bundles remain tracked as today.
- Note in the plan: this adds binaries to git history; acceptable per owner's choice for cross-laptop continuity.

## 9. Risks & mitigations

1. **`node-pty` native rebuild for Electron on Windows** — the one piece that can fail. Mitigation: pin Electron, `@electron/rebuild` in postinstall, conpty backend; **prove the terminal echoes before building gallery polish**. Degraded fallback: `child_process` PowerShell (no full TTY) if node-pty can't build.
2. **Loading local mp4 in the renderer** — solved by the `media://` custom protocol registered in main (avoids `file://` + webSecurity pitfalls).
3. **Indexer drift** if naming changes — covered by unit tests; the indexer is the single source of grouping truth.

## 10. Build order (milestones)

1. **Scaffold** `studio/` (electron-vite + React + Tailwind), secure window, blank 3-zone shell.
2. **Terminal first (de-risk):** node-pty PowerShell ↔ xterm; verify echo + `claude` launches; quick-actions row.
3. **Indexer + data join** (TDD) and `media://` protocol.
4. **Gallery** (grouped tiles, poster frames, filters).
5. **Detail panel** (player/slides + data + caption + copy/reveal).
6. **Polish** (house styling), `npm run studio` script, README, git-ignore changes + commit deliverables.
7. Cross-OS build config (electron-builder targets) — Windows now; Mac/Linux configs included, built on demand.

## 11. Testing

- **Unit (Vitest):** media indexer (`filenames → Post[]`), data join (`ticker → record`), caption-section parser.
- **Smoke (manual):** launch; terminal echoes + `claude` runs; gallery lists today's bundle; click plays the mp4; copy caption works; Refresh picks up a newly made reel.

## 12. Disclaimer

Personal research/automation tool. Content it surfaces is educational/market-commentary only — not financial advice; congress data is public-record transparency, not accusation.
