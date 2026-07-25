// TradingQuiz.tsx — "guess the next move" candlestick quiz reel (9:16, silent).
//
// Format benchmarked from the trading-quiz reels that do numbers on IG: hook
// card -> chart prints candle by candle -> the level and the pattern get
// named -> BUY/SELL fork -> countdown -> reveal. The difference here is that
// the answer is derived from an actual, nameable setup rather than a vibe:
// the fixture carries a real OHLC sequence, the level it tests, and the
// pattern that resolves it, so the reveal is teachable instead of a coin flip.
//
// Data is SYNTHETIC and labeled as such on-screen (see `footer`) — this is a
// pattern illustration, not a real market chart, and must never be presented
// as one.
//
// Engine, not a one-off: swap the fixture (candles + revealFrom + answer +
// rule text) and the same composition renders a different pattern quiz.
import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {z} from 'zod';
import {C, FONT} from '../slides/theme';
import {EASE, SPRINGS, fadeOf} from '../motion/craft';
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
  answerLine: z.string(),
  ruleTitle: z.string(),
  ruleText: z.string(),
  footer: z.string(),
  /** Index of the first candle that belongs to the REVEAL (everything before
   * it is the visible setup the viewer is quizzed on). */
  revealFrom: z.number(),
  candles: z.array(candleSchema).min(6),
  durationInFrames: z.number(),
});
export type TradingQuizProps = z.infer<typeof tradingQuizSchema>;

// ---------------------------------------------------------------- timing
const DRAW_START = 36;
const DRAW_PER = 6; // frames per setup candle
const CANDLE_FORM = 7; // frames a single candle takes to "print"
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
const CHART = {x0: 62, x1: 822, y0: 470, y1: 1250};
const PAD = {lo: 4, hi: 4}; // price padding around the data range
/** Clear band below the candle field where the pattern name is parked. */
const PATTERN_LABEL_Y = 1222;

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
  const answerColor = isDown ? C.redHot : C.emerald;

  // ------------------------------------------------------------ hook card
  const hookP = spring({frame, fps, config: SPRINGS.hero});
  // The title shrinks up out of the way once the chart starts drawing.
  const hookShift = interpolate(frame, [DRAW_START, DRAW_START + 18], [0, -26], {
    easing: EASE.cruise,
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

  // -------------------------------------------------------- pattern frame
  const patP = spring({frame: frame - PATTERN_IN, fps, config: SPRINGS.pop});
  const patPulse = 1 + Math.sin(Math.max(0, frame - PATTERN_IN) / 7) * 0.03;

  // ------------------------------------------------------------- arrows
  const arrowsP = spring({frame: frame - ARROWS_IN, fps, config: SPRINGS.pop});
  // After the answer lands, the losing arrow drops away and the winner holds.
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

  // ------------------------------------------------------------- answer
  const answerP = spring({frame: frame - ANSWER_IN, fps, config: SPRINGS.hero});

  // --------------------------------------------------------------- rule
  const ruleP = spring({frame: frame - RULE_IN, fps, config: SPRINGS.heavy});

  const renderCandle = (k: z.infer<typeof candleSchema>, i: number, appearAt: number) => {
    const t = interpolate(frame, [appearAt, appearAt + CANDLE_FORM], [0, 1], {
      easing: EASE.enter,
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    if (t <= 0) return null;
    // The candle "prints" outward from its open price — reads as live tape.
    const hNow = k.o + (k.h - k.o) * t;
    const lNow = k.o + (k.l - k.o) * t;
    const cNow = k.o + (k.c - k.o) * t;
    const up = k.c >= k.o;
    const col = up ? C.emerald : C.redHot;
    const x = cx(i);
    const yTop = priceToY(Math.max(k.o, cNow));
    const yBot = priceToY(Math.min(k.o, cNow));
    return (
      <g key={i} opacity={fadeOf(t)} style={{filter: `drop-shadow(0 0 7px ${col}88)`}}>
        <line x1={x} x2={x} y1={priceToY(hNow)} y2={priceToY(lNow)} stroke={col} strokeWidth={2.5} />
        <rect
          x={x - bodyW / 2}
          y={yTop}
          width={bodyW}
          height={Math.max(2, yBot - yTop)}
          rx={2}
          fill={col}
        />
      </g>
    );
  };

  // The two candles that form the pattern (setup candle + the engulfing one).
  const pA = p.revealFrom - 2;
  const pB = p.revealFrom - 1;
  const patX = cx(pA) - slot * 0.58;
  const patW = slot * 2.16;
  const patTop = priceToY(Math.max(p.candles[pA].h, p.candles[pB].h)) - 16;
  const patBot = priceToY(Math.min(p.candles[pA].l, p.candles[pB].l)) + 16;

  // Arrow origin: just right of the last setup candle.
  const oX = cx(p.revealFrom - 1) + slot * 0.8;
  const oY = priceToY(p.candles[p.revealFrom - 1].c);

  // Arrow geometry is deliberately short: the label sits to the right of the
  // head, and at 1080 wide there is only ~1040px of usable width before the
  // text clips off-frame.
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
      <g opacity={op} style={{filter: `drop-shadow(0 0 10px ${color}99)`}}>
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
    <AbsoluteFill style={{background: C.bg, fontFamily: FONT.body}}>
      {/* ambient wash so the frame is never flat black */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 34%, ${answerColor}14, transparent 62%)`,
        }}
      />

      {/* ---------------------------------------------------------- hook */}
      <div
        style={{
          position: 'absolute',
          top: 150 + hookShift,
          left: 0,
          right: 0,
          textAlign: 'center',
          opacity: fadeOf(hookP),
          transform: `scale(${interpolate(hookP, [0, 1], [0.86, 1])})`,
        }}
      >
        <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 76, color: C.ink, letterSpacing: -1}}>
          {p.kick.split(' ')[0]}{' '}
          <span style={{color: C.emerald}}>{p.kick.split(' ').slice(1).join(' ')}</span>
        </div>
      </div>

      {/* ----------------------------------------------------- countdown */}
      {countActive ? (
        <div
          style={{
            position: 'absolute',
            top: 268,
            left: 0,
            right: 0,
            display: 'flex',
            justifyContent: 'center',
            gap: 14,
          }}
        >
          <div
            style={{
              fontFamily: FONT.mono,
              fontWeight: 800,
              fontSize: 92,
              color: C.ink,
              border: `4px solid ${C.line}`,
              borderRadius: 18,
              padding: '6px 34px',
              background: 'rgba(255,255,255,.04)',
              opacity: fadeOf(countP),
              transform: `scale(${interpolate(countP, [0, 1], [1.5, 1])})`,
              boxShadow: `0 0 40px ${answerColor}33`,
            }}
          >
            {countDigit}
          </div>
        </div>
      ) : null}

      {/* -------------------------------------------------------- answer */}
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
              fontSize: 84,
              color: C.bg,
              background: answerColor,
              padding: '10px 52px',
              borderRadius: 999,
              boxShadow: `0 0 60px ${answerColor}66`,
            }}
          >
            {p.answer}
          </div>
          <div
            style={{
              fontFamily: FONT.body,
              fontWeight: 500,
              fontSize: 34,
              color: C.inkSoft,
              marginTop: 16,
              padding: '0 90px',
            }}
          >
            {p.answerLine}
          </div>
        </div>
      ) : null}

      {/* --------------------------------------------------------- chart */}
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        {/* resistance / support level */}
        {levelP > 0 ? (
          <g opacity={fadeOf(levelP)}>
            <line
              x1={CHART.x0}
              x2={CHART.x0 + (CHART.x1 + 150 - CHART.x0) * levelP}
              y1={levelY}
              y2={levelY}
              stroke={C.amber}
              strokeWidth={3}
              strokeDasharray="14 10"
              style={{filter: `drop-shadow(0 0 8px ${C.amber}aa)`}}
            />
            <text
              x={CHART.x0 + 4}
              y={levelY - 18}
              fill={C.amber}
              fontFamily={FONT.mono}
              fontWeight={700}
              fontSize={25}
              letterSpacing={2}
            >
              {p.levelLabel}
            </text>
          </g>
        ) : null}

        {/* setup candles */}
        {setup.map((k, i) => renderCandle(k, i, DRAW_START + i * DRAW_PER))}

        {/* reveal candles */}
        {reveal.map((k, i) => renderCandle(k, p.revealFrom + i, REVEAL_START + i * REVEAL_PER))}

        {/* pattern highlight */}
        {patP > 0 ? (
          <g opacity={fadeOf(patP) * 0.95}>
            <rect
              x={patX}
              y={patTop}
              width={patW}
              height={(patBot - patTop) * patPulse}
              rx={12}
              fill="none"
              stroke={C.amber}
              strokeWidth={3.5}
              style={{filter: `drop-shadow(0 0 12px ${C.amber}99)`}}
            />
            {/* The label is parked in the clear band under the candle field
             * with a leader line back up to the box — anchoring it directly
             * beneath the box put it on top of the reveal candles. */}
            <line
              x1={patX + patW / 2}
              y1={patBot}
              x2={patX + patW / 2}
              y2={PATTERN_LABEL_Y - 30}
              stroke={C.amber}
              strokeWidth={2}
              strokeDasharray="6 7"
              opacity={0.6}
            />
            <text
              x={patX + patW / 2}
              y={PATTERN_LABEL_Y}
              fill={C.amber}
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
            <Arrow
              dir="up"
              label="BUY"
              color={C.emerald}
              op={fadeOf(arrowsP) * (isDown ? arrowsOut : winnerOut)}
            />
            <Arrow
              dir="down"
              label="SELL"
              color={C.redHot}
              op={fadeOf(arrowsP) * (isDown ? winnerOut : arrowsOut)}
            />
          </>
        ) : null}
      </svg>

      {/* ---------------------------------------------------------- rule */}
      {ruleP > 0 ? (
        <div
          style={{
            position: 'absolute',
            top: 1350,
            left: 62,
            right: 62,
            opacity: fadeOf(ruleP),
            transform: `translateY(${interpolate(ruleP, [0, 1], [30, 0])}px)`,
            background: C.panel,
            border: `1px solid ${C.line}`,
            borderRadius: 26,
            padding: '30px 34px',
          }}
        >
          <div
            style={{
              fontFamily: FONT.mono,
              fontWeight: 700,
              fontSize: 24,
              letterSpacing: 3,
              color: C.amber,
              marginBottom: 12,
            }}
          >
            {p.ruleTitle.toUpperCase()}
          </div>
          <div style={{fontFamily: FONT.body, fontWeight: 500, fontSize: 35, lineHeight: 1.34, color: C.ink}}>
            {p.ruleText}
          </div>
        </div>
      ) : null}

      {/* -------------------------------------------------------- footer */}
      <div
        style={{
          position: 'absolute',
          bottom: 78,
          left: 0,
          right: 0,
          textAlign: 'center',
          fontFamily: FONT.mono,
          fontSize: 21,
          color: C.muted,
          padding: '0 70px',
        }}
      >
        {p.footer}
      </div>

      <Grain />
      <Vignette />
    </AbsoluteFill>
  );
};
