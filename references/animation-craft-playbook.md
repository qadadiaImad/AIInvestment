# Animation Craft Playbook — AI STACK video pipeline

How professional explainer studios (best-documented: Kurzgesagt) actually make
their motion feel premium, translated into our code-based Remotion pipeline.
Compiled 2026-07-22 from a 105-agent deep-research pass (25/25 claims survived
3-vote adversarial verification). Confidence labels per section; sources at
bottom. This is the **methodology of record** for every video we ship —
`remotion/src/motion/craft.ts` implements it in code.

---

## 1. The studio pipeline (verified, first-party)

Kurzgesagt's own disclosures ("How to Make a Kurzgesagt Video in 1200 Hours",
their Skillshare courses):

1. **Research → script** (finished narration text FIRST).
2. **Storyboard the whole video scene by scene** — this is explicitly where
   visual metaphors and scene transitions are invented, not during animation.
3. **Illustration**: ~200 unique panels per 10-min video, 2–3 illustrators,
   8–12 weeks, Adobe Illustrator, artwork broken into hundreds of layers.
4. **Animation**: After Effects, 2–3 animators, 8–10 weeks. Hand-keyframed +
   graph-editor easing. Rigging with Duik (IK chains) and RubberHose limbs;
   `wiggle` expressions for ambient/secondary motion; track mattes for
   reveals; trim paths for line draws; null-object parenting for grouped moves.
5. Classical principles throughout: key poses, exaggeration, overlapping
   action / follow-through, fake 3D depth.
6. Total ≈ **1200+ hours per 10-minute video**. The premium feel is hand-tuned
   easing + overshoot/settle physics — **not** procedural automation.

**Our translation** (already partially in place):
script (`educational-video-creator` Phase 1.5) → storyboard (Phase 2) →
component/fixture design (Phase 3) → coded animation (Phase 4) → audio +
timeline rebuild (Phase 4.5) → QA (Phase 5). Narration-tied start frames MUST
derive from `AUDIO_SEGMENTS` variables, never hardcoded — visuals auto-resync
when real TTS timing replaces estimates. Our per-character rigs are the code
analog of Duik/RubberHose rigs; `craft.ts` is our graph editor.

## 2. Easing — the graph editor in code (verified)

- `interpolate()` is **linear by default** — supplying easing is mandatory for
  anything spatial. Never linear for movement.
- `Easing.bezier(x1,y1,x2,y2)` is exactly CSS cubic-bezier — hand-tuned curves
  from motion practice transplant verbatim.
- Since Remotion 4.0.462, `interpolate()` takes an **array of easings, one per
  segment** — the per-keyframe easing of the AE graph editor.
- `spring()` (defaults damping 10 / stiffness 100 / mass 1) is the code analog
  of overshoot-and-settle keyframing; feed it into `interpolate()` to remap.
  Lower damping = bouncier; higher stiffness = faster; mass = weight.
- Careful: `extrapolate: 'clamp'` clips overshoot — clamp inputs, not outputs,
  when a curve intentionally exceeds 1.

**House curves** (in `craft.ts`):
| Name | Curve | Use |
|---|---|---|
| `EASE.enter` | bezier(0.05, 0.7, 0.1, 1) — MD3 Emphasized | everything entering |
| `EASE.exit` | bezier(0.3, 0, 1, 1) — MD3 Accelerate | everything leaving |
| `EASE.settleBack` | bezier(0.175, 0.885, 0.32, 1.275) — easeOutBack | bounce-settle without spring |
| `EASE.cruise` | bezier(0.4, 0, 0.2, 1) | camera moves, long drifts |
| `SPRINGS.pop` | d12 s170 m0.6 | UI chips, cards |
| `SPRINGS.hero` | d10 s130 m0.7 | big numbers, hero elements |
| `SPRINGS.heavy` | d14 s90 m1.1 | large slabs, charts |
| `SPRINGS.snappy` | d16 s220 m0.5 | captions, small labels |

## 3. Timing — frames per beat at 30fps (verified guidance, UI-derived)

| Element | Duration | Frames |
|---|---|---|
| Micro feedback (tooltip-ish) | 80–120ms | 2–4f |
| Card / chip enter | 200–350ms | 6–10f |
| Modal-weight element | 300–400ms | 9–12f |
| Scene/section transition | 400–600ms | 12–18f |
| Dramatic reveal | 600–1200ms | 18–36f |
| Fade-in beat | — | 20f |
| Number counter | — | 60f |
| Highlight reveal | — | 15f |

- **Exits run at 65–75% of entrance duration** (entrances ~30–50% longer).
- **Stagger**: micro 20–40ms (1f), standard 50–100ms (2–3f), dramatic
  100–200ms (3–6f), wave 30–60ms (1–2f). **Total stagger < 500ms (15f)** no
  matter how many elements — scale per-item delay down as count grows.
- **Overshoot by personality**: playful 10–20%, energetic 15–30%,
  premium/serious 0% (clamped). Our house style: playful characters (10–15%),
  near-zero on data (bars/numbers land confidently, no wobble on facts).
- Caveat: these bands are prescriptive practitioner guidance (LottieFiles /
  Resemble, corroborated by Material 3) written for UI motion; for
  narration-paced video, beats stretch to voiceover cadence — the bands govern
  the *transitions*, the voiceover governs the *holds*.

## 4. The anticipation → action → settle grammar (verified recipe)

Every deliberate action reads as three phases (AE keyframe practice → code):
1. **Anticipation**: small counter-move (~scale 0.97 or 4–8px opposite), ~2f.
2. **Action**: fast primary move with `EASE.enter` or a spring, may overshoot.
3. **Settle**: spring tail or `EASE.settleBack`, ~6f.
Plain `spring()` gives overshoot+settle but NOT anticipation — pre-key it
(negative segment first). `craft.ts` ships `anticipatePop()` implementing all
three phases.

## 5. Polish layers (practitioner-standard; research pass had no surviving
claims here — treat as our own craft standard, validated visually)

- **Secondary motion / follow-through**: appendages (Chip's antenna, Cap's
  flag, Cloudy's dangling boots) lag the body by 2–4f and keep moving after
  the body stops (code: drive from the body's velocity with a delayed copy —
  `followThrough()` helper).
- **Ambient life ("wiggle")**: layered incommensurate sines (our
  FloatingBlob/OrbitDots idiom) on everything — nothing is ever static, but
  amplitude stays ≤ 4px on content, more on background.
- **Smears**: at high per-frame velocity (> ~20px/f), stretch along motion
  vector (scaleX up to 1.6, 1–2 frames only) — `smearScale()` helper.
- **Camera**: scenes get ONE camera intention max — slow push-in (2–4% scale
  over the scene) as default "life", fast push-in (8–12% over 5f) as emphasis
  hit. Parallax: background layers move at 0.3×, midground 0.6×, foreground
  1× of camera delta (fake 3D depth, the Kurzgesagt way).
- **Transitions between scenes**: prefer *object-carried* transitions (an
  element wipes/carries into the next scene, invented at storyboard time) over
  crossfades; track-matte-style reveals (clip-path in code) for panels.
- **Texture/grain**: one subtle film-grain overlay (SVG feTurbulence, ~3–4%
  opacity, animated seed every 2f) + vignette. Kills the "flat CSS" look.
- **Light**: one warm radial key glow behind the subject; rim-light accent on
  hero elements (we already do glow shadows on bars).

## 6. QA bar (what "professional" means for us, checkable)

Every shipped scene must pass:
1. No linear easing on any spatial move.
2. Every entrance has settle; every exit accelerates; exits ≤ 0.75× entrance.
3. Staggered builds: ≤15f total stagger, items spring in, never simultaneous.
4. At least one ambient-life layer + grain + vignette present.
5. One camera intention per scene, parallax on ≥2 depth layers.
6. Characters: blink cycle, idle bob, and ≥1 secondary-motion appendage live.
7. Narration-synced starts derive from AUDIO_SEGMENTS (when audio exists).
8. Nothing static for >45f anywhere in frame.

## Sources

- Kurzgesagt, "How to Make a Kurzgesagt Video in 1200 Hours" (Feb 2020,
  YouTube uFk0mgljtns) — pipeline, panel counts, hours (first-party).
- Skillshare "Motion Graphics with Kurzgesagt" Parts 1–3 (Kurzgesagt-authored)
  — AE toolchain: graph editor, track mattes, trim paths, Duik, RubberHose,
  wiggle, key poses, fake 3D depth, overlapping action.
- remotion.dev/docs/easing, /interpolate, /spring + remotion@4.0.496 source —
  easing/spring semantics (verified at source level).
- LottieFiles motion-design-skill, Resemble AI remotion skill, Material 3
  motion tokens — numeric duration/stagger/overshoot bands (prescriptive).
- skindhu educational-video-creator SKILL.md — AUDIO_SEGMENTS-derived timing.
- Caveats: Kurzgesagt figures are 2020 self-reports; no verified claims
  surfaced for Infographics Show / TED-Ed / Vox / Johnny Harris pipelines;
  §5 topics had no surviving research claims and are practitioner-standard.
