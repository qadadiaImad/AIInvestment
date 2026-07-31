// PatternCell.tsx — one box of the living cheat sheet: a compact panel in
// which a real pattern DRAWS itself. Candles tape-print, the level dashes in,
// the trendlines pen themselves, the breakout arrow fires, the verdict chip
// pops — all inside a ~510x306 cell that stays on screen for the whole reel,
// beside nine others doing the same.
//
// This is deliberately its own component rather than a third PatternCard
// variant: the hero card and the cell share the tape-engine idiom (the house
// pattern — TapeChart and StructureChart duplicate it too, by design) but
// nothing else: different chrome, different label economy, different pacing.
//
// Geometry comes from the real-pattern fixture (scripts/patterns_post/
// find_real_patterns.py): real candles, real dates, levels and trendlines
// from the detected pivots. This file decides when and how, never where.
import React from 'react';
import {interpolate, random, useCurrentFrame} from 'remotion';
import {FONT} from '../slides/theme';
import {EASE} from '../motion/craft';
import {PT, type PatternData} from './PatternCard';

/** Cell schedule, in the cell's local frames. Adaptive: the setup candles
 * always finish at SETUP_END regardless of bar count, so ten cells with 24-45
 * bars each keep one shared rhythm — the sheet breathes together. */
const T = {
  setupStart: 6,
  setupEnd: 170,
  levelIn: 104,
  trendIn: 140,
  revealPer: 13,
  chipAfter: 14,
};
const CANDLE_TICKS = 3;

/** When this cell's target-hit bar finishes printing, in CELL-LOCAL frames —
 * the composition schedules the coin on exactly this frame so sound and pixel
 * cannot drift apart. Null when the fixture carries no trade. */
export const cellTpFrame = (d: PatternData): number | null => {
  if (d.tpAt === undefined || d.tpAt === null) return null;
  const i = d.revealFrom + d.tpAt;
  return T.setupEnd + 8 + (i - d.revealFrom) * T.revealPer + T.revealPer + 4;
};

export type PatternCellProps = {
  data: PatternData;
  width: number;
  height: number;
};

export const PatternCell: React.FC<PatternCellProps> = ({data, width, height}) => {
  const frame = useCurrentFrame();
  const d = data;
  const n = d.candles.length;

  const HEAD = 36;
  const DATE_H = 30;
  const PAD_R = 52;
  const PLOT = {x0: 10, x1: width - PAD_R, y0: HEAD + 8, y1: height - DATE_H - 8};

  const lo = Math.min(...d.candles.map((k) => k.l));
  const hi = Math.max(...d.candles.map((k) => k.h));
  const pad = (hi - lo) * 0.08;
  const pY = (v: number) => PLOT.y1 - ((v - (lo - pad)) / (hi + pad - (lo - pad))) * (PLOT.y1 - PLOT.y0);
  const slot = (PLOT.x1 - PLOT.x0) / n;
  const cx = (i: number) => PLOT.x0 + slot * i + slot / 2;
  const bodyW = Math.max(2.2, Math.min(12, slot * 0.62));
  const wickW = Math.max(0.9, bodyW * 0.28);

  const setupPer = (T.setupEnd - T.setupStart) / Math.max(1, d.revealFrom);
  const appearAt = (i: number) =>
    i < d.revealFrom ? T.setupStart + i * setupPer : T.setupEnd + 8 + (i - d.revealFrom) * T.revealPer;
  const formOf = (i: number) => (i < d.revealFrom ? Math.max(3, setupPer) : T.revealPer + 4);
  const lastAppear = appearAt(n - 1) + formOf(n - 1);
  const arrowIn = appearAt(Math.min(n - 1, d.revealFrom + 1)) + 6;
  const chipIn = lastAppear + T.chipAfter;

  const livePrint = (i: number) => {
    const k = d.candles[i];
    const raw = (frame - appearAt(i)) / formOf(i);
    if (raw <= 0) return null;
    const step = Math.min(CANDLE_TICKS, Math.ceil(Math.min(1, raw) * CANDLE_TICKS));
    const f = step / CANDLE_TICKS;
    const settled = step >= CANDLE_TICKS;
    const hNow = k.o + (k.h - k.o) * Math.min(1, f * 1.25);
    const lNow = k.o + (k.l - k.o) * Math.min(1, f * 1.25);
    const drift = (random(`s${d.id}c${i}t${step}`) - 0.5) * (k.h - k.l) * 0.6;
    const close = settled ? k.c : Math.max(lNow, Math.min(hNow, k.o + (k.c - k.o) * f + drift));
    return {close, hNow, lNow, settled};
  };

  const prog = (at: number, dur: number) =>
    interpolate(frame, [at, at + dur], [0, 1], {
      easing: EASE.enter,
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  const levelP = prog(T.levelIn, 18);
  const trendP = d.trend ? prog(T.trendIn, 22) : 0;
  const arrowP = prog(arrowIn, 12);
  const chipP = prog(chipIn, 8);
  const chipScale = interpolate(frame, [chipIn, chipIn + 10], [1.45, 1], {
    easing: EASE.settleBack,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const bull = d.bias === 'bullish';
  const dirCol = bull ? PT.up : PT.down;
  const levelY = pY(d.levelPrice);
  const tl = d.trend;
  const tY = (line: {m: number; c: number}, i: number) => pY(line.m * i + line.c);

  const bx = cx(Math.min(n - 1, d.revealFrom + 1));
  const arrowLen = (PLOT.y1 - PLOT.y0) * 0.3;
  const ay1 = bull ? levelY - arrowLen : levelY + arrowLen;

  // The winning trade. All four or none: entry, stop, target, R — a target
  // with no stop shows the upside and hides what being wrong would have cost.
  const hasTrade =
    d.entry !== undefined && d.stop !== undefined && d.target !== undefined && d.rr !== undefined;
  const tradeIn = arrowIn + 8;
  const tradeP = hasTrade ? prog(tradeIn, 14) : 0;
  const tpF = cellTpFrame(d);
  const tpP = tpF !== null ? prog(tpF, 8) : 0;
  const tpPulse =
    tpF !== null && frame >= tpF && frame < tpF + 16
      ? Math.sin(((frame - tpF) / 16) * Math.PI)
      : 0;
  const tx0 = cx(d.revealFrom);

  const shortName = d.name
    .replace('Inverse Head and Shoulders', 'Inv. Head & Shoulders')
    .replace('Head and Shoulders', 'Head & Shoulders')
    .replace(' (continuation)', '');

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{display: 'block'}}>
      <defs>
        <linearGradient id={`cell${d.id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={PT.panelTop} />
          <stop offset="1" stopColor={PT.panelBot} />
        </linearGradient>
      </defs>
      <rect x={0} y={0} width={width} height={height} rx={12} fill={`url(#cell${d.id})`} stroke={PT.edge} strokeWidth={1.4} />
      {/* everything price-anchored clips to the plot — a trendline fitted to
          steep pivots otherwise runs through the box title */}
      <clipPath id={`cellclip${d.id}`}>
        <rect x={1} y={HEAD + 1} width={width - 2} height={height - HEAD - DATE_H - 2} />
      </clipPath>

      {/* --------------------------------------------------------- header */}
      <text x={14} y={24} fontFamily={FONT.mono} fontSize={17} fontWeight={700} fill="#BFE9D2" letterSpacing={0.8}>
        {shortName.toUpperCase()}
      </text>
      <line x1={0} x2={width} y1={HEAD} y2={HEAD} stroke={PT.gridBold} strokeWidth={1.2} />

      {/* verdict chip pops into the header once the break has printed */}
      {chipP > 0 ? (
        <g opacity={chipP} transform={`translate(${width - 40} 18) scale(${chipScale}) translate(${-(width - 40)} -18)`}>
          <rect x={width - 68} y={7} width={56} height={22} rx={6} fill={dirCol} />
          <text x={width - 40} y={23} fontFamily={FONT.mono} fontSize={13.5} fontWeight={700} fill="#04120B" textAnchor="middle" letterSpacing={0.8}>
            {d.answer}
          </text>
        </g>
      ) : null}

      {/* ------------------------------------------------------ trendlines */}
      {tl ? (
        <g opacity={trendP} clipPath={`url(#cellclip${d.id})`}>
          {(['hi', 'lo'] as const).map((side) => {
            const L = tl[side];
            const x0 = cx(tl.from);
            const x1v = cx(tl.to);
            const xE = x0 + (x1v - x0) * trendP;
            const yE = tY(L, tl.from) + (tY(L, tl.to) - tY(L, tl.from)) * trendP;
            return (
              <g key={side}>
                <line x1={x0} y1={tY(L, tl.from)} x2={xE} y2={yE} stroke={PT.trendline} strokeWidth={1.6} opacity={0.85} />
                {trendP > 0.02 && trendP < 0.985 ? (
                  <circle cx={xE} cy={yE} r={3} fill="#EAFFF4" style={{filter: `drop-shadow(0 0 5px ${PT.trendline})`}} />
                ) : null}
              </g>
            );
          })}
        </g>
      ) : null}

      {/* ----------------------------------------------------------- level */}
      <g opacity={levelP}>
        <line
          x1={PLOT.x0}
          x2={PLOT.x0 + (PLOT.x1 - PLOT.x0) * levelP}
          y1={levelY}
          y2={levelY}
          stroke={PT.level}
          strokeWidth={1.4}
          strokeDasharray="7 5"
        />
        <text x={PLOT.x1 + 6} y={levelY + 4} fontFamily={FONT.mono} fontSize={12.5} fill={PT.level}>
          {d.levelPrice.toFixed(0)}
        </text>
      </g>

      {/* --------------------------------------------------------- candles */}
      {d.candles.map((k, i) => {
        const pr = livePrint(i);
        if (!pr) return null;
        const col = pr.close >= k.o ? PT.up : PT.down;
        const x = cx(i);
        const yT = pY(Math.max(k.o, pr.close));
        const yB = pY(Math.min(k.o, pr.close));
        return (
          <g key={i} style={{filter: `drop-shadow(0 0 ${pr.settled ? 2 : 5}px ${col}${pr.settled ? '44' : 'aa'})`}}>
            <line x1={x} x2={x} y1={pY(pr.hNow)} y2={pY(pr.lNow)} stroke={col} strokeWidth={wickW} />
            <rect x={x - bodyW / 2} y={yT} width={bodyW} height={Math.max(1.6, yB - yT)} rx={1} fill={col} />
          </g>
        );
      })}

      {/* ----------------------------------------------------------- marks */}
      {(d.marks ?? []).map((mk, ix) => {
        const k = d.candles[mk.i];
        if (!k) return null;
        const at = appearAt(mk.i) + formOf(mk.i) + 2;
        if (frame < at) return null;
        const mp = interpolate(frame, [at, at + 8], [0, 1], {
          easing: EASE.settleBack,
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        const above = mk.side === 'above';
        const my = above ? pY(k.h) - 11 : pY(k.l) + 11;
        return (
          <g key={`mk${ix}`} opacity={Math.min(1, mp * 1.3)}>
            <circle cx={cx(mk.i)} cy={my} r={8 * mp} fill="#04140D" stroke={PT.ice} strokeWidth={1.3} />
            <text x={cx(mk.i)} y={my + 3.4} fontFamily={FONT.mono} fontSize={10 * Math.max(0.6, mp)} fontWeight={700} fill={PT.ice} textAnchor="middle">
              {mk.label}
            </text>
          </g>
        );
      })}

      {/* ------------------------------------------------- the trade frame.
          Entry, stop, target — drawn the moment the break prints, resolved
          when the target bar lands. Winners only made this sheet, and the R
          on the chip is the R that really paid. */}
      {hasTrade && tradeP > 0 ? (
        <g opacity={tradeP} clipPath={`url(#cellclip${d.id})`}>
          <rect
            x={tx0}
            y={bull ? pY(d.target!) : pY(d.entry!)}
            width={(PLOT.x1 - tx0) * tradeP}
            height={Math.max(1, Math.abs(pY(d.entry!) - pY(d.target!)))}
            fill={PT.up}
            opacity={0.10 + tpPulse * 0.12}
          />
          <rect
            x={tx0}
            y={bull ? pY(d.entry!) : pY(d.stop!)}
            width={(PLOT.x1 - tx0) * tradeP}
            height={Math.max(1, Math.abs(pY(d.stop!) - pY(d.entry!)))}
            fill={PT.down}
            opacity={0.12}
          />
          {[
            {v: d.target!, c: PT.up},
            {v: d.entry!, c: '#E8EDF2'},
            {v: d.stop!, c: PT.down},
          ].map((l, ix) => (
            <line
              key={ix}
              x1={tx0}
              x2={tx0 + (PLOT.x1 - tx0) * tradeP}
              y1={pY(l.v)}
              y2={pY(l.v)}
              stroke={l.c}
              strokeWidth={ix === 0 && tpPulse > 0 ? 1.6 + tpPulse * 1.6 : 1.3}
              style={ix === 0 && tpPulse > 0 ? {filter: `drop-shadow(0 0 ${4 + tpPulse * 6}px ${PT.up})`} : undefined}
            />
          ))}
          {/* the payoff, on the frame its bar prints — the REAL gain the
              trade banked, with the R beside it. Numbers are the point. */}
          {tpP > 0 ? (
            <g
              opacity={tpP}
              transform={`translate(${PLOT.x1 - 62} ${pY(d.target!) - 14}) scale(${interpolate(tpP, [0, 1], [1.6, 1])}) translate(${-(PLOT.x1 - 62)} ${-(pY(d.target!) - 14)})`}
            >
              <rect x={PLOT.x1 - 124} y={pY(d.target!) - 26} width={124} height={24} rx={6} fill={PT.up} />
              <text
                x={PLOT.x1 - 62}
                y={pY(d.target!) - 9}
                fontFamily={FONT.mono}
                fontSize={13.5}
                fontWeight={700}
                fill="#04120B"
                textAnchor="middle"
                letterSpacing={0.4}
              >
                ✓ +{(d.gainPct ?? 0).toFixed(1)}% · {d.rr!.toFixed(1).replace('.0', '')}R
              </text>
            </g>
          ) : null}
        </g>
      ) : null}

      {/* ----------------------------------------------------------- arrow */}
      <g opacity={arrowP}>
        <line
          x1={bx}
          y1={levelY}
          x2={bx}
          y2={levelY + (ay1 - levelY) * arrowP}
          stroke={dirCol}
          strokeWidth={2.6}
          strokeLinecap="round"
          style={{filter: `drop-shadow(0 0 4px ${dirCol})`}}
        />
        {arrowP > 0.85 ? (
          <path
            d={`M ${bx - 5.5} ${ay1 + (bull ? 8 : -8)} L ${bx} ${ay1} L ${bx + 5.5} ${ay1 + (bull ? 8 : -8)}`}
            fill="none"
            stroke={dirCol}
            strokeWidth={2.6}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ) : null}
      </g>

      {/* ------------------------------------------------------ date strip */}
      <text
        x={width / 2}
        y={height - 11}
        fontFamily={FONT.mono}
        fontSize={13.5}
        fill={PT.steel}
        textAnchor="middle"
        letterSpacing={0.6}
      >
        {d.ticker ?? 'SPY'} · {d.from} → {d.to} · 1D
        {typeof d.sampleN === 'number' && d.sampleN > 0
          ? ` · HIT ${d.sampleWins ?? 0}/${d.sampleN}`
          : ''}
      </text>
    </svg>
  );
};
