// StructureChart.tsx — the chart that plays inside the monitor on the 40s
// trade-fail reel. TapeChart's cousin, one level up: it draws market STRUCTURE
// (support/resistance zones, a validated trendline, the pattern tag) and then a
// bounded trade on top of it, rather than a single horizontal level.
//
// Everything it draws is computed in Python by scripts/btc_reel/find_failed_setup.py
// and arrives as a fixture. This component decides WHEN each element appears
// and HOW it is drawn; it never decides WHERE a level sits, which pivots count
// as touches, or whether the trade won. Per CLAUDE.md §10.1 the numbers are not
// authored here and cannot be — there is no arithmetic in this file that could
// move a level.
//
// It renders at its own native 1324x800 and is perspective-mapped onto the
// monitor quad by ScreenInsert. Rendering large and mapping down is what keeps
// the type legible after the homography squashes it.
//
// ------------------------------------------------------------------------
// THE Y-AXIS IS THE ANSWER LEAK, AND IT IS THE WHOLE REASON THIS FILE IS LONG.
//
// CLAUDE.md §10.3 records this failing once already: an axis scaled to include
// the reveal leaves empty headroom on whichever side price is about to travel,
// and a viewer reads that headroom before the timer ends. So the axis moves
// through three deliberate views:
//
//   1. CONTEXT   the whole setup window. The downtrend into the base is the
//                reason the level matters, so the viewer has to see it.
//   2. DECISION  entry +/- k*risk, EXACTLY SYMMETRIC. This is the view the quiz
//                is asked over. Symmetric is not a style choice: any asymmetry
//                is a hint, and the padding is derived from the trade's own
//                risk so it cannot be quietly tuned toward the outcome.
//   3. OUTCOME   opened downward only as the reveal actually prints.
//
// View 2 is also the readable one — the trade occupies ~40% of the panel
// instead of ~20% — so the honest framing and the legible framing are the same
// framing, which is the only reason this is not a running temptation.
import React from 'react';
import {interpolate, random, useCurrentFrame} from 'remotion';
import {FONT} from '../slides/theme';
import {EASE} from '../motion/craft';

export type Bar = {d?: string; o: number; h: number; l: number; c: number};
export type Zone = {price: number; touches: number; bars: number[]};
export type Trendline = {m: number; c: number; from: number; touches: number};

const CANDLE_TICKS = 3;

/** Half-width of the DECISION view, in units of the trade's own risk. 4R puts
 * the stop a quarter of the way down and the 2R target halfway up, with the
 * same slack above the target as below the stop. */
const DECISION_R = 4.0;

const T = {
  bg: '#02070A',
  chrome: '#04100C',
  grid: 'rgba(0,224,130,0.055)',
  gridBold: 'rgba(0,224,130,0.115)',
  axis: '#4E7A64',
  ice: '#22E07E',
  up: '#00E676',
  down: '#FF3B30',
  sup: '#38BDF8',
  res: '#E0A23B',
  trend: '#A78BFA',
};

export type StructureChartProps = {
  bars: Bar[];
  setupBars: number;
  /** Frame each bar starts printing, and how long it takes. The composition
   * owns the beat: the hammer and the break get long prints, the history and
   * the collapse get short ones. */
  appearFrames: number[];
  formFrames: number[];

  support: Zone;
  resistance?: Zone;
  trendline?: Trendline | null;
  /** Bar index of the reversal candle, and what the scanner called it. */
  triggerBar: number;
  triggerName: string;

  entry: number;
  stop: number;
  target: number;

  /** When each layer draws in. */
  supportIn: number;
  resistanceIn: number;
  trendIn: number;
  patternIn: number;
  tradeIn: number;
  /** Frame the axis starts easing from CONTEXT to DECISION, and from DECISION
   * to OUTCOME. */
  decisionIn: number;
  outcomeIn: number;

  subject: string;
  stamp: string;
  width?: number;
  height?: number;
};

export const StructureChart: React.FC<StructureChartProps> = ({
  bars,
  setupBars,
  appearFrames,
  formFrames,
  support,
  resistance,
  trendline,
  triggerBar,
  triggerName,
  entry,
  stop,
  target,
  supportIn,
  resistanceIn,
  trendIn,
  patternIn,
  tradeIn,
  decisionIn,
  outcomeIn,
  subject,
  stamp,
  width = 1324,
  height = 800,
}) => {
  const frame = useCurrentFrame();

  const CHROME_H = 52;
  const PLOT = {x0: 66, x1: width - 168, y0: CHROME_H + 40, y1: height - 78};

  // ------------------------------------------------------------- the axis
  const setup = bars.slice(0, setupBars);
  const ctxLo = Math.min(...setup.map((k) => k.l));
  const ctxHi = Math.max(...setup.map((k) => k.h));
  const ctxPad = (ctxHi - ctxLo) * 0.07;

  const risk = entry - stop;
  // Symmetric about entry, sized by risk. Nothing in here can be nudged toward
  // the outcome without changing the trade itself.
  const decHalf = DECISION_R * risk;
  const decLo = entry - decHalf;
  const decHi = entry + decHalf;

  const outLo = Math.min(...bars.map((k) => k.l));
  const outPad = (decHi - outLo) * 0.05;

  const toDecision = interpolate(frame, [decisionIn, decisionIn + 44], [0, 1], {
    easing: EASE.cruise,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const toOutcome = interpolate(frame, [outcomeIn, outcomeIn + 52], [0, 1], {
    easing: EASE.cruise,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const mix = (a: number, b: number, t: number) => a + (b - a) * t;
  const yLo = mix(mix(ctxLo - ctxPad, decLo, toDecision), outLo - outPad, toOutcome);
  const yHi = mix(mix(ctxHi + ctxPad, decHi, toDecision), decHi, toOutcome);

  const priceToY = (v: number) => PLOT.y1 - ((v - yLo) / (yHi - yLo)) * (PLOT.y1 - PLOT.y0);

  const slot = (PLOT.x1 - PLOT.x0) / bars.length;
  const bodyW = Math.max(2.5, Math.min(18, slot * 0.62));
  const wickW = Math.max(1.1, Math.min(2.4, bodyW * 0.3));
  const cx = (i: number) => PLOT.x0 + slot * i + slot / 2;

  // ------------------------------------------------------- the tape engine
  // Identical to TapeChart/TradingQuiz: discrete hard ticks, wicks that only
  // widen, a live print that wanders inside the bar's range and only commits
  // on the final tick. Candles print like tape, not like an animation.
  const livePrint = (i: number) => {
    const k = bars[i];
    if (!k) return null;
    const form = formFrames[i];
    const ticks = Math.max(CANDLE_TICKS, Math.round((form / 6) * CANDLE_TICKS));
    const raw = (frame - appearFrames[i]) / form;
    if (raw <= 0) return null;
    const step = Math.min(ticks, Math.ceil(Math.min(1, raw) * ticks));
    const settled = step >= ticks;
    const f = step / ticks;
    const hNow = k.o + (k.h - k.o) * Math.min(1, f * 1.22);
    const lNow = k.o + (k.l - k.o) * Math.min(1, f * 1.22);
    const drift = (random(`sc${i}t${step}`) - 0.5) * (k.h - k.l) * 0.7;
    const close = settled ? k.c : Math.max(lNow, Math.min(hNow, k.o + (k.c - k.o) * f + drift));
    return {close, hNow, lNow, settled};
  };

  let lastIdx = -1;
  for (let i = 0; i < bars.length; i++) if (frame >= appearFrames[i]) lastIdx = i;
  const live = lastIdx >= 0 ? livePrint(lastIdx) : null;
  const liveClose = live?.close ?? bars[0].o;
  const liveUp = lastIdx >= 0 ? liveClose >= bars[lastIdx].o : true;

  // ------------------------------------------------------------ draw-in ps
  const p = (at: number, dur = 22) =>
    interpolate(frame, [at, at + dur], [0, 1], {
      easing: EASE.enter,
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  const supP = p(supportIn);
  const resP = resistance ? p(resistanceIn) : 0;
  const trendP = trendline ? p(trendIn, 28) : 0;
  const patP = p(patternIn, 16);
  const tradeP = p(tradeIn, 26);

  const gridStep = (yHi - yLo) / 5;

  /** A zone is a BAND, not a line — that is the whole reason the scanner
   * clusters pivots instead of picking one. Drawing it as a hairline would
   * assert a precision the data does not have. */
  const band = (price: number, colour: string, prog: number, label: string, side: 'up' | 'down') => {
    const halfPx = Math.max(5, Math.abs(priceToY(price * 0.994) - priceToY(price * 1.006)) / 2);
    const y = priceToY(price);
    return (
      <g opacity={prog}>
        <rect
          x={PLOT.x0}
          y={y - halfPx}
          width={(PLOT.x1 - PLOT.x0) * prog}
          height={halfPx * 2}
          fill={colour}
          opacity={0.13}
        />
        <line
          x1={PLOT.x0}
          x2={PLOT.x0 + (PLOT.x1 - PLOT.x0) * prog}
          y1={y}
          y2={y}
          stroke={colour}
          strokeWidth={2.2}
          strokeDasharray="11 8"
        />
        <rect x={PLOT.x1 + 6} y={y - 15} width={152} height={30} rx={4} fill={colour} opacity={0.18} />
        <text
          x={PLOT.x1 + 14}
          y={y + 6}
          fontFamily={FONT.mono}
          fontSize={17}
          fill={colour}
          letterSpacing={1}
        >
          {label}
        </text>
        {/* the actual pivots the level was built from — the evidence, drawn */}
        <g opacity={prog}>
          {(side === 'up' ? resistance?.bars ?? [] : support.bars).map((bi) =>
            frame >= appearFrames[bi] ? (
              <circle key={bi} cx={cx(bi)} cy={y} r={4.5} fill="none" stroke={colour} strokeWidth={2} />
            ) : null
          )}
        </g>
      </g>
    );
  };

  const renderCandle = (i: number) => {
    const pr = livePrint(i);
    if (!pr) return null;
    const k = bars[i];
    const col = pr.close >= k.o ? T.up : T.down;
    const x = cx(i);
    const yTop = priceToY(Math.max(k.o, pr.close));
    const yBot = priceToY(Math.min(k.o, pr.close));
    return (
      <g key={i} style={{filter: `drop-shadow(0 0 ${pr.settled ? 4 : 9}px ${col}${pr.settled ? '55' : 'bb'})`}}>
        <line x1={x} x2={x} y1={priceToY(pr.hNow)} y2={priceToY(pr.lNow)} stroke={col} strokeWidth={wickW} />
        <rect x={x - bodyW / 2} y={yTop} width={bodyW} height={Math.max(2, yBot - yTop)} rx={1.5} fill={col} />
      </g>
    );
  };

  const tlY = (i: number) => (trendline ? trendline.m * i + trendline.c : 0);

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{display: 'block'}}>
      <rect x={0} y={0} width={width} height={height} fill={T.bg} />

      {/* -------------------------------------------------------- chrome */}
      <rect x={0} y={0} width={width} height={CHROME_H} fill={T.chrome} />
      <line x1={0} x2={width} y1={CHROME_H} y2={CHROME_H} stroke={T.gridBold} strokeWidth={1.5} />
      <circle cx={26} cy={CHROME_H / 2} r={6} fill={T.up} opacity={0.55 + Math.sin(frame / 9) * 0.35} />
      <text x={46} y={CHROME_H / 2 + 7} fontFamily={FONT.mono} fontSize={20} fill="#BFE9D2" letterSpacing={2}>
        {subject}
      </text>
      <text
        x={width - 22}
        y={CHROME_H / 2 + 7}
        fontFamily={FONT.mono}
        fontSize={15}
        fill={T.axis}
        textAnchor="end"
        letterSpacing={1.2}
      >
        {stamp}
      </text>

      {/* ---------------------------------------------------------- grid */}
      {Array.from({length: 6}, (_, i) => yLo + gridStep * i).map((v, i) => {
        const y = priceToY(v);
        return (
          <g key={`g${i}`}>
            <line x1={PLOT.x0} x2={PLOT.x1} y1={y} y2={y} stroke={T.grid} strokeWidth={1.1} />
            <text x={PLOT.x1 + 122} y={y + 6} fontFamily={FONT.mono} fontSize={17} fill={T.axis} textAnchor="end">
              {v.toFixed(1)}
            </text>
          </g>
        );
      })}
      {bars.map((_, i) =>
        i % 8 === 0 ? (
          <line key={`v${i}`} x1={cx(i)} x2={cx(i)} y1={PLOT.y0} y2={PLOT.y1} stroke={T.grid} strokeWidth={1} />
        ) : null
      )}
      <line x1={PLOT.x0} x2={PLOT.x1} y1={PLOT.y1} y2={PLOT.y1} stroke={T.gridBold} strokeWidth={1.5} />

      {/* ------------------------------------------------------ structure */}
      {resistance ? band(resistance.price, T.res, resP, `RES ${resistance.price.toFixed(2)}`, 'up') : null}
      {band(support.price, T.sup, supP, `SUP ${support.price.toFixed(2)}`, 'down')}

      {trendline ? (
        <g opacity={trendP}>
          <line
            x1={cx(trendline.from)}
            y1={priceToY(tlY(trendline.from))}
            x2={cx(trendline.from) + (cx(setupBars - 1) - cx(trendline.from)) * trendP}
            y2={priceToY(
              tlY(trendline.from) + (tlY(setupBars - 1) - tlY(trendline.from)) * trendP
            )}
            stroke={T.trend}
            strokeWidth={2.4}
          />
          <text
            x={cx(trendline.from) + 10}
            y={priceToY(tlY(trendline.from)) + 26}
            fontFamily={FONT.mono}
            fontSize={16}
            fill={T.trend}
            letterSpacing={1}
          >
            {trendline.touches} TOUCHES
          </text>
        </g>
      ) : null}

      {/* ----------------------------------------------------- the trade.
          Drawn BEFORE the quiz, never after. A viewer asked to call a trade
          without seeing what being wrong costs is guessing, and the loss then
          reads as unearned rather than as a bounded, stated bet. */}
      {tradeP > 0 ? (
        <g opacity={tradeP}>
          <rect
            x={cx(setupBars - 1)}
            y={priceToY(target)}
            width={(PLOT.x1 - cx(setupBars - 1)) * tradeP}
            height={Math.max(1, priceToY(entry) - priceToY(target))}
            fill={T.up}
            opacity={0.11}
          />
          <rect
            x={cx(setupBars - 1)}
            y={priceToY(entry)}
            width={(PLOT.x1 - cx(setupBars - 1)) * tradeP}
            height={Math.max(1, priceToY(stop) - priceToY(entry))}
            fill={T.down}
            opacity={0.13}
          />
          {[
            {v: target, c: T.up, t: `TARGET ${target.toFixed(2)}`},
            {v: entry, c: '#E8EDF2', t: `ENTRY ${entry.toFixed(2)}`},
            {v: stop, c: T.down, t: `STOP ${stop.toFixed(2)}`},
          ].map((l) => (
            <g key={l.t}>
              <line
                x1={cx(setupBars - 1)}
                x2={cx(setupBars - 1) + (PLOT.x1 - cx(setupBars - 1)) * tradeP}
                y1={priceToY(l.v)}
                y2={priceToY(l.v)}
                stroke={l.c}
                strokeWidth={2}
              />
              <text
                x={cx(setupBars - 1) + 10}
                y={priceToY(l.v) - 7}
                fontFamily={FONT.mono}
                fontSize={17}
                fontWeight={700}
                fill={l.c}
                letterSpacing={1}
              >
                {l.t}
              </text>
            </g>
          ))}
        </g>
      ) : null}

      {/* -------------------------------------------------------- candles */}
      {bars.map((_, i) => renderCandle(i))}

      {/* ------------------------------------------------- the pattern tag.
          Boxed, pointing at the actual bar. The label is the scanner's own
          verdict string — this component does not classify candles. */}
      {patP > 0 && frame >= appearFrames[triggerBar] ? (
        <g opacity={patP}>
          <line
            x1={cx(triggerBar)}
            y1={priceToY(bars[triggerBar].l) + 12}
            x2={cx(triggerBar)}
            y2={priceToY(bars[triggerBar].l) + 44}
            stroke={T.ice}
            strokeWidth={2}
          />
          <rect
            x={Math.min(cx(triggerBar) - 132, PLOT.x1 - 268)}
            y={priceToY(bars[triggerBar].l) + 44}
            width={264}
            height={34}
            rx={5}
            fill="#04140D"
            stroke={T.ice}
            strokeWidth={1.6}
          />
          <text
            x={Math.min(cx(triggerBar), PLOT.x1 - 136)}
            y={priceToY(bars[triggerBar].l) + 67}
            fontFamily={FONT.mono}
            fontSize={17}
            fontWeight={700}
            fill={T.ice}
            textAnchor="middle"
            letterSpacing={1.1}
          >
            {triggerName}
          </text>
        </g>
      ) : null}

      {/* ------------------------------------------------- live price tag.
          PRICE ONLY — never a P&L figure, per §10.6. */}
      {lastIdx >= 0 ? (
        <g>
          <line
            x1={PLOT.x0}
            x2={PLOT.x1 + 4}
            y1={priceToY(liveClose)}
            y2={priceToY(liveClose)}
            stroke={liveUp ? T.up : T.down}
            strokeWidth={1.1}
            strokeDasharray="4 6"
            opacity={0.4}
          />
          <rect
            x={PLOT.x1 + 6}
            y={priceToY(liveClose) - 18}
            width={112}
            height={36}
            rx={5}
            fill={liveUp ? T.up : T.down}
          />
          <text
            x={PLOT.x1 + 62}
            y={priceToY(liveClose) + 8}
            fontFamily={FONT.mono}
            fontSize={22}
            fontWeight={700}
            fill="#03130B"
            textAnchor="middle"
          >
            {liveClose.toFixed(2)}
          </text>
        </g>
      ) : null}

      <text x={PLOT.x0} y={height - 34} fontFamily={FONT.mono} fontSize={16} fill={T.axis} letterSpacing={1.3}>
        DAILY BARS · IBKR · STRUCTURE FOUND, NOT DRAWN
      </text>
      <text
        x={PLOT.x1}
        y={height - 34}
        fontFamily={FONT.mono}
        fontSize={16}
        fill={T.axis}
        textAnchor="end"
        letterSpacing={1.3}
      >
        PRICE — NOT P&amp;L
      </text>
    </svg>
  );
};
