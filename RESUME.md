# RESUME — session handoff for a fresh Claude (e.g. on another laptop)

> **New Claude: read this first, then `CLAUDE.md`.** It captures the state, decisions, and next
> action so you can continue without the original chat (Claude Code sessions don't sync between
> machines; this file + git are the handoff). Last updated 2026-06-22.

## 0. What this repo is
Data-acquisition engine for an AI/quantum/congress investing-research assistant **+** a social-content
layer (image carousels + narrated video reels for TikTok/Instagram). See `CLAUDE.md` (engine soul +
Playwright-MCP concurrency contract) and `references/investing-brief.md` (the investing mission).

## 1. How to resume on a new machine
1. `git clone https://github.com/qadadiaImad/AIInvestment.git && cd AIInvestment`
   then `git checkout feat/multi-sector-research-platform && git pull`
2. Run `claude`, `/login` to the same account.
3. Regenerate gitignored data (see §6): `cd scripts && pip install -r requirements.txt && python refresh_daily.py`
   (gated GuruFocus tier = ask Claude "update GuruFocus fundamentals" — Playwright MCP, serial).
4. To continue the active build, tell Claude:
   *"Read RESUME.md, CLAUDE.md, and docs/superpowers/plans/2026-06-22-ai-stack-studio.md, then start executing the studio plan."*

## 2. What was built this session (2026-06-20 → 06-22)
- **Full terminal-data refresh + prod deploy.** Refreshed AI-stack/quantum/congress/news/graph via a
  Workflow (parallel no-gate stages) + GuruFocus GF-Value via Playwright-MCP (serial Mode B); built and
  deployed to Vercel → **https://web-gules-three-67.vercel.app**. GF chart API version drifted to
  `v=1.8.70` (docs/memory updated).
- **Social posts → catchy, image-rich.** Iterated from bare-type cards to a news-story voice, then to
  image-rich carousels (Higgsfield hero art + real logo + BIG ticker). De-cringe rule: disclaimers stay
  thin on the footer only.
- **Reel engine (narrated 9:16 videos).** Animated AI hero + Higgsfield "Harrison" AI voice + ffmpeg
  Ken-Burns. Built 4 reels: NVDA (chips outlier), IONQ (quantum), ADBE (software), Congress (Van Epps).
  See `higgs/README_reels.md`.
- **AI STACK STUDIO** — spec + implementation plan written for a local Electron content cockpit
  (gallery + data viewer + embedded PowerShell/Claude terminal). **Not yet built** — this is the next task.

## 3. Where we are / NEXT ACTION
The Studio is **BUILT** (2026-06-22, all 13 plan tasks via subagent-driven-development; on branch
`feat/multi-sector-research-platform`, ~20 commits, HEAD `b1ed940`). It's in `studio/` (electron-vite +
React 19 + Tailwind v4): embedded PowerShell terminal (node-pty), `media://` protocol, IPC api, gallery +
detail panel, quick-actions, electron-builder packaging. 7/7 Vitest unit tests pass; `npm run dist` produced
a working installer (`studio/dist/AI STACK Studio Setup 0.1.0.exe`). node-pty needed NO rebuild — it loads
via NAPI prebuilds (see memory `studio-node-pty-electron`); packaging uses `npmRebuild:false`.

**Run it:** `cd studio && npm install && npm run dev`.
**NEXT (remaining/owner items):** (a) INTERACTIVE verification at the live Electron window — terminal echo +
`claude` launch, gallery tiles render, click-tile→detail, copy/reveal. (b) The live DATA panel is empty until
you regenerate `web/public/data/*.json` via `python scripts/refresh_daily.py` (gitignored). (c) Minor: Detail
caption `<textarea>` is uncontrolled — Copy copies the original caption, not in-box edits (confirm if you want
edits reflected). (d) Optional: add indexer tests for the v4-slide/caption-attach edge cases.
Full task-by-task record: `.superpowers/sdd/progress.md`.

## 4. Key files
| Path | What |
|---|---|
| `docs/superpowers/specs/2026-06-22-ai-stack-studio-design.md` | Studio design spec (approved) |
| `docs/superpowers/plans/2026-06-22-ai-stack-studio.md` | Studio implementation plan (13 TDD tasks) |
| `higgs/README_reels.md` | Reel engine: 2-phase pipeline, ffmpeg gotchas, costs |
| `higgs/make_reel.py` | Assemble one reel end-to-end (deterministic) |
| `higgs/_build_reel_stock.py` | 9:16 reel frames per stock (config-driven CFG dict) |
| `higgs/_build_v4.py` | Static image-rich carousels |
| `higgs/_workflow_make_reels.js` | `make-all-reels` workflow (parallel assembly) |
| `higgs/reels_manifest.json` | Reels + resolved Higgsfield asset URLs |
| `higgs/reels_2026-06-22.txt` | Captions for the 4 reels |
| `scripts/refresh_daily.py` / `refresh_congress.py` | Data refresh orchestrators |

## 5. Decisions locked (don't re-litigate)
- **Studio = Electron desktop** (Win/Mac/Linux; no mobile — a local PowerShell/Claude terminal can't run on phones).
- **Layout = gallery-first, terminal docked**; full cockpit at once; detail panel holds the data (no separate left rail).
- **No auto-posting** to IG/TikTok in v1 (copy-caption + reveal-file → drop into native app).
- **Commit reels/posts to git** (done — `higgs/` is tracked); raw `data/` + `web/public/data/*.json` stay gitignored.
- **Reel voice = Harrison** (Higgsfield ElevenLabs preset `573e5163-59b3-4926-aab1-951ef2985f81`).
- **ffmpeg ken-burns** MUST use `-loop 1` (no `-t`) + `-frames:v N` cap + `-crf` (else zoompan runaway → 500MB+ files).
- **Social rails:** no first person (analyst/anchor voice); never name the news outlet → "reportedly"; congress = transparency, NOT accusation; thin footer NFA only; catchy news-story structure.

## 6. What does NOT travel via git (regenerate on the new machine)
- `web/public/data/*.json` (live bundles the posts/studio read) — **gitignored.** Regenerate: `python scripts/refresh_daily.py` (+ GuruFocus via MCP).
- `data/` raw fundamentals — gitignored; same refresh regenerates.
- `higgs/hero_*`, `logo_*`, `voice_*.mp3`, `*_anim.mp4` — Higgsfield source art/scratch (regen via the reel engine; the FINAL `reel_*.mp4` deliverables ARE committed).
- This chat history + the `~/.claude/.../memory/` files (outside the repo). Condensed memory is in §7; to carry the full memory, copy `C:\Users\imadq\.claude\projects\C--Users-imadq-AIInvestment\memory\` to the new machine's matching `~/.claude` path.

## 7. Carried project memory (condensed — full files in ~/.claude)
- **Reel engine** — narrated 9:16: animated hero + Harrison voice + ffmpeg; 2-phase hybrid (MCP gen serial, assembly via parallel workflow); `higgs/`.
- **Social copy rules** — no first person; never name the source (esp. Yahoo) → "reportedly"; educational/NFA; congress not-accusation.
- **Social narrative style** — catchy news-story (hook→tension→reveal→so-what); congress posts tie trade to the member's committee/policy ("oversees X, sold X"); de-cringe = thin footer disclaimers; image-rich format (`_build_v4.py`).
- **Higgsfield → save to higgs/** — can't copy terminal URLs; always download generated media into `higgs/` and report the local path.
- **Ticker renames 2026** — BK→BNY, FI→FISV, K/DAY delisted, CTRA dead on GF, ALKAL needs `XPAR:`; GF `gf_value=0` = "no value" sentinel; GF chart API version drifts (now `v=1.8.70`) — read it from the page's XHR each run.
- **Prefer workflows** — default to the Workflow tool for substantial multi-step work; gated MCP stays serial, parallelism on no-gate stages.
- **Gated-source rule** — GuruFocus/paywall: isolated Playwright instance, harvest-in-one-pass, rotate; never store a gated read.
- **Cowork channel** — always read `cowork_instructions.txt` each turn; changes below its `---` line are new requests.

## 8. External state
- **Vercel prod:** https://web-gules-three-67.vercel.app (deployed 2026-06-20 with fresh data).
- **Higgsfield credits:** ~52 left as of 2026-06-22 (≈18/reel: hero+animate+voice).
- **GitHub:** branch `feat/multi-sector-research-platform` (also the de-facto main).
