# Semis "Out of Buyers" Reel — Design Spec

> Educational/research only — **not financial advice**. This reel recreates the *format* and
> *narrative* of a third-party finance reel (Nicholas Crown, FB reel 2521427861663714) as an
> animated piece. Borrowed market figures are **relayed as reported and tagged on-screen "as
> reported · not independently verified"** — we are reporting a claim, not asserting our own
> data. The CTA does **not** offer trade setups/signals (hard rail).

**Date:** 2026-08-02
**Branch:** feat/multi-sector-research-platform (no push until owner says)
**Consumer:** @valuewithvalues IG/FB — a dramatic, retention-first market-story reel.

---

## 1. Goal

A ~35–40s vertical (1080×1920) animated reel that faithfully retells the source reel's 7-beat
"semis are running out of buyers" story — but with **no talking head**: cinematic **Grok video
clips** for the scenes + **Remotion** chart/gauge/typography animations, on our existing
`halal-reels` spine. Plus a short **mini cut**. Dramatic tone, matched to the original.

### Locked decisions (owner, 2026-08-02)
- **Numbers:** use the original's exact figures, **attributed** on-screen ("as reported"); no
  independent verification required. Honesty preserved by *relaying-a-claim* framing + micro-tag.
- **Medium:** **hybrid** — Grok video clips (cinematic scenes) + Remotion (charts, gauges, text,
  compositing). **Pipeline CONFIRMED (test `byu5pxyvs`):** `grok-cli video --json` returns a
  `vidgen.x.ai` MP4 URL (subscription, no credits), ~64s for a 6s 9:16 720p clip, **downloadable
  with plain `curl`** (no session auth, unlike images), high quality — a panic-trading-floor test
  clip is already usable for segment 1. Stills fallback documented but not needed.
- **Tone:** match the original's drama (crash / forced sellers / panic), within rails.
- **Presenter:** none — pure scenes + graphics.
- **CTA:** comment-keyword → DM mechanic kept, but payload is our **educational breakdown**, not
  "setups/signals" (hard rail; this is the one deliberate deviation from the source).

---

## 2. Segments → animation → asset

Persistent overlay across all beats: a **StickerHook** ("Semis are running out of **buyers**",
keyword gold) that stays pinned, plus a **RollingCaption** burned subtitle that advances per beat
(the two-caption system studied from the source).

| # | ~Len | Caption (rolling) | Animation | Asset source |
|---|---|---|---|---|
| 1 CRASH | 6s | "SanDisk crashed 14.1% today — semis are running out of buyers." | `CrashChart`: candlesticks free-fall −14.1%, red; cut to panic floor | **Grok video** (Seoul panic floor) + Remotion chart overlay |
| 2 LEVERAGE | 5s | "Retail leverage just hit a record $39B." | `LeverageGauge` slams to MAX; debt bar spikes past a record line | Remotion (reuse `LimitMeter`) over a Grok still |
| 3 KOREA | 5s | "It worked in Korea — until the market kept gapping lower." | Chart **gaps down** in violent steps over a Seoul skyline | **Grok video** (Seoul skyline dusk) + Remotion gap chart |
| 4 FORCED | 5s | "Now margin buyers are becoming forced sellers." | Buy-arrows flip red; margin-call **domino cascade** | Remotion motion over Grok still |
| 5 US | 5s | "Today showed it's a U.S. problem too." | Flag/map morph Korea→USA; same gap-down on a US index | **Grok video** (US exchange exterior) + Remotion |
| 6 ROTATION | 6s | "Bizarrely, healthcare just had its best week since 2022 — defensive rotation." | Capital flows **chips → healthcare** (amber→mint) | Remotion `RotationFlow` over Grok still |
| 7 CTA | 6s | "Comment SEMIS — I'll DM the full breakdown." | Sticker resolves; comment pill; rails | Grok terminal still + Remotion |

All figures on-screen carry a small **"as reported"** tag; the CLOSE carries the full rail.

### Numbers displayed (relayed as reported, not our data)
- SanDisk (SNDK) **−14.1%** one day · retail leverage record **$39B** · healthcare **best week
  since 2022**. Source attribution on the CTA/close: "market reports; relayed, not independently
  verified."

---

## 3. Architecture — reuse the `halal-reels` spine

Remotion 4 (30fps, 1080×1920). Reuse unchanged: `theme.ts` (`C` palette — dark `#0A0D12`, gold
`#E0A23B`, mint `#7FE9C2`, emerald; **red only inside chart candles/price-down, never as text
emphasis** — dramatic tone permits red *price* action, which is data, not decoration), `ui.tsx`
(`Bg`, `Kicker`, `Slam`, `Foot`, `LimitMeter`, easing), the `quiz/` music+whoosh audio bed, and
the `mini?: boolean` pattern.

### New units (presentational, deterministic)
- **`StickerHook`** — pinned white rounded caption box, bold near-black text + one gold keyword,
  drop-shadow; entrance pop, then holds.
- **`RollingCaption`** — burned subtitle line; per-beat advance with fade/slide.
- **`GrokClip`** — wraps Remotion `<OffthreadVideo src={staticFile(...)}>` with a dark scrim +
  optional Ken-Burns for stills; the compositing layer the charts sit on.
- **`CrashChart`** — candlestick free-fall (deterministic OHLC, accelerating drop, red candles).
- **`RotationFlow`** — particles/arrows flowing from an amber "chips" node to a mint "healthcare"
  node.
- Reuse `LimitMeter` for `LeverageGauge` (relabel MAX/record).
- **`SemisReel.tsx`** (full + `mini`), registered in `Root.tsx`.

### Assets
- Grok **video** clips → `halal-reels/public/semis/*.mp4` (via `grok-cli video`, subscription;
  returned URL fetched to disk — mechanic confirmed by test `byu5pxyvs`).
- Grok **stills** → `halal-reels/public/semis/*.jpg`.
- Media is gitignored; `.ts/.tsx` sources tracked.

---

## 4. Rails & honesty
- On-screen **"as reported · not independently verified"** tag on every borrowed figure.
- Persistent `Foot`: "Relaying reported market data · educational only — not financial advice ·
  not a recommendation or trade signal."
- CTA is a DM of our **educational** semis breakdown — never "setups/signals."
- "Panic floor" scene rendered tastefully as a Seoul trading floor (contextual to the Korea
  reference), not caricature.

## 5. Deliverables
- `halal-reels/src/SemisReel.tsx`, new components in `ui.tsx`/`charts.tsx`; `Root.tsx` two comps.
- Grok assets in `halal-reels/public/semis/`.
- Renders `higgs/semis_reel.mp4` (full) + `higgs/semis_reel_mini.mp4`; `higgs/semis_caption.txt`.

## 6. Build process (owner-requested)
- **Workflow + subagent-driven development**, all subagents/`agent()` calls on **`model:'sonnet'`**
  (orchestrator alone on the top model). Commit trailer `Co-Authored-By: Claude Opus 4.8 (1M
  context) <noreply@anthropic.com>`.
- TDD the deterministic chart/gauge math (superpowers:test-driven-development); visual comps
  verified by render + still review (superpowers:verification-before-completion — show frames).
- Asset generation (Grok video/stills) is an orchestrator step, verified visually before wiring.

## 7. Testing / verification
- `cd halal-reels && npx tsc --noEmit` clean.
- Unit-test deterministic OHLC/gauge/flow math.
- Render full + mini; **visually verify stills** for each of the 7 beats: hook sticker persists,
  captions legible, crash chart reads, rails + "as reported" present, palette correct.

## 8. Self-review notes
- Scope: one reel + mini, ~5 new presentational units, Grok asset batch — single plan.
- YAGNI: no VO in v1 (Grok TTS is a later add), no presenter/character, no live data fetch (the
  figures are relayed-as-reported by design).
- Risk: `grok-cli video` availability/latency — de-risked by test `byu5pxyvs`; documented stills
  fallback keeps the plan viable either way.
