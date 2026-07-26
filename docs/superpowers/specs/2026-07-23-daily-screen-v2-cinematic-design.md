# The Daily Screen v2 — cinematic upgrade (design)

**Date:** 2026-07-23 · **Status:** approved by owner
**Goal:** make the daily reel land harder — a photographic hero spine, a shocking
factual intro built from the real leverage number, a dedicated company-explainer
carousel slide, all built into the pipeline for every ticker and showcased on WKEY.

Owner decisions (2026-07-23): (1) hero images = **sector-theme library generated once**,
reused per ticker by its `layer`; (2) drama = **factual-extreme** — shock from the real
number, no buy/sell, trust rails intact; (3) company definition = **dedicated carousel
slide + spoken reel intro**.

## Components

### 1. Hero library (8 images, one-time)
- One hero per `layer` value in `web/public/data/halal.json` (8 values today: L0-energy,
  L1-chips, L2-infra, L4-application, Q1-hardware, Q3-software, Q5-applications,
  **Q4-security**). Q3/Q5 may share a "quantum-compute" hero → ≥7 distinct images.
- Generated via Higgsfield (owner picks 1 of 2 style directions **before** any credit
  spend — two-suggestions rule). Native 9:16 (1080×1920) so the reel uses them full-bleed;
  the 4:5 carousel uses `object-fit: cover`.
- Stored committed as brand assets: `remotion/public/heroes/<layer>.jpg` (reusable, needed
  for reproducible renders — NOT per-run media). A `data/heroes/manifest.json` records
  prompt + style + generated_at per hero (provenance).
- Resolver `hero_for_layer(layer) -> "heroes/<layer>.jpg" | default` (pure, in a new
  `scripts/aiinvest/heroes.py`); unknown/None layer → `heroes/_default.jpg`.
- **Placeholder-first:** ship solid-color placeholder JP0s at those paths so code/tests/
  renders work before generation; real images overwrite in place, no code change.

### 2. Reel hero layer (Remotion)
- `slideProps.ts`: add `heroSrc: z.string().optional()`.
- `SlideStoryReel.tsx`: new `HeroLayer` behind the beat content. Full-bleed on the FIRST
  (hook) beat with a dark bottom-to-top scrim (text stays legible); from the second beat
  on it recedes to a dimmed (opacity ~0.14), slightly blurred backdrop so charts read.
  Ken-Burns-style slow scale (1.0→1.06) for life. When `heroSrc` absent → current look,
  no regression.

### 3. Shocking factual intro + dramatize (daily_copy)
- New `dramatize(card) -> str`: from the binding ratio build a factual-extreme line scaled
  by severity multiple `ratio/threshold`:
  - ≥3× → "It owes {mult}× what the whole company is worth — the screen's ceiling is
    {threshold}. It isn't close."
  - 1–3× over → "Its {label} sits at {ratio} — past the {threshold} line."
  - pass → "Every debt line comes in under the limit."
  All money/limit-anchored (passes `lint_visceral`); NO buy/sell.
- Hook VO[0] rewrite: `{TICKER} — {company_descriptor}. But here's the shock: {dramatize}`.
  Removes the double-ticker seam. Hook beat `sub` = the descriptor; a new shock sub-line
  shows the dramatize text on the hero.
- `lint_editorial(lines) -> list[str]`: flags banned judgment words
  (dangerous, danger, trap, too much, overvalued, avoid, risky, terrible, crash, plummet,
  soar, guaranteed) so factual-extreme copy can't drift into advice. Wired as a hard gate
  in `build_daily` alongside the existing lints.

### 4. Company-definition carousel slide
- Carousel 3→4 slides: **define → hook → data → takeaway**. The define slide = big ticker +
  exchange, the plain-words descriptor, one leverage teaser line, hero image as background
  with scrim. Reuses `_build_v4.py`'s existing `hero_map` slot (already a parameter).
- New kit field `company_def` (via `kit_md.parse_cfg`); `daily_copy.kit_fields` emits it.
- `daily_post` carousel step passes the layer hero into `hero_map` for the ticker.

### 5. Build method
Spec → plan → subagent-driven dev for §1–4 (placeholder heroes, TDD). Then a **Workflow**
fan-out generates + quality-checks the ≥7 heroes in parallel (after owner style pick).
Finally regenerate WKEY (`--ticker WKEY`) as the showcase and verify stills.

## Rails (unchanged, enforced)
Screen phrasing only; non-fatwa footer; spoken disclaimer; never name the data vendor;
"a read, not a call"; no signals/returns. NEW: `lint_editorial` bans judgment words.
All build subagents on Sonnet. Media gitignored; hero library + code committable.

## Out of scope
Per-ticker unique heroes, video heroes, 16:9, auto-posting, French. Hero regeneration when
a new layer appears is a manual re-run of the generation workflow.
