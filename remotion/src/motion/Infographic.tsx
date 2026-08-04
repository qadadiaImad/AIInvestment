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

export const TickerTape: React.FC<{
  frame: number; w: number; h: number; label: string; sub?: string;
  /** Drop the tape's own header/price chrome. Used when the episode title
   *  is over the monitor: two unrelated blocks of text stacked on each
   *  other read as a layout bug, and the candles alone still say
   *  "this is a market" perfectly well. */
  bare?: boolean;
}> = ({frame, w, h, label, sub, bare}) => {
  const VIS = 26;                       // bars on screen
  const FPB = 7;                        // frames per new bar
  const head = Math.floor(frame / FPB);
  const sub01 = (frame % FPB) / FPB;    // sub-bar scroll, so it glides
  const bars: Bar[] = [];
  for (let i = 0; i < VIS + 1; i++) bars.push(barAt(head - VIS + i));

  // The newest bar is still forming: walk its close inside its own range,
  // then let it settle onto its real close as it leaves the live slot.
  const live = bars[bars.length - 1];
  const t = sub01;
  if (t <= 0.86) {
    live.c = live.l + (live.h - live.l) *
      (0.5 + 0.42 * Math.sin(t * 9.1 + head) * (1 - t * 0.55));
  }

  const top = 54, bot = h - 40;
  const lo = Math.min(...bars.map((b) => b.l));
  const hi = Math.max(...bars.map((b) => b.h));
  const pad = (hi - lo) * 0.12 || 1;
  const yOf = (v: number) =>
    bot - ((v - (lo - pad)) / ((hi + pad) - (lo - pad))) * (bot - top);

  const slot = w / VIS;
  const bw = slot * 0.56;
  const UP = '#00E676', DOWN = '#FF3B30';
  const last = live.c, prev = bars[bars.length - 2].c;
  const upNow = last >= prev;

  return (
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden',
      background: 'linear-gradient(180deg,#0A1018 0%,#050A12 100%)'}}>
      <svg width={w} height={h} style={{position: 'absolute', inset: 0}}>
        {[0.2, 0.4, 0.6, 0.8].map((g) => (
          <line key={g} x1={0} x2={w} y1={top + (bot - top) * g}
            y2={top + (bot - top) * g} stroke="#16202F" strokeWidth={2} />
        ))}
        {/* the tape scrolls a whole slot per bar, offset sub-bar so it
            glides instead of stepping */}
        <g transform={`translate(${-sub01 * slot},0)`}>
          {bars.map((b, i) => {
            const x = i * slot + slot / 2;
            const col = b.c >= b.o ? UP : DOWN;
            const yO = yOf(b.o), yC = yOf(b.c);
            const isLive = i === bars.length - 1;
            return (
              <g key={i} opacity={i === 0 ? 1 - sub01 : 1}>
                <line x1={x} x2={x} y1={yOf(b.h)} y2={yOf(b.l)}
                  stroke={col} strokeWidth={isLive ? 3 : 2} opacity={0.85} />
                <rect x={x - bw / 2} y={Math.min(yO, yC)} width={bw}
                  height={Math.max(2, Math.abs(yC - yO))} fill={col}
                  opacity={isLive ? 0.95 : 0.8} />
              </g>
            );
          })}
        </g>
        {/* last-price rule — the one line the eye can track across a cut */}
        <line x1={0} x2={w} y1={yOf(last)} y2={yOf(last)}
          stroke={upNow ? UP : DOWN} strokeWidth={1.5}
          strokeDasharray="7 6" opacity={0.5} />
      </svg>

      {bare ? null : (
        <>
          <div style={{position: 'absolute', left: 22, top: 12,
            fontFamily: 'Impact, Arial', fontSize: 23, letterSpacing: 2.5,
            color: '#7C93B5'}}>{label}</div>
          {sub ? (
            <div style={{position: 'absolute', left: 22, top: 38, fontSize: 15,
              letterSpacing: 1, color: '#4C6488', fontFamily: 'Arial'}}>{sub}</div>
          ) : null}
          <div style={{position: 'absolute', right: 22, top: 12,
            fontFamily: 'Impact, Arial', fontSize: 30,
            color: upNow ? UP : DOWN}}>{last.toFixed(2)}</div>
        </>
      )}

      {/* Non-negotiable: this series is synthetic and says so on its face. */}
      <div style={{position: 'absolute', right: 22, bottom: 10, fontSize: 13,
        letterSpacing: 2, color: '#3C4C66', fontFamily: 'Arial'}}>
        ILLUSTRATIVE
      </div>
    </div>
  );
};
