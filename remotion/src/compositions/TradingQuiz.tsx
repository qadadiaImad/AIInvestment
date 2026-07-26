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
  answer: z.enum(['BUY', 'SELL']),
  /** Overrides the badge text without changing the colour semantics. Real
   * tickers use this ("IT FELL 21%") so a hindsight reel never puts a literal
   * SELL call on a live name; synthetic patterns leave it unset. */
  answerLabel: z.string().optional(),
  answerLine: z.string(),
  ruleTitle: z.string(),
  ruleText: z.string(),
  footer: z.string(),
  /** Index of the first candle that belongs to the REVEAL (everything before
   * it is the visible setup the viewer is quizzed on). */
  revealFrom: z.number(),
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
const DRAW_PER = 6; // frames per setup candle
// Kept <= DRAW_PER so exactly one bar is live at a time; a finished bar must
// never still be moving after the next one opens.
const CANDLE_FORM = 6; // frames a single candle takes to "print"
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
const REVEAL_PER = 11;
const RULE_IN = REVEAL_START + 48;
/** Minimum duration the timeline needs; fixtures should meet or exceed it. */
export const TRADING_QUIZ_MIN_FRAMES = RULE_IN + 88; // -> 546

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

  const lo = Math.min(...p.candles.map((k) => k.l)) - PAD.lo;
  const hi = Math.max(...p.candles.map((k) => k.h)) + PAD.hi;
  const priceToY = (v: number) => CHART.y1 - ((v - lo) / (hi - lo)) * (CHART.y1 - CHART.y0);

  const slot = (CHART.x1 - CHART.x0) / p.candles.length;
  const bodyW = Math.min(24, slot * 0.62);
  const cx = (i: number) => CHART.x0 + slot * i + slot / 2;

  const isDown = p.answer === 'SELL';
  const answerColor = isDown ? T.down : T.up;

  // Slow push-in with an emphasis hit when the answer lands.
  const zoom = cameraPushIn(frame, p.durationInFrames, {base: 0.035, hitFrame: ANSWER_IN, hitAmount: 0.02});

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
  const axisOut = interpolate(frame, [ARROWS_IN - 12, ARROWS_IN + 2], [1, 0.12], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // ------------------------------------------------------------ the level
  const levelP = interpolate(frame, [LEVEL_IN, LEVEL_IN + 22], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const levelY = priceToY(p.levelPrice);
  const levelPulse = 0.55 + Math.sin(Math.max(0, frame - LEVEL_IN) / 11) * 0.45;

  // -------------------------------------------------------- pattern frame
  const patP = spring({frame: frame - PATTERN_IN, fps, config: SPRINGS.pop});
  const patPulse = 1 + Math.sin(Math.max(0, frame - PATTERN_IN) / 7) * 0.03;

  // ------------------------------------------------------------- arrows
  const arrowsP = spring({frame: frame - ARROWS_IN, fps, config: SPRINGS.pop});
  const arrowsOut = interpolate(frame, [ANSWER_IN, ANSWER_IN + 14], [1, 0], {
    easing: EASE.exit,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const winnerOut = interpolate(frame, [REVEAL_START - 6, REVEAL_START + 8], [1, 0], {
    easing: EASE.exit,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // ----------------------------------------------------------- countdown
  const countIdx = Math.floor((frame - COUNT_START) / COUNT_PER);
  const countActive = frame >= COUNT_START && frame < ANSWER_IN;
  const countDigit = COUNT_N - countIdx;
  const countLocal = (frame - COUNT_START) % COUNT_PER;
  const countP = spring({frame: countLocal, fps, config: SPRINGS.hero});
  // Ring drains over the whole 5s window, not per digit — reads as one timer.
  const countFrac = Math.min(1, Math.max(0, (frame - COUNT_START) / (COUNT_PER * COUNT_N)));

  // ------------------------------------------------------------- answer
  const answerP = spring({frame: frame - ANSWER_IN, fps, config: SPRINGS.hero});
  const ruleP = spring({frame: frame - RULE_IN, fps, config: SPRINGS.heavy});

  // ------------------------------------------------- live price tag
  // Tracks the last bar printed so far. Hands off to the BUY/SELL fork when
  // the fork appears — they'd otherwise fight for the same gutter.
  const drawnCount = Math.min(
    setup.length,
    Math.max(0, Math.floor((frame - DRAW_START) / DRAW_PER) + 1)
  );
  const revealedCount = Math.min(
    reveal.length,
    Math.max(0, Math.floor((frame - REVEAL_START) / REVEAL_PER) + 1)
  );
  const lastIdx = frame >= REVEAL_START && revealedCount > 0
    ? p.revealFrom + revealedCount - 1
    : Math.max(0, drawnCount - 1);
  const lastK = p.candles[lastIdx];
  // Same tick maths the bar itself uses, so the tag reads the live print rather
  // than jumping straight to a close that hasn't happened yet.
  const liveClose = (() => {
    if (!lastK) return 0;
    const appearAt =
      lastIdx >= p.revealFrom
        ? REVEAL_START + (lastIdx - p.revealFrom) * REVEAL_PER
        : DRAW_START + lastIdx * DRAW_PER;
    const raw = (frame - appearAt) / CANDLE_FORM;
    const step = Math.min(CANDLE_TICKS, Math.ceil(Math.min(1, Math.max(0, raw)) * CANDLE_TICKS));
    if (step >= CANDLE_TICKS) return lastK.c;
    const f = step / CANDLE_TICKS;
    const hN = lastK.o + (lastK.h - lastK.o) * Math.min(1, f * 1.22);
    const lN = lastK.o + (lastK.l - lastK.o) * Math.min(1, f * 1.22);
    const drift = (random(`k${lastIdx}t${step}`) - 0.5) * (lastK.h - lastK.l) * 0.7;
    return Math.max(lN, Math.min(hN, lastK.o + (lastK.c - lastK.o) * f + drift));
  })();
  const liveUp = liveClose >= (lastK?.o ?? 0);
  const tagOpacity =
    interpolate(frame, [DRAW_START + 6, DRAW_START + 20], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) *
    interpolate(frame, [ARROWS_IN - 10, ARROWS_IN + 4], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) +
    interpolate(frame, [REVEAL_START, REVEAL_START + 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // A bar prints the way a live one actually does, not the way an animation
  // does: it opens, ticks in hard discrete jumps, wanders inside its own range,
  // flips colour when the last trade crosses the open, and only snaps to the
  // real close on the final tick. No easing, no fade-in — those are what made
  // the old version read as a diagram assembling itself.
  const renderCandle = (k: z.infer<typeof candleSchema>, i: number, appearAt: number) => {
    const raw = (frame - appearAt) / CANDLE_FORM;
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
      <g key={i} style={{filter: `drop-shadow(0 0 ${settled ? 6 : 11}px ${col}${settled ? '77' : 'cc'})`}}>
        <line x1={x} x2={x} y1={priceToY(hNow)} y2={priceToY(lNow)} stroke={col} strokeWidth={2.5} />
        <rect x={x - bodyW / 2} y={yTop} width={bodyW} height={Math.max(2, yBot - yTop)} rx={2} fill={col} />
      </g>
    );
  };

  // The candles that form the pattern, counting back from the last setup bar.
  const span = Math.max(1, Math.min(p.patternSpan ?? 2, p.revealFrom));
  const pA = p.revealFrom - span;
  const pB = p.revealFrom - 1;
  const patX = cx(pA) - slot * 0.58;
  const patW = slot * (span + 0.16);
  const boxed = p.candles.slice(pA, pB + 1);
  const patTop = priceToY(Math.max(...boxed.map((k) => k.h))) - 16;
  const patBot = priceToY(Math.min(...boxed.map((k) => k.l))) + 16;

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

      {/* everything below rides the camera push-in together */}
      <AbsoluteFill style={{transform: `scale(${zoom})`}}>
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
            MAYA LAB
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
              top: 250,
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
        {frame >= ANSWER_IN ? (
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
         * the screen panel starts, and was painted over on every render. Here it
         * also fills the gap between the answer landing and the rule card. */}
        {frame >= ANSWER_IN ? (
          <div
            style={{
              position: 'absolute',
              top: 1418,
              left: 70,
              right: 70,
              textAlign: 'center',
              opacity:
                fadeOf(answerP) *
                interpolate(frame, [RULE_IN - 16, RULE_IN - 2], [1, 0], {
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
            {[T.down, '#E0A23B', T.up].map((col) => (
              <div key={col} style={{width: 11, height: 11, borderRadius: 999, background: col, opacity: 0.62}} />
            ))}
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

          {/* level line */}
          {levelP > 0 ? (
            <line
              x1={CHART.x0 - 6}
              x2={CHART.x0 - 6 + (SCREEN.x + SCREEN.w - 26 - (CHART.x0 - 6)) * levelP}
              y1={levelY}
              y2={levelY}
              stroke={T.ice}
              strokeWidth={3}
              strokeDasharray="14 10"
              style={{filter: `drop-shadow(0 0 ${6 + levelPulse * 8}px ${T.ice}dd)`}}
            />
          ) : null}

          {setup.map((k, i) => renderCandle(k, i, DRAW_START + i * DRAW_PER))}
          {reveal.map((k, i) => renderCandle(k, p.revealFrom + i, REVEAL_START + i * REVEAL_PER))}

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

          {/* level label, above the candles so bars can't paint over it */}
          {levelP > 0 ? (
            <g opacity={fadeOf(levelP)}>
              <rect
                x={CHART.x0 - 10}
                y={levelY - 44}
                width={p.levelLabel.length * 15.5 + 16}
                height={34}
                rx={8}
                fill={T.panelTop}
                opacity={0.92}
              />
              <text
                x={CHART.x0 - 2}
                y={levelY - 18}
                fill={T.ice}
                fontFamily={FONT.mono}
                fontWeight={700}
                fontSize={25}
                letterSpacing={2}
              >
                {p.levelLabel}
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

          {/* BUY / SELL fork */}
          {arrowsP > 0 ? (
            <>
              <Arrow dir="up" label="BUY" color={T.up} op={fadeOf(arrowsP) * (isDown ? arrowsOut : winnerOut)} />
              <Arrow dir="down" label="SELL" color={T.down} op={fadeOf(arrowsP) * (isDown ? winnerOut : arrowsOut)} />
            </>
          ) : null}
        </svg>

        {/* -------------------------------------- 7. the ask (pre-answer) */}
        {/* Fills the band under the screen while the viewer is deciding —
         * without it the lower third sits empty for most of the reel. Hands
         * straight over to the rule card once the answer lands. */}
        {frame >= ARROWS_IN && frame < ANSWER_IN + 10 ? (
          <div
            style={{
              position: 'absolute',
              top: 1420,
              left: 0,
              right: 0,
              textAlign: 'center',
              opacity:
                fadeOf(spring({frame: frame - ARROWS_IN, fps, config: SPRINGS.pop})) *
                interpolate(frame, [ANSWER_IN - 12, ANSWER_IN + 2], [1, 0], {
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

        {/* ----------------------------------------------------- 7. rule */}
        {ruleP > 0 ? (
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

      {/* --------------------------------------------------- 8. footer
       * Split on the middle dot into a ruled row, like the reference boards'
       * three-cell footer, instead of one long wrapped sentence. */}
      <div
        style={{
          position: 'absolute',
          bottom: 68,
          left: 46,
          right: 46,
          display: 'flex',
          alignItems: 'stretch',
          justifyContent: 'center',
          borderTop: `1px solid ${T.edge}`,
          paddingTop: 18,
        }}
      >
        {p.footer.split('·').map((cell, i, all) => (
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
       * COUNT_START/COUNT_PER constants the digits use, so the sound cannot
       * drift from the number on screen. */}
      {Array.from({length: COUNT_N}, (_, i) => (
        <Sequence key={i} from={COUNT_START + i * COUNT_PER} durationInFrames={COUNT_PER}>
          <Audio src={staticFile(i % 2 === 0 ? 'audio/tick.wav' : 'audio/tock.wav')} volume={0.55} />
        </Sequence>
      ))}

      <Grain />
      <Vignette />
    </AbsoluteFill>
  );
};
