# Enhancement plan — hybrid infographic explainer with characters

Written 2026-08-04 after a 13-agent study (Kurzgesagt narration + animation
craft, from the local `educational-video-creator` style library and web
research), a 4-agent audit of the current episode, a synthesis pass and an
adversarial critic. Target: `FairMarketEp1`, currently v16, 60.0s.

**Brief (owner):** "it should be an infographic explainer but with character
speaking — a mix of both would be amazing", after "transitions and images are
not fluid and catchy".

---

## 0. The measured problem

From `scripts/vector/pacing_audit.py` against the current cut:

| | ours | reference |
|---|---|---|
| shots | **36 in 60s — a cut every 1.67s** | scenes held 3–8s |
| holds over 3s | 1 (the outro) | that is the ceiling, not the target |
| cuts | 35, **all instantaneous** | 0.3–1.0s transition per segment change |
| runtime in transition | **0%** | a meaningful fraction |

We are not too slow. We cut **faster** than the reference and connect nothing
across the cuts. Fast cutting + zero continuity = staccato. Every fix so far
(visemes, blinks, breathing, entrances) improved a *frame*; the defect is
*between* frames.

### The critic's central finding — the reason this plan was restructured

> "No deliverable actually reduces cut COUNT or increases average shot hold.
> Every one of the 8 ranked changes either softens an individual cut, adds
> content within an existing cut window, or adds decoration... Polishing 36
> cuts individually can still read as frantic even if each one is smoother."

That is correct and it invalidated the original ranking. **Softening 36 cuts is
not the same as having fewer cuts.** Cut-count reduction is now Tier 0.

---

## 1. What is actually wrong (verified against current HEAD)

Confirmed by reading the code, not inherited from the stale audit:

1. `moves:` and `turns:` appear on **3 of ~15** beat-to-beat cuts. The other
   ~80% are a bare 3-frame opacity fade. `interact.ts`'s own header names this
   exact failure and ships the fix — it is simply not wired up.
2. `toon.ts`'s `holdCurve()` and `squash()` are **never imported** by this
   composition, so held shots have no secondary-move life beyond breathing.
   (They are already used by `poseCut.tsx` / `AnaVectorPilot.tsx` — port, don't
   invent.)
3. `FlashCut` fires **unconditionally** on every beat's frame 0, so the flash
   that should sell "WHAT?!" is identical to the one on a flat aside.
4. `Room`'s dark mode is a **hard ternary hex swap** under a softly-fading
   overlay — the room snaps while the overlay implies a slow squeeze.
5. The monitor is conditionally rendered, so it is **absent from the room for
   the first 13.3s** and pops in and out at beat boundaries instead of being
   furniture.
6. Narration: "fair" — the cold-open thesis — is spoken **once** and never
   called back; the episode closes on a different question than it opened with.
   And no line ever addresses the viewer, despite the format calling for it.

---

## 2. The plan

### Tier 0 — reduce the cut count (the actual fix)

**T0.1 Collapse ~10 of ~15 beat boundaries into continuous camera moves.**
Hard cuts survive only at true structural boundaries: cold open, the reveal at
beat 400, the two act breaks, the closer pop-in — 5–6 total, each then *earning*
FlashCut/impact treatment because it is rare.
*Acceptance:* re-run `pacing_audit.py`; target **≤22 shots**, average hold
**≥2.4s**, **≥30%** of runtime in continuous camera motion. Numbers, not vibes
(house rule §10.7).

**T0.2 Infographic elements as connective tissue across a cut.** A counter, a
bar or a timeline tick starts animating *before* a character cut and continues
*through* it, so the eye has continuity even while the character art snaps.
Critic's point: this is the single most direct lever against choppy cuts and it
**touches no coordinate system at all**. Cheapest real win in the plan.

### Tier 1 — cheap, proven, do first (current geometry, no rebuild)

**T1.1 Complete the move/turn/kEnd coverage — but differentiated per
character.** Not a uniform data fill: Sol is a veteran and economical (slower
settle, undershoots the recoil); Rex is eager and jumpy (overshoots). A
two-hander's characters need distinct *physical* vocabularies, not just distinct
lines. Files: `FairMarketEp1.tsx` BEATS data only.

**T1.2 Import `holdCurve()` + `squash()`** into held shots. Named in the
diagnosis, dropped from the original plan; it is the cheapest
Kurzgesagt-aligned fix available and the pattern is already proven elsewhere in
this repo.

**T1.3 Gate `FlashCut`** on `cur.energy >= 1.2 || !!cur.shout` — reuse the
boolean already computed for SpeedLines/ShockRing. One conditional.

**T1.4 Sound on every remaining cut**, with 2–3 frame offsets where a reveal,
a camera move and an FX would otherwise land on the same frame, so the eye gets
a read order.

**→ OWNER CHECKPOINT.** Render and compare. The critic's sequencing fix: decide
here whether the cheap tier closed enough of the gap that the L-effort rebuild
is unnecessary. Do not authorise Tier 2 blind.

### Tier 2 — the format pivot

**T2.1 Lock the script first** (before any word-synced timing is built against
it): close the "fair" thesis loop in the closer, and add one direct-to-camera
line. Regenerate VO + mouth tracks for the touched clips only. Doing this late
would force rebuilding every graphic cue timed to the audio.

**T2.2 Pilot the infographic layer in the EXISTING flat frame.** Critic's
decoupling: this tests the real risk — do Sol and Rex become mascots? —
*independently* of camera geometry. Build a timeline rail (Jul 2022 → Feb 2023),
a bar-growth (25,000 shares / $341K) and a counter (45 days) as code-drawn
SVG/CSS in `motion/Infographic/`, reusing `craft.ts`'s springs/frames/stagger
(built, currently unused). Derive every start frame from the VO segment
boundary, stagger siblings ~5f, cap at 2–3 animating elements. Pilot on beat 400
only, get approval, then roll out.

**T2.3 World-space + virtual camera — scoped as a 2–3 beat proof, not the
backbone.** Downgraded from "rank 1 / transformative" on the critic's argument:
a camera move over one flat painted room reads as a pan over a photograph, not a
push into a scene — it needs **parallax/depth layering** (wall, mid, character,
foreground moving at different rates) or it is not worth the coordinate-system
rewrite. Unresolved technical collision to settle first: `kind:"closeup"` scales
to cover *the viewport* (`1.04 * max(W/d.w, H/d.h)`), a formula anchored to the
frame — undefined once "the frame" is a moving camera window, and that governs
the highest-impact reaction shots. Explicit go/no-go render before rollout.

### Tier 3 — after camera and graphics are stable

**T3.1** Interpolate the dark-mode grade (0..1 `darkT`, 12–16f ramp) instead of
a hex swap.
**T3.2** Speaking/listening focus differential — **only with a reaction-beat
exception.** Critic killed the blanket version: dimming the listener during
Sol's long expository beats mutes Rex exactly when his reaction *is* the comedy.
Skip the dim whenever the listener has a reaction cue that beat.
**T3.3** Make the monitor permanent furniture in the room.

---

## 3. Explicitly not doing

- **Not installing `@remotion/transitions`.** Its fade/slide/wipe model assumes
  discrete scenes to transition *between*, which stops being the right model
  once most of the piece is continuous; and crossfading flat cel-shaded
  character art produces a double-exposure ghost. Our own
  `smear()`/`actionCurve()`/entrance-ramp vocabulary is better fitted and
  already partly proven here.
- **Not reviving intra-beat pose cycling.** Already rejected — it glitched Sol's
  haircut every 14 frames.
- **Not letting any infographic stretch run with both characters absent.** Every
  graphic sequence keeps a character in frame reacting, or gets a camera swing
  back to a reaction. This is the named failure mode of the hybrid: narrator
  with mascots pasted on.
- **Not doing a ground-up script rewrite** — targeted fixes only, or it forces a
  second full VO/mouth-track/viseme regeneration.
- **Not generating new character art in this pass** — keeping it an
  animation-engineering change means a clean before/after; new drawings would
  make it impossible to tell whether an improvement came from motion or from a
  better picture.
- **Not chasing the style library's numeric fill-ratio / rule-of-thirds /
  isolation-opacity targets as hard rules.** Over-fitting to explainer
  convention is how the piece stops sounding like Sol and Rex.

---

## 4. The honest caveat

The critic's verdict on the original plan, which Tier 0 exists to answer:

> "Executed as written, this plan would visibly raise per-cut craft... but it
> does not clearly solve the stated complaint, because nothing in the eight
> ranked items reduces cut frequency or increases shot hold time, which is the
> actual mechanism behind '36 shots/60s, 0% transition'... The plan would ship a
> smoother-looking cut reel, not necessarily a piece that stops feeling like
> one."

If Tier 0 is not delivered, the rest is polish on a structural defect.
