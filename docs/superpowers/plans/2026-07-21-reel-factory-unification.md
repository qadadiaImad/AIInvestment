# Reel Factory Unification — Implementation Plan (Phase 2a, zero-credit)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One parameterized `SlideStoryReel` in `remotion/` that reproduces the other contributor's WULF visual language from props (parity-provable against `higgs/reel_wulf_2026-07-21.mp4`), fed by live `halal.json` via a props-builder script, with an optional non-looping full-span talking-bubble layer and a Studio quick-action — **zero Higgsfield spend** (set anchors/voice/talking clips are Phase 2b, gated on the voice slot).

**Architecture:** Port `halal-reels/src/{theme.ts,ui.tsx}` primitives into `remotion/`, parameterize the `WulfReel.tsx` beat structure into one schema-driven composition, replace the manual `cp halal.json` ritual with `scripts/build_reel_props.py`, extend the bubble to a `<Series>` of non-looping clips per the amended spec §0-bis. `halal-reels/` itself stays **untouched** (the other contributor's project; retirement is their call).

**Tech Stack:** Remotion 4.x (`remotion/`), React + TS + zod, Tailwind v4 IF `ui.tsx` requires it (see T1), Python (props builder, pytest).

## Global Constraints

- **Zero Higgsfield generation** in this plan.
- `halal-reels/` is read-only reference — no file in it may be modified or deleted.
- Visual parity target: `higgs/reel_wulf_2026-07-21.mp4` (owner-validated look). Reference frames: `higgs/wulf_f1.png`, `higgs/wulf_f2.png`.
- Spec: `docs/superpowers/specs/2026-07-21-remotion-reel-factory-design.md` incl. §0-bis bubble contract (full-span, NO loops, one clip per beat).
- Copy rails: methodology framing, never "haram" as accusation head, disclaimer footer `Computed methodology result — not a fatwa · not financial advice` (match the WULF footer text exactly).
- Verify per task: `cd remotion; npx tsc --noEmit` (+ per-task specifics). Python: `cd scripts; python -m pytest -q`.
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`. Branch `feat/multi-sector-research-platform`, no push until final task.

---

### Task 1: Port `theme.ts` + `ui.tsx` primitives into `remotion/`

**Files:**
- Create: `remotion/src/slides/theme.ts`, `remotion/src/slides/ui.tsx` (ported copies, imports adjusted)
- Possibly modify: `remotion/remotion.config.ts` + `package.json` (ONLY if ui.tsx uses Tailwind classes — then mirror `halal-reels/remotion.config.ts`'s Tailwind v4 webpack override and install the same deps; if the primitives are inline-style only, no config change).

**Steps:** read `halal-reels/src/theme.ts` and `halal-reels/src/ui.tsx` fully; copy into `remotion/src/slides/` adjusting relative imports; decide the Tailwind question from evidence (grep `className=` usage in ui.tsx) and document the decision in the commit body; `npx tsc --noEmit` clean; commit `feat(reels): port slide theme + animation primitives from halal-reels (verbatim, imports adjusted)`.

---

### Task 2: `SlideStoryReel` — parameterized WULF beat structure

**Files:**
- Create: `remotion/src/slides/slideProps.ts`, `remotion/src/compositions/SlideStoryReel.tsx`, `remotion/src/fixtures/wulf_slides.json`
- Modify: `remotion/src/Root.tsx` (register `SlideStoryReel`)

**Interfaces (produces — T3/T4/T6 consume):**

```ts
// slideProps.ts
import {z} from 'zod';
export const beatSchema = z.discriminatedUnion('kind', [
  z.object({kind: z.literal('hook'), headline: z.string(), sub: z.string(),
            accentWord: z.string().optional(), durationInFrames: z.number()}),
  z.object({kind: z.literal('donut'), title: z.string(), pct: z.number(),
            centerLabel: z.string(), caption: z.string(),
            tone: z.enum(['pass', 'fail', 'warn']), durationInFrames: z.number()}),
  z.object({kind: z.literal('bars'), title: z.string(), caption: z.string().optional(),
            bars: z.array(z.object({label: z.string(), ratio: z.number().nullable(),
              threshold: z.number(), status: z.enum(['pass', 'fail', 'unknown'])})),
            durationInFrames: z.number()}),
  z.object({kind: z.literal('stamp'), verdict: z.enum(['halal', 'not_halal', 'questionable', 'insufficient_data']),
            basis: z.string(), line: z.string(), durationInFrames: z.number()}),
  z.object({kind: z.literal('endcard'), headline: z.string(), sub: z.string(),
            durationInFrames: z.number()}),
]);
export const bubbleClipSchema = z.object({src: z.string(), durationInFrames: z.number()});
export const slideStoryPropsSchema = z.object({
  ticker: z.string(), tickerSub: z.string(), badge: z.string(),
  beats: z.array(beatSchema).min(2),
  vo: z.array(z.string()),               // one narration line per beat (Phase 2b consumes)
  bubbleClips: z.array(bubbleClipSchema).default([]),   // empty = friend's VO-less slide mode
  captions: z.array(z.object({text: z.string(), fromMs: z.number(), toMs: z.number()})).default([]),
  disclaimer: z.string(),
});
export type SlideStoryProps = z.infer<typeof slideStoryPropsSchema>;
```

- Composition duration = sum of `beats[].durationInFrames`; each beat renders via the ported primitives with a **beat-kind → WulfReel-section mapping** the implementer derives by reading `halal-reels/src/WulfReel.tsx` (150 lines): header chip = ticker/tickerSub/badge persistent (WULF frames show it top-anchored all reel), `hook` = the Slam headline section, `donut` = the animated arc (WULF "38.2% BITCOIN MINING"), `bars` = threshold bars (reuse/port of the section GevReel/EtnReel use), `stamp` = verdict Stamp, `endcard` = EndCard primitive. Footer disclaimer persistent.
- Fixture `wulf_slides.json`: rebuild the WULF story as props — values from `halal-reels/src/data.ts` `WULF` constant (read it) with the beats/copy transcribed from the actual reel (hook: "This stock earns **bitcoin** money." / sub "Muslim investors run a halal screen — a math test for stocks. Watch it work."; donut: 38.2% BITCOIN MINING, caption "38% of its income is still bitcoin mining — that slice is flagged impermissible."; then the remaining beats per WulfReel.tsx source). `bubbleClips: []`.
- Verify: `npx tsc --noEmit`; `npx remotion compositions src/index.ts` lists `SlideStoryReel` with duration = fixture beat sum. Commit.

---

### Task 3: Live-data props builder — `scripts/build_reel_props.py`

**Files:**
- Create: `scripts/build_reel_props.py`, `scripts/tests/test_build_reel_props.py`

**Interfaces:** `build_props(ticker, halal_bundle, story=None) -> dict` (pure) matching `slideStoryPropsSchema` field-for-field; CLI `python build_reel_props.py WULF --out ../remotion/src/fixtures/generated_wulf.json` reading `web/public/data/halal.json` (+ `aiinvest.halal_stories` for ranking hooks when `--auto` picks the ticker). VO lines generated per beat from templates obeying the copy rails. Aborts (exit 2, named reason) when the verdict lacks the decisive data for a story — never emits a half-empty props file.

**Steps (TDD):** failing tests first — WULF-shaped bundle fixture → props with 5 beats, hook copy contains no "haram"-as-accusation, durations sum >0, `vo` length == beats length, insufficient-data bundle → SystemExit(2). Implement; suite green; commit.

---

### Task 4: Non-looping full-span bubble

**Files:**
- Modify: `remotion/src/compositions/SlideStoryReel.tsx` (render bubble layer when `bubbleClips` non-empty: `<Series>` of `<OffthreadVideo>` in the 30% rounded frame — NO `<Loop>`), `remotion/src/components/BubbleFrame.tsx` (accept `clips: {src, durationInFrames}[]`; keep old single-src signature working for `HalalVerdictReel` or update that call site too — implementer's choice, documented)
- Modify: `remotion/src/fixtures/ddog.json`-consuming `HalalVerdictReel` only if the shared component signature changes (keep it compiling).

**Steps:** implement; add a second fixture `wulf_slides_bubble.json` = same as `wulf_slides.json` plus `bubbleClips: [{"src": "bubble_ddog.mp4", "durationInFrames": 240}, {"src": "bubble_ddog.mp4", "durationInFrames": 240}]` (the placeholder clip stands in until Phase 2b Karim clips exist — played twice as two DISTINCT Series entries, not a loop, proving the mechanism); `npx tsc --noEmit`; compositions list ok; commit.

---

### Task 5: Studio quick-action + docs

**Files:**
- Modify: `studio/src/main/api.ts` (quick-command table: add `'render-slide-reel': 'python scripts/build_reel_props.py --auto --out remotion/src/fixtures/generated.json; cd remotion; npx remotion render SlideStoryReel ../higgs/reel_slide_latest.mp4 --props=src/fixtures/generated.json'`), `studio/src/renderer/src/components/QuickActions.tsx` (button entry, matching existing pattern — it types, never executes)
- Create: `remotion/README_FACTORY.md` — one page: the unified pipe (props builder → render → Phase 2b voice/bubble), the parity story, pointer to the spec, and an explicit note that `halal-reels/` is the original reference implementation kept intact.

**Steps:** read the existing quickCmd/QuickActions patterns first; implement; `cd studio; npx tsc --noEmit` (or the studio's own typecheck script); commit.

---

### Task 6: Parity render + owner review artifact

**Steps:**
1. `cd remotion; npx remotion render SlideStoryReel ../higgs/preview_wulf_unified.mp4 --props=src/fixtures/wulf_slides.json` (VO-less slide mode — the friend's format).
2. Extract frames at the hook and donut beats (`ffmpeg -ss` per beat timing) and compare **side-by-side against `higgs/wulf_f1.png` / `wulf_f2.png`** — the reviewer must judge: same header chip layout, same Fraunces hook scale, same donut treatment, same footer. Deviations listed, not hidden.
3. Render the bubble variant: `--props=src/fixtures/wulf_slides_bubble.json` → `../higgs/preview_wulf_unified_bubble.mp4` (proves full-span Series bubble).
4. Do NOT commit MP4s/frames (media gitignored). Final commit of any source fixes; **push the branch**.

---

## Self-Review

1. **Spec coverage:** §0-bis full-span no-loop bubble → T4; one parameterized composition replacing per-ticker files → T2; live-data feed replacing cp ritual → T3; studio integration → T5; parity vs owner-liked WULF → T2 fixture + T6; zero-credit → all; friend's project untouched → global constraint + T5 README note. Phase 2b (Karim set anchors, voice clone, real talking clips, whisper timings) deliberately out — gated on the voice slot.
2. **Placeholders:** T2's beat→section mapping directs the implementer to derive from `WulfReel.tsx` (in-tree, 150 lines) rather than reproducing the friend's code in the plan — deliberate: the source of truth is the code being ported, and parity is enforced by T6's frame comparison. All NEW interfaces (schemas, CLI, quick-action string) are spelled out.
3. **Type consistency:** `slideStoryPropsSchema` (T2) ⇄ `build_props` output (T3) ⇄ fixtures (T2/T4) ⇄ render commands (T5/T6); `bubbleClips` default `[]` keeps VO-less mode; `vo`/`captions` fields dormant until Phase 2b — schema-stable so no breaking change later.
