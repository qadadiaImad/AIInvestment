// TapeChart.tsx — the chart that plays INSIDE the monitor in the meme reel.
//
// This is the lean, screen-native cousin of TradingQuiz: the same live-tape
// candle-printing engine (hard discrete ticks, wicks that only widen, colour
// that flips on the live print and only commits on the close), with all of the
// quiz UI — countdown, BUY/SELL fork, answer badge, rule card — stripped out.
// A monitor sitting on a desk in a room shows a chart, not a quiz.
//
// It renders at its OWN native resolution (default 1280x800, a 16:10 desktop
// panel) and is then perspective-mapped onto the monitor quad by ScreenInsert.
// Rendering large and mapping down is deliberate: the text stays crisp after
// the homography squashes it.
//
// Two hard rails, inherited from references/meme-reel-pipeline.md §5:
//   1. The OHLC is REAL and comes from the fixture. Nothing here invents a bar.
//   2. The on-screen readout is PRICE. There is no P&L, no return, no position
//      size, and no cumulative counter anywhere in this component.
//
// The parent owns the beat: `appearFrames[i]` is the frame candle i starts
// printing, so a reel can dwell on one bar (the breakout) and rush others.
import React from 'react';
import {interpolate, random, useCurrentFrame} from 'remotion';
import {C, FONT} from '../slides/theme';
import {EASE} from '../motion/craft';

export type Candle = {o: number; h: number; l: number; c: number};

/** Frames a single bar takes to finish printing, and how many discrete ticks
 * it takes to get there. Same values as TradingQuiz so the two reels share a
 * visual cadence — a bar "feels" the same length across the channel. */
const CANDLE_FORM = 6;
const CANDLE_TICKS = 3;

export type TapeChartProps = {
  candles: Candle[];
  /** Frame at which each candle starts printing. Must be same length as
   * `candles` and ascending. The parent composition owns the story beat. */
  appearFrames: number[];
  /** Per-candle print duration, defaulting to CANDLE_FORM. The story bar — the
   * one the whole reel is about — gets a long form so the viewer watches it
   * trade through the level and settle back, instead of it flicking past in
   * six frames like every other bar. */
  formFrames?: number[];
  /** The horizontal level the story is about (e.g. the resistance that fails). */
  levelPrice: number;
  levelLabel: string;
  /** Frame the level line draws in. */
  levelInFrame: number;
  /** Chrome-bar text, e.g. "INTC · DAILY". */
  subject: string;
  /** Native render size. Mapped onto the monitor quad by ScreenInsert. */
  width?: number;
  height?: number;
};

const T = {
  bg: '#070A11',
  panel: '#0B111C',
  chrome: '#0E1524',
  grid: 'rgba(126,150,190,0.13)',
  gridStrong: 'rgba(126,150,190,0.22)',
  axis: '#5E6E88',
  level: '#E0A23B',
};

export const TapeChart: React.FC<TapeChartProps> = ({
  candles,
  appearFrames,
  formFrames,
  levelPrice,
  levelLabel,
  levelInFrame,
  subject,
  width = 1280,
  height = 800,
}) => {
  const frame = useCurrentFrame();

  // ------------------------------------------------------------- geometry
  const CHROME_H = 54;
  const PLOT = {x0: 62, x1: width - 186, y0: CHROME_H + 46, y1: height - 92};

  // The price scale is fixed by the WHOLE series, not by what has printed so
  // far. A rescaling axis would make earlier bars slide around as new ones
  // arrive, which no real terminal does and which would break the perspective
  // illusion badly.
  const lo = Math.min(...candles.map((k) => k.l));
  const hi = Math.max(...candles.map((k) => k.h));
  const pad = (hi - lo) * 0.08;
  const yLo = lo - pad;
  const yHi = hi + pad;
  const priceToY = (v: number) =>
    PLOT.y1 - ((v - yLo) / (yHi - yLo)) * (PLOT.y1 - PLOT.y0);

  const slot = (PLOT.x1 - PLOT.x0) / candles.length;
  const bodyW = Math.min(26, slot * 0.62);
  const cx = (i: number) => PLOT.x0 + slot * i + slot / 2;

  // --------------------------------------------------------------- grid
  const gridStep = (yHi - yLo) / 5;
  const gridLines = Array.from({length: 6}, (_, i) => yLo + gridStep * i);

  // -------------------------------------------------------------- level
  const levelY = priceToY(levelPrice);
  const levelP = interpolate(frame, [levelInFrame, levelInFrame + 20], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // ------------------------------------------------------- live price tag
  // Index of the last bar that has begun printing.
  let lastIdx = -1;
  for (let i = 0; i < candles.length; i++) {
    if (frame >= appearFrames[i]) lastIdx = i;
  }

  /** The live print of bar `i` at the current frame — the same tick maths the
   * bar itself draws with, so the tag and the candle never disagree. */
  const livePrint = (i: number): {close: number; hNow: number; lNow: number; settled: boolean} | null => {
    const k = candles[i];
    if (!k) return null;
    const form = formFrames?.[i] ?? CANDLE_FORM;
    // A long-form bar gets proportionally more ticks, so a 46-frame story bar
    // wanders through its range instead of holding three values for 15 frames
    // each. Short bars keep exactly the cadence TradingQuiz established.
    const ticks = Math.max(CANDLE_TICKS, Math.round((form / CANDLE_FORM) * CANDLE_TICKS));
    const raw = (frame - appearFrames[i]) / form;
    if (raw <= 0) return null;
    const step = Math.min(ticks, Math.ceil(Math.min(1, raw) * ticks));
    const settled = step >= ticks;
    const f = step / ticks;
    // Wicks only ever widen: a bar's high cannot come back down once traded.
    const hNow = k.o + (k.h - k.o) * Math.min(1, f * 1.22);
    const lNow = k.o + (k.l - k.o) * Math.min(1, f * 1.22);
    // Mid-bar the last trade wanders inside the range; the closing tick lands
    // exactly on `c`. Seeded off (bar, tick) so every render is identical.
    const drift = (random(`tc${i}t${step}`) - 0.5) * (k.h - k.l) * 0.7;
    const close = settled
      ? k.c
      : Math.max(lNow, Math.min(hNow, k.o + (k.c - k.o) * f + drift));
    return {close, hNow, lNow, settled};
  };

  const live = lastIdx >= 0 ? livePrint(lastIdx) : null;
  const liveClose = live?.close ?? candles[0].o;
  const liveUp = lastIdx >= 0 ? liveClose >= candles[lastIdx].o : true;
  const tagColor = liveUp ? C.emerald : C.redHot;
  const tagY = priceToY(liveClose);

  const renderCandle = (i: number) => {
    const p = livePrint(i);
    if (!p) return null;
    const k = candles[i];
    const col = p.close >= k.o ? C.emerald : C.redHot;
    const x = cx(i);
    const yTop = priceToY(Math.max(k.o, p.close));
    const yBot = priceToY(Math.min(k.o, p.close));
    return (
      <g
        key={i}
        style={{filter: `drop-shadow(0 0 ${p.settled ? 5 : 10}px ${col}${p.settled ? '66' : 'bb'})`}}
      >
        <line x1={x} x2={x} y1={priceToY(p.hNow)} y2={priceToY(p.lNow)} stroke={col} strokeWidth={2.6} />
        <rect
          x={x - bodyW / 2}
          y={yTop}
          width={bodyW}
          height={Math.max(2.5, yBot - yTop)}
          rx={2}
          fill={col}
        />
      </g>
    );
  };

  // A bar whose high has traded through the level while its live close is
  // still below it — the moment the reel is about. Purely a highlight of what
  // the data already says; it asserts nothing the bars do not.
  const pokingThrough =
    live !== null && live.hNow > levelPrice && live.close < levelPrice;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      style={{display: 'block'}}
    >
      <rect x={0} y={0} width={width} height={height} fill={T.bg} />

      {/* ------------------------------------------------------ chrome bar */}
      <rect x={0} y={0} width={width} height={CHROME_H} fill={T.chrome} />
      <line x1={0} x2={width} y1={CHROME_H} y2={CHROME_H} stroke={T.grid} strokeWidth={1.5} />
      <circle cx={26} cy={CHROME_H / 2} r={6} fill={C.emerald} opacity={0.55 + Math.sin(frame / 9) * 0.35} />
      <text
        x={48}
        y={CHROME_H / 2 + 7}
        fontFamily={FONT.mono}
        fontSize={21}
        fill={C.inkSoft}
        letterSpacing={2.2}
      >
        {subject}
      </text>
      <text
        x={width - 24}
        y={CHROME_H / 2 + 7}
        fontFamily={FONT.mono}
        fontSize={18}
        fill={T.axis}
        textAnchor="end"
        letterSpacing={1.6}
      >
        LIVE TAPE
      </text>

      {/* ----------------------------------------------------------- grid */}
      {gridLines.map((v, i) => {
        const y = priceToY(v);
        return (
          <g key={`g${i}`}>
            <line x1={PLOT.x0} x2={PLOT.x1} y1={y} y2={y} stroke={T.grid} strokeWidth={1.2} />
            <text
              x={PLOT.x1 + 16}
              y={y + 6}
              fontFamily={FONT.mono}
              fontSize={19}
              fill={T.axis}
            >
              {v.toFixed(0)}
            </text>
          </g>
        );
      })}
      {/* vertical rules every 4 bars — enough to read time, not enough to
          compete with the candles */}
      {candles.map((_, i) =>
        i % 4 === 0 ? (
          <line
            key={`v${i}`}
            x1={cx(i)}
            x2={cx(i)}
            y1={PLOT.y0}
            y2={PLOT.y1}
            stroke={T.grid}
            strokeWidth={1}
            opacity={0.55}
          />
        ) : null
      )}
      <line x1={PLOT.x0} x2={PLOT.x1} y1={PLOT.y1} y2={PLOT.y1} stroke={T.gridStrong} strokeWidth={1.6} />

      {/* ---------------------------------------------------------- level */}
      <g opacity={levelP}>
        <line
          x1={PLOT.x0}
          x2={PLOT.x0 + (PLOT.x1 - PLOT.x0) * levelP}
          y1={levelY}
          y2={levelY}
          stroke={T.level}
          strokeWidth={2.4}
          strokeDasharray="12 9"
          opacity={pokingThrough ? 0.6 + Math.sin(frame / 4) * 0.4 : 0.85}
        />
        <rect
          x={PLOT.x1 + 8}
          y={levelY - 17}
          width={168}
          height={34}
          rx={5}
          fill={T.level}
          opacity={0.16}
        />
        <text
          x={PLOT.x1 + 18}
          y={levelY + 6}
          fontFamily={FONT.mono}
          fontSize={19}
          fill={T.level}
          letterSpacing={1.1}
        >
          {levelLabel}
        </text>
      </g>

      {/* --------------------------------------------------------- candles */}
      {candles.map((_, i) => renderCandle(i))}

      {/* -------------------------------------------------- live price tag */}
      {/* PRICE ONLY. Never a P&L figure — see the module header. */}
      {lastIdx >= 0 ? (
        <g>
          <line
            x1={PLOT.x0}
            x2={PLOT.x1 + 4}
            y1={tagY}
            y2={tagY}
            stroke={tagColor}
            strokeWidth={1.2}
            strokeDasharray="4 6"
            opacity={0.45}
          />
          <rect x={PLOT.x1 + 8} y={tagY - 20} width={124} height={40} rx={6} fill={tagColor} />
          <text
            x={PLOT.x1 + 70}
            y={tagY + 8}
            fontFamily={FONT.mono}
            fontSize={24}
            fontWeight={700}
            fill="#06131C"
            textAnchor="middle"
          >
            {liveClose.toFixed(2)}
          </text>
        </g>
      ) : null}

      {/* ------------------------------------------------------ axis strip */}
      <text
        x={PLOT.x0}
        y={height - 46}
        fontFamily={FONT.mono}
        fontSize={18}
        fill={T.axis}
        letterSpacing={1.4}
      >
        DAILY BARS · IBKR
      </text>
      <text
        x={PLOT.x1}
        y={height - 46}
        fontFamily={FONT.mono}
        fontSize={18}
        fill={T.axis}
        textAnchor="end"
        letterSpacing={1.4}
      >
        PRICE — NOT P&amp;L
      </text>
    </svg>
  );
};
