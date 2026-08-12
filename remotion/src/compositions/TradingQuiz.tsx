// TradingQuiz.tsx — "guess the next move" candlestick quiz reel (9:16, silent).
//
// The chart is presented as a live trading terminal on a physical screen —
// bezel, glass reflection, scanlines, grid, a price tag that tracks the last
// printed bar — rather than candles floating on a flat background. Nothing
// about the pattern data changes; this is purely the presentation layer, and
// it exists because a bare chart on black reads as a diagram, not as a feed
// someone is watching in real time.
//
// Layer stack (playbook §5 / motion-graphics rule 5), bottom to top:
//   bg mesh -> screen bezel -> plot (grid, level, candles, annotations)
//   -> glass reflection + scanlines -> overlay UI -> grade -> grain + vignette
//
// The answer is derived from an actual, nameable setup rather than a vibe:
// the fixture carries a real OHLC sequence, the level it tests, and the
// pattern that resolves it, so the reveal is teachable instead of a coin flip.
//
// Data is SYNTHETIC and labeled as such on-screen (see `footer`) — a pattern
// illustration, not a real market chart, and must never be presented as one.
//
// Engine, not a one-off: swap the fixture and the same composition renders a
// different pattern quiz. See scripts/ta_quiz/ and the ta-chart-quiz skill.
//
// Palette: green trading-terminal on near-black, matching TradingStyles — ruled
// grid, dotted world map, glowing candles. Earlier versions tinted the whole
// frame with `answerColor`, which read as generated-looking wash AND leaked the
// answer: a green countdown ring told you "BUY" before the timer ran out. The
// terminal green here is the house colour and carries no direction; only the
// candles, the price tag and the reveal badge mean bullish or bearish.
//
// The countdown ticks. Five escapement sounds, one per second, alternating
// tick/tock — see scripts/audio/make_tick.py. It is the only audio in the reel,
// and it is doing real work: on a silent feed the timer is easy to miss, and a
// clock is the one sound that says "you have until this stops" without a word.
import React from 'react';
import {AbsoluteFill, Audio, interpolate, random, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {z} from 'zod';
import {C, FONT} from '../slides/theme';
import {EASE, SPRINGS, fadeOf, cameraPushIn} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';

const candleSchema = z.object({
  o: z.number(),
  h: z.number(),
  l: z.number(),
  c: z.number(),
});

export const tradingQuizSchema = z.object({
  kick: z.string(),
  patternName: z.string(),
  levelPrice: z.number(),
  levelLabel: z.string(),
  /** Optional second reference line (e.g. previous-day LOW under a previous-day
   * HIGH). When present the y-frame is computed symmetrically around the setup
   * midpoint so BOTH lines are on screen from the start — and held static for
   * the whole reel, so the extra room cannot telegraph the answer's direction. */
  level2Price: z.number().optional(),
  level2Label: z.string().optional(),
  answer: z.enum(['BUY', 'SELL']),
  /** Overrides the badge text without changing the colour semantics. Real
   * tickers use this ("IT FELL 21%") so a hindsight reel never puts a literal
   * SELL call on a live name; synthetic patterns leave it unset. */
  answerLabel: z.string().optional(),
  answerLine: z.string(),
  ruleTitle: z.string(),
  ruleText: z.string(),
  /** Compliance strip under the chart. Optional since 2026-08-12 (owner
   * ruling): on the shipped post it sat under Instagram's comment row and was
   * unreadable, so it cost screen and delivered nothing. Absent -> not drawn. */
  footer: z.string().optional(),
  /** Index of the first candle that belongs to the REVEAL (everything before
   * it is the visible setup the viewer is quizzed on). */
  revealFrom: z.number(),
  /** Time-axis zoom. Present -> the reel runs the 900-frame two-act timeline:
   * open tight on a scrolling window playing forward in real time, widen as
   * time advances, pull back to the level's whole history, then return to the
   * decision zone. Absent -> the original 682-frame timeline, untouched.
   *
   * Indices are into THIS fixture's `candles` array, already rebased.
   * `live0` is the first bar the tape is allowed to PLAY; everything before it
   * is settled history that the camera reveals but never prints. The 6-month
   * cap on live0 is enforced by scripts/ta_quiz/find_anchored_level.py, because
   * watching three years of tape print is dead screen time. */
  zoom: z
    .object({
      live0: z.number(),
      breakout: z.number(),
      touches: z.array(
        z.object({i: z.number(), date: z.string(), inLive: z.boolean()})
      ),
      /** Headline for the justify act, e.g. "TESTED 10x SINCE AUG 2021". */
      historyLabel: z.string(),
      /** Beat overrides in absolute frames. Present when a narrated cut needs
       * the picture to follow the VOICE: the script is synthesised first, each
       * segment measured, and the acts sized to what was actually said. Sizing
       * the acts first and then writing to fit produced 75 seconds of narration
       * for a 36 second reel. */
      beats: z
        .object({
          LEVEL: z.number(), PATTERN: z.number(), ARROWS: z.number(),
          COUNT: z.number(), ANSWER: z.number(),
          RR: z.number(), RR_STOP: z.number(), RR_TARGET: z.number(), RR_ZONES: z.number(),
          REVEAL: z.number(), REVEAL_SPAN: z.number(),
          RULE: z.number(), ENDCARD: z.number(), TOTAL: z.number(),
          tape: z.number(), fastFrom: z.number(), fastTo: z.number(),
          deepTo: z.number(), justifyTo: z.number(),
          touchIn: z.number(), touchStep: z.number(),
        })
        .optional(),
    })
    .optional(),
  /** Chrome-bar identity. Real-data reels name the instrument here; the mark is
   * looked up at public/logos/<TICKER>.svg and falls back to a mono tile. */
  ticker: z.string().optional(),
  timeframe: z.string().optional(),
  dateRange: z.string().optional(),
  /** How many candles the highlight box encloses, counting back from the last
   * setup candle. A doji is 1, an engulfing is 2, a morning star is 3 —
   * boxing the wrong count visually mislabels the pattern. Multi-bar chart
   * formations use this to mark the completion bars, not the whole shape. */
  patternSpan: z.number().optional(),
  /** Small index chip above the title, e.g. "#14" — the library id. */
  indexLabel: z.string().optional(),
  /** Terminal chrome-bar label. Defaults to the pattern name; real-data reels
   * put the instrument and timeframe here ("INTC · DAILY"). */
  subject: z.string().optional(),
  /** The trade frame, drawn after the reveal. All four must be present together
   * or the risk/reward act is skipped entirely — half a trade frame (a target
   * with no stop) is worse than none, because it shows the upside and hides
   * what it cost to be wrong. */
  entry: z.number().optional(),
  stop: z.number().optional(),
  target: z.number().optional(),
  rrLabel: z.string().optional(),
  /** Fluid focus-tracking camera: the terminal glides in on the decision zone
   * for the countdown and releases wide when the answer lands, while the HUD
   * (hook, countdown ring, badge, rule card) stays unscaled. The countdown
   * ring relocates onto the chart's empty lower band so the tight framing has
   * somewhere to breathe. Off = the original flat slow push-in. */
  fluidCamera: z.boolean().optional(),
  candles: z.array(candleSchema).min(6),
  durationInFrames: z.number(),
});
export type TradingQuizProps = z.infer<typeof tradingQuizSchema>;

// ------------------------------------------------------------------ palette
/** Board theme: deep navy, ruled grid, cool neutral accent. Kept local to this
 * composition so the shared slide theme is untouched. */
const T = {
  bg: '#02070A',
  grid: 'rgba(0,224,130,0.055)',
  gridBold: 'rgba(0,224,130,0.115)',
  /** Neutral accent — carries no bullish/bearish meaning. Green here is the
   * house terminal colour, not a bullish signal; the answer badge is the only
   * thing that means direction. */
  ice: '#22E07E',
  steel: '#4E7A64',
  panelTop: '#04100C',
  panelBot: '#020806',
  edge: 'rgba(0,224,130,0.20)',
  up: '#00E676',
  down: '#FF3B30',
  /** Amber, matching the reference boards' level colour. Reserved for
   * structure — the line and its prior tests — so it never competes with the
   * up/down semantics of the tape. */
  level: '#E0A23B',
};

// Coarse landmass mask, drawn as a dot matrix behind the frame. Deliberately
// crude — at ~5% opacity it is texture, not a map to navigate by.
const WORLD = [
  '................................................................',
  '.......########....................#####........................',
  '....###############..........################################...',
  '...###############.........###############################......',
  '....#############........###############################.......',
  '.....###########........##############################.........',
  '......########..........############################...........',
  '.......######............#########.####..#########.............',
  '........####..............#######...##....######...............',
  '.........###...............#####...........####................',
  '.........####...............####............###................',
  '..........####...............###.............##................',
  '..........####................##..............#................',
  '...........###.................#..............................',
  '...........###.................##.............................',
  '...........###.................###...........#####.............',
  '...........##..................####.........########...........',
  '...........##..................####........##########..........',
  '............#..................###.........#########...........',
  '............#..................###..........#######............',
  '............#..................##............#####.............',
  '...............................##.............###.............',
  '................................#..............#..............',
  '................................................................',
  '....................######################......................',
  '................................................................',
];
const WORLD_DOTS = WORLD.flatMap((row, r) =>
  row.split('').flatMap((ch, c) =>
    ch === '#'
      ? [{x: (c + 0.5) * (1080 / WORLD[0].length), y: 300 + (r + 0.5) * (1120 / WORLD.length)}]
      : []
  )
);

// ---------------------------------------------------------------- timing
const DRAW_START = 40;
/** The setup always finishes printing here, whatever the bar count. Real charts
 * carry 60-80 bars of context; a fixed frames-per-bar would run a 62-bar window
 * past the countdown. Frames-per-bar is derived instead. */
const DRAW_END = 152;
// Kept <= DRAW_PER so exactly one bar is live at a time; a finished bar must
// never still be moving after the next one opens.
// Derived per fixture below; kept as the floor so a bar never prints instantly.
const CANDLE_FORM_MIN = 2;
/** Discrete price ticks a bar prints in. Deliberately few: real tape jumps, it
 * doesn't ease. Three hard steps read as a bar trading; a smooth grow reads as
 * an animation of a bar. */
const CANDLE_TICKS = 3;
const SCREEN_IN = 8;
const GRID_IN = 26;
const LEVEL_IN = 118;
const PATTERN_IN = 158;
const ARROWS_IN = 196;
const COUNT_START = 232;
// 5-second answer window: 5 digits at 1s each. Everything after the countdown
// is derived from it, so changing COUNT_N/COUNT_PER can't desync the reveal.
const COUNT_PER = 30;
const COUNT_N = 5;
const ANSWER_IN = COUNT_START + COUNT_PER * COUNT_N; // 382
const REVEAL_START = ANSWER_IN + 28;
/** The reveal is slower than it used to be, because it now carries sound: one
 * tone per candle. Twelve bars crammed into 38 frames was ten hits a second,
 * which is a machine gun rather than a tape. */
const REVEAL_SPAN = 84;
const REVEAL_END = REVEAL_START + REVEAL_SPAN;      // 494
/** Risk/reward act: stop and target draw, then the outcome resolves. */
const RR_IN = REVEAL_END + 8;                       // 502
const RR_ZONES_IN = RR_IN + 18;                     // 520
const RULE_IN = RR_IN + 92;                         // 594
/** Minimum duration the timeline needs; fixtures should meet or exceed it. */
export const TRADING_QUIZ_MIN_FRAMES = RULE_IN + 88; // -> 682

// ------------------------------------------------------- beat tables
/** Two orderings, not one timeline with an offset. The classic reel reveals
 * the outcome and THEN prices the trade; the zoom reel prices the trade FIRST
 * -- stop, target, then the range -- and only then lets the curve run, so the
 * viewer is committed to a level of risk before they find out whether it paid.
 * An offset could express the shift but not the reordering, which is why the
 * earlier ZOOM_SHIFT approach was replaced. */
type Beats = {
  LEVEL: number; PATTERN: number; ARROWS: number;
  COUNT: number; ANSWER: number;
  /** entry / stop / target draw as three separate explained beats */
  RR: number; RR_STOP: number; RR_TARGET: number; RR_ZONES: number;
  REVEAL: number; REVEAL_SPAN: number;
  RULE: number; ENDCARD: number; TOTAL: number;
};
const CLASSIC: Beats = {
  LEVEL: LEVEL_IN, PATTERN: PATTERN_IN, ARROWS: ARROWS_IN,
  COUNT: COUNT_START, ANSWER: ANSWER_IN,
  RR: RR_IN, RR_STOP: RR_IN, RR_TARGET: RR_IN, RR_ZONES: RR_ZONES_IN,
  REVEAL: REVEAL_START, REVEAL_SPAN,
  RULE: RULE_IN, ENDCARD: -1, TOTAL: TRADING_QUIZ_MIN_FRAMES,
};
const ZOOM: Beats = {
  LEVEL: 290, PATTERN: 330, ARROWS: 380,
  COUNT: 410, ANSWER: 560,
  RR: 600, RR_STOP: 665, RR_TARGET: 735, RR_ZONES: 800,
  REVEAL: 830, REVEAL_SPAN: 120,
  RULE: 960, ENDCARD: 1020, TOTAL: 1080,
};
export const TRADING_QUIZ_ZOOM_FRAMES = ZOOM.TOTAL; // -> 1080 / 36s
/** Act boundaries of the zoom prologue, in absolute frames. */
const Z_ACTS = {
  tape: DRAW_START,   // 40
  fastFrom: 170,
  fastTo: 240,
  deepTo: 310,
  justifyTo: 370,
  backTo: ZOOM.COUNT, // 410
};
const Z_TIGHT = 24;
/** Bars the real-time tape prints before it accelerates. */
const Z_TAPE_BARS = 22;
/** Bars on screen for the countdown, answer, trade frame and reveal. */
const Z_DECISION = 46;
/** Below this many px per bar a candle is a smudge, so the series cross-fades
 * to a close-line silhouette -- the same substitution PatternCard makes for
 * its mini cells. At the deep stop this reel runs ~1.2px/bar. */
const SILHOUETTE_PX = 3.5;
/** The justify act: prior tests of the level light one at a time. */
const TOUCH_IN_DEF = 314;
const TOUCH_STEP_DEF = 5;
const LOGO_TICKERS = ['AMD', 'DUOL', 'INTC', 'INTU', 'QBTS', 'SMCI'];

// ---------------------------------------------------------------- geometry
/** The physical screen the chart lives on. */
const SCREEN = {x: 34, y: 384, w: 1012, h: 958};
const CHROME_H = 56;
/** Candle plot area, inset inside the screen. The right gutter is left free
 * for the live price tag and, later, the BUY/SELL fork. */
const CHART = {x0: 78, x1: 754, y0: 492, y1: 1198};
const PAD = {lo: 4, hi: 4};
/** Clear band inside the screen, below the plot, where the pattern name sits. */
const PATTERN_LABEL_Y = 1278;

export const TradingQuiz: React.FC<TradingQuizProps> = (p) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const setup = p.candles.slice(0, p.revealFrom);
  const reveal = p.candles.slice(p.revealFrom);

  // ------------------------------------------------------------- timeline
  // Every act from the level draw onward reads `frame`, never `frame`. In zoom
  // mode that shifts the entire back half by the prologue's length in ONE
  // place, so the countdown / answer / reveal / risk-reward beats keep their
  // relative spacing and cannot drift apart. Legacy: frame === frame exactly.
  const zm = p.zoom;
  const B: Beats = zm ? {...ZOOM, ...(zm.beats ?? {})} : CLASSIC;
  // Prologue boundaries follow the same override, so a narrated cut can
  // stretch the tape or the pull-back without touching the composition.
  const ZB = {
    tape: zm?.beats?.tape ?? Z_ACTS.tape,
    fastFrom: zm?.beats?.fastFrom ?? Z_ACTS.fastFrom,
    fastTo: zm?.beats?.fastTo ?? Z_ACTS.fastTo,
    deepTo: zm?.beats?.deepTo ?? Z_ACTS.deepTo,
    justifyTo: zm?.beats?.justifyTo ?? Z_ACTS.justifyTo,
    backTo: B.COUNT,
  };
  const touchIn = zm?.beats?.touchIn ?? TOUCH_IN_DEF;
  const touchStep = zm?.beats?.touchStep ?? TOUCH_STEP_DEF;

  // ------------------------------------------------------------- viewport
  // The time axis. Legacy: the whole array, fixed, for the whole reel — which
  // is why only price could ever move. Zoom: a bar-index window [v0,v1] that
  // opens tight on the oldest playable bars, scrolls forward with the tape,
  // widens as time advances, pulls back across the level's whole history, then
  // returns to the decision zone.
  //
  // Chronology is the constraint that shapes this. The tape plays FORWARD out
  // of the past, so the window may only ever widen to expose OLDER bars. It can
  // never print a recent bar and then reveal an older one — that is a tape
  // running backwards, and it is the thing that made the first sketch wrong.
  const nAll = p.candles.length;
  const lastSetup = p.revealFrom - 1;
  const live0 = zm ? Math.max(0, Math.min(zm.live0, lastSetup)) : 0;
  /** First bar the tape is allowed to print. Everything before it is settled
   * history the camera reveals but never plays — the 6-month rule, enforced
   * upstream in scripts/ta_quiz/find_anchored_level.py. */
  const playFrom = zm ? Math.min(live0 + Z_TIGHT, lastSetup) : 0;

  const zStops = [ZB.tape, ZB.fastFrom, ZB.fastTo, ZB.deepTo, ZB.justifyTo, ZB.backTo];
  const zEase = {easing: EASE.cruise, extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
  // Right edge follows the newest printed bar, then holds with room to its
  // right for the reveal to print into.
  const v1 = zm
    ? interpolate(frame, zStops,
        [playFrom, playFrom + Z_TAPE_BARS, lastSetup + 1, lastSetup + 1, lastSetup + 1, nAll], zEase)
    : nAll;
  const vW = zm
    ? interpolate(frame, zStops,
        [Z_TIGHT, Z_TIGHT, lastSetup + 1 - live0, lastSetup + 1, lastSetup + 1, Z_DECISION], zEase)
    : nAll;
  const v0 = zm ? v1 - vW : 0;

  // ------------------------------------------------------- print schedule
  // Absolute frame at which bar `i` opens. Two rates in zoom mode: a real-time
  // tape while the window is tight, then a fast-forward as it widens. The
  // acceleration is not decoration — 126 bars at tape speed is 14 seconds we
  // do not have, and speeding up IS what "time is passing" looks like.
  const REVEAL_PER = Math.max(1, B.REVEAL_SPAN / Math.max(1, reveal.length));
  const DRAW_PER = Math.max(1, (DRAW_END - DRAW_START) / Math.max(1, setup.length));
  const ffBars = Math.max(1, lastSetup - playFrom - Z_TAPE_BARS + 1);
  const appearOf = (i: number): number => {
    if (i >= p.revealFrom) return B.REVEAL + (i - p.revealFrom) * REVEAL_PER;
    if (!zm) return DRAW_START + i * DRAW_PER;
    if (i < playFrom) return -1e6;                     // settled: never prints
    if (i <= playFrom + Z_TAPE_BARS)
      return ZB.tape + (i - playFrom) * ((ZB.fastFrom - ZB.tape) / Z_TAPE_BARS);
    return ZB.fastFrom + (i - playFrom - Z_TAPE_BARS) * ((ZB.fastTo - ZB.fastFrom) / ffBars);
  };
  const CANDLE_FORM = Math.max(CANDLE_FORM_MIN, Math.round(DRAW_PER));
  const formOf = (i: number): number => {
    if (i >= p.revealFrom) return Math.max(CANDLE_FORM_MIN, Math.round(REVEAL_PER));
    if (!zm) return CANDLE_FORM;
    return Math.max(CANDLE_FORM_MIN, Math.round(appearOf(i + 1) - appearOf(i)));
  };

  // The y-scale must NOT span the reveal while the viewer is still guessing.
  // Scaling to every candle up front leaves empty headroom on whichever side
  // price is about to travel, and that empty space telegraphs the answer just
  // as surely as a coloured countdown ring did. So: frame the setup with
  // SYMMETRIC padding until the reveal starts, then ease out to the full range
  // as the new bars print — which is what a real chart does when price leaves
  // the visible window anyway.
  // In zoom mode the frame is fitted to the bars actually ON SCREEN AND ALREADY
  // PRINTED. Both halves of that matter: fitting to off-screen bars would make
  // a 5-year pull-back unreadable, and fitting to bars that have not printed
  // yet would let a future bar move the axis — the same leak the symmetric
  // padding below exists to prevent.
  const yBars = zm
    ? p.candles.filter((_, i) => i >= Math.floor(v0) && i <= Math.ceil(v1) && appearOf(i) <= frame)
    : setup;
  const ySrc = yBars.length ? yBars : setup.slice(0, 1);
  const sLo = Math.min(...ySrc.map((k) => k.l));
  const sHi = Math.max(...ySrc.map((k) => k.h));
  const sPad = (sHi - sLo) * 0.16;
  // The reveal eases out to the DECISION ZONE's range, not the whole array —
  // in zoom mode the array carries five years of history whose extremes have
  // nothing to do with the trade being revealed.
  const fSrc = zm ? p.candles.slice(Math.max(0, nAll - Z_DECISION)) : p.candles;
  const fLo = Math.min(...fSrc.map((k) => k.l)) - PAD.lo;
  const fHi = Math.max(...fSrc.map((k) => k.h)) + PAD.hi;
  const zoomOut = interpolate(frame, [B.REVEAL - 4, B.REVEAL + 24], [0, 1], {
    easing: EASE.cruise,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const lo1 = (sLo - sPad) + (fLo - (sLo - sPad)) * zoomOut;
  const hi1 = (sHi + sPad) + (fHi - (sHi + sPad)) * zoomOut;
  // With a second line the frame is "yesterday's range plus today's action":
  // symmetric about the setup midpoint, wide enough for both lines and every
  // bar, and STATIC for the whole reel. Symmetry is what keeps the extra room
  // from telegraphing which way the reveal travels — reveal extents enter the
  // max() too, but they widen BOTH sides equally.
  const mid = (sLo + sHi) / 2;
  const half =
    Math.max(
      sHi - mid,
      mid - sLo,
      Math.abs(p.levelPrice - mid),
      Math.abs((p.level2Price ?? p.levelPrice) - mid),
      fHi - PAD.hi - mid,
      mid - (fLo + PAD.lo),
    ) * 1.1;
  const lo = p.level2Price !== undefined ? mid - half : lo1;
  const hi = p.level2Price !== undefined ? mid + half : hi1;
  const priceToY = (v: number) => CHART.y1 - ((v - lo) / (hi - lo)) * (CHART.y1 - CHART.y0);

  const slot = (CHART.x1 - CHART.x0) / Math.max(1, v1 - v0);
  const bodyW = Math.min(24, Math.max(2.5, slot * 0.62));
  // Wick weight tracks body width — a 2.5px wick on a 5px body reads as a blob.
  const wickW = Math.min(2.5, Math.max(1.1, bodyW * 0.3));
  const cx = (i: number) => CHART.x0 + (i - v0 + 0.5) * slot;
  /** 0 = candles, 1 = close-line silhouette. Below SILHOUETTE_PX a candle is
   * fewer pixels wide than its own glow and the field reads as a green smear;
   * the silhouette is what a chart at that scale is actually for. */
  const silh = interpolate(slot, [SILHOUETTE_PX, SILHOUETTE_PX * 2.2], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const isDown = p.answer === 'SELL';
  const answerColor = isDown ? T.down : T.up;

  // Camera. Legacy: one slow push-in with an emphasis hit when the answer
  // lands. Fluid: a keyframed focus-tracking move — settle in while the tape
  // prints, glide INTO the decision zone as the fork appears, hold tight
  // through the countdown, release wide the moment the answer lands, then
  // breathe through the reveal and the rule card. Zooming about a focus point
  // f is translate((1-s)(f-center)) scale(s), which keeps every frame edge
  // covered for any s >= 1. The focus constants are tuned against this layout
  // so the level labels, fork arrows and lower-band text all survive the tight
  // phase — move them and re-check those collisions frame by frame.
  const legacyZoom = cameraPushIn(frame, p.durationInFrames, {base: 0.035, hitFrame: B.ANSWER, hitAmount: 0.02});
  // In zoom mode the viewport IS the camera; a transform scale on top of it
  // would fight the bar-index window and magnify strokes the viewport just
  // resized. Fixtures that zoom leave fluidCamera off.
  const fluid = p.fluidCamera === true;
  const camS = fluid
    ? interpolate(
        frame,
        [0, DRAW_END, B.PATTERN, B.ARROWS + 16, B.ANSWER, B.ANSWER + 44, (B.REVEAL + B.REVEAL_SPAN) + 6, B.RULE, p.durationInFrames],
        [1.0, 1.045, 1.045, 1.18, 1.19, 1.02, 1.06, 1.03, 1.045],
        {easing: EASE.cruise, extrapolateRight: 'clamp'}
      )
    : 1;
  const camFx = fluid
    ? interpolate(frame, [B.PATTERN, B.ARROWS + 16, B.ANSWER, B.ANSWER + 44], [540, 220, 220, 540], {
        easing: EASE.cruise,
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 540;
  const camFy = fluid
    ? interpolate(frame, [B.PATTERN, B.ARROWS + 16, B.ANSWER, B.ANSWER + 44], [960, 1010, 1010, 960], {
        easing: EASE.cruise,
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 960;
  const chartT = fluid
    ? `translate(${(1 - camS) * (camFx - 540)}px, ${(1 - camS) * (camFy - 960)}px) scale(${camS})`
    : `scale(${legacyZoom})`;
  const uiT = fluid ? undefined : `scale(${legacyZoom})`;

  // ------------------------------------------------------------ hook card
  const hookP = spring({frame, fps, config: SPRINGS.hero});
  const hookShift = interpolate(frame, [DRAW_START, DRAW_START + 18], [0, -22], {
    easing: EASE.cruise,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // ---------------------------------------------------------- the screen
  const screenP = spring({frame: frame - SCREEN_IN, fps, config: SPRINGS.heavy});
  // Panel boot: a couple of flickers before it settles, like a display waking.
  const boot = frame < SCREEN_IN + 16 ? (frame % 3 === 0 ? 0.72 : 1) : 1;

  // ------------------------------------------------------------ the grid
  const gridP = interpolate(frame, [GRID_IN, GRID_IN + 26], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  // ~5 horizontal rules at round prices — enough to read depth, not enough to
  // compete with the candles.
  const step = (hi - lo) / 5;
  const gridLines = Array.from({length: 6}, (_, i) => lo + step * i);

  // The price axis hands the right gutter over to the BUY/SELL fork.
  const axisOut = interpolate(frame, [B.ARROWS - 12, B.ARROWS + 2], [1, 0.12], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // ----------------------------------------------------------- the level(s)
  // One reference line, or the previous-day pair. The second line draws a beat
  // after the first so they read as two decisions, not one stamp.
  const levels = [
    {price: p.levelPrice, label: p.levelLabel, at: B.LEVEL},
    ...(p.level2Price !== undefined
      ? [{price: p.level2Price, label: p.level2Label ?? '', at: B.LEVEL + 10}]
      : []),
  ];
  // Once the trade frame draws, the reference line has done its job and its
  // label sits right on top of the STOP tag. Fade it out rather than stack
  // them. Without a trade frame there is nothing to make room for — and on a
  // two-line reel the lines ARE the lesson — so they stay lit.
  const levelOut =
    p.entry !== undefined && p.stop !== undefined && p.target !== undefined
      ? interpolate(frame, [B.RR - 4, B.RR + 16], [1, 0.18], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : 1;

  // --------------------------------------------------- justify headline
  // Rides the real frame: it belongs to the prologue, not to the shifted
  // back half. In and out inside the deep + justify acts.
  const historyP = interpolate(
    frame,
    [ZB.deepTo - 44, ZB.deepTo - 20, ZB.justifyTo + 6, ZB.justifyTo + 26],
    [0, 1, 1, 0],
    {easing: EASE.cruise, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // -------------------------------------------------------- pattern frame
  const patP = spring({frame: frame - B.PATTERN, fps, config: SPRINGS.pop});
  const patPulse = 1 + Math.sin(Math.max(0, frame - B.PATTERN) / 7) * 0.03;

  // ------------------------------------------------------------- arrows
  const arrowsP = spring({frame: frame - B.ARROWS, fps, config: SPRINGS.pop});
  const arrowsOut = interpolate(frame, [B.ANSWER, B.ANSWER + 14], [1, 0], {
    easing: EASE.exit,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const winnerOut = interpolate(frame, [B.REVEAL - 6, B.REVEAL + 8], [1, 0], {
    easing: EASE.exit,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // ----------------------------------------------------------- countdown
  const countIdx = Math.floor((frame - B.COUNT) / COUNT_PER);
  const countActive = frame >= B.COUNT && frame < B.ANSWER;
  const countDigit = COUNT_N - countIdx;
  const countLocal = (frame - B.COUNT) % COUNT_PER;
  const countP = spring({frame: countLocal, fps, config: SPRINGS.hero});
  // Ring drains over the whole 5s window, not per digit — reads as one timer.
  const countFrac = Math.min(1, Math.max(0, (frame - B.COUNT) / (COUNT_PER * COUNT_N)));

  // ------------------------------------------------------------- answer
  const answerP = spring({frame: frame - B.ANSWER, fps, config: SPRINGS.hero});
  const ruleP = spring({frame: frame - B.RULE, fps, config: SPRINGS.heavy});


  // ------------------------------------------------- live price tag
  // Tracks the last bar printed so far. Hands off to the BUY/SELL fork when
  // the fork appears — they'd otherwise fight for the same gutter. Derived by
  // walking the schedule rather than dividing by a rate, because in zoom mode
  // there are two rates and a settled prefix that never prints at all.
  const revealedCount = Math.min(
    reveal.length,
    Math.max(0, Math.floor((frame - B.REVEAL) / REVEAL_PER) + 1)
  );
  let drawnLast = -1;
  for (let i = lastSetup; i >= 0; i--) {
    if (appearOf(i) <= frame) {
      drawnLast = i;
      break;
    }
  }
  const lastIdx = frame >= B.REVEAL && revealedCount > 0
    ? p.revealFrom + revealedCount - 1
    : Math.max(0, drawnLast);
  const lastK = p.candles[lastIdx];
  // Same tick maths the bar itself uses, so the tag reads the live print rather
  // than jumping straight to a close that hasn't happened yet.
  const liveClose = (() => {
    if (!lastK) return 0;
    const raw = (frame - appearOf(lastIdx)) / formOf(lastIdx);
    const step = Math.min(CANDLE_TICKS, Math.ceil(Math.min(1, Math.max(0, raw)) * CANDLE_TICKS));
    if (step >= CANDLE_TICKS) return lastK.c;
    const f = step / CANDLE_TICKS;
    const hN = lastK.o + (lastK.h - lastK.o) * Math.min(1, f * 1.22);
    const lN = lastK.o + (lastK.l - lastK.o) * Math.min(1, f * 1.22);
    const drift = (random(`k${lastIdx}t${step}`) - 0.5) * (lastK.h - lastK.l) * 0.7;
    return Math.max(lN, Math.min(hN, lastK.o + (lastK.c - lastK.o) * f + drift));
  })();
  const liveUp = liveClose >= (lastK?.o ?? 0);
  // Fade-in rides the real frame (the tape starts at DRAW_START either way);
  // the hand-off and the reveal ride the shifted timeline. The price tag is
  // also hidden while the field is a silhouette — at 1.2px/bar there is no
  // "last bar" to pin it to, and it would sit on a smear.
  const tagOpacity =
    (interpolate(frame, [DRAW_START + 6, DRAW_START + 20], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) *
      interpolate(frame, [B.ARROWS - 10, B.ARROWS + 4], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) +
      interpolate(frame, [B.REVEAL, B.REVEAL + 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})) *
    (1 - silh);

  // A bar prints the way a live one actually does, not the way an animation
  // does: it opens, ticks in hard discrete jumps, wanders inside its own range,
  // flips colour when the last trade crosses the open, and only snaps to the
  // real close on the final tick. No easing, no fade-in — those are what made
  // the old version read as a diagram assembling itself.
  const renderCandle = (k: z.infer<typeof candleSchema>, i: number) => {
    const raw = (frame - appearOf(i)) / formOf(i);
    if (raw <= 0) return null;
    const step = Math.min(CANDLE_TICKS, Math.ceil(Math.min(1, raw) * CANDLE_TICKS));
    const settled = step >= CANDLE_TICKS;
    const f = step / CANDLE_TICKS;

    // Wicks only ever widen — a bar's high can't come back down once traded.
    const hNow = k.o + (k.h - k.o) * Math.min(1, f * 1.22);
    const lNow = k.o + (k.l - k.o) * Math.min(1, f * 1.22);

    // Mid-bar the last trade wanders inside the range; the closing tick lands
    // exactly on `c`. Seeded off (bar, tick) so every render is identical.
    const drift = (random(`k${i}t${step}`) - 0.5) * (k.h - k.l) * 0.7;
    const cNow = settled
      ? k.c
      : Math.max(lNow, Math.min(hNow, k.o + (k.c - k.o) * f + drift));

    // Colour tracks the live print, so a bar can flip red/green while it trades
    // and only commits on the close — which is what a real chart does.
    const col = cNow >= k.o ? C.emerald : C.redHot;
    const x = cx(i);
    const yTop = priceToY(Math.max(k.o, cNow));
    const yBot = priceToY(Math.min(k.o, cNow));
    return (
      <g
        key={i}
        opacity={candleOp}
        style={{filter: `drop-shadow(0 0 ${settled ? 6 : 11}px ${col}${settled ? '77' : 'cc'})`}}
      >
        <line x1={x} x2={x} y1={priceToY(hNow)} y2={priceToY(lNow)} stroke={col} strokeWidth={wickW} />
        <rect x={x - bodyW / 2} y={yTop} width={bodyW} height={Math.max(2, yBot - yTop)} rx={2} fill={col} />
      </g>
    );
  };

  // ------------------------------------------------- what is on screen now
  // Only bars inside the window are built. At the deep stop the array holds
  // 589 bars; rendering all of them with drop-shadow filters every frame is
  // minutes of render time for pixels nobody sees.
  const visFrom = Math.max(0, Math.floor(v0) - 1);
  const visTo = Math.min(nAll - 1, Math.ceil(v1) + 1);
  const candleOp = 1 - silh;
  /** The wide-zoom stand-in: one polyline through the closes of every printed
   * bar in view. This is what a chart at 1.2px/bar is for — the SHAPE, which
   * is the whole argument the pull-back is making. */
  const silhouette =
    silh > 0.02
      ? p.candles
          .slice(visFrom, visTo + 1)
          .map((k, j) => ({i: visFrom + j, k}))
          .filter(({i}) => appearOf(i) <= frame)
          .map(({i, k}) => `${cx(i).toFixed(1)},${priceToY(k.c).toFixed(1)}`)
          .join(' ')
      : '';

  // The candles that form the pattern, counting back from the last setup bar.
  const span = Math.max(1, Math.min(p.patternSpan ?? 2, p.revealFrom));
  const pA = p.revealFrom - span;
  const pB = p.revealFrom - 1;
  const patWRaw = slot * (span + 0.16);
  const patW = Math.max(patWRaw, 34);           // stays visible on thin slots
  const patX = cx(pA) - slot * 0.58 - (patW - patWRaw) / 2;
  const boxed = p.candles.slice(pA, pB + 1);
  const patTop = priceToY(Math.max(...boxed.map((k) => k.h))) - 16;
  const patBot = priceToY(Math.min(...boxed.map((k) => k.l))) + 16;

  // ------------------------------------------------- the trade frame
  // Present only if all four fields are set. `tpBar` is the first REVEAL bar
  // whose high actually reaches the target — derived from the data, not stated
  // in the fixture, so the coins cannot fire on a bar that never got there.
  const hasRR =
    p.entry !== undefined && p.stop !== undefined && p.target !== undefined &&
    p.entry > p.stop && p.target > p.entry;
  const tpBar = hasRR
    ? reveal.findIndex((k) => k.h >= (p.target as number))
    : -1;
  // ------------------------------------------- building the trade, in words
  // Numbers here are FORMATTED from the fixture, never restated by hand — the
  // risk and the reward have to stay arithmetically tied to entry/stop/target
  // or the caption can drift away from the lines drawn beside it.
  const riskAmt = hasRR ? (p.entry as number) - (p.stop as number) : 0;
  const rewardAmt = hasRR ? (p.target as number) - (p.entry as number) : 0;
  const setupCaps = hasRR
    ? [
        {
          at: B.RR,
          col: '#D8E6DE',
          head: `ENTRY ${(p.entry as number).toFixed(2)}`,
          body: 'Buy the close that reclaimed the rim. The level the whole base was built against is now underneath price.',
        },
        {
          at: B.RR_STOP,
          col: T.down,
          head: `STOP ${(p.stop as number).toFixed(2)}`,
          body: `Under the handle's low. If price falls back into the cup the setup never happened — so that is where you admit it. Being wrong costs ${riskAmt.toFixed(2)}.`,
        },
        {
          at: B.RR_TARGET,
          col: T.up,
          head: `TARGET ${(p.target as number).toFixed(2)}`,
          body: `Risk appetite sets this, not hope: ${p.rrLabel ?? '1:2'} means aim ${rewardAmt.toFixed(2)} for the ${riskAmt.toFixed(2)} at stake. Chosen before the outcome is known.`,
        },
        {
          at: B.RR_ZONES,
          col: T.ice,
          head: 'RANGE SET',
          body: 'Both ends are on the chart. Now let it run.',
        },
      ]
    : [];
  const capIdx = setupCaps.reduce((acc, c, i) => (frame >= c.at ? i : acc), -1);
  const setupCap =
    capIdx >= 0 && frame < B.REVEAL
      ? {
          ...setupCaps[capIdx],
          op:
            interpolate(frame, [setupCaps[capIdx].at, setupCaps[capIdx].at + 12], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }) *
            interpolate(frame, [B.REVEAL - 18, B.REVEAL - 2], [1, 0], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
        }
      : null;

  const rrP = spring({frame: frame - B.RR, fps, config: SPRINGS.heavy});
  const zonesP = interpolate(frame, [B.RR_ZONES, B.RR_ZONES + 22], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  // The payoff lands when the zone fill sweeps past the winning bar.
  // The tick fires on the frame the winning bar PRINTS, not on a fixed beat.
  // Anchoring it to a constant would let it land before or after the bar that
  // earned it, which is the same defect as a sound arriving two frames late.
  const payoutAt = tpBar >= 0 ? B.REVEAL + tpBar * REVEAL_PER : B.RR_ZONES + 26;
  const checkT = frame - payoutAt;
  const checkS = spring({frame: checkT, fps, config: SPRINGS.pop});
  const checkO = interpolate(checkT, [0, 5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const oX = cx(p.revealFrom - 1) + slot * 0.8;
  const oY = priceToY(p.candles[p.revealFrom - 1].c);

  const Arrow: React.FC<{dir: 'up' | 'down'; label: string; color: string; op: number}> = ({
    dir,
    label,
    color,
    op,
  }) => {
    const dy = dir === 'up' ? -118 : 118;
    const ex = oX + 132;
    const ey = oY + dy;
    return (
      <g opacity={op} style={{filter: `drop-shadow(0 0 12px ${color}aa)`}}>
        <line x1={oX} y1={oY} x2={ex} y2={ey} stroke={color} strokeWidth={9} strokeLinecap="round" />
        <polygon
          points={`${ex + 28},${ey + (dir === 'up' ? -12 : 12)} ${ex - 8},${ey - 19} ${ex - 8},${ey + 19}`}
          fill={color}
          transform={`rotate(${dir === 'up' ? -36 : 36} ${ex} ${ey})`}
        />
        <text
          x={ex + 42}
          y={ey + (dir === 'up' ? -4 : 16)}
          fill={C.ink}
          fontFamily={FONT.display}
          fontWeight={700}
          fontSize={46}
        >
          {label}
        </text>
      </g>
    );
  };

  return (
    <AbsoluteFill style={{background: T.bg, fontFamily: FONT.body}}>
      {/* ------------------------------------------------- 1. background
       * Dotted world map + ruled grid on near-black. Soft blurred colour blobs
       * were what made the old frame read as machine-made filler; a drafting
       * grid reads as something laid out on purpose. It drifts a few px so the
       * plate isn't dead, and never carries the answer's colour. */}
      <AbsoluteFill>
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
          {WORLD_DOTS.map((d, i) => (
            <circle
              key={i}
              cx={d.x}
              cy={d.y}
              r={2.1}
              fill={T.up}
              opacity={0.05 + Math.sin(frame / 40 + i * 0.35) * 0.018}
            />
          ))}
        </svg>
        <svg
          width={1080}
          height={1920}
          style={{
            position: 'absolute',
            inset: 0,
            transform: `translate(${Math.sin(frame / 220) * 5}px, ${Math.cos(frame / 260) * 6}px)`,
          }}
        >
          {Array.from({length: 14}, (_, i) => i * 90).map((x, i) => (
            <line
              key={`v${x}`}
              x1={x}
              x2={x}
              y1={-40}
              y2={1960}
              stroke={i % 3 === 0 ? T.gridBold : T.grid}
              strokeWidth={1}
            />
          ))}
          {Array.from({length: 23}, (_, i) => i * 90).map((y, i) => (
            <line
              key={`h${y}`}
              x1={-40}
              x2={1120}
              y1={y}
              y2={y}
              stroke={i % 3 === 0 ? T.gridBold : T.grid}
              strokeWidth={1}
            />
          ))}
        </svg>
        {/* single cool wash so the grid isn't uniformly flat — neutral, never
         * keyed to BUY/SELL */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(120% 55% at 50% 6%, rgba(0,224,130,0.11), transparent 60%),' +
              'radial-gradient(110% 50% at 20% 104%, rgba(0,224,130,0.09), transparent 62%),' +
              'radial-gradient(110% 50% at 85% 104%, rgba(255,59,48,0.06), transparent 62%)',
          }}
        />
      </AbsoluteFill>

      {/* HUD layer — hook, countdown, answer. zIndex keeps it painted above
       * the chart group even though it comes first in the DOM; in fluid mode
       * it does not ride the camera, so the text stays screen-fixed the way
       * the reference reels hold their titles. */}
      <AbsoluteFill style={{transform: uiT, zIndex: 2}}>
        {/* ---------------------------------------------------- 2. hook */}
        <div
          style={{
            position: 'absolute',
            top: 112 + hookShift,
            left: 0,
            right: 0,
            textAlign: 'center',
            opacity: fadeOf(hookP),
            transform: `scale(${interpolate(hookP, [0, 1], [0.86, 1])})`,
          }}
        >
          {/* index chip — the reference boards number every card */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              fontFamily: FONT.mono,
              fontWeight: 700,
              fontSize: 21,
              letterSpacing: 4,
              color: T.ice,
              border: `1px solid ${T.edge}`,
              borderRadius: 999,
              padding: '6px 18px',
              marginBottom: 14,
            }}
          >
            {p.indexLabel ? <span style={{color: T.steel}}>{p.indexLabel}</span> : null}
            {p.ticker ? `${p.ticker.toUpperCase()} · ${p.timeframe ?? ''}`.trim() : 'MAYA LAB'}
          </div>
          <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 76, color: C.ink, letterSpacing: -1}}>
            {p.kick.split(' ')[0]}{' '}
            <span style={{color: T.ice}}>{p.kick.split(' ').slice(1).join(' ')}</span>
          </div>
        </div>

        {/* ------------------------------------------------ 3. countdown */}
        {countActive ? (
          <div
            style={{
              position: 'absolute',
              // Fluid camera: the ring floats over the chart's empty band above
              // the lower reference line (the reference reels do exactly this)
              // because the tight framing leaves no room in the top band.
              top: fluid ? 1000 : 250,
              left: 0,
              right: 0,
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            <div style={{position: 'relative', width: 132, height: 132}}>
              <svg width={132} height={132} style={{position: 'absolute', inset: 0, transform: 'rotate(-90deg)'}}>
                <circle cx={66} cy={66} r={58} fill="none" stroke={T.edge} strokeWidth={6} />
                {/* neutral on purpose: a green ring would announce "BUY" */}
                <circle
                  cx={66}
                  cy={66}
                  r={58}
                  fill="none"
                  stroke={T.ice}
                  strokeWidth={6}
                  strokeLinecap="round"
                  strokeDasharray={2 * Math.PI * 58}
                  strokeDashoffset={2 * Math.PI * 58 * countFrac}
                  style={{filter: `drop-shadow(0 0 10px ${T.ice}cc)`}}
                />
              </svg>
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: FONT.mono,
                  fontWeight: 800,
                  fontSize: 68,
                  color: C.ink,
                  opacity: fadeOf(countP),
                  transform: `scale(${interpolate(countP, [0, 1], [1.45, 1])})`,
                }}
              >
                {countDigit}
              </div>
            </div>
          </div>
        ) : null}

        {/* --------------------------------------------------- 4. answer */}
        {frame >= B.ANSWER ? (
          <div
            style={{
              position: 'absolute',
              top: 262,
              left: 0,
              right: 0,
              textAlign: 'center',
              opacity: fadeOf(answerP),
              transform: `scale(${interpolate(answerP, [0, 1], [0.7, 1])})`,
            }}
          >
            <div
              style={{
                display: 'inline-block',
                fontFamily: FONT.display,
                fontWeight: 700,
                fontSize: 74,
                color: T.bg,
                background: answerColor,
                padding: '8px 48px',
                borderRadius: 999,
                boxShadow: `0 0 70px ${answerColor}88`,
              }}
            >
              {p.answerLabel ?? p.answer}
            </div>
          </div>
        ) : null}

        {/* The one-liner that justifies the answer. It lives in the lower band,
         * not under the badge — under the badge it sits at y≈376, exactly where
         * the screen panel starts, and was painted over on every render.
         *
         * On a zoom reel it must wait for the REVEAL. It states the outcome
         * ("+3.7% banked in 12 sessions"), so showing it while the trade is
         * still being priced both collides with the setup captions AND hands
         * the viewer the result before a single reveal bar has printed. */}
        {frame >= (zm ? B.REVEAL : B.ANSWER) ? (
          <div
            style={{
              position: 'absolute',
              top: 1418,
              left: 70,
              right: 70,
              textAlign: 'center',
              opacity:
                fadeOf(zm ? spring({frame: frame - B.REVEAL, fps, config: SPRINGS.hero}) : answerP) *
                interpolate(frame, [B.RULE - 16, B.RULE - 2], [1, 0], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                }),
              transform: `translateY(${interpolate(answerP, [0, 1], [22, 0])}px)`,
            }}
          >
            <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 46, lineHeight: 1.24, color: C.ink}}>
              {p.answerLine}
            </div>
          </div>
        ) : null}
      </AbsoluteFill>

      {/* chart layer — the terminal and its plot ride the camera (fluid focus
       * glide, or the legacy push-in) while the HUD above stays put. */}
      <AbsoluteFill style={{transform: chartT, zIndex: 1}}>
        {/* --------------------------------------------- 5. the terminal */}
        <div
          style={{
            position: 'absolute',
            left: SCREEN.x,
            top: SCREEN.y,
            width: SCREEN.w,
            height: SCREEN.h,
            borderRadius: 30,
            opacity: fadeOf(screenP) * boot,
            transform: `translateY(${interpolate(screenP, [0, 1], [26, 0])}px)`,
            background: `linear-gradient(180deg, ${T.panelTop} 0%, ${T.panelBot} 100%)`,
            border: `1px solid ${T.edge}`,
            boxShadow: `0 40px 100px -30px #000, inset 0 1px 0 rgba(255,255,255,.05), 0 0 70px ${T.up}18`,
            overflow: 'hidden',
          }}
        >
          {/* chrome bar */}
          <div
            style={{
              height: CHROME_H,
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '0 22px',
              borderBottom: `1px solid ${T.edge}`,
              background: 'rgba(0,224,130,.045)',
            }}
          >
            {[T.down, T.level, T.up].map((col) => (
              <div key={col} style={{width: 11, height: 11, borderRadius: 999, background: col, opacity: 0.62}} />
            ))}
            {/* Instrument identity. A real ticker gets its mark when one exists
              * at public/logos/<TICKER>.svg, and a typographic tile when it does
              * not — which is most of them, and reads as a terminal either way.
              * Without a ticker this falls back to the original lab label. */}
            {p.ticker ? (
              <div style={{marginLeft: 12, display: 'flex', alignItems: 'center', gap: 11}}>
                {LOGO_TICKERS.includes(p.ticker.toUpperCase()) ? (
                  <img
                    src={staticFile(`logos/${p.ticker.toUpperCase()}.svg`)}
                    width={30}
                    height={30}
                    style={{display: 'block', borderRadius: 6}}
                  />
                ) : (
                  <div
                    style={{
                      padding: '3px 9px',
                      border: `1px solid ${T.edge}`,
                      borderRadius: 7,
                      background: 'rgba(0,224,130,.07)',
                      fontFamily: FONT.mono,
                      fontWeight: 800,
                      fontSize: 19,
                      letterSpacing: 1,
                      color: T.ice,
                    }}
                  >
                    {p.ticker.toUpperCase()}
                  </div>
                )}
                <div style={{fontFamily: FONT.mono, fontSize: 19, letterSpacing: 2, color: T.steel}}>
                  {[p.ticker.toUpperCase(), p.timeframe, p.dateRange].filter(Boolean).join(' · ')}
                </div>
              </div>
            ) : (
              <div
                style={{
                  marginLeft: 12,
                  fontFamily: FONT.mono,
                  fontSize: 19,
                  letterSpacing: 2,
                  color: T.steel,
                }}
              >
                MAYA LAB — {p.subject ?? p.patternName}
              </div>
            )}
            <div style={{marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8}}>
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: 999,
                  background: T.up,
                  opacity: 0.4 + Math.sin(frame / 8) * 0.35,
                }}
              />
              <div style={{fontFamily: FONT.mono, fontSize: 17, letterSpacing: 2, color: T.steel}}>LIVE</div>
            </div>
          </div>

          {/* scanlines — very low contrast, sells "display" without banding */}
          <AbsoluteFill
            style={{
              pointerEvents: 'none',
              background: 'repeating-linear-gradient(0deg, rgba(255,255,255,.020) 0px, rgba(255,255,255,.020) 1px, transparent 1px, transparent 4px)',
            }}
          />
          {/* glass reflection sweeping slowly across the panel */}
          <AbsoluteFill
            style={{
              pointerEvents: 'none',
              background: `linear-gradient(115deg, transparent ${20 + Math.sin(frame / 150) * 12}%, rgba(255,255,255,.045) ${38 + Math.sin(frame / 150) * 12}%, transparent ${56 + Math.sin(frame / 150) * 12}%)`,
            }}
          />
        </div>

        {/* ------------------------------------- 6. plot (above the glass) */}
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
          {/* grid */}
          {gridP > 0
            ? gridLines.map((v, i) => (
                <g key={`g${i}`} opacity={gridP * 0.5}>
                  <line
                    x1={CHART.x0 - 6}
                    x2={SCREEN.x + SCREEN.w - 26}
                    y1={priceToY(v)}
                    y2={priceToY(v)}
                    stroke={T.edge}
                    strokeWidth={1}
                  />
                  <text
                    x={SCREEN.x + SCREEN.w - 20}
                    y={priceToY(v) - 6}
                    fill={T.steel}
                    fontFamily={FONT.mono}
                    fontSize={16}
                    textAnchor="end"
                    opacity={0.75 * axisOut}
                  >
                    {v.toFixed(0)}
                  </text>
                </g>
              ))
            : null}

          {/* reference line(s) */}
          {levels.map((lv) => {
            const lp = interpolate(frame, [lv.at, lv.at + 22], [0, 1], {
              easing: EASE.enter,
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            if (lp <= 0) return null;
            const ly = priceToY(lv.price);
            const pulse = 0.55 + Math.sin(Math.max(0, frame - lv.at) / 11) * 0.45;
            return (
              <line
                key={`line-${lv.label}`}
                opacity={levelOut}
                x1={CHART.x0 - 6}
                x2={CHART.x0 - 6 + (SCREEN.x + SCREEN.w - 26 - (CHART.x0 - 6)) * lp}
                y1={ly}
                y2={ly}
                stroke={T.ice}
                strokeWidth={3}
                strokeDasharray="14 10"
                style={{filter: `drop-shadow(0 0 ${6 + pulse * 8}px ${T.ice}dd)`}}
              />
            );
          })}

          {/* the tape — only what is inside the window */}
          {candleOp > 0.02
            ? p.candles
                .slice(visFrom, visTo + 1)
                .map((k, j) => renderCandle(k, visFrom + j))
            : null}
          {/* wide-zoom silhouette: the shape the pull-back exists to show */}
          {silhouette ? (
            <polyline
              points={silhouette}
              fill="none"
              stroke={T.ice}
              strokeWidth={2.4}
              strokeLinejoin="round"
              opacity={silh * 0.92}
              style={{filter: `drop-shadow(0 0 9px ${T.ice}88)`}}
            />
          ) : null}

          {/* prior tests of the level — the justify act's whole argument.
            * Each tick sits ON the line at a bar the scanner actually found
            * price touching it, and lights in sequence so the count is
            * something the viewer watches accumulate rather than reads. */}
          {zm && silh > 0.02
            ? zm.touches.map((t, j) => {
                const at = touchIn + j * touchStep;
                const tp = interpolate(frame, [at, at + 12], [0, 1], {
                  easing: EASE.enter,
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                });
                if (tp <= 0 || t.i < visFrom || t.i > visTo) return null;
                const tx = cx(t.i);
                const ty = priceToY(p.levelPrice);
                return (
                  // Deliberately small. Three of these tests fall inside seven
                  // weeks of 2021, which at 1.15px/bar puts them 14px apart —
                  // a 7px ring made them one amber smudge. The cluster is the
                  // truth (price really did camp there), so the marks shrink
                  // to keep it legible rather than the count being thinned.
                  <g key={`t${t.i}`} opacity={tp * silh}>
                    <circle
                      cx={tx}
                      cy={ty}
                      r={4.5 + (1 - tp) * 9}
                      fill="none"
                      stroke={T.level}
                      strokeWidth={1.8}
                      style={{filter: `drop-shadow(0 0 7px ${T.level})`}}
                    />
                    <circle cx={tx} cy={ty} r={2.2} fill={T.level} />
                  </g>
                );
              })
            : null}

          {/* live price tag — pinned at the right of the candle field */}
          {tagOpacity > 0.01 && lastK ? (
            <g opacity={Math.min(1, tagOpacity)}>
              <line
                x1={cx(lastIdx)}
                x2={CHART.x1 + 6}
                y1={priceToY(liveClose)}
                y2={priceToY(liveClose)}
                stroke={liveUp ? C.emerald : C.redHot}
                strokeWidth={1.5}
                strokeDasharray="4 5"
                opacity={0.7}
              />
              <rect
                x={CHART.x1 + 8}
                y={priceToY(liveClose) - 19}
                width={104}
                height={38}
                rx={8}
                fill={liveUp ? C.emerald : C.redHot}
                style={{filter: `drop-shadow(0 0 12px ${liveUp ? C.emerald : C.redHot}77)`}}
              />
              <text
                x={CHART.x1 + 60}
                y={priceToY(liveClose) + 8}
                fill={T.bg}
                fontFamily={FONT.mono}
                fontWeight={800}
                fontSize={23}
                textAnchor="middle"
              >
                {liveClose.toFixed(1)}
              </text>
            </g>
          ) : null}

          {/* level label(s), above the candles so bars can't paint over them */}
          {levels.map((lv) => {
            const lp = interpolate(frame, [lv.at, lv.at + 22], [0, 1], {
              easing: EASE.enter,
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            if (lp <= 0) return null;
            const ly = priceToY(lv.price);
            return (
              <g key={`label-${lv.label}`} opacity={fadeOf(lp) * levelOut}>
                <rect
                  x={CHART.x0 - 10}
                  y={ly - 44}
                  width={lv.label.length * 15.5 + 16}
                  height={34}
                  rx={8}
                  fill={T.panelTop}
                  opacity={0.92}
                />
                <text
                  x={CHART.x0 - 2}
                  y={ly - 18}
                  fill={T.ice}
                  fontFamily={FONT.mono}
                  fontWeight={700}
                  fontSize={25}
                  letterSpacing={2}
                >
                  {lv.label}
                </text>
              </g>
            );
          })}

          {/* the justify act's headline — what the pull-back just proved.
            * Sits in the plot's upper band, backed so the silhouette cannot
            * run through the letterforms, and clears out before the pattern
            * name lands in the lower band. */}
          {zm && historyP > 0.01 ? (
            <g opacity={historyP}>
              <rect
                x={CHART.x0 - 10}
                y={CHART.y0 + 8}
                width={zm.historyLabel.length * 19.2 + 28}
                height={46}
                rx={9}
                fill={T.panelTop}
                opacity={0.93}
              />
              <text
                x={CHART.x0 + 4}
                y={CHART.y0 + 40}
                fill={T.level}
                fontFamily={FONT.mono}
                fontWeight={800}
                fontSize={28}
                letterSpacing={2}
              >
                {zm.historyLabel}
              </text>
            </g>
          ) : null}

          {/* pattern highlight */}
          {patP > 0 ? (
            <g opacity={fadeOf(patP) * 0.95}>
              <rect
                x={patX}
                y={patTop}
                width={patW}
                height={(patBot - patTop) * patPulse}
                rx={12}
                fill={`${T.ice}12`}
                stroke={T.ice}
                strokeWidth={3.5}
                style={{filter: `drop-shadow(0 0 14px ${T.ice}aa)`}}
              />
              <line
                x1={patX + patW / 2}
                y1={patBot}
                x2={patX + patW / 2}
                y2={PATTERN_LABEL_Y - 30}
                stroke={T.ice}
                strokeWidth={2}
                strokeDasharray="6 7"
                opacity={0.6}
              />
              <text
                x={patX + patW / 2}
                y={PATTERN_LABEL_Y}
                fill={T.ice}
                fontFamily={FONT.mono}
                fontWeight={800}
                fontSize={27}
                letterSpacing={2}
                textAnchor="middle"
              >
                {p.patternName}
              </text>
            </g>
          ) : null}

          {/* ------------------------------------- risk / reward frame */}
          {hasRR && rrP > 0.01 ? (
            <g opacity={fadeOf(rrP)}>
              {/* risk band: entry down to the stop */}
              <rect
                x={CHART.x0 - 6}
                y={priceToY(p.entry as number)}
                width={(CHART.x1 + 100 - CHART.x0) * zonesP}
                height={Math.max(1, priceToY(p.stop as number) - priceToY(p.entry as number))}
                fill={`${T.down}1c`}
              />
              {/* reward band: entry up to the target */}
              <rect
                x={CHART.x0 - 6}
                y={priceToY(p.target as number)}
                width={(CHART.x1 + 100 - CHART.x0) * zonesP}
                height={Math.max(1, priceToY(p.entry as number) - priceToY(p.target as number))}
                fill={`${T.up}1c`}
              />
              {/* Entry, stop and target draw as three SEPARATE beats, each with
                * its own reason. Drawing all three at once states a trade;
                * drawing them in order argues one — this is the level, this is
                * where being wrong is admitted, and only then is the target,
                * because the target is a multiple of the risk and cannot be
                * chosen before the risk exists. */}
              {[
                {v: p.entry as number, col: '#D8E6DE', tag: `ENTRY ${(p.entry as number).toFixed(2)}`, at: B.RR, dash: '2 6'},
                {v: p.stop as number, col: T.down, tag: `STOP ${(p.stop as number).toFixed(2)}`, at: B.RR_STOP, dash: '14 8'},
                {v: p.target as number, col: T.up, tag: `TARGET ${(p.target as number).toFixed(2)}  ${p.rrLabel ?? '2R'}`, at: B.RR_TARGET, dash: '14 8'},
              ].map((row) => {
                const rowP = interpolate(frame, [row.at, row.at + 20], [0, 1], {
                  easing: EASE.enter,
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                });
                if (rowP <= 0.01) return null;
                return (
                  <g key={row.tag}>
                    <line
                      x1={CHART.x0 - 6}
                      x2={CHART.x0 - 6 + (CHART.x1 + 100 - (CHART.x0 - 6)) * rowP}
                      y1={priceToY(row.v)}
                      y2={priceToY(row.v)}
                      stroke={row.col}
                      strokeWidth={2.5}
                      strokeDasharray={row.dash}
                      style={{filter: `drop-shadow(0 0 7px ${row.col}bb)`}}
                    />
                    <rect
                      x={CHART.x0 - 4}
                      y={priceToY(row.v) - 30}
                      width={row.tag.length * 12 + 22}
                      height={26}
                      rx={6}
                      fill="rgba(2,10,7,.88)"
                      stroke={row.col}
                      strokeWidth={1.2}
                      opacity={rowP}
                    />
                    <text
                      x={CHART.x0 + 7}
                      y={priceToY(row.v) - 11}
                      fill={row.col}
                      fontFamily={FONT.mono}
                      fontWeight={700}
                      fontSize={17}
                      letterSpacing={1.4}
                      opacity={rowP}
                    >
                      {row.tag}
                    </text>
                  </g>
                );
              })}
            </g>
          ) : null}

          {/* BUY / SELL fork */}
          {arrowsP > 0 ? (
            <>
              <Arrow dir="up" label="BUY" color={T.up} op={fadeOf(arrowsP) * (isDown ? arrowsOut : winnerOut)} />
              <Arrow dir="down" label="SELL" color={T.down} op={fadeOf(arrowsP) * (isDown ? winnerOut : arrowsOut)} />
            </>
          ) : null}
        </svg>

        {/* ------------------------------------------- 6b. target reached
       * A check mark on the bar that ACTUALLY reached the target, on the frame
       * that bar prints. `tpBar` is derived from the price data, so nothing
       * fires on a trade that never got there - no bar, no tick.
       *
       * This replaced a coin fountain. Money raining out of a chart sells an
       * outcome; a check mark says a level was reached, which is what happened. */}
      {hasRR && tpBar >= 0 && checkT > 0 ? (
        <AbsoluteFill style={{pointerEvents: 'none'}}>
          {checkT < 40 ? (
            <div
              style={{
                position: 'absolute',
                left: cx(p.revealFrom + tpBar),
                top: priceToY(reveal[tpBar].h) - 66,
                width: 104 + checkT * 6,
                height: 104 + checkT * 6,
                marginLeft: -(104 + checkT * 6) / 2,
                marginTop: -(104 + checkT * 6) / 2,
                borderRadius: 999,
                border: `3px solid ${T.up}`,
                opacity: Math.max(0, 0.75 - checkT / 40),
              }}
            />
          ) : null}
          <div
            style={{
              position: 'absolute',
              left: cx(p.revealFrom + tpBar),
              top: priceToY(reveal[tpBar].h) - 66,
              width: 104,
              height: 104,
              marginLeft: -52,
              marginTop: -52,
              borderRadius: 999,
              background: T.up,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 60,
              transform: `scale(${checkS})`,
              opacity: checkO,
              boxShadow: `0 0 46px ${T.up}cc`,
            }}
          >
            {'✅'}
          </div>
          {/* Beside the badge, not above it. The winning bar sits near the top
            * of the plot, so a label stacked over the mark collided with both
            * the mark and the panel's chrome edge. */}
          <div
            style={{
              position: 'absolute',
              left: cx(p.revealFrom + tpBar) - 82,
              top: priceToY(reveal[tpBar].h) - 66,
              transform: 'translate(-100%, -50%)',
              fontFamily: FONT.mono,
              fontWeight: 800,
              fontSize: 27,
              letterSpacing: 2,
              color: T.up,
              opacity: checkO,
              textShadow: `0 0 18px ${T.up}`,
              whiteSpace: 'nowrap',
            }}
          >
            TARGET HIT
          </div>
        </AbsoluteFill>
      ) : null}
      </AbsoluteFill>

      {/* HUD layer — the ask and the rule card, screen-fixed like the hook. */}
      <AbsoluteFill style={{transform: uiT, zIndex: 2}}>
      {/* -------------------------------------- 7. the ask (pre-answer) */}
        {/* Fills the band under the screen while the viewer is deciding —
         * without it the lower third sits empty for most of the reel. Hands
         * straight over to the rule card once the answer lands. */}
        {frame >= B.ARROWS && frame < B.ANSWER + 10 ? (
          <div
            style={{
              position: 'absolute',
              top: 1420,
              left: 0,
              right: 0,
              textAlign: 'center',
              opacity:
                fadeOf(spring({frame: frame - B.ARROWS, fps, config: SPRINGS.pop})) *
                interpolate(frame, [B.ANSWER - 12, B.ANSWER + 2], [1, 0], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                }),
            }}
          >
            <div
              style={{
                fontFamily: FONT.display,
                fontWeight: 700,
                fontSize: 62,
                color: C.ink,
                letterSpacing: -0.5,
              }}
            >
              What happens <span style={{color: T.ice}}>next?</span>
            </div>
            <div
              style={{
                fontFamily: FONT.mono,
                fontSize: 26,
                letterSpacing: 3,
                color: T.steel,
                marginTop: 16,
              }}
            >
              CALL IT BEFORE THE TIMER
            </div>
          </div>
        ) : null}

        {/* ------------------------------------- 7b. building the trade
          * One caption per beat, in the empty band under the screen, while the
          * matching line draws on the chart. The order is the argument: the
          * stop comes before the target because the target is a MULTIPLE of the
          * risk — you cannot size a reward before you have priced being wrong.
          * Deliberately not narration-dependent; the reel reads silently. */}
        {zm && setupCap ? (
          <div
            style={{
              position: 'absolute',
              top: 1400,
              left: 52,
              right: 52,
              opacity: setupCap.op,
              transform: `translateY(${(1 - setupCap.op) * 18}px)`,
            }}
          >
            <div
              style={{
                fontFamily: FONT.mono,
                fontWeight: 800,
                fontSize: 30,
                letterSpacing: 3,
                color: setupCap.col,
                marginBottom: 14,
                textShadow: `0 0 20px ${setupCap.col}66`,
              }}
            >
              {setupCap.head}
            </div>
            <div style={{fontFamily: FONT.body, fontWeight: 500, fontSize: 35, lineHeight: 1.28, color: C.ink}}>
              {setupCap.body}
            </div>
          </div>
        ) : null}

        {/* ----------------------------------------------------- 7. rule */}
        {ruleP > 0 && (B.ENDCARD < 0 || frame < B.ENDCARD) ? (
          <div
            style={{
              position: 'absolute',
              top: 1392,
              left: 46,
              right: 46,
              opacity: fadeOf(ruleP),
              transform: `translateY(${interpolate(ruleP, [0, 1], [30, 0])}px)`,
              background: 'rgba(0,224,130,.07)',
              border: `1px solid ${T.edge}`,
              borderRadius: 26,
              padding: '24px 30px',
              backdropFilter: 'blur(6px)',
            }}
          >
            <div
              style={{
                fontFamily: FONT.mono,
                fontWeight: 700,
                fontSize: 24,
                letterSpacing: 3,
                color: T.ice,
                marginBottom: 12,
              }}
            >
              {p.ruleTitle.toUpperCase()}
            </div>
            <div style={{fontFamily: FONT.body, fontWeight: 500, fontSize: 33, lineHeight: 1.3, color: C.ink}}>
              {p.ruleText}
            </div>
          </div>
        ) : null}
      </AbsoluteFill>

      {/* ------------------------------------------------- 7c. end card
       * Two seconds, full-bleed over the chart. It is the last thing on screen
       * and it asks for exactly one thing — a reel that ends on a rule card
       * ends on homework, and nobody follows homework. */}
      {B.ENDCARD > 0 && frame >= B.ENDCARD ? (
        <AbsoluteFill
          style={{
            background: `radial-gradient(120% 70% at 50% 42%, ${T.panelTop} 0%, ${T.bg} 72%)`,
            opacity: interpolate(frame, [B.ENDCARD, B.ENDCARD + 9], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 30,
            zIndex: 5,
          }}
        >
          {(() => {
            const eP = spring({frame: frame - B.ENDCARD - 4, fps, config: SPRINGS.hero});
            return (
              <>
                <div
                  style={{
                    fontSize: 110,
                    transform: `scale(${interpolate(eP, [0, 1], [0.5, 1])}) rotate(${interpolate(eP, [0, 1], [-24, 0])}deg)`,
                    filter: `drop-shadow(0 0 34px ${T.up}aa)`,
                  }}
                >
                  {'❤️'}
                </div>
                <div
                  style={{
                    fontFamily: FONT.display,
                    fontWeight: 700,
                    fontSize: 88,
                    lineHeight: 1.05,
                    color: C.ink,
                    textAlign: 'center',
                    letterSpacing: -1,
                    opacity: fadeOf(eP),
                    transform: `translateY(${interpolate(eP, [0, 1], [26, 0])}px)`,
                  }}
                >
                  LIKE <span style={{color: T.ice}}>&</span> FOLLOW
                </div>
                <div
                  style={{
                    fontFamily: FONT.mono,
                    fontSize: 34,
                    letterSpacing: 6,
                    color: T.steel,
                    opacity: fadeOf(eP),
                  }}
                >
                  FOR MORE SETUPS
                </div>
                <div
                  style={{
                    marginTop: 16,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 13,
                    padding: '11px 24px',
                    border: `1px solid ${T.edge}`,
                    borderRadius: 999,
                    fontFamily: FONT.mono,
                    fontSize: 24,
                    letterSpacing: 3,
                    color: T.ice,
                    opacity: fadeOf(eP) * 0.9,
                  }}
                >
                  {p.ticker ? `${p.ticker.toUpperCase()} · ${p.patternName}` : p.patternName}
                </div>
              </>
            );
          })()}
        </AbsoluteFill>
      ) : null}

      {/* --------------------------------------------------- 8. footer
       * Split on the middle dot into a ruled row, like the reference boards'
       * three-cell footer, instead of one long wrapped sentence. */}
      <div
        style={{
          position: 'absolute',
          bottom: 68,
          left: 46,
          right: 46,
          display: p.footer ? 'flex' : 'none',
          alignItems: 'stretch',
          justifyContent: 'center',
          borderTop: `1px solid ${T.edge}`,
          paddingTop: 18,
        }}
      >
        {(p.footer ?? '').split('·').map((cell, i, all) => (
          <div
            key={cell}
            style={{
              flex: 1,
              textAlign: 'center',
              padding: '0 14px',
              borderRight: i < all.length - 1 ? `1px solid ${T.edge}` : undefined,
              fontFamily: FONT.mono,
              fontSize: 19,
              lineHeight: 1.35,
              color: T.steel,
            }}
          >
            {cell.trim()}
          </div>
        ))}
      </div>

      {/* ------------------------------------------- 9. finish layers
       * No colour grade: tinting the whole frame with the answer colour is
       * what produced the green cast, and it leaked the answer besides. */}
      {/* ------------------------------------------- 10. the ticking clock
       * One escapement per countdown second, alternating tick/tock so five in a
       * row read as a clock rather than a metronome. Placed on the same
       * B.COUNT/COUNT_PER constants the digits use, so the sound cannot
       * drift from the number on screen. */}
      {Array.from({length: COUNT_N}, (_, i) => (
        <Sequence key={i} from={B.COUNT + i * COUNT_PER} durationInFrames={COUNT_PER}>
          <Audio src={staticFile(i % 2 === 0 ? 'audio/tick.wav' : 'audio/tock.wav')} volume={0.55} />
        </Sequence>
      ))}

      {/* ------------------------------------------ the two pull-backs
       * One whoosh per zoom-out. The deep one is the only sound over that
       * whole act — 500 bars of settled history cannot each take a hit, and
       * silence under a moving camera is what makes the move feel like scale
       * rather than like more events happening. */}
      {zm ? (
        <>
          <Sequence from={ZB.fastFrom - 4} durationInFrames={46}>
            <Audio src={staticFile('audio/whoosh_out.wav')} volume={0.34} />
          </Sequence>
          <Sequence from={ZB.fastTo - 6} durationInFrames={70}>
            <Audio src={staticFile('audio/whoosh_out.wav')} volume={0.5} />
          </Sequence>
          <Sequence from={ZB.justifyTo - 2} durationInFrames={54}>
            <Audio src={staticFile('audio/whoosh_in.wav')} volume={0.42} />
          </Sequence>
          {/* one click per prior test as it lights — the count made audible */}
          {zm.touches.map((t, j) => (
            <Sequence key={`tc${t.i}`} from={touchIn + j * touchStep} durationInFrames={touchStep}>
              <Audio src={staticFile('audio/key_click.wav')} volume={0.3} />
            </Sequence>
          ))}
        </>
      ) : null}

      {/* One tone per REVEAL candle, pitched by direction — up-bars glide up,
       * down-bars glide down. Only the reveal is scored: the setup prints 62
       * bars in under four seconds, and a hit per bar there is seventeen a
       * second, which is noise rather than information. */}
      {reveal.map((k, i) => (
        <Sequence
          key={`rs${i}`}
          from={Math.round(B.REVEAL + i * REVEAL_PER)}
          durationInFrames={Math.max(3, Math.round(REVEAL_PER))}
        >
          <Audio
            src={staticFile(k.c >= k.o ? 'audio/candle_up.wav' : 'audio/candle_down.wav')}
            volume={0.42}
          />
        </Sequence>
      ))}

      {/* The chime lands on the frame the winning bar prints — the same frame
       * the check mark scales in. Anchored to payoutAt, which is derived from
       * the bar index, so it cannot drift away from the mark it belongs to. */}
      {hasRR && tpBar >= 0 ? (
        <Sequence from={Math.round(payoutAt)} durationInFrames={40}>
          <Audio src={staticFile('audio/coin.wav')} volume={0.7} />
        </Sequence>
      ) : null}

      {/* one soft click per trade-frame line as it draws */}
      {zm && hasRR
        ? [B.RR, B.RR_STOP, B.RR_TARGET].map((at) => (
            <Sequence key={`sc${at}`} from={at} durationInFrames={14}>
              <Audio src={staticFile('audio/key_click.wav')} volume={0.36} />
            </Sequence>
          ))
        : null}

      {/* end card sting */}
      {B.ENDCARD > 0 ? (
        <Sequence from={B.ENDCARD} durationInFrames={50}>
          <Audio src={staticFile('audio/sfx_pop.wav')} volume={0.5} />
        </Sequence>
      ) : null}

      <Grain />
      <Vignette />
    </AbsoluteFill>
  );
};
