# Strategy Episode 1 — Breakout & Retest (~90s, 2026-08-02)

Extends the science reel into an educational episode. Owner brief: keep the
accusation intro; pivot to "one medium-complexity strategy" instead of the
science list; synthetic QUIZ example (countdown → strategy unfolds →
simulated take-profit) with Maya speaking at the beats; then "this strategy
is not fiction" — a REAL dated occurrence (Brent) walked through with
trendlines/S-R drawn at display time while the chart advances; outro
"like and follow for more". Strategy: breakout + retest (owner-picked).

## Acts

| Act | ~s | Source | Content |
|---|---|---|---|
| 1 | 14 | existing dlg0/dlg1 windows + shots | accusations (unchanged) |
| 2 | 6 | NEW anchored dialogue window | "But here's what it actually runs on. Let's dive into one medium-complexity setup — the breakout and retest." |
| 3 | ~28 | TradingQuiz engine + NEW synthetic fixture | ceiling touched twice → breakout → retest → 5s countdown quiz → reveal rally, entry/stop/target/R:R, TP hit + coin. Footer: SYNTHETIC label. Maya voice-over at beats. |
| 4 | ~32 | NEW StrategyWalkthrough comp + real BZ=F bars | real Brent daily window found by scanner; candles print in time; resistance line drawn the moment its 2nd touch forms; breakout tag, retest arrow, entry/stop/target, real outcome; instrument+dates on screen; provenance footer. Maya VO per signal. |
| 5 | 6 | NEW anchored dialogue window | "That's one setup out of dozens. If you want more candlestick strategies like this — like and follow for more." + FOLLOW overlay |

## Rules honored

- Numbers Python-owned: quiz candles built+validated by script, labeled
  SYNTHETIC on-screen; real act uses Yahoo BZ=F daily (REST, stamped
  source/retrieved_at/source_class), IBKR-style bar sanity checks, dirty
  bars quarantined (rule 10.1 adapted — IBKR MCP unauthenticated this
  session, Yahoo is the live REST source).
- Trade frame all-four-or-none: entry/stop/target/rrLabel; tpBar derived
  from data (10.5). Stop chosen from setup logic before outcome.
- Progressive annotation (owner's key ask): every line/level appears at
  the bar where it becomes knowable, never earlier.
- Compliance (10.6): no returns promises; R multiples are chart geometry
  with the stop visible; real outcome shown as it printed; footer on every
  frame naming real vs synthetic and source+timestamp. CTA is engagement
  only.

## Voice

- On-camera (acts 2, 5): standard maya-talking-pipeline (anchored start
  frame, STT-verified, VC, drift-locked).
- Off-camera narration (acts 3, 4): Chatterbox TTS in the cloned voice
  (no lips on screen), lines placed at chart-event times exactly like
  make_vo's grid (lead 0.15s, overlap-free by construction).

## Build units

1. `scripts/strategy_reel/find_breakout_retest.py` — pull BZ=F daily
   (6-24mo), scan: resistance = swing-high level touched >=2 within tol;
   breakout = close > level; retest = later low within tol of level;
   success = rally >= 1.5R from entry(level) vs stop(retest swing low).
   Emits window JSON + provenance; UNMATCHED reported honestly if nothing
   qualifies (then try CL=F, GC=F before widening tolerances).
2. `scripts/strategy_reel/make_quiz_fixture.py` — synthetic candles for
   the same setup shape; validates monotonic wicks, level touches, RR;
   emits TradingQuiz props (kick/patternName/level/answer/rule/footer/
   revealFrom/candles).
3. `remotion/src/compositions/StrategyWalkthrough.tsx` — house terminal
   style (10.2), event-driven timeline: print bars on CANDLE_TICKS pacing,
   annotations keyed to bar indices (level line at touch2, BREAKOUT tag,
   RETEST arrow, trade frame at entry, TP flash+coin at hit), date axis,
   provenance footer.
4. `scripts/strategy_reel/make_episode_vo.py` — all lines, two modes
   (dialogue windows for acts 2/5; clone TTS at event offsets for 3/4);
   emits per-act audio + any cut/timing props.
5. Assembly: render acts, ffmpeg concat (all 1080x1920@30, CRF-19),
   single continuous audio check (no voice collisions at joins), upload.

Sounds (10.4): existing remotion/public/audio ticks per countdown second,
coin on TP in both acts; reveal candles only.
