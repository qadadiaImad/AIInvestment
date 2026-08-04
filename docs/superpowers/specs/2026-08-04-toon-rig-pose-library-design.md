# Toon Character Rig + Pose Library — Design

**Date:** 2026-08-04
**Status:** approved (design), pending spec review
**Context:** Inspired by the Cyanide & Happiness "Quarterly Report" reel format. We want
a way to produce "as many granular character poses/descriptions as required for animation."
The mechanical option — vectorizing the reel's frames (potrace) — is rejected: (a) it copies
C&H's copyrighted characters, and (b) traced frames are disconnected, non-riggable blobs, the
opposite of what animation needs. Instead we build our OWN posable rig in that flat style.

## Goal

A **parametric SVG character rig** plus a **generated, validated pose/expression library** for
our own flat-2D mascot, feeding Remotion animation. Unlimited granular poses, 100% frame-to-frame
consistency (vector = code, no AI-art drift), animation-ready.

## Decisions (from brainstorming)

1. **Posable rig + pose library** for our own mascot (not frame-tracing, not AI-vectorize).
2. **Hybrid** control: a parametric skeleton PLUS a named preset library on top.
3. **Generator + validation sheet**, skill-driven: hand-author a few hero poses, a generator
   (Sonnet subagent per model policy) fans out a larger catalog, each batch auto-renders to a
   contact sheet that is verified and culled before entering the catalog.
4. **Single character skin first**: the deadpan "analyst" (extends the existing
   `QuarterlyReport.tsx` `Guy`). The rig is skin-parametric so more characters can be added later
   without changing the rig.

## Components (isolated units, one job each)

| Unit | File | Responsibility |
|---|---|---|
| Rig | `halal-reels/src/toon/rig.tsx` | Pure `Character(params: RigParams)` → SVG. Single source of truth. |
| Types | `halal-reels/src/toon/types.ts` | `RigParams`, `PosePatch`, `Keyframe` type defs. |
| Library | `halal-reels/src/toon/poses.ts` | `POSES` (body patches) + `EXPR` (face patches), each with a `desc`. |
| Catalog | `halal-reels/src/toon/catalog.json` | Generated master list: `{id, desc, params, tags}[]`. |
| Generator | `halal-reels/src/toon/gen_catalog.py` | Fans out param combos + deterministic `desc`, dedupes; Sonnet subagent proposes expressive combos; renders contact sheet for culling. |
| Contact sheet | `halal-reels/src/toon/PoseSheet.tsx` | Remotion composition rendering a grid of catalog poses → PNG still for full-res verification. |
| Animation helper | `halal-reels/src/toon/animate.ts` | `posed(frame, keyframes)` tweens between named poses/params. |
| Merge/tween logic | `halal-reels/src/toon/merge.ts` | Pure `merge(...patches)` and `tween(a, b, t)` — unit-tested. |

### RigParams (initial shape)

```
skin:    { skinFill, outline, shirtFill }         // one preset: ANALYST
headTurn: number(deg)   lean: number(deg)   bob: number(px)
brows:   { l: 'flat'|'raise'|'furrow'|'sad', r: same }
eyes:    'open'|'blink'|'wide'|'dead'|'sideL'|'sideR'
mouth:   'flat'|'open'|'frown'|'smile'|'grimace'|'o'
sweat:   boolean
armL/armR: { shoulder: deg, elbow: deg, wrist: deg }   // noodle-limb angles (no IK solver)
prop:    'none'|'fiddle'|'paper'|'phone'|'pointer'
```

A **pose** is a `Partial<RigParams>` patch (body); an **expression** is a `Partial<RigParams>`
patch (face). Final params = `merge(skin, pose, expr)` with later patches winning.

## Data flow

`catalog entry → params → merge(skin + pose + expr) → Character() → SVG`.
Animation = keyframe list `[{frame, pose|params}]` → per-frame `posed()` merged params → rig.

## Descriptions

Each pose's `desc` is composed **deterministically from its params** (a template mapping
param values → phrases), e.g. *"deadpan analyst, seated, right arm pointing left, left arm on
desk, brows flat, mouth flat."* No hallucination. Optional Sonnet-enrichment adds flavor text
in a separate field. Descriptions are searchable metadata; **params drive rendering**.

## Validation & testing

- **TDD (Vitest, already in repo)** for pure logic: `merge()` patch precedence, `tween()`
  numeric interpolation + enum switching at thresholds, `posed()` keyframe lookup.
- **Visual gate**: every generator batch → contact sheet → cull broken limbs / unclear
  expressions BEFORE entries land in `catalog.json`. (Applies the "verify at full res, never
  thumbnails" lesson from the LoRA post-mortem.)

## Scope / YAGNI

- One skin (analyst); rig is skin-parametric for later characters.
- ~10 hand-authored hero poses → generator expands to ~40–60 validated.
- No IK solver (angle approximation fits flat noodle limbs); no GUI pose editor.
- `QuarterlyReport.tsx` refactors to consume the rig once it exists (proves reuse).

## Payoff

Unlimited granular, consistent poses; every future episode = a script + a keyframe list of pose
names. The animation foundation the AI-art path could not provide.

## Milestones

1. Types + rig (analyst skin, all params render) + a PoseSheet composition.
2. `merge`/`tween`/`posed` pure logic with Vitest tests (TDD).
3. ~10 hand-authored hero poses + expressions in `poses.ts`; contact sheet verified.
4. Generator (Sonnet subagent) → ~40–60 catalog entries; contact-sheet cull → `catalog.json`.
5. Refactor `QuarterlyReport` to consume the rig; re-render to confirm parity.
