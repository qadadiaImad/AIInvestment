---
name: newsroom-reel
description: >
  Build a "V&V Quarterly Report" broadcast news-reel episode in Remotion (halal-reels/):
  a parametric SVG news anchor + a NewsStudio broadcast set (back video-wall, floating LIVE
  screen, branded desk, scrolling ticker) + a shared kit (karaoke captions, chyron, lower-
  thirds, ambient money motif, stat chips) + a custom back-wall data-viz per beat + reusable
  newsroom artifacts (e.g. the live Debt Clock). Use whenever creating or editing an animated
  finance news-reel episode. Pair with expressive-voiceover (VO) and finance-reel-formats
  (pick the format) and short-form-scripting (write the beats).
---

# Newsroom Reel — broadcast finance sketch production

**Stack:** Remotion 4 in `halal-reels/`, 1080×1920 @ 30fps. Pure-SVG characters/sets (100%
frame-consistent). Render: `npx remotion render <CompId> out/x.mp4`; still:
`npx remotion still <CompId> out/x.png --frame=N`. Register every composition in `src/Root.tsx`.

## The four building blocks (`src/toon/`)

- **`host.tsx` — the anchor.** `PremiumHost` (refined flat-illustration bust, ~540×680 space,
  head ~270,248). Expression `HostExpr = {mouth:"rest"|"open"|"soft"|"flat"; blink; brow; look}`.
  Palette-swap `HostTheme`. Presets: `HOST_ANCHOR` (plum), `HOST_ANALYST` (navy),
  `HOST_QUANT` (green+glasses), `HOST_ANCHOR_M` (navy **male**: `masc:true` → short crop,
  jaw/stubble shading, muted lips, red tie). Add a theme for a new presenter; set `masc:true`
  for male. `HostPreview` composition shows busts side-by-side to eyeball a new face.
- **`studio.tsx` — the set.** `NewsStudio({host, screen, ticker, accent, skin, f, wall, screenLabel})`.
  Draws dark studio + back video-wall (dotted map, ambient chart screens, V&V bug), spotlight,
  host behind a branded curved desk, a floating LIVE screen (inject compact readouts via `screen`),
  and a scrolling ticker. **`wall`** = the big back-wall hero viz region (896×410 at translate(92 250)).
  Ticker scroll period is length-aware (two copies tile seamlessly) — just pass a long `ticker` string.
- **`reelkit.tsx` — shared UI.** `FUN`/`BODY` fonts; `PAL` {gold,mint,red,green,ink,paper}; `isBlink`,`flap`.
  - `Karaoke{caps,id,cue,hot,max,reveal}` — word-timed captions. `max` chunks long lines into
    subtitle-sized groups; `reveal` pops each word in as spoken (use both for multi-second lines).
  - `Chyron{f,tag,text,red}`, `Bug`, `Disclaimer{text}`, `Source{t}` — broadcast furniture.
  - `studioHost(f,theme,mouthTalk)` — the bobbing/blinking/lip-flapping anchor for the set.
  - `BigFace{theme,f,mouth,brow}` — big reaction head for a full-bleed turn/reaction beat.
  - `MoneyMotif{f,tint,count,base}` — ambient drifting $/coins to fill empty full-bleed backgrounds.
  - `Chip{big,small,tint}` — stat pill; use a row of them to fill space AND reinforce numbers.
- **`props.tsx` — reusable newsroom artifacts.** `DebtClock{f,base,rate,digitSize,label,color}` — a
  live LED counter (fixed-cell digits so it never wobbles; single glow layer, no ghost). Drop into a
  `screen`/`wall` slot or render big on a CTA. **Build new fixtures here** (a rate board, an index
  ticker) the same way so any episode can reuse them.

## Episode anatomy

One episode file `src/QuarterlyReport<Name>.tsx` = VO/captions + a back-wall viz per beat + scene text.
Standard three-scene shape:

1. **Studio** (`<NewsStudio>`) — the main run; the `wall` morphs across beats (pick by frame), the
   `screen` shows a compact live readout, a `Chyron` labels the segment, `Karaoke` runs the VO.
2. **Kicker / reaction** — a full-bleed beat (`BigFace` reaction, or a stark chart like a bar duel).
3. **CTA** — the payoff card; mirror the opening visual (loop bait) + one earned CTA + disclaimer.

**Data-driven timeline (do this):** derive beat offsets from the actual VO durations so a
voice/script change re-times itself:
```
const F = (id) => Math.round(C[id].dur * 30);   // C = imported captions json
const _d2 = _d1 + F("d1") + GAP; ...            // sequential offsets
const A = _d5 + F("d5") + tail;                 // studio length
const ABS = { d1:_d1, ..., d6: A+6, d7: A+Cn+6 };
```
Pass `from={ABS.dN}` into any wall whose internal animation must track its beat. Export
`QR_<NAME>_BEATS = { total: A+Cn+D }` and register in `Root.tsx`.

## Back-wall viz conventions

Each beat's `wall` is an SVG `<g>` filling the **896×410** region. Reveal elements by frame
(`interpolate(f-from, …)`), color from `PAL`, headline top-left, keep it legible at phone size.
Examples in the repo: `LoopWall` (circular money diagram), `TierWall` (ranked bars), `CascadeWall`
(seed→ripple counter), `StackWall`/`BondWall`/`HoldersWall` (debt ep). Copy the closest one.

## Build workflow

1. **Format** → `finance-reel-formats` (don't default to over/undervalued myth-busts).
2. **Script** → `short-form-scripting` + `viral-short-storytelling` (hook → beats → one CTA).
3. **Voice** → `expressive-voiceover` (Chatterbox, per-sentence inflection) → writes
   `public/<ep>_*.wav` + `<ep>_captions.json`.
4. **Build** the episode file (studio + custom wall + reaction + CTA), register in `Root.tsx`.
5. **Verify with stills** at key frames (`npx remotion still …`) — check each wall, host, captions,
   ticker; read them back before rendering the full clip.
6. **Render** the mp4, then commit only the reel files.

## Design conventions & rails

- Disclaimers sit **above** the ticker (`Disclaimer` at bottom:108); ticker is the very bottom.
- Long VO lines → `Karaoke max={6} reveal`; short beat lines → plain.
- Fill dry full-bleed lower-thirds with `MoneyMotif` + a `Chip` row (also reinforces the story).
- **Rails (non-negotiable):** on-screen `Source`/source line for every data claim; spoken +
  on-screen "educational, not financial advice"; label fact vs rumor; congress content is
  correlational ("not-accusation") never wrongdoing. Stamp figures with the retrieval month.
