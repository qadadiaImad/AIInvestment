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

## `halal-reels/` stays untouched

`halal-reels/` is the **other contributor's** original project and the porting source
of truth for the primitives and the WULF beat structure above. It is read-only from
this factory's perspective — nothing here modifies or deletes any file in it, and its
retirement (if any) is that contributor's call, not this plan's.
