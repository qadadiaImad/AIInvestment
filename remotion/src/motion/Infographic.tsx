// Infographic.tsx — the exhibits, drawn in code instead of typed on a card.
//
// WHY. The episode's evidence was a text card: a rectangle with lines of
// prose that faded in and restated whatever Sol had just said. That is a
// caption, not a graphic — and captioning the narration is the specific
// anti-pattern the style reference names, because the viewer reads the
// same fact twice and sees it once.
//
// A graphic instead SHOWS the mechanism, and because these are code-drawn
// SVG rather than fixed drawings they can animate without limit: a rail
// draws itself, a marker pops, a bracket measures a gap, a number counts.
// That asymmetry is the whole point of the hybrid — the character art is
// locked flat pictures, so the fluid motion lives here.
//
// Everything is deterministic in `since` (frames from the element's own
// start), staggered so the eye is led one element at a time rather than
// everything arriving at once.
import React from 'react';
import {Easing, interpolate} from 'remotion';

const INK = '#141A26';
const PAPER = '#F7F4E9';
const RED = '#8E2233';
const BLUE = '#1F5C99';
const MUTED = '#6C7890';

const ease = (v: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(v, [a, b], [from, to], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

/** Springy 0..1 with a small overshoot — for things that POP in. */
const pop = (v: number, a: number, b: number) =>
  interpolate(v, [a, (a + b) / 2, b], [0, 1.12, 1], {
    easing: Easing.out(Easing.quad),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

/**
 * THE TIMELINE. Two dated events and the gap between them — which is the
 * entire point of the July 2022 exhibit and the one thing a paragraph of
 * text cannot make you FEEL. The rail draws, the first marker lands, the
 * second lands, then a bracket measures the space between them and the
 * number counts up inside it.
 */
export const TimelineExhibit: React.FC<{
  since: number;
  w: number;
  h: number;
  title: string;
  left: {date: string; label: string};
  right: {date: string; label: string};
  gapLabel: string;
  counter?: {to: number; suffix?: string; label: string};
  foot?: string;
}> = ({since, w, h, title, left, right, gapLabel, counter, foot}) => {
  const padX = 56;
  const railY = h * 0.52;
  const x0 = padX, x1 = w - padX;
  // Timed to COMPLETE inside the shot that shows it. The first cut of
  // this ran to frame 116 while the beat cut away at 58, so the counter
  // and the bracket — the payoff — were never once seen.
  const draw = ease(since, 4, 20);
  const aIn = pop(since, 18, 30);
  const bIn = pop(since, 30, 42);
  const brIn = ease(since, 42, 56);
  const cIn = ease(since, 46, 70);
  const ax = x0 + (x1 - x0) * 0.16;
  const bx = x0 + (x1 - x0) * 0.78;
  const count = Math.round((counter?.to ?? 0) * cIn);

  return (
    <div style={{position: 'absolute', inset: 0, background: PAPER,
      fontFamily: 'Arial', color: INK}}>
      <div style={{position: 'absolute', left: padX - 8, top: 22,
        fontFamily: 'Impact, Arial', fontSize: 34, letterSpacing: 1,
        opacity: ease(since, 0, 10)}}>{title}</div>

      <svg width={w} height={h} style={{position: 'absolute', inset: 0}}>
        {/* the rail draws itself left to right */}
        <line x1={x0} y1={railY} x2={x0 + (x1 - x0) * draw} y2={railY}
          stroke={INK} strokeWidth={5} strokeLinecap="round" />

        {/* gap bracket between the two events */}
        <g opacity={brIn}>
          <line x1={ax} y1={railY - 74} x2={bx} y2={railY - 74}
            stroke={RED} strokeWidth={4} />
          <line x1={ax} y1={railY - 74} x2={ax} y2={railY - 16}
            stroke={RED} strokeWidth={4} />
          <line x1={bx} y1={railY - 74} x2={bx} y2={railY - 16}
            stroke={RED} strokeWidth={4} />
        </g>

        {[{x: ax, t: aIn, c: BLUE}, {x: bx, t: bIn, c: RED}].map((m, i) => (
          <g key={i}>
            <circle cx={m.x} cy={railY} r={15 * m.t} fill={m.c} />
            <circle cx={m.x} cy={railY} r={26 * m.t} fill="none"
              stroke={m.c} strokeWidth={3} opacity={0.35 * m.t} />
          </g>
        ))}
      </svg>

      {/* gap label sits inside the bracket */}
      <div style={{position: 'absolute', left: ax, width: bx - ax,
        top: railY - 118, textAlign: 'center', opacity: brIn,
        fontFamily: 'Impact, Arial', fontSize: 30, color: RED,
        letterSpacing: 1}}>{gapLabel}</div>

      {[{m: left, x: ax, t: aIn}, {m: right, x: bx, t: bIn}].map((e, i) => (
        <div key={i} style={{position: 'absolute', left: e.x - 150, width: 300,
          top: railY + 26, textAlign: 'center', opacity: e.t,
          transform: `translateY(${(1 - e.t) * 10}px)`}}>
          <div style={{fontFamily: 'Impact, Arial', fontSize: 25,
            letterSpacing: 1}}>{e.m.date}</div>
          <div style={{fontSize: 21, color: MUTED, lineHeight: 1.25,
            marginTop: 3}}>{e.m.label}</div>
        </div>
      ))}

      {counter ? (
        <div style={{position: 'absolute', right: padX - 8, top: 20,
          textAlign: 'right', opacity: ease(since, 44, 56)}}>
          <div style={{fontFamily: 'Impact, Arial', fontSize: 52,
            color: RED, lineHeight: 1}}>
            {count.toLocaleString('en-US')}{counter.suffix ?? ''}
          </div>
          <div style={{fontSize: 19, color: MUTED}}>{counter.label}</div>
        </div>
      ) : null}

      {foot ? (
        <div style={{position: 'absolute', left: padX - 8, bottom: 16,
          fontSize: 18, color: MUTED, opacity: ease(since, 62, 74)}}>
          {foot}
        </div>
      ) : null}
    </div>
  );
};

/**
 * THE COUNTER BAR. For a single quantity that is the whole point of a
 * beat — the disclosure window. The bar grows, the number counts with
 * it, and a marker shows where the useful part of the window ended.
 */
export const CounterExhibit: React.FC<{
  since: number; w: number; h: number;
  title: string; to: number; unit: string; caption: string; foot?: string;
}> = ({since, w, h, title, to, unit, caption, foot}) => {
  const padX = 56;
  const grow = ease(since, 8, 44);
  const barY = h * 0.5;
  const barW = (w - padX * 2) * grow;
  const n = Math.round(to * grow);
  return (
    <div style={{position: 'absolute', inset: 0, background: PAPER,
      fontFamily: 'Arial', color: INK}}>
      <div style={{position: 'absolute', left: padX - 8, top: 22,
        fontFamily: 'Impact, Arial', fontSize: 34, letterSpacing: 1,
        opacity: ease(since, 0, 10)}}>{title}</div>
      <svg width={w} height={h} style={{position: 'absolute', inset: 0}}>
        <rect x={padX} y={barY - 26} width={w - padX * 2} height={52}
          rx={8} fill="#E4DFCE" />
        <rect x={padX} y={barY - 26} width={barW} height={52} rx={8}
          fill={RED} />
      </svg>
      <div style={{position: 'absolute', left: padX, top: barY - 96,
        fontFamily: 'Impact, Arial', fontSize: 58, color: RED}}>
        {n}<span style={{fontSize: 30, marginLeft: 8}}>{unit}</span>
      </div>
      <div style={{position: 'absolute', left: padX, top: barY + 44,
        right: padX, fontSize: 25, lineHeight: 1.35,
        opacity: ease(since, 30, 46)}}>{caption}</div>
      {foot ? (
        <div style={{position: 'absolute', left: padX, bottom: 16,
          fontSize: 18, color: MUTED, opacity: ease(since, 46, 58)}}>
          {foot}
        </div>
      ) : null}
    </div>
  );
};

/**
 * THE TRACKER TAPE — what the studio monitor runs when it has no specific
 * exhibit to show.
 *
 * It replaces a single scrolling polyline, which was legible as "a chart"
 * and nothing more. The subject of this episode is a *tracker* — a
 * portfolio reconstructed from disclosures — so the screen behind the
 * hosts should be that tracker, printing. Candles carry information a
 * line cannot: each one is a period with a range, so the eye reads
 * volatility and direction rather than a decorative squiggle.
 *
 * PRINTS LIKE TAPE, per the house rules in CLAUDE.md 10.2 — the newest
 * bar is LIVE: its close wanders inside its own high/low and its colour
 * tracks that live print, so a bar can flip green-to-red while you watch
 * it. Only when it scrolls out of the live slot does it settle. That is
 * the difference between a chart that is animated and one that is running.
 *
 * The series is a deterministic pseudo-random walk — a *seeded* one, so
 * every render of a given frame is identical — and it is labelled
 * ILLUSTRATIVE on the face of the chart. This is not a real price history
 * and the episode may not imply that it is (10.6): the real numbers in
 * this episode live in the filings, and those are cited.
 */
const rnd = (i: number, salt = 0) => {
  const n = Math.sin(i * 127.1 + salt * 311.7) * 43758.5453;
  return n - Math.floor(n);
};

type Bar = {o: number; h: number; l: number; c: number};

/** One deterministic bar of the walk. Drift is mild and NOT monotonic — a
 *  chart that only ever goes up is a performance claim. */
const barAt = (i: number): Bar => {
  let p = 100;
  for (let k = 0; k <= i; k++) {
    p += (rnd(k) - 0.46) * 3.2 + Math.sin(k / 11) * 0.55;
  }
  const o = p;
  const c = p + (rnd(i, 1) - 0.47) * 3.4;
  const wick = 0.6 + rnd(i, 2) * 2.4;
  return {o, c, h: Math.max(o, c) + wick, l: Math.min(o, c) - wick};
};


/** Trading-day calendar without Date(): 21 sessions a month, deterministic. */
const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
const dayLabel = (i: number) => {
  const k = ((i % 252) + 252) % 252;      // 252 sessions ≈ one year
  return `${MONTHS[Math.floor(k / 21)]} ${(k % 21) * 1 + 1}`;
};

/** Round a span out to a readable step, so the axis lands on flat numbers
 *  (100, 102.5, 105 …) instead of 101.37. */
const niceStep = (span: number) => {
  const raw = span / 4;
  const mag = Math.pow(10, Math.floor(Math.log10(Math.max(raw, 1e-6))));
  const n = raw / mag;
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * mag;
};

export const TickerTape: React.FC<{
  frame: number; w: number; h: number; label: string; sub?: string;
  /** Drop the chart's header chrome. Used when the episode title is over
   *  the monitor: two unrelated blocks of text stacked on each other read
   *  as a layout bug, and the candles alone still say "this is a market". */
  bare?: boolean;
}> = ({frame, w, h, label, sub, bare}) => {
  const VIS = 30;                       // bars on screen
  const FPB = 7;                        // frames per new bar
  const head = Math.floor(frame / FPB);
  const sub01 = (frame % FPB) / FPB;
  const bars: Bar[] = [];
  for (let i = 0; i < VIS + 1; i++) bars.push(barAt(head - VIS + i));

  // the newest bar is still forming: its close wanders inside its own range
  const live = bars[bars.length - 1];
  if (sub01 <= 0.86) {
    live.c = live.l + (live.h - live.l) *
      (0.5 + 0.42 * Math.sin(sub01 * 9.1 + head) * (1 - sub01 * 0.55));
  }

  // THE SCALE MUST NOT BREATHE. Fitting min/max to the visible window
  // recomputed the axis every single frame, so the candles inflated and
  // deflated as bars scrolled in and out — the "widening" that made this
  // unpleasant to watch. The range is taken from a long trailing window
  // and then SNAPPED to a round step, so it holds still for seconds at a
  // time and only ever steps by a whole gridline.
  const wide: Bar[] = [];
  for (let i = 0; i < 110; i++) wide.push(barAt(head - 110 + i));
  const wLo = Math.min(...wide.map((b) => b.l));
  const wHi = Math.max(...wide.map((b) => b.h));
  const step = niceStep(wHi - wLo);
  const lo = Math.floor(wLo / step) * step - step * 0.25;
  const hi = Math.ceil(wHi / step) * step + step * 0.25;

  const padR = 96, padB = 34, top = bare ? 18 : 62;
  const plotW = w - padR, bot = h - padB;
  const yOf = (v: number) => bot - ((v - lo) / (hi - lo)) * (bot - top);

  const levels: number[] = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi; v += step) levels.push(v);

  const slot = plotW / VIS;
  const bw = Math.max(4, slot * 0.58);
  const UP = '#00E676', DOWN = '#FF3B30';
  const last = live.c, prev = bars[bars.length - 2].c;
  const upNow = last >= prev;
  const chg = ((last / bars[0].c - 1) * 100);

  return (
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden',
      background: 'linear-gradient(180deg,#040A12 0%,#02070A 100%)'}}>
      <svg width={w} height={h} style={{position: 'absolute', inset: 0}}>
        {/* PRICE LEVELS — ruled, labelled, and they stay put */}
        {levels.map((v) => (
          <g key={v}>
            <line x1={0} x2={plotW} y1={yOf(v)} y2={yOf(v)}
              stroke="#12202E" strokeWidth={1.5} />
            <text x={plotW + 10} y={yOf(v) + 5} fill="#5A7290"
              fontFamily="Arial" fontSize={15}>{v.toFixed(step < 1 ? 2 : 1)}</text>
          </g>
        ))}
        {/* SESSION MARKERS — a dated x-axis, so the chart reads as time */}
        <g transform={`translate(${-sub01 * slot},0)`}>
          {bars.map((b, i) => {
            const idx = head - VIS + i;
            if (i % 6 !== 0) return null;
            return (
              <g key={`d${i}`}>
                <line x1={i * slot + slot / 2} x2={i * slot + slot / 2}
                  y1={top} y2={bot} stroke="#0D1926" strokeWidth={1} />
                <text x={i * slot + slot / 2} y={bot + 20} fill="#4C6488"
                  fontFamily="Arial" fontSize={14} textAnchor="middle">
                  {dayLabel(idx)}
                </text>
              </g>
            );
          })}
        </g>
        <line x1={0} x2={plotW} y1={bot} y2={bot} stroke="#1E3348" strokeWidth={2} />
        <line x1={plotW} x2={plotW} y1={top} y2={bot} stroke="#1E3348" strokeWidth={2} />

        {/* the candles */}
        <g transform={`translate(${-sub01 * slot},0)`}>
          {bars.map((b, i) => {
            const x = i * slot + slot / 2;
            const col = b.c >= b.o ? UP : DOWN;
            const yO = yOf(b.o), yC = yOf(b.c);
            const isLive = i === bars.length - 1;
            return (
              <g key={i} opacity={i === 0 ? 1 - sub01 : 1}>
                <line x1={x} x2={x} y1={yOf(b.h)} y2={yOf(b.l)}
                  stroke={col} strokeWidth={isLive ? 2.6 : 1.8} opacity={0.9} />
                <rect x={x - bw / 2} y={Math.min(yO, yC)} width={bw}
                  height={Math.max(2, Math.abs(yC - yO))} fill={col}
                  opacity={isLive ? 1 : 0.86} />
              </g>
            );
          })}
        </g>

        {/* last-price rule + tag on the axis, the one line the eye tracks */}
        <line x1={0} x2={plotW} y1={yOf(last)} y2={yOf(last)}
          stroke={upNow ? UP : DOWN} strokeWidth={1.4}
          strokeDasharray="6 6" opacity={0.55} />
        <rect x={plotW + 2} y={yOf(last) - 12} width={padR - 6} height={24}
          rx={3} fill={upNow ? UP : DOWN} />
        <text x={plotW + 8} y={yOf(last) + 5} fill="#04120A"
          fontFamily="Arial" fontSize={15} fontWeight="bold">
          {last.toFixed(2)}
        </text>
      </svg>

      {bare ? null : (
        <>
          {/* SYMBOL — deliberately fictional. Attaching a synthetic series
              to a real ticker would be a claim about a real fund. */}
          <div style={{position: 'absolute', left: 20, top: 10,
            display: 'flex', alignItems: 'baseline', gap: 10}}>
            <span style={{fontFamily: 'Impact, Arial', fontSize: 30,
              letterSpacing: 1, color: '#E9F1FF'}}>LTX</span>
            <span style={{fontFamily: 'Arial', fontSize: 14, letterSpacing: 1.5,
              color: '#7C93B5'}}>{label}</span>
          </div>
          <div style={{position: 'absolute', left: 20, top: 40, fontSize: 13,
            letterSpacing: 1, color: '#4C6488', fontFamily: 'Arial'}}>
            {sub} · 1D
          </div>
          <div style={{position: 'absolute', right: 20, top: 10,
            textAlign: 'right'}}>
            <div style={{fontFamily: 'Impact, Arial', fontSize: 30,
              color: upNow ? UP : DOWN, lineHeight: 1}}>{last.toFixed(2)}</div>
            <div style={{fontFamily: 'Arial', fontSize: 14, marginTop: 2,
              color: chg >= 0 ? UP : DOWN}}>
              {chg >= 0 ? '+' : ''}{chg.toFixed(2)}%
            </div>
          </div>
        </>
      )}

      {/* Non-negotiable: the series is synthetic and says so on its face. */}
      <div style={{position: 'absolute', left: 20, bottom: 8, fontSize: 12,
        letterSpacing: 2, color: '#3C4C66', fontFamily: 'Arial'}}>
        ILLUSTRATIVE — NOT A REAL PRICE HISTORY
      </div>
    </div>
  );
};

/**
 * THE PERFORMANCE BARS. Two bars racing: a tracked lawmaker portfolio
 * against the index, for one named year.
 *
 * COMPLIANCE, because this one carries a real number about a real
 * household. Every figure is what a PUBLIC TRACKER REPORTED and the
 * graphic says so on its face — the word "reported", the source and the
 * year are all printed, and the subject is DISCLOSED trades, which are
 * public record under the STOCK Act. No accusation is made or implied:
 * outperforming an index is not an allegation. The episode's parody /
 * public-record / not-advice footer still runs underneath.
 */
export const PerformanceExhibit: React.FC<{
  since: number; w: number; h: number;
  title: string; year: string;
  rows: {label: string; pct: number; tone?: 'red' | 'blue' | 'grey'}[];
  foot: string;
}> = ({since, w, h, title, year, rows, foot}) => {
  const padX = 52;
  const maxPct = Math.max(...rows.map((r) => r.pct));
  const trackW = w - padX * 2 - 150;
  const n = rows.length;
  // rows share the plot evenly, so 2 or 3 bars both sit correctly
  const top0 = h * 0.34, gap = (h * 0.58 - top0) / Math.max(1, n - 1);
  const rowY = rows.map((_, i) => (n === 1 ? h * 0.5 : top0 + gap * i + h * 0.06));
  const TONE = {red: RED, blue: BLUE, grey: '#8A93A6'} as const;
  return (
    <div style={{position: 'absolute', inset: 0, background: PAPER,
      fontFamily: 'Arial', color: INK}}>
      <div style={{position: 'absolute', left: padX - 6, top: 16,
        fontFamily: 'Impact, Arial', fontSize: 32, letterSpacing: 1,
        opacity: ease(since, 0, 10)}}>{title}</div>
      <div style={{position: 'absolute', right: padX - 6, top: 20,
        fontFamily: 'Impact, Arial', fontSize: 30, color: MUTED,
        opacity: ease(since, 4, 14)}}>{year}</div>

      <svg width={w} height={h} style={{position: 'absolute', inset: 0}}>
        {rows.map((r, i) => {
          // staggered, so the eye reads one bar and then the next
          const g = ease(since, 12 + i * 14, 50 + i * 14);
          return (
            <g key={i}>
              <rect x={padX} y={rowY[i] - 24} width={trackW} height={48}
                rx={6} fill="#E4DFCE" />
              <rect x={padX} y={rowY[i] - 24}
                width={trackW * (r.pct / maxPct) * g} height={48} rx={6}
                fill={TONE[r.tone ?? (i === 0 ? 'red' : 'blue')]} />
            </g>
          );
        })}
      </svg>

      {rows.map((r, i) => {
        const g = ease(since, 12 + i * 14, 50 + i * 14);
        // With three bars the rows sit close enough that a label ABOVE a
        // bar lands on top of the bar above it — which hid the middle
        // label entirely. Labels ride INSIDE their own track instead, so
        // the layout holds at any row count.
        return (
          <div key={i}>
            <div style={{position: 'absolute', left: padX + 14,
              top: rowY[i] - 11, width: trackW - 28, fontSize: 17,
              letterSpacing: 0.8, fontWeight: 700, color: '#FFFFFF',
              mixBlendMode: 'difference',
              opacity: ease(since, 10 + i * 14, 24 + i * 14)}}>{r.label}</div>
            <div style={{position: 'absolute', left: padX + trackW + 14,
              top: rowY[i] - 24, fontFamily: 'Impact, Arial', fontSize: 34,
              color: TONE[r.tone ?? (i === 0 ? 'red' : 'blue')]}}>
              +{(r.pct * g).toFixed(1)}%
            </div>
          </div>
        );
      })}

      <div style={{position: 'absolute', left: padX, bottom: 12, right: padX,
        fontSize: 15, lineHeight: 1.3, color: MUTED,
        opacity: ease(since, 50, 64)}}>{foot}</div>
    </div>
  );
};
