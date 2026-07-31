// PatternCard.tsx — one chart formation, drawn live: candles tape-print, the
// trendlines and neckline pen themselves in, the breakout candles fire, an
// arrow marks the break, the verdict stamps.
//
// Used at two sizes by PatternGallery: the HERO card (one pattern at a time,
// full tape-print treatment) and the MINI cell (the assembled poster at the
// end + the collection rail). The mini renders the SETTLED state of exactly
// the same geometry — a close-line silhouette instead of 22 unreadable
// candles, which is also what the classic cheat sheets draw at that size.
//
// The geometry is the fixture's: candles from the validated synthetic pattern
// library, trendlines least-squares fit in Python, the level from the library.
// This file decides when and how; it never invents a price. The post's footer
// declares the illustrations synthetic on every frame — these are idealized
// diagrams, like every cheat sheet's, and are labelled as such.
import React from 'react';
import {interpolate, random, useCurrentFrame} from 'remotion';
import {FONT} from '../slides/theme';
import {EASE} from '../motion/craft';

export type PCandle = {o: number; h: number; l: number; c: number};
export type PTrend = {
  from: number;
  to: number;
  hi: {m: number; c: number};
  lo: {m: number; c: number};
};
export type PatternData = {
  id: number;
  name: string;
  ticker?: string;
  from?: string;
  to?: string;
  bias: string;
  answer: string;
  answerLine: string;
  context: string;
  levelPrice: number;
  levelLabel: string;
  revealFrom: number;
  trend: PTrend | null;
  /** Defining pivots, marked like a textbook diagram: the two tops of a
   * double top, S/H/S of a head-and-shoulders. Computed by the scanner from
   * the ACTUAL pivots it detected — never placed by eye. */
  marks?: {i: number; label: string; side: 'above' | 'below'}[];
  /** The winning trade the scanner verified: entry at the breakout close,
   * stop behind the structure, target actually HIT before the stop. All four
   * or none — a target with no stop shows upside and hides cost. */
  entry?: number;
  stop?: number;
  target?: number;
  rr?: number;
  tpAt?: number | null;
  /** Real percent from entry to the target that was actually hit. */
  gainPct?: number;
  /** What the formation did across EVERY detection of it in the series, not
   * just the one drawn above — the card's own antidote to itself. The drawn
   * instance is a winner by construction (the scanner keeps winners so the
   * card can illustrate a resolution), so without these the sheet reads as a
   * 100% strike rate. `hitRate` is null when nothing was tradeable. */
  hitRate?: number | null;
  sampleN?: number;
  sampleWins?: number;
  sampleOpen?: number;
  candles: PCandle[];
};

export const PT = {
  bg: '#02070A',
  panelTop: '#04100C',
  panelBot: '#020806',
  grid: 'rgba(0,224,130,0.055)',
  gridBold: 'rgba(0,224,130,0.115)',
  edge: 'rgba(0,224,130,0.20)',
  ice: '#22E07E',
  steel: '#4E7A64',
  up: '#00E676',
  down: '#FF3B30',
  level: '#E0A23B',
  trendline: '#8FB6E8',
  ink: '#E8EDF2',
};

const CANDLE_TICKS = 3;

/** Timing inside a hero card, in local frames (card mounts inside a Sequence).
 * The setup candles print quickly, the structure draws while they finish, the
 * BREAKOUT candles get long prints — they are the payoff — and the verdict
 * stamps once the break is undeniable. */
export const CARD_T = {
  setupStart: 4,
  setupPer: 1.6, // ~18 setup candles in ~29 frames
  levelIn: 16,
  trendIn: 26,
  revealStart: 46,
  revealPer: 9,
  arrowIn: 58,
  stampIn: 68,
  total: 96,
};

export type PatternCardProps = {
  data: PatternData;
  width: number;
  height: number;
  /** 'hero' = live tape print driven by the local frame; 'mini' = settled
   * poster cell (close-line silhouette, overlay, arrow, chip). */
  variant: 'hero' | 'mini';
  /** Chapter accent for the mini chip row. */
  accent?: string;
};

export const PatternCard: React.FC<PatternCardProps> = ({data, width, height, variant, accent = PT.ice}) => {
  const frame = useCurrentFrame();
  const hero = variant === 'hero';
  const d = data;
  const n = d.candles.length;

  const CHROME = hero ? 64 : 0;
  const PAD_R = hero ? 108 : 10;
  const PLOT = {
    x0: hero ? 30 : 10,
    x1: width - PAD_R,
    y0: CHROME + (hero ? 26 : 10),
    y1: height - (hero ? 30 : d.name ? 40 : 10),
  };

  const lo = Math.min(...d.candles.map((k) => k.l));
  const hi = Math.max(...d.candles.map((k) => k.h));
  const pad = (hi - lo) * 0.09;
  const pY = (v: number) => PLOT.y1 - ((v - (lo - pad)) / (hi + pad - (lo - pad))) * (PLOT.y1 - PLOT.y0);
  const slot = (PLOT.x1 - PLOT.x0) / n;
  const cx = (i: number) => PLOT.x0 + slot * i + slot / 2;
  const bodyW = Math.max(3, Math.min(26, slot * 0.6));

  // ------------------------------------------------------- hero tape print
  const appearAt = (i: number) =>
    i < d.revealFrom
      ? CARD_T.setupStart + i * CARD_T.setupPer
      : CARD_T.revealStart + (i - d.revealFrom) * CARD_T.revealPer;
  const formOf = (i: number) => (i < d.revealFrom ? 4 : CARD_T.revealPer + 4);

  const livePrint = (i: number) => {
    if (!hero) return {close: d.candles[i].c, hNow: d.candles[i].h, lNow: d.candles[i].l, on: true};
    const k = d.candles[i];
    const raw = (frame - appearAt(i)) / formOf(i);
    if (raw <= 0) return null;
    const step = Math.min(CANDLE_TICKS, Math.ceil(Math.min(1, raw) * CANDLE_TICKS));
    const f = step / CANDLE_TICKS;
    const settled = step >= CANDLE_TICKS;
    const hNow = k.o + (k.h - k.o) * Math.min(1, f * 1.25);
    const lNow = k.o + (k.l - k.o) * Math.min(1, f * 1.25);
    const drift = (random(`p${d.id}c${i}t${step}`) - 0.5) * (k.h - k.l) * 0.6;
    const close = settled ? k.c : Math.max(lNow, Math.min(hNow, k.o + (k.c - k.o) * f + drift));
    return {close, hNow, lNow, on: true, settled};
  };

  const prog = (at: number, dur: number) =>
    hero
      ? interpolate(frame, [at, at + dur], [0, 1], {
          easing: EASE.enter,
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : 1;

  const levelP = prog(CARD_T.levelIn, 16);
  const trendP = d.trend ? prog(CARD_T.trendIn, 22) : 0;
  const arrowP = prog(CARD_T.arrowIn, 12);
  const stampP = prog(CARD_T.stampIn, 10);
  const stampScale = hero
    ? interpolate(frame, [CARD_T.stampIn, CARD_T.stampIn + 11], [1.5, 1], {
        easing: EASE.settleBack,
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;

  const bull = d.bias === 'bullish';
  const dirCol = bull ? PT.up : PT.down;
  const levelY = pY(d.levelPrice);
  const tl = d.trend;
  const tY = (line: {m: number; c: number}, i: number) => pY(line.m * i + line.c);

  // Arrow: from the level at the breakout bar, pointing the way it broke.
  const bx = cx(Math.min(n - 1, d.revealFrom + 1));
  const arrowLen = (PLOT.y1 - PLOT.y0) * 0.3 * (hero ? 1 : 0.85);
  const ay0 = levelY;
  const ay1 = bull ? levelY - arrowLen : levelY + arrowLen;

  const strokeMain = hero ? 3 : 2;

  // The verdict stamp takes whichever top corner the chart leaves emptier —
  // fixed top-left sat exactly on the double top's first peak mark. Emptiness
  // is measured from the data: the corner above the third with the lower
  // highs has more room.
  const third = Math.max(1, Math.floor(n / 3));
  const leftHi = Math.max(...d.candles.slice(0, third).map((k) => k.h));
  const rightHi = Math.max(...d.candles.slice(n - third).map((k) => k.h));
  const stampLeft = leftHi <= rightHi;
  const stX = stampLeft ? PLOT.x0 + 12 : PLOT.x1 - 180;
  const stCx = stX + 84;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{display: 'block'}}>
      <defs>
        <linearGradient id={`pnl${d.id}${variant}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={PT.panelTop} />
          <stop offset="1" stopColor={PT.panelBot} />
        </linearGradient>
      </defs>
      <rect x={0} y={0} width={width} height={height} rx={hero ? 20 : 12} fill={`url(#pnl${d.id}${variant})`} stroke={PT.edge} strokeWidth={1.5} />

      {hero ? (
        <g>
          {/* window chrome, matching the prod quiz reels */}
          <circle cx={30} cy={CHROME / 2} r={7} fill="#FF5F57" />
          <circle cx={56} cy={CHROME / 2} r={7} fill="#FEBC2E" />
          <circle cx={82} cy={CHROME / 2} r={7} fill="#28C840" />
          <text x={108} y={CHROME / 2 + 7} fontFamily={FONT.mono} fontSize={22} fill="#BFE9D2" letterSpacing={2.4}>
            {(d.ticker ?? 'MAYA LAB').toUpperCase()} — {d.name.toUpperCase()}
          </text>
          {/* real data gets its real date range where a live badge would lie */}
          <text x={width - 24} y={CHROME / 2 + 6} fontFamily={FONT.mono} fontSize={16.5} fill={PT.steel} textAnchor="end" letterSpacing={1}>
            {d.from && d.to ? `${d.from} → ${d.to} · 1D` : ''}
          </text>
          <line x1={0} x2={width} y1={CHROME} y2={CHROME} stroke={PT.gridBold} strokeWidth={1.5} />
          {Array.from({length: 5}, (_, i) => {
            const y = PLOT.y0 + ((PLOT.y1 - PLOT.y0) / 4) * i;
            return <line key={i} x1={PLOT.x0} x2={PLOT.x1} y1={y} y2={y} stroke={PT.grid} strokeWidth={1.1} />;
          })}
        </g>
      ) : null}

      {/* ------------------------------------------------------ trendlines */}
      {tl ? (
        <g opacity={hero ? trendP : 0.9}>
          {(['hi', 'lo'] as const).map((side) => {
            const L = tl[side];
            const x0 = cx(tl.from);
            const x1v = cx(tl.to);
            const xEnd = x0 + (x1v - x0) * (hero ? trendP : 1);
            const yEnd = tY(L, tl.from) + (tY(L, tl.to) - tY(L, tl.from)) * (hero ? trendP : 1);
            return (
              <g key={side}>
                <line x1={x0} y1={tY(L, tl.from)} x2={xEnd} y2={yEnd} stroke={PT.trendline} strokeWidth={strokeMain - 0.6} opacity={0.85} />
                {hero && trendP > 0.02 && trendP < 0.985 ? (
                  <circle cx={xEnd} cy={yEnd} r={4.5} fill="#EAFFF4" style={{filter: `drop-shadow(0 0 8px ${PT.trendline})`}} />
                ) : null}
              </g>
            );
          })}
        </g>
      ) : null}

      {/* ----------------------------------------------------------- level */}
      <g opacity={hero ? levelP : 0.95}>
        <line
          x1={PLOT.x0}
          x2={PLOT.x0 + (PLOT.x1 - PLOT.x0) * (hero ? levelP : 1)}
          y1={levelY}
          y2={levelY}
          stroke={PT.level}
          strokeWidth={strokeMain - 0.8}
          strokeDasharray="10 7"
        />
        {hero ? (
          <text x={PLOT.x1 + 8} y={levelY + 6} fontFamily={FONT.mono} fontSize={17} fill={PT.level} letterSpacing={0.8}>
            {d.levelPrice.toFixed(1)}
          </text>
        ) : null}
      </g>

      {/* --------------------------------------------------------- candles
          (hero) — the mini draws a close-line silhouette instead: 22 candles
          at 300px wide are noise, and the line IS what cheat sheets draw. */}
      {hero
        ? d.candles.map((k, i) => {
            const pr = livePrint(i);
            if (!pr) return null;
            const col = pr.close >= k.o ? PT.up : PT.down;
            const x = cx(i);
            const yT = pY(Math.max(k.o, pr.close));
            const yB = pY(Math.min(k.o, pr.close));
            return (
              <g key={i} style={{filter: `drop-shadow(0 0 ${pr.settled ? 4 : 9}px ${col}${pr.settled ? '55' : 'bb'})`}}>
                <line x1={x} x2={x} y1={pY(pr.hNow)} y2={pY(pr.lNow)} stroke={col} strokeWidth={2.2} />
                <rect x={x - bodyW / 2} y={yT} width={bodyW} height={Math.max(2.5, yB - yT)} rx={2} fill={col} />
              </g>
            );
          })
        : (() => {
            const pts = d.candles.map((k, i) => `${cx(i)},${pY(k.c)}`).join(' ');
            return (
              <polyline
                points={pts}
                fill="none"
                stroke={PT.ice}
                strokeWidth={2.4}
                strokeLinejoin="round"
                strokeLinecap="round"
                style={{filter: `drop-shadow(0 0 4px ${PT.ice}66)`}}
              />
            );
          })()}

      {/* ---------------------------------------------------------- arrow */}
      <g opacity={hero ? arrowP : 1}>
        <line
          x1={bx}
          y1={ay0}
          x2={bx}
          y2={ay0 + (ay1 - ay0) * (hero ? arrowP : 1)}
          stroke={dirCol}
          strokeWidth={strokeMain + 1}
          strokeLinecap="round"
          style={{filter: `drop-shadow(0 0 6px ${dirCol})`}}
        />
        {(hero ? arrowP : 1) > 0.85 ? (
          <path
            d={`M ${bx - 9} ${ay1 + (bull ? 12 : -12)} L ${bx} ${ay1} L ${bx + 9} ${ay1 + (bull ? 12 : -12)}`}
            fill="none"
            stroke={dirCol}
            strokeWidth={strokeMain + 1}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ) : null}
      </g>

      {/* ----------------------------------------------------------- marks.
          Each appears as its own candle finishes printing — the diagram
          annotates the tape, it does not precede it. */}
      {(d.marks ?? []).map((mk, ix) => {
        const k = d.candles[mk.i];
        if (!k) return null;
        const on = hero ? frame >= appearAt(mk.i) + formOf(mk.i) + 2 : true;
        if (!on) return null;
        const above = mk.side === 'above';
        const my = above ? pY(k.h) - (hero ? 20 : 9) : pY(k.l) + (hero ? 20 : 9);
        const mp = hero
          ? interpolate(frame, [appearAt(mk.i) + formOf(mk.i) + 2, appearAt(mk.i) + formOf(mk.i) + 10], [0, 1], {
              easing: EASE.settleBack,
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            })
          : 1;
        const rr = (hero ? 15 : 7) * mp;
        return (
          <g key={`mk${ix}`} opacity={Math.min(1, mp * 1.3)}>
            <circle cx={cx(mk.i)} cy={my} r={rr} fill="#04140D" stroke={PT.ice} strokeWidth={hero ? 2 : 1.2} />
            <text
              x={cx(mk.i)}
              y={my + (hero ? 6 : 3.2)}
              fontFamily={FONT.mono}
              fontSize={(hero ? 17 : 8.5) * Math.max(0.6, mp)}
              fontWeight={700}
              fill={PT.ice}
              textAnchor="middle"
            >
              {mk.label}
            </text>
          </g>
        );
      })}

      {/* ---------------------------------------------------------- stamp */}
      {hero && stampP > 0 ? (
        <g
          opacity={stampP}
          transform={`translate(${stCx} ${PLOT.y0 + 44}) scale(${stampScale}) translate(${-stCx} ${-(PLOT.y0 + 44)})`}
        >
          <rect x={stX} y={PLOT.y0 + 14} width={168} height={58} rx={10} fill={dirCol} />
          <text
            x={stCx}
            y={PLOT.y0 + 53}
            fontFamily={FONT.mono}
            fontSize={32}
            fontWeight={700}
            fill="#04120B"
            textAnchor="middle"
            letterSpacing={2}
          >
            {d.answer}
          </text>
        </g>
      ) : null}

      {/* mini caption row */}
      {!hero && d.name ? (
        <g>
          <text x={12} y={height - 15} fontFamily={FONT.mono} fontSize={16.5} fill="#BFE9D2" letterSpacing={0.4}>
            {d.name.replace(' (continuation)', '').replace(' (Megaphone)', '').replace(' (Saucer)', '').toUpperCase()}
          </text>
          <rect x={width - 66} y={height - 32} width={54} height={24} rx={6} fill={dirCol} />
          <text x={width - 39} y={height - 15} fontFamily={FONT.mono} fontSize={14.5} fontWeight={700} fill="#04120B" textAnchor="middle" letterSpacing={1}>
            {d.answer}
          </text>
        </g>
      ) : null}
    </svg>
  );
};
