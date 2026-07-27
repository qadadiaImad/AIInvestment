# Build Spec — reconciled

> ## ⚠️ OWNER DECISIONS OVERRIDE THE RESEARCH
> The spec below was produced by the research workflow **before** the owner's ten
> answers came back. Where they disagree, the owner's answer is what gets built.
> Five deltas, each recorded here rather than silently applied:
>
> | # | Spec says | Owner chose | Resolution |
> |---|---|---|---|
> | 1 | Quiz window **5.0s / 150f**, fixed | **4s, character in shot** | **4s / 120f.** The spec argues window length tracks decision complexity, not runtime, and that two lanes converged on 5s — a real argument, and it is wrong here for a reason the research could not know: the character is *in shot sweating* for the whole timer, so the window is no longer dead air being endured, it is a performance beat. The 30 saved frames go to the wait beat. |
> | 2 | Ends on a **question to comments** ("Would you have waited?") | **The lesson as a rule** | Last frame is the RULE, held. The comment-bait question is cut. The spec itself calls the question "the most obvious engagement-bait" in its own alternatives; the owner picked the rule and that is the ending. |
> | 3 | Character and chart **co-present throughout** | **Cut between them** | Beats 1 and 6 cut to a monitor-filling close-up; beats 0, 3, 4, 5, 7 are the wide room shot. Never both competing for focus. See §0.2. |
> | 4 | Character grounding **not addressed** | **Lock to a measured floor plane** | Hard requirement, and the top build risk. See §0.1 — nothing gets animated until stills prove he sits in the room. |
> | 5 | Character choice flagged **open** | (not asked) | Undecorated `rubberHoseRig`, matching `MemeReel.tsx`. IBIT is not an AI-stack layer and force-fitting Chip/Watt/Cap onto a Bitcoin ETF would break the family's own logic. |
>
> Everything else in the spec stands as written.

## §0.1 Grounding — the gate before any animation

The owner's note: *"make sure caractere is homogenuous with desktop and screen so
that it does not look weird and unprofessional."* This is not a polish pass, it
is a gate.

1. Measure the monitor quad and desk edge out of the room plate
   (`scripts/meme_reel/measure_screen_quad.py` already does the monitor).
2. Derive the **floor line** and **horizon** from the desk/room perspective.
3. Place and scale the rig against that horizon: feet on the measured floor,
   eye-line consistent with the room's, one shared light direction.
4. **Render three stills at different scales and show them before animating.**

The failure this prevents is the expensive one — a character that reads as
pasted on top of a photo. It is only fixable at the placement stage, and only
visible by looking.

## §0.2 Shot plan — cutting, not co-presence

| Beat | Shot |
|---|---|
| 0 Hook | WIDE — him and the monitor, motion already happening |
| 1 Chart build | **CLOSE on the monitor** — the tape and the structure are the whole content here, and the spec already says he should be at his quietest |
| 2 Pattern | CLOSE, then cut WIDE on his notices-take |
| 3 Entry | WIDE — the decisive gesture is the beat |
| 4 Quiz | WIDE — he is in shot for the whole timer, per the owner's answer |
| 5 Wait | WIDE, slow push-in — the anxiety is the content |
| 6 Fail | **CLOSE on the reveal candle**, hard cut WIDE on the shock |
| 7 Lesson | WIDE, settling |

Cuts land on the beat boundary, never mid-gesture. The close-ups are the same
composition scaled and re-framed, not a second render.

## §0.3 Data — settled

**IBIT**, 250 real IBKR daily bars, 2025-07-28 → 2026-07-24, saved at
`data/prices/IBIT_1d_2026-07-27.json`. Zero OHLC integrity violations.
High $71.82 (2025-10-06), low $32.84 (2026-06-25) — a **-54% drawdown**.

That year-long bear market is why the failure beat can be honest: a bullish
setup that loses is the *common* case in this window, so the scanner will find
a real one rather than needing a manufactured outcome. Spot BTC is unavailable
(not on the brokerage feed; the egress policy blocks every crypto API), so the
chart is labelled IBIT on screen and never presented as BTC/USD itself.

---

# Build Spec: "The Setup That Failed" — IBIT 40s Trade-Fail Reel

**Format:** 1080×1920, 30fps, 1200 frames total, silent-first (music-only, no VO).
**Instrument:** IBIT (Bitcoin ETF) — outside the six AI-stack layers, see Production Note below.
**Data discipline:** real IBKR daily bars via `get_price_history`, structure found (not authored) by a ZigZag/fractal + trendline scanner per §4; if no qualifying real window exists, this is **UNMATCHED**, not fudged.
**Reuses:** `remotion/src/components/TapeChart.tsx` (candle-print engine), `remotion/src/compositions/TradingQuiz.tsx` (countdown/RR/footer patterns — timeline is *not* reused verbatim, see Production Note), `remotion/src/motion/craft.ts` (`EASE`, `SPRINGS`, `FRAMES`, `wiggle`, `cameraPushIn`), `remotion/src/characters/rubberHoseRig.tsx` (`Pose`, `track()`, blink/breath/gaze channels).

---

## Production note: where this deviates from existing code, and why

1. **Entry/stop/target moves *before* the quiz, not after the reveal.** `TradingQuiz.tsx` currently draws the RR frame at `RR_IN = REVEAL_END + 8` — i.e., after the outcome is already known, as an explanatory overlay. The narrative research is explicit that for a *prediction* format the risk frame must be visible **before** the ask, or the viewer is guessing blind and the loss reads as unearned. This piece is a new composition (call it `TradeFailReel.tsx`) that borrows `TapeChart`'s tick engine, `TradingQuiz`'s countdown/footer/RR-band rendering *code*, but reorders the **timeline**: entry beat → quiz → wait → reveal, not build → quiz → reveal → RR.
2. **Quiz window is fixed at 5.0s (150 frames), not scaled to the 40s runtime.** The algorithms/levels lane's own house code already encodes this exact value (`COUNT_PER = 30`, `COUNT_N = 5` in `TradingQuiz.tsx`) and the narrative research independently derives the same number as a ceiling on decision-window length regardless of video length. Two independent sources agree; use it verbatim rather than re-deriving.
3. **Character choice is an open call, flagged not resolved here.** IBIT isn't Chip/Watt/Qubit/Cap/Nova/Cloudy's layer (`family.tsx`), and Maya/Karim are explicitly out of scope for `video/` per CLAUDE.md §9. Recommendation: use the **undecorated `rubberHoseRig`** (as `MemeReel.tsx` already does) rather than force-fitting an AI-stack mascot onto a Bitcoin ETF — the character research's silhouette/palette rules apply regardless of which named character it is. If the owner wants series continuity, **Cap** ("reads every filing," policy-adjacent) is the closest analog, but this is the owner's call, not an engineering one.

---

## 1. Second-by-second beat sheet (1200 frames @ 30fps)

Eight beats, summing exactly to 1200f / 40.00s. Split: 3.0s hook / 9.0s build / 5.0s pattern / 5.0s entry / 5.0s quiz / 5.0s wait / 4.0s fail / 4.0s lesson — a 30/25/25/20 build-decision-tension-payoff ratio, matching the narrative lane's inverted-from-instinct budget (setup is the smallest fraction of runtime).

A **footer strip** (source ticker/timeframe/timestamp, "Educational — not advice") is present on **every frame, 0–1200**, per §10.6 — it is not a beat, it is a persistent layer and is omitted from the table below to avoid repetition.

### Beat 0 — HOOK · frames 0–90 (0:00.0–0:03.0)

| | |
|---|---|
| **Chart** | Cold open, mid-motion: 3–4 candles already visibly printed on entry (no blank canvas, no fade-up) — satisfies "mid-motion open," the retention lane's #1 fix for the 0–3s drop. |
| **Character** | Already in frame, already leaning toward the monitor (small 3–5° `leanChest`), one hand mid-gesture (not a static T-pose) — motion already happening at frame 0. |
| **Text** | Hard-cut caption, on screen 0–90: **"WATCH THIS CANDLE."** Short fragment, not a sentence. No pleasantries, no channel branding. |
| **Sound** | Music only; a single low tick/anticipation cue at frame ~75 as a pattern-interrupt into Beat 1. |

### Beat 1 — CHART BUILD · frames 90–360 (0:03.0–0:12.0), 270f

Draw sequence follows §6 of the algorithms lane exactly (candles → swing pivots inline → S/R zones ranked → trendline last):

| Sub-range | Event |
|---|---|
| 90–300 (210f) | Candles print at tape speed. `CANDLE_FORM` derived per-bar exactly as `TradingQuiz.tsx` does it: `CANDLE_FORM = max(2, round((300−90)/barCount))`, `CANDLE_TICKS = 3` fixed (house constant, do not raise — 3 hard steps reads as tape, more reads as smooth animation). |
| inline, per bar | Swing pivot markers (small dot/triangle) pulse on **exactly** the bar whose ZigZag/fractal confirmation lands that frame — never retroactively on an already-printed bar. Pop timing: 6f anticipation-free micro-pop (`SPRINGS.snappy`), no separate dedicated window. |
| 300–320 (20f) | Top-scored S/R zone fades in (`EASE.enter`, matches `TapeChart`'s existing `levelP` 20f fade). Rendered as a soft translucent band, not a hairline (§2). |
| 315–335 (20f, staggered +15f) | Second zone (opposite side of price) fades in. **Cap at 2 zones** — one support, one resistance, both within the "close to current price" gate (§5 of algorithms lane). |
| 335–360 (25f) | Trendline draws left-to-right from anchor 1 to anchor 2, then extends as a dashed projection to the current bar. Neutral/structural color only (`#22E07E`-family accent, never the bull/bear hues) — this is "the analyst drew this," not a signal. |
| **Text** | None yet — let the tape speak, per the chart-craft lane's explicit rule ("candles print first, structure-free"). |
| **Character** | Idle loop only: breathing (`wiggle`, ~3.2s period), blink `frame % 118`, no discrete beat yet. This is the one stretch of the video allowed to be visually quiet on the character side — attention belongs to the chart. |

Element count check at frame 360: candles + 2 pivot markers visible + 2 S/R zones + 1 trendline = **5 elements**, inside the 5–7 ceiling (§4 chart-craft).

### Beat 2 — PATTERN DETECTED · frames 360–510 (0:12.0–0:17.0), 150f

| Sub-range | Event |
|---|---|
| 360–375 (15f) | Everything except the pattern's 2–3 candles dims/desaturates (opacity drop via `interpolate`, `EASE.cruise`) — the single most-used attention technique per the chart-craft lane, chosen over adding a new element. |
| 375–410 (35f) | A **boxed** tag (matching the house "SUPPORT/RESISTANCE" visual language, not free-floating text) draws around the pattern candles, `EASE.enter`. One leader-line only if needed, pointed at the exact wick. |
| 400–430 | Pattern name prints inside the box: e.g. **"BULLISH ENGULFING"** — the "why," named on screen per narrative lane §2. |
| 385–430 | Character "notices" take: 4f anticipation counter-move, 14–16f head/torso lean toward screen (overshoot ~10–15% past target), 8–10f `EASE.settleBack` correction. This is the rig's existing `notices` beat pattern (`leanChest` target ~+6°), reused, not reinvented. |
| 430–450 | Held "processing" pause — near-zero motion on the big channels, breath/blink still running underneath (character research §2: the stillness *before* a small aha is what sells "he's thinking"). |
| 450–510 | Full-frame color restores (dim reverses over ~15f); character returns to neutral-alert stance, walking the arc toward the confidence beat. |

### Beat 3 — ENTRY · frames 510–660 (0:17.0–0:22.0), 150f

Confidence performance (character lane §2), then the trade frame (§10.5 "all four or none," moved to *before* the quiz per the Production Note):

| Sub-range | Event |
|---|---|
| 510–516 (6f) | Anticipation: small counter-dip, shoulders drop slightly *before* the confident gesture. |
| 516–530 (14f) | Action: one decisive gesture — hand plants on desk / points at the chart. Reuses the rig's IK-plant pattern (`plantIK`/`facepalmW` blend technique, same mechanism, different target pose). Chest lifts, opens (`leanChest` goes upright-to-slightly-back, −2° to −6°, **not** forward — forward-fast reads as aggression). |
| 530–540 (10f) | Overshoot + `EASE.settleBack` correction. |
| 540–560 (20f) | Entry marker (small pin/flag, not a banner) places at entry price+time on the chart. |
| 560–600 (40f) | Stop and target lines bracket the entry, fading in together (~staggered 8f apart, never sequential-with-a-gap): risk band (entry→stop, red-tint fill) and reward band (entry→target, green-tint fill) — literally the `TradingQuiz.tsx` RR-band rendering code, just moved earlier in the timeline. `rrLabel` text (e.g. "2.1R") is the last element to land. |
| 600–660 (60f) | **Static hold.** Per narrative lane: let the RR number sit a beat longer than feels necessary — it's what makes the later loss read as "planned" not "unlucky." This is also, per character research, the character's **most still** moment in the whole piece — the contrast against the anxious loop that follows is the point. Only breath/blink/idle-drift run under the hold. |

Element count at 660: candles + 2 S/R zones (now dimmed/de-emphasized as background context) + trendline + entry/stop/target/RR = at ceiling; the pattern-detection box should have faded out by now (do not carry it forward — see checklist item on stacking).

### Beat 4 — QUIZ · frames 660–810 (0:22.0–0:27.0), exactly 150f

See §2 below for full quiz mechanics. Chart is **frozen** on the entry bar — no new candles print in this window.

| Sub-range | Event |
|---|---|
| 660–675 | Question text lands: **"BOUNCE OR BREAKDOWN?"** — answerable only from what's already on screen (support zone below, trendline/resistance above, both visible per Beat 1/3). |
| 660–810 | Countdown: 5 digits × 30f each (`COUNT_PER=30`, `COUNT_N=5`, verbatim from `TradingQuiz.tsx`). Ring is **uncolored** — see §2 leak rule. Tick/tock alternating SFX, one per second, 5 hits total. |
| 660–810 | Character's anxious-wait loop **starts here** (not in Beat 5) — see §3. The viewer's countdown and the character's first visible nerves should land in the same window, so the tension is shared, not sequential. |

### Beat 5 — ANXIOUS WAIT · frames 810–960 (0:27.0–0:32.0), 150f

| Sub-range | Event |
|---|---|
| 810–960 | 2–3 more real bars print, chopping/stalling near the entry price — genuinely ambiguous, not a fake-out choreographed to mislead (the bars are what `find_real_pattern.py` actually returned; no nudging). Candle form stretched to ~45–55f/bar (vs. 20–25f/bar in Beat 1) — tension needs the beats to feel slower, not faster. `CANDLE_TICKS` stays 3 — do not smooth these bars just because the pace slows. |
| 810–960 | Y-axis stays **symmetric**, not yet zoomed to the eventual outcome range (this is the leak vector in Beat 6's setup — see checklist). Candle color naturally flips per the live print (a chopping bar can print green then red) — that's honest tape, not a leak. |
| 810–960 | Anxious loop continues, intensifying: weight-rock amplitude/period unchanged, but the "held breath then bigger exhale" beat (character lane §1) should land once in this window, timed to a moment the chart chops against the character (e.g. a wick pokes toward the stop and retreats). |

### Beat 6 — TRADE FAILS · frames 960–1080 (0:32.0–0:36.0), 120f — shortest beat, deliberately

| Sub-range | Event |
|---|---|
| 960–988 (28f) | Zoom-out interpolation begins (`EASE.cruise`, matches `TradingQuiz.tsx`'s existing `zoomOut` window shape) — this is the *only* point the y-axis is allowed to open up to the full range, and it's timed to start exactly as the reveal candle begins, not before. |
| ~1000–1040 | One clean reveal candle prints, `CANDLE_TICKS=3`, red, with a single `candle_down` SFX hit landing exactly on the settle tick — per house sound doctrine, one hit per reveal candle, not one per tick. |
| ~1000–1010 | **Shock beat**, timed to land on the same frame as the SFX hit: 2–4 frame pose-snap — `eyeBulge` spike-then-settle, `leanHead` recoil, whole-body `squash` stretch >1, all **simultaneous**, not sequential (character lane §2: sequential = three small surprises, not one big one). |
| 1010–1070 (60f) | **Deflation ramp** immediately follows: `slouch` 0→~0.85 over ~35f, chest/head sink, facepalm-or-chin-in-hand via IK contact. Contact does **not** stop the motion dead — it keeps sinking 15–25f past the hand landing (`EASE.cruise`, same "sag keeps deepening after contact" pattern already in the rig). |
| ~1010 | Price tag snaps to the stop level; the stop line gets **one** brief pulse (not a flash-the-whole-screen moment) — per §2 "pulse limited to one element, at the decision moment." |
| throughout | RR label / risk-reward numbers from Beat 3 **stay on screen through the reveal** — per narrative §5, keeping the R:R visible through the loss is what reframes "one loss" as "one data point inside a stated edge," not a wound. |

### Beat 7 — LESSON + LAST-FRAME HOOK · frames 1080–1200 (0:36.0–0:40.0), 120f

Three-second-structure from the narrative lane, stretched to fit the 4s budget:

| Sub-range | Event |
|---|---|
| 1080–1110 (30f) | **Stillness.** Big channels (torso, arm) stop; breath/blink keep running. Expression reads "recalibrating," not defeated — this is the emotional turn, and it must not be rushed into the next beat. |
| 1080–1110 | Optional small caption, understated, naming the mistake internally (mistake-based framing, relatable, not preachy): e.g. *"No volume behind that breakout."* |
| 1110–1150 (40f) | On-screen rule lands, boxed like the pattern tag from Beat 2 (visual echo is intentional — same "this is a labeled fact" language): **"BREAKOUTS NEED VOLUME."** Rule-based framing — generic enough to be portable, but anchored to the specific chart just shown, not a floating maxim. Character does a small "aha" — linear head-tilt completing, no overshoot (overshoot = surprise, linear = thought, per character lane §2). |
| 1150–1200 (50f) | Closing line, question-based framing, drives comments: e.g. **"Would you have waited for the retest?"** Final expression holds resolve/curiosity through frame 1200 — **never** end on the red candle or a number. Last frame on screen is the character + the question, not the loss. |

---

## 2. Quiz mechanics

**Placement:** immediately after the entry beat, once entry/stop/target/RR are all visible (frame 660) — never before risk is defined, per narrative lane §3. The quiz question is answerable strictly from information already drawn: the support zone (Beat 1), the trendline/resistance (Beat 1), and the entry bar (Beat 3). No off-screen knowledge required.

**Window length: fixed 150 frames / 5.0s**, not scaled to the 40s runtime. This is the one place two independent research lanes converge on an identical, non-obvious number: the narrative lane derives it analytically (a countdown is a fixed cognitive task — glance, form an opinion, commit — and 5–6s is near the ceiling before dead air sets in, *regardless* of total video length), and the existing codebase already encodes exactly this (`COUNT_PER=30 × COUNT_N=5` in `TradingQuiz.tsx`). Use the code constant verbatim — do not stretch it to "fill" the extra 40s budget; that budget goes into the wait beat instead (Beat 5), per the narrative lane's explicit instruction to lengthen the *frame around* the quiz, not the quiz itself.

**How the "he already entered before the quiz" tension is staged:**
1. The chart is **frozen** for the full 150f window — no new bars print during the countdown. The only things moving are the countdown ring/digits, the character's anxious loop, and the tick/tock SFX. This isolates the tension source: the viewer isn't watching new information arrive, they're watching a clock run out on a bet that's already been placed.
2. The character's anxious-wait loop **starts at the same frame the quiz starts** (660), not after it (Beat 5 is the *continuation*, not the origin). This means the viewer's own countdown-anxiety and the character's on-screen nervousness are synchronized — the character is visibly experiencing the same wait the viewer is being timed through.
3. The RR frame from Beat 3 (entry/stop/target/rrLabel) **stays visible, unchanged, through the entire quiz window** — the viewer isn't just guessing direction, they're evaluating a stated, bounded-risk bet, which is what separates this from a trivia gimmick (narrative lane §4).
4. **No colored countdown ring.** This is a hard rule already in the house style (§10.3) and independently flagged by the retention lane as the single most concrete, falsifiable failure mode in this content type ("a viewer who notices feels patronized"). The ring is one neutral accent color regardless of what the eventual answer is.
5. **Symmetric y-axis through the entire quiz and wait beats.** The zoom-out that reveals the true range happens only in Beat 6, timed to the reveal candle, not before. An axis that already has headroom on the "breakdown" side during the countdown is a leak exactly as loud as a colored ring.
6. The quiz question is phrased as the two-way outcome the setup actually supports ("bounce or breakdown") — not a three-way or hedged question. Per the algorithms-lane-adjacent note in the narrative research: window length is a function of decision complexity, not video length, and a single pattern with an obvious two-way outcome stays at 5s even at 40s+ runtime. Do not add a third option "just because there's more runtime available" — that would force a longer window and break the fixed-150f rule.

---

## 3. Character performance spec

All frame counts are relative to the beat's own start frame unless given as an absolute frame number. Built directly on `rubberHoseRig.tsx`'s `Pose` channels (`bob`, `weightShift`, `leanChest`, `leanHead`, `gazeX/gazeY`, `eyeBulge`, `squash`, `slouch`, `shoulderR/L`, `blink`) and `craft.ts`'s `track()`/`EASE`/`SPRINGS`/`wiggle()` primitives.

### Persistent, never-stop layer (runs under every beat, including holds)

| Channel | Period / rule |
|---|---|
| Blink | `frame % 118` neutral cycle (rig default) — 4f closed, 5f re-open. Tighten to `% 60–70` with an occasional double-blink (two cycles 6–8f apart) during the anxious-wait window (660–960). **Suppressed** for 20–30f windows bracketing the notices-take (Beat 2, ~385–430) and the shock-snap (Beat 6, ~1000–1012) — a blink landing mid-take reads as a rendering bug. |
| Breath | `wiggle(frame, seed, amp≈0.85px, period≈3.2s)` on `bob`. Amplitude dampens (not to zero) under `slouch` in Beat 6/7 — reduce by up to 40%, never fully stop. |
| Idle limb drift | `wiggle()` per limb, own random seed, 4–6s period, ±3–6° on shoulders. Never synchronize two limbs on the same seed. |
| Gaze saccades | `gazeX/gazeY` independent of `leanHead` — reposition every 20–40f, 1–3f snap, then hold. This channel alone is the cheapest, highest-value "alive" signal; keep it running through every beat except the shock-snap frame itself. |

### Beat 0 (Hook, 0–90)
Already mid-gesture at frame 0 — no entrance animation to "arrive" into frame. Small forward `leanChest` (3–5°) toward the monitor, one hand already raised/pointing. No new discrete beat; idle+drift channels only.

### Beat 1 (Chart Build, 90–360)
Idle only — this is the one stretch where the character should be the *quietest* thing on screen, deliberately, so attention stays on the tape. Resist the urge to add a reaction here; per the chart-craft lane, "a real terminal has quiet stretches — let non-reveal moments sit still."

### Beat 2 (Pattern Detected, 360–510) — the "notices" take
- **385–389 (4f):** anticipation, small counter-move opposite the coming lean.
- **389–405 (16f):** action — `leanChest` rides from rest toward +6°, `leanHead` layers a further tilt, gaze snaps to the pattern box.
- **405–413 (8f):** overshoot ~10–15% past +6°, then `EASE.settleBack` correction over the same window.
- **413–430 (17f):** hold — near-zero big-channel motion (the "processing" pause), breath/blink/gaze still running.
- **430–450 (20f):** small "aha" tick — brief `eyeBulge` nudge (much smaller than Beat 6's shock spike), light nod, `EASE.settleBack`.
- **450–510:** transition posture toward the confident entry stance — shoulders begin to widen/drop over this window rather than snapping, so Beat 3's decisive gesture reads as building on this, not starting cold.

### Beat 3 (Entry, 510–660) — confidence
- **510–516 (6f):** anticipation dip.
- **516–530 (14f):** the decisive gesture — hand plants on desk / points at screen, reusing the rig's IK-plant blend (`plantIK`/`facepalmW`-style technique, different target). `shoulderR` arcs to its extreme with the far arm at a *different* extreme than the near arm (never mirror both arms — character lane §5 "classic mistakes" #2).
- **530–540 (10f):** overshoot + settle.
- **540–600:** feet/stance widen slightly (`hipL/hipR` delta) as the trade frame draws.
- **600–660 (60f):** the held stance — the single stillest moment in the whole piece, contrast is the point. Idle/breath/blink/gaze keep running; nothing else moves.

### Beat 4 (Quiz, 660–810) + Beat 5 (Wait, 810–960) — the anxious-waiting loop (starts at 660, continues to 960; the single largest and most craft-sensitive stretch, 300f/10s total)
This is a **held frame that refuses to fully hold**, layered *under* the persistent channels above:
- **Weight rock, not shift:** lateral `weightShift` oscillation, amplitude 4–8px, period 45–60f (1.5–2.0s). Never resolves to zero — it's a stance that can't commit to stillness.
- **Shoulder creep:** slow asymmetric breath-linked rise on `bob`/shoulder height — rise slightly faster than fall (tension-in, release-slow). This asymmetry is what reads as *held* breath rather than relaxed breathing; a symmetric sine here reads as merely idle, not nervous.
- **Hand fidget:** the single strongest anxious tell at phone size. A small repeating elbow/hand rotation loop, 8–12f period, ±6–10° amplitude, never resolving — finger-drum or thumb-twiddle on the desk edge. Cheap to implement (one more `wiggle()` channel on `elbowR`/`handR`), highest legibility-per-cost of anything in this spec.
- **Blink rate:** roughly doubled vs. neutral (see persistent-layer table), occasional double-blink.
- **Gaze:** rapid flicks toward the chart every 20–35f, independent of head — decoupling this from `leanHead` is what separates "nervous" from "just looking around."
- **Micro-lean:** 3–5° toward the chart, held (deliberately smaller than Beat 3's confident lean, which was 15–25°-scale by comparison — the contrast is legible even without measuring).
- **One held-breath beat**, once, timed inside Beat 5 (810–960) to coincide with a chop toward the stop level: breathing amplitude drops near-zero for 15–20f, then resumes larger (relief-adjacent gasp) on the retreat.
- **Squash:** creeps fractionally below 1.0 (coiled, compressed) rather than sitting at neutral — a slow, barely-perceptible tightening across the full 300f.

### Beat 6 (Trade Fails, 960–1080) — shock then deflation, two distinct timing signatures
- **Shock (~1000–1012, 4–8f + settle):** simultaneous, not sequential — `eyeBulge` spike-then-overshoot-then-settle, `leanHead` hard recoil (fast, steep interpolation, near-cut rather than eased), `bob` lift, whole-body `squash` stretch to ~1.1–1.15, all landing in the same handful of frames, timed exactly to the `candle_down` SFX hit. Hands fly up/out asymmetrically (near arm and far arm at different extremes, so the silhouette doesn't mirror-freeze).
- **Deflation (1010–1070, ~35–40f ramp, continuing to bleed for 15–25f past the facepalm contact):** inverse of Beat 3's confidence — chest/head sink, `slouch` 0→~0.85–1.0, `bob` settles lower, breathing amplitude drops. Facepalm or chin-in-hand via IK is the workhorse pose here (instant "deflated" read with zero facial nuance required — this is exactly why the rig leans on it). Motion must **not** stop dead on hand-contact; it keeps sinking for another beat, per `EASE.cruise`'s existing "sag keeps deepening" pattern.
- **Explicitly not devastation.** Calibrate the deflation's depth to "deflate → about to recalibrate," not collapse — per narrative lane §5, a brief arc teaches "losses are routine," a catastrophic one teaches "losses are catastrophic," and the second is both the wrong lesson and the one that drives people off the next video.

### Beat 7 (Lesson, 1080–1200) — dawning realisation, deliberately NOT a second shock
- **1080–1110 (30f):** stillness, big channels frozen, breath/blink alone running — this pause is what sells "he's thinking," not the motion itself.
- **1110–1150 (40f):** slow, **linear** `leanHead` drift (4–8° over the window, no overshoot) — overshoot here would read as a second surprise and muddy the arc; realisation must have its own timing signature, distinct from Beat 6's snap.
- **~1140–1150:** small "aha" — a much smaller `eyeBulge` tick than Beat 6's, one hand gesture (finger up / light nod), landing on `EASE.settleBack`, not a hard snap.
- **1150–1200:** final held expression — resolve/curiosity, idle/breath/blink/gaze still running underneath, this is the frame the video ends on.

---

## 4. Chart-structure plan

Structures are computed once (ZigZag pivots → S/R clustering → trendline scan, per the algorithms lane), then a **narrative relevance filter** decides what actually gets drawn — a statistically valid structure that the reveal window never revisits is clutter even if well-scored (algorithms lane §5).

| Structure | Detector | Gate before it's eligible to draw | Draw window | Cap |
|---|---|---|---|---|
| Swing pivots | ZigZag, ATR-adaptive threshold (`atr_mult` 1.5–3×), fractal(k=2) as tie-breaker for the exact turn bar | Confirmed pivot only (never draw the unconfirmed provisional tail) | inline, pulses on the confirming bar as it finishes printing, frames 90–300 | no explicit cap — sparse by construction |
| Horizontal S/R | 1-D cluster of pivots, ATR-scaled `merge_dist`, scored (touches, recency half-life, duration, touch quality, close-violation penalty) | `touches ≥ 2`, at least one touch within the last ~60–90 bars, within a bounded % of current price | fades in 300–335, ranked-score order (highest first) | **top 2** (1 support + 1 resistance) |
| Trendline | Pivot-pair candidate scan + violation walk (close-through = violation, wick-through = tolerated) | `touches ≥ 3`, zero (or tolerance-graded) close-violations as of the last bar shown, not degenerate-flat (defer to S/R if so) | draws left-to-right 335–360, then dashed-projects to the current bar | **1**, whichever side (support/resistance) the pattern in Beat 2 is testing |
| Candlestick pattern | Whatever `find_real_pattern.py` confirms on the real window (engulfing / hammer / etc.) | Must occur at or near the trendline/S/R interaction the reel is building toward — narrative necessity, not just a valid pattern anywhere in the window | boxed tag, 375–430 | 1 |
| Entry/stop/target/RR | Derived from the pattern + nearest S/R/trendline levels, per §10.5 "all four or none" | All four present or none drawn | 540–600, held through frame ~1080 | 1 trade frame |
| Reveal candle(s) | The actual next real bars in the fixture | N/A — this is ground truth, not a detected structure | 960–1040 | as many as the real data provides between entry and stop-out, typically 1–3 |

**Simultaneous on-screen cap: 5–7 distinct graphic elements**, per the chart-craft lane's ceiling (2–3 indicators, ~4 legible text labels). At the busiest point (end of Beat 3 / through Beat 4–5) the live set is: candles + 2 S/R zones + 1 trendline + entry/stop/target/RR cluster (counted as one "trade frame" element, not four separate ones) = **5**. The pattern-detection box from Beat 2 must be faded out by the time the trade frame lands — do not let it accumulate on top.

**Sequencing discipline (algorithms lane §6, chart-craft lane §1–2 agree):** structures are *sequenced in*, one type at a time, never all revealed simultaneously — candles → pivots → S/R → trendline → pattern box → trade frame → reveal. Each layer gets its own on-screen "moment"; nothing materializes with the first frame of the video.

**Color discipline (chart-craft lane §5):** exactly two directional hues (`#00E676` up / `#FF3B30` down), reserved *exclusively* for price. Structure (S/R zones, trendline) uses the neutral structural accent (`#22E07E`-family or a grey/white), never a new hue. The trade frame distinguishes itself by **line weight and dash pattern**, not a new color. This is also why the countdown ring in Beat 4 must stay neutral — it would otherwise be a *sixth* semantic color competing with the same palette.

---

## 5. Quality checklist

Checkable items only, each traceable to a specific research finding or house rule — not generic advice.

**Leak vectors (house rule §10.3, independently flagged by retention lane as the most concrete failure mode in this content type):**
- [ ] Countdown ring (frames 660–810) uses one neutral color throughout — never tints toward the eventual answer color.
- [ ] Y-axis stays symmetric (no directional headroom) from frame 90 through frame 987 — the zoom-out interpolation does not begin before frame 960.
- [ ] No text, box color, or icon anywhere before frame 1000 states or implies the outcome direction.

**Structural / real-data discipline (§10.1, algorithms lane):**
- [ ] Every drawn structure (pivot, S/R zone, trendline, pattern) passes its own minimum-evidence gate (§4 table) — nothing is drawn "because it looks right."
- [ ] The reveal window (Beat 5–6 bars) is the actual next bars in the fixture, not selected/trimmed to guarantee a clean stop-out.
- [ ] Any IBKR wick deviating >15c from session high/low is quarantined per house rule; any window containing one is rejected outright, not patched.
- [ ] The pattern named in Beat 2 is the pattern `find_real_pattern.py` actually confirmed — not a plausible-looking candle chosen by eye.

**Trade-frame integrity (§10.5, narrative lane §1/§5):**
- [ ] Entry, stop, target, and `rrLabel` all appear together in Beat 3 — never a target with no stop.
- [ ] The RR numbers stay visible and unchanged through the Beat 6 loss — not removed at the moment of failure.
- [ ] No dollar P&L figure anywhere, on any frame (compliance rail §10.6) — R-multiple or the abstract `answerLabel` pattern only.

**Pacing / element density (chart-craft lane §2, §4):**
- [ ] No more than 5–7 distinct graphic elements on screen at any single instant (count them at the busiest frame, ~660).
- [ ] The pattern-detection box (Beat 2) is faded out before the trade frame (Beat 3) lands — nothing accumulates indefinitely.
- [ ] Only one element pulses/glows at a time, and only at its own decision moment (pivot confirmation, pattern box, stop-hit) — never two simultaneously.

**Character performance (character lane §3, §5, §7):**
- [ ] No target-to-target pose cut anywhere — every discrete beat (notices, entry, shock, deflation, aha) has an anticipation counter-move, even if only 4f.
- [ ] Blink, breath, gaze-saccade, and idle-drift are still running during every *held* pose, including the 600–660 confidence hold and the 1080–1110 stillness beat — no channel goes fully dead during a hold.
- [ ] Both arms are never in mirrored lockstep at the same timing/extreme (checked explicitly at Beat 6's shock throw).
- [ ] The anxious-wait loop (660–960) never fully resolves/settles — if any single anxious-loop channel holds perfectly still for more than ~2s, it has drifted out of "held frame that refuses to fully hold" into just "idle."
- [ ] Shock (Beat 6, ~1000–1012) is a fast near-cut (4–8f) on eye/head/squash simultaneously; realisation (Beat 7, 1110–1150) is a slow linear ramp with no overshoot — confirm these two are not accidentally using the same easing curve.

**Sound (§10.4):**
- [ ] Tick/tock alternates correctly across the 5 countdown seconds (660–810), never two of the same in a row.
- [ ] Exactly one `candle_down` hit lands on the Beat 6 reveal candle's settle frame — not one per tick.
- [ ] No SFX during the 90–360 build (ambient tick/tock only starts meaningfully once the countdown or reveal beats are active) — confirm the build doesn't accidentally run at "seventeen hits a second" density.

**Muted-viewer self-sufficiency (retention lane §7):**
- [ ] The quiz question, the countdown value, and the outcome are all legible from on-screen text/visuals alone — none of them require the audio track to land.
- [ ] The hook (Beat 0) does not depend on a spoken line — it's mid-motion + text only.

**Ending discipline (narrative lane §4, retention lane §3):**
- [ ] The last frame on screen (1200) is the character + the closing question — not the red candle, not a number, not a "follow for more" card.
- [ ] Runtime after the reveal resolves (from ~1080) is ≤4s — matches the retention lane's warning that post-reveal attention drops regardless of quality, so the tail must be short by design, not trimmed after the fact.

---

## 6. What the research says NOT to do

Compiled directly from the "overused / cheap / retention-killing" flags across all five lanes — not generic production advice.

- **Static establishing frame at open, or a logo/branding/"hey guys" intro.** Named across the retention lane as the #1 retention killer; burns the highest-leverage 1–3s window on zero information. This reel opens mid-motion instead.
- **A hook or pattern-interrupt that depends on audio to register.** ~85% of first-impression views are muted by platform default; an audio-only cue in the first seconds is invisible to the majority of viewers.
- **Colored countdown ring or asymmetric y-axis padding during the quiz window.** Already an internal house-style violation (§10.3) that shipped once before being caught; independently named by the retention lane as the most concrete, falsifiable way a quiz reads as "cosmetic" rather than genuine.
- **Arrows pointing at multiple things at once, or multiple simultaneously-pulsing elements.** Chart-craft lane: competing motion cancels the attention cue it's supposed to create.
- **Full-screen flash, screen-shake, or neon glow/drop-shadow stacked on every element.** Reads as an infographic/explainer, not a terminal — directly contradicts the "real terminal vs. cartoon of one" tells (motion physics, restraint in idle moments, flat chrome).
- **Spring/bounce/elastic easing applied to the candle print itself.** That motion vocabulary belongs to UI chrome (badges, the character's `Entrance` wrapper) only; applied to price data it turns tape into an animated infographic. `TapeChart`'s discrete-tick engine is correct — do not "smooth" it for the slower wait-beat bars.
- **Model-authored OHLC or a nudged reveal to guarantee a clean stop-out.** House rule §10.1 and narrative lane §1 both flag this: a viewer who senses a constructed outcome stops trusting the *next* quiz in the series, not just this one.
- **A dollar P&L figure, an animated counting-up number, or a percentage badge without R-context on an open position.** Chart-craft lane §6 names this cluster explicitly as "the profit flex" and the direct fix (R-multiple / bounded-band visualization) is already built into the Beat 3 trade frame.
- **Recapping the whole trade in the closing seconds, or ending on the red candle/losing number.** Named as a proven exit-signal in both the retention and narrative lanes — the last frame must be the reframe/character, not the loss.
- **A second question mid-video, or closing on a statement instead of a question.** Narrative lane §6: a stated lesson invites agreement/disagreement (fine, but weaker); an unresolved question at the very end is what converts a passive viewer into a commenter — don't spend that device twice (the quiz already used the "posed question" mechanic once).
- **Devastated, prolonged character reaction to the loss.** Character lane + narrative lane agree: this teaches "losses are catastrophic," which is both the wrong lesson and the one that drives people away from the format. Deflation is calibrated to "deflate → about to recalibrate," and it is the *shortest* beat in the piece (120f/4s) by design, not by budget accident.
- **Multiple stacked "here's everything that went wrong" causes.** Narrative lane §5: dilutes into "the market is unpredictable," which is a shrug, not a lesson. One pattern-detection beat (Beat 2) names the one variable; Beat 7's rule traces back to exactly that one thing and nothing else.
- **Stretching the quiz countdown to "use" the extra runtime a 40s format buys.** Both the narrative lane's explicit warning and the existing `COUNT_PER×COUNT_N` code constant agree the window is fixed near 5–6s regardless of total length; the extra seconds belong to the wait beat, not the countdown.
- **A synthetic-looking, evenly-spaced setup with no wick/overlap noise.** Chart-craft lane names this the single biggest "cartoon of a terminal" tell — reinforces why this piece is built exclusively on a real, scanner-confirmed IBIT window rather than an authored one.

---

**Files referenced for grounding (no files modified — research/spec only):**
`/home/user/AIInvestment/remotion/src/components/TapeChart.tsx`, `/home/user/AIInvestment/remotion/src/compositions/TradingQuiz.tsx`, `/home/user/AIInvestment/remotion/src/motion/craft.ts`, `/home/user/AIInvestment/remotion/src/characters/rubberHoseRig.tsx`, `/home/user/AIInvestment/remotion/src/characters/family.tsx`, `/home/user/AIInvestment/scripts/ta_quiz/find_real_pattern.py`, `/home/user/AIInvestment/scripts/trading_styles/find_real_windows.py`.