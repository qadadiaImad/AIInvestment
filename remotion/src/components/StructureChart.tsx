// StructureChart.tsx — the structure-drawing chart used by the 40s trade-fail
// reels: TradeFailReel plays it inside a monitor in a room; TradeFailCam plays
// it full-frame as the screen itself. TapeChart's cousin, one level up: it
// draws market STRUCTURE (support/resistance zones, a validated trendline, the
// pattern tag) and then a bounded trade on top of it, rather than a single
// horizontal level.
//
// Everything it draws is computed in Python by scripts/btc_reel/find_failed_setup.py
// and arrives as a fixture. This component decides WHEN each element appears
// and HOW it is drawn; it never decides WHERE a level sits, which pivots count
// as touches, or whether the trade won. Per CLAUDE.md §10.1 the numbers are not
// authored here and cannot be — there is no arithmetic in this file that could
// move a level.
//
// `ui` scales the CHROME — fonts, label boxes, tag rects — without touching
// the price geometry. It exists because the same component now renders at two
// very different final sizes: mapped down onto a 417px-wide monitor (ui=1) and
// full-bleed on a 1080px phone screen (ui≈1.3). Type sized for the first is
// squint-material at the second, and scaling the whole SVG would fatten the
// candles too.
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

  /** Frame the stop FIRES, visually: a short terminal-style alarm — red wash
   * over the plot, the stop line pulsing. This is the one moment the panel is
   * allowed to editorialise, because it is not editorial: a stop order
   * triggering IS an alarm, and the wash marks the event the data itself
   * produced. Omit for no alarm. */
  alarmAt?: number;

  subject: string;
  stamp: string;
  width?: number;
  height?: number;
  /** Chrome scale — see the header. 1 for the monitor insert, ~1.3 full-frame. */
  ui?: number;
  /** Frames [from, to) during which the live price tag drops its tick colour
   * for a neutral slate. The colour is tick direction — data — but a red pill
   * held through an entire countdown reads as a lean toward one answer, and
   * the candles still carry the direction. Same rule as the neutral ring. */
  neutralTagDuring?: [number, number];
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
  alarmAt,
  subject,
  stamp,
  width = 1324,
  height = 800,
  ui = 1,
  neutralTagDuring,
}) => {
  const frame = useCurrentFrame();
  const U = (n: number) => n * ui;

  const CHROME_H = U(52);
  const PLOT = {x0: 66, x1: width - U(168), y0: CHROME_H + U(40), y1: height - U(78)};

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
  const tagNeutral =
    neutralTagDuring !== undefined && frame >= neutralTagDuring[0] && frame < neutralTagDuring[1];
  const tagFill = tagNeutral ? '#9FB4A9' : liveUp ? T.up : T.down;

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

  // The pattern tag POPS — anticipatePop-style overshoot about its own centre
  // — rather than fading in. A label that fades reads as UI; a label that pops
  // reads as a call.
  const patS = interpolate(frame, [patternIn, patternIn + 13], [1.28, 1], {
    easing: EASE.settleBack,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const gridStep = (yHi - yLo) / 5;

  /** The PEN. While a line is drawing, a bright head rides its leading edge —
   * the difference between a line that is being DRAWN and a line that is
   * merely appearing. Gone the moment the draw completes. */
  const pen = (x: number, y: number, colour: string, prog: number) =>
    prog > 0.02 && prog < 0.985 ? (
      <circle
        cx={x}
        cy={y}
        r={U(5)}
        fill="#EAFFF4"
        style={{filter: `drop-shadow(0 0 ${U(9)}px ${colour})`}}
        opacity={0.95}
      />
    ) : null;

  /** A zone is a BAND, not a line — that is the whole reason the scanner
   * clusters pivots instead of picking one. Drawing it as a hairline would
   * assert a precision the data does not have. */
  const band = (price: number, colour: string, prog: number, label: string, side: 'up' | 'down') => {
    const halfPx = Math.max(5, Math.abs(priceToY(price * 0.994) - priceToY(price * 1.006)) / 2);
    const y = priceToY(price);
    // The live price tag rides the same right-hand rail. While it is passing
    // through this label's slot, the label steps back — two boxes stacked at
    // the same y are neither readable.
    const tagNear = lastIdx >= 0 && Math.abs(priceToY(liveClose) - y) < U(38);
    const labelOp = tagNear ? 0.22 : 1;
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
        {pen(PLOT.x0 + (PLOT.x1 - PLOT.x0) * prog, y, colour, prog)}
        <rect
          x={PLOT.x1 + U(6)}
          y={y - U(15)}
          width={U(152)}
          height={U(30)}
          rx={4}
          fill={colour}
          opacity={0.18 * labelOp}
        />
        <text
          x={PLOT.x1 + U(14)}
          y={y + U(6)}
          fontFamily={FONT.mono}
          fontSize={U(17)}
          fill={colour}
          letterSpacing={1}
          opacity={labelOp}
        >
          {label}
        </text>
        {/* the actual pivots the level was built from — the evidence, drawn */}
        <g opacity={prog}>
          {(side === 'up' ? resistance?.bars ?? [] : support.bars).map((bi) =>
            frame >= appearFrames[bi] ? (
              <circle key={bi} cx={cx(bi)} cy={y} r={U(4.5)} fill="none" stroke={colour} strokeWidth={2} />
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

  // Pattern-tag geometry, shared by the box and its pop transform.
  const tagRectX = Math.min(cx(triggerBar) - U(132), PLOT.x1 - U(268));
  const tagTextX = Math.min(cx(triggerBar), PLOT.x1 - U(136));
  const tagY = frame >= appearFrames[triggerBar] ? priceToY(bars[triggerBar].l) : 0;

  // The alarm — see the prop doc. 18 frames, decaying.
  const alarmT =
    alarmAt !== undefined && frame >= alarmAt && frame < alarmAt + 18 ? (frame - alarmAt) / 18 : null;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{display: 'block'}}>
      <rect x={0} y={0} width={width} height={height} fill={T.bg} />

      {/* -------------------------------------------------------- chrome */}
      <rect x={0} y={0} width={width} height={CHROME_H} fill={T.chrome} />
      <line x1={0} x2={width} y1={CHROME_H} y2={CHROME_H} stroke={T.gridBold} strokeWidth={1.5} />
      <circle cx={U(26)} cy={CHROME_H / 2} r={U(6)} fill={T.up} opacity={0.55 + Math.sin(frame / 9) * 0.35} />
      <text x={U(46)} y={CHROME_H / 2 + U(7)} fontFamily={FONT.mono} fontSize={U(20)} fill="#BFE9D2" letterSpacing={2}>
        {subject}
      </text>
      <text
        x={width - U(22)}
        y={CHROME_H / 2 + U(7)}
        fontFamily={FONT.mono}
        fontSize={U(15)}
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
            <text
              x={PLOT.x1 + U(122)}
              y={y + U(6)}
              fontFamily={FONT.mono}
              fontSize={U(17)}
              fill={T.axis}
              textAnchor="end"
            >
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
          {pen(
            cx(trendline.from) + (cx(setupBars - 1) - cx(trendline.from)) * trendP,
            priceToY(tlY(trendline.from) + (tlY(setupBars - 1) - tlY(trendline.from)) * trendP),
            T.trend,
            trendP
          )}
          <text
            x={cx(trendline.from) + U(10)}
            y={priceToY(tlY(trendline.from)) + U(26)}
            fontFamily={FONT.mono}
            fontSize={U(16)}
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
              {pen(cx(setupBars - 1) + (PLOT.x1 - cx(setupBars - 1)) * tradeP, priceToY(l.v), l.c, tradeP)}
              {/* At full-frame scale the label would run under the live price
                  tag (the tag sits just outside the plot's right edge), so it
                  right-aligns INSIDE the plot instead — the terminal idiom for
                  an order label. At monitor scale the original fits. */}
              <text
                x={ui > 1.15 ? PLOT.x1 - U(6) : cx(setupBars - 1) + U(10)}
                y={priceToY(l.v) - U(7)}
                fontFamily={FONT.mono}
                fontSize={U(17)}
                fontWeight={700}
                fill={l.c}
                letterSpacing={1}
                textAnchor={ui > 1.15 ? 'end' : 'start'}
              >
                {l.t}
              </text>
            </g>
          ))}
        </g>
      ) : null}

      {/* -------------------------------------------------------- candles.
          Clipped to the plot: once the axis narrows to the DECISION view, the
          early bars' prices map far above y0, and unclipped wicks punch
          through the chrome bar. Only the candles need the clip — every drawn
          level is near price by construction. */}
      <clipPath id="sc-plot-clip">
        <rect x={PLOT.x0 - 20} y={PLOT.y0} width={PLOT.x1 - PLOT.x0 + 40} height={PLOT.y1 - PLOT.y0} />
      </clipPath>
      <g clipPath="url(#sc-plot-clip)">{bars.map((_, i) => renderCandle(i))}</g>

      {/* --------------------------------------------------- the alarm.
          The stop fired. Red wash + the stop line pulsing, 18 frames. */}
      {alarmT !== null ? (
        <g>
          <rect
            x={PLOT.x0}
            y={PLOT.y0}
            width={PLOT.x1 - PLOT.x0}
            height={PLOT.y1 - PLOT.y0}
            fill={T.down}
            opacity={0.13 * (1 - alarmT)}
          />
          <line
            x1={cx(setupBars - 1)}
            x2={PLOT.x1}
            y1={priceToY(stop)}
            y2={priceToY(stop)}
            stroke={T.down}
            strokeWidth={2 + 3.5 * (1 - alarmT)}
            style={{filter: `drop-shadow(0 0 ${U(10)}px ${T.down})`}}
          />
          {/* BELOW the line — "STOP 49.15" is right-aligned just above it,
              and stacking the two at the same y mushed the climax frame. */}
          <text
            x={PLOT.x1 - U(8)}
            y={priceToY(stop) + U(28)}
            fontFamily={FONT.mono}
            fontSize={U(19)}
            fontWeight={700}
            fill={T.down}
            textAnchor="end"
            letterSpacing={1.4}
            opacity={1 - alarmT * 0.6}
          >
            STOP FILLED
          </text>
        </g>
      ) : null}

      {/* ------------------------------------------------- the pattern tag.
          Boxed, pointing at the actual bar. The label is the scanner's own
          verdict string — this component does not classify candles. */}
      {patP > 0 && frame >= appearFrames[triggerBar] ? (
        <g
          opacity={patP}
          transform={`translate(${tagTextX} ${tagY + U(61)}) scale(${patS}) translate(${-tagTextX} ${-(
            tagY + U(61)
          )})`}
        >
          <line x1={cx(triggerBar)} y1={tagY + U(12)} x2={cx(triggerBar)} y2={tagY + U(44)} stroke={T.ice} strokeWidth={2} />
          <rect
            x={tagRectX}
            y={tagY + U(44)}
            width={U(264)}
            height={U(34)}
            rx={5}
            fill="#04140D"
            stroke={T.ice}
            strokeWidth={1.6}
          />
          <text
            x={tagTextX}
            y={tagY + U(67)}
            fontFamily={FONT.mono}
            fontSize={U(17)}
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
            stroke={tagFill}
            strokeWidth={1.1}
            strokeDasharray="4 6"
            opacity={0.4}
          />
          <rect
            x={PLOT.x1 + U(6)}
            y={priceToY(liveClose) - U(18)}
            width={U(112)}
            height={U(36)}
            rx={U(5)}
            fill={tagFill}
          />
          <text
            x={PLOT.x1 + U(62)}
            y={priceToY(liveClose) + U(8)}
            fontFamily={FONT.mono}
            fontSize={U(22)}
            fontWeight={700}
            fill="#03130B"
            textAnchor="middle"
          >
            {liveClose.toFixed(2)}
          </text>
        </g>
      ) : null}

      {/* At full-frame scale the two strips would collide mid-panel, so the
          left one shortens — the full provenance line is in the footer. */}
      <text x={PLOT.x0} y={height - U(34)} fontFamily={FONT.mono} fontSize={U(16)} fill={T.axis} letterSpacing={1.3}>
        {ui > 1.15 ? 'DAILY BARS · IBKR · NOT DRAWN' : 'DAILY BARS · IBKR · STRUCTURE FOUND, NOT DRAWN'}
      </text>
      <text
        x={PLOT.x1}
        y={height - U(34)}
        fontFamily={FONT.mono}
        fontSize={U(16)}
        fill={T.axis}
        textAnchor="end"
        letterSpacing={1.3}
      >
        PRICE — NOT P&amp;L
      </text>
    </svg>
  );
};
