# Reel Factory — unified `SlideStoryReel`

One parameterized Remotion composition that replaces the old one-`.tsx`-per-ticker
pattern with a schema-driven pipe: **live data → props JSON → render**.

```
web/public/data/halal.json                       (live verdicts bundle)
        │
        ▼
scripts/build_reel_props.py --auto --out ...json  (pure build_props(); zod-shaped output)
        │
        ▼
remotion/src/fixtures/generated.json              (SlideStoryReel props)
        │
        ▼
npx remotion render SlideStoryReel out.mp4 --props=generated.json
```

Studio quick-action `render-slide-reel` (Studio tab → Quick actions) types this whole
pipe into the terminal in one shot — review it, then press Enter to run:

```
python scripts/build_reel_props.py --auto --out remotion/src/fixtures/generated.json
cd remotion
npx remotion render SlideStoryReel ../higgs/reel_slide_latest.mp4 --props=src/fixtures/generated.json
```

`--auto` ranks the next story-worthy ticker via `aiinvest.halal_stories.pick_stories`;
pass a ticker positionally (`build_reel_props.py WULF --out ...`) to target one directly.
The builder aborts with exit 2 and a named reason rather than emit a half-empty props
file when a verdict has no decisive ratio test or business-revenue split to visualize.

## What's in `remotion/src/`

- `slides/theme.ts`, `slides/ui.tsx` — ported animation/typography primitives (colors,
  `Slam`/`Kicker`/`Caption`/`Stamp`/`Head`/`Foot`, easing helpers).
- `slides/slideProps.ts` — the zod schema (`slideStoryPropsSchema`) that is the single
  contract between the props builder, the fixtures, and the composition. Five beat
  kinds: `hook`, `bars`, `donut`, `stamp`, `endcard`.
- `compositions/SlideStoryReel.tsx` — the composition itself. Persistent header chip
  (ticker/sub/badge) and footer disclaimer span the whole reel; beats play back-to-back
  in a `<Series>`; an optional bubble layer (`components/BubbleFrame.tsx`) renders a
  `<Series>` of **distinct, non-looping** talking clips when `bubbleClips` is non-empty
  (spec §0-bis) — empty array (the default) is the VO-less slide mode used today.
- `fixtures/wulf_slides.json` — the WULF story hand-transcribed as props, the parity
  target for `npx remotion render` comparisons.
- `fixtures/wulf_slides_bubble.json` — same story with two placeholder bubble clips,
  proving the full-span `<Series>` mechanism ahead of Phase 2b's real talking clips.

## Parity story

Visual target: `higgs/reel_wulf_2026-07-21.mp4` (owner-validated look), reference
frames `higgs/wulf_f1.png` / `higgs/wulf_f2.png`. `SlideStoryReel` reproduces
`halal-reels/src/WulfReel.tsx`'s beat structure and visual vocabulary from *props*
instead of from one hardcoded component per ticker — see the beat-kind → WulfReel-section
mapping documented at the top of `compositions/SlideStoryReel.tsx`. Full design
rationale, the §0-bis bubble contract, and the copy rails live in
[`docs/superpowers/specs/2026-07-21-remotion-reel-factory-design.md`](../docs/superpowers/specs/2026-07-21-remotion-reel-factory-design.md).

## Phase 2b (not in this pass — gated on the voice slot)

Zero Higgsfield spend so far: no set anchors, no voice clone, no real talking clips.
The schema already carries the dormant fields Phase 2b needs (`vo`: one narration line
per beat, `captions`: whisper-timed caption spans, `bubbleClips`: real Karim clips) so
wiring them in later is additive, not a breaking schema change.

## Daily line — `daily_post.py`

One command, one ticker, one day's post — the full halal-screen content pipeline
end to end, built on top of the props → render pipe above:

```
cd scripts
PYTHONIOENCODING=utf-8 python daily_post.py --auto
```

**What it produces.** A finished folder at `higgs/daily/YYYY-MM-DD_TICKER/`
(gitignored — see the `higgs/daily/` / `data/halal_history/` /
`remotion/public/daily/` entries in `.gitignore`) containing:

```
daily_A.mp4, daily_B.mp4        two SlideStoryReel renders — the same story,
                                 two different hooks (A/B test)
v4_<tk>_1_hook.png,              a 3-slide carousel kit built by
v4_<tk>_2_data.png,               higgs/_build_v4.py (skipped, without
v4_<tk>_3_takeaway.png            failing the run, if that step errors —
                                   see manifest.json's carousel_note)
caption.txt                      the post caption + hashtags
manifest.json                    ticker, reason, score, story, generated_at,
                                  inputs_asof, lint_ok, seeds, files,
                                  posting_instructions, carousel_note?
props_A.json, props_B.json       the whisper-timed SlideStoryReel props behind
                                  each MP4 (voiceSrc, captions, beat durations)
```

**The folder contract.** Everything above lands together, atomically — the
pipeline builds in a temp dir and moves it into `higgs/daily/<folder>/` as its
last effectful step, so a failure anywhere in steps 1-8 never strands a
partial, manifest-less folder in `higgs/daily/`. `manifest.json` is always the
source of truth for *why* that ticker was picked and what's inside.

**Posting instructions** (also echoed in `manifest.json`'s
`posting_instructions`): **B = Trial Reel first** (test the alternate hook
with less downside), **A = main slot** (the primary hook, once B's numbers
look fine).

**Flags:**

| Flag | Effect |
|---|---|
| `--auto` | picks the top-ranked candidate, no interactive prompt |
| `--ticker X` | forces a specific symbol, bypassing ranking/prompt |
| `--dry-run` | stops after building copy; prints both VO scripts + the caption; exits 0 — no GPU, no browser, no render touched |
| `--skip-refresh` | skips the `pull_halal.py`/`export_halal.py` freshness refresh even if `halal.json` is stale |
| `--skip-carousel` | skips the carousel PNG build step |

Full step-by-step (freshness → history → candidates → copy → voice → align →
render → carousel → finalize) is documented in `scripts/daily_post.py`'s
module docstring — that's the single source of truth for the pipeline
internals; this section is the operator-facing summary.

**Studio note.** `higgs/daily/<folder>/` is not yet picked up by Studio's
gallery indexer (`studio/src/main/api.ts`'s `posts:list` handler does a
non-recursive `readdirSync(HIGGS)`, and `buildIndex` in
`studio/src/main/indexer.ts` only recognizes top-level `higgs/` filenames
matching `reel_<ticker>_<date>.mp4` / `v4_<ticker>_<n>_<kind>.png` /
`reels_<date>.txt` — it never descends into `higgs/daily/`). Until the
indexer is extended to walk `higgs/daily/<folder>/`, review daily-post output
directly in the folder rather than through the Studio app.

## `halal-reels/` stays untouched

`halal-reels/` is the **other contributor's** original project and the porting source
of truth for the primitives and the WULF beat structure above. It is read-only from
this factory's perspective — nothing here modifies or deletes any file in it, and its
retirement (if any) is that contributor's call, not this plan's.
