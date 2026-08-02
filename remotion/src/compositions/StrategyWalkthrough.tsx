// StrategyWalkthrough.tsx — Act 4 of the strategy episode: a REAL chart,
// walked forward in time. Every number on screen comes from the scanner's
// stamped window (Python owns the schedule too — this file renders a
// precomputed frame plan, it invents nothing). The owner's key ask: each
// annotation appears at the bar where it becomes knowable — the resistance
// line only draws once its second touch has printed, the trade frame only
// after the retest — so the viewer learns to see the setup form, not to
// admire hindsight. House terminal style (rule 10.2); provenance footer on
// every frame (10.6); entry/stop/target/rr all present (10.5).
import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {FONT} from '../slides/theme';
import {Grain, Vignette} from '../motion/Polish';

const bar = z.object({t: z.string(), o: z.number(), h: z.number(), l: z.number(), c: z.number()});
export const strategyWalkthroughSchema = z.object({
  bars: z.array(bar),
  barStart: z.array(z.number()),
  level: z.number(), entry: z.number(), stop: z.number(), target: z.number(), rr: z.number(),
  idx: z.object({touch1: z.number(), touch2: z.number(), breakout: z.number(),
                 retest: z.number(), resolve: z.number()}),
  resistDrawAt: z.number(), breakoutTagAt: z.number(), retestTagAt: z.number(),
  tradeFrameAt: z.number(), tpAt: z.number(), totalFrames: z.number(),
  header: z.string(), subheader: z.string(),
  eventDates: z.record(z.string(), z.string()),
  dateTicks: z.array(z.object({i: z.number(), label: z.string()})),
  footer: z.string(),
  event_times_s: z.record(z.string(), z.number()).optional(),
});
type P = z.infer<typeof strategyWalkthroughSchema>;

const BG = '#02070A';
const UP = '#00E676';
const DOWN = '#FF3B30';
const ACCENT = '#22E07E';
const GRID = 'rgba(34,224,126,0.10)';
const INK = '#A0B9B2';

const CHART = {x0: 70, x1: 1010, y0: 470, y1: 1420};

export const StrategyWalkthrough: React.FC<P> = (p) => {
  const frame = useCurrentFrame();
  const n = p.bars.length;
  const lo = Math.min(...p.bars.map((b) => b.l), p.stop) - 0.6;
  const hi = Math.max(...p.bars.map((b) => b.h), p.target) + 0.6;
  const y = (price: number) =>
    CHART.y1 - ((price - lo) / (hi - lo)) * (CHART.y1 - CHART.y0);
  const xw = (CHART.x1 - CHART.x0) / n;
  const x = (i: number) => CHART.x0 + (i + 0.5) * xw;
  const bw = Math.max(6, xw * 0.55);

  const seen = (at: number, len = 12) =>
    interpolate(frame, [at, at + len], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  const tag = (px: number, py: number, text: string, color: string, at: number) => {
    const o = seen(at);
    if (o <= 0) return null;
    return (
      <div style={{position: 'absolute', left: Math.min(px, 720), top: py, opacity: o,
                   transform: `translateY(${(1 - o) * 10}px)`,
                   background: 'rgba(2,7,10,0.92)', border: `2px solid ${color}`,
                   color, fontFamily: FONT.mono, fontSize: 30, fontWeight: 800,
                   letterSpacing: 2, padding: '10px 16px'}}>
        {text}
      </div>
    );
  };

  const priceLine = (price: number, color: string, at: number, dash: string,
                     label: string, dy = -34, lx = CHART.x0 + 8) => {
    const o = seen(at, 20);
    if (o <= 0) return null;
    return (
      <>
        <div style={{position: 'absolute', left: CHART.x0, top: y(price) - 1,
                     width: (CHART.x1 - CHART.x0) * o, height: 2,
                     background: dash === 'solid' ? color : undefined,
                     borderTop: dash === 'solid' ? undefined : `2px dashed ${color}`,
                     opacity: 0.9}} />
        <div style={{position: 'absolute', left: lx, top: y(price) + dy,
                     opacity: o, color, fontFamily: FONT.mono, fontSize: 26,
                     fontWeight: 800, letterSpacing: 1,
                     background: 'rgba(2,7,10,0.85)', padding: '2px 8px'}}>
          {label} {price.toFixed(2)}
        </div>
      </>
    );
  };

  const flashAt = (at: number) => {
    if (frame < at) return null; // extrapolateLeft would tint every frame before the hit
    const o = interpolate(frame, [at, at + 2, at + 6], [0.55, 0.3, 0],
                          {extrapolateRight: 'clamp'});
    return o > 0 ? <AbsoluteFill style={{background: '#fff', opacity: o}} /> : null;
  };

  return (
    <AbsoluteFill style={{backgroundColor: BG, fontFamily: FONT.mono}}>
      {/* header */}
      <div style={{position: 'absolute', top: 120, left: 60, right: 60, textAlign: 'center'}}>
        <div style={{color: '#F2F7F4', fontSize: 58, fontWeight: 900, letterSpacing: 6}}>
          {p.header}
        </div>
        <div style={{color: ACCENT, fontSize: 30, fontWeight: 700, letterSpacing: 3, marginTop: 12,
                     opacity: seen(6)}}>
          {p.subheader}
        </div>
        <div style={{color: INK, fontSize: 26, marginTop: 10, opacity: seen(14)}}>
          THIS HAPPENED. HERE IS THE TAPE.
        </div>
      </div>

      {/* grid */}
      {[0, 1, 2, 3, 4, 5].map((k) => (
        <div key={k} style={{position: 'absolute', left: CHART.x0,
                             top: CHART.y0 + (k * (CHART.y1 - CHART.y0)) / 5,
                             width: CHART.x1 - CHART.x0, height: 1, background: GRID}} />
      ))}

      {/* candles — 3-tick quantized print, per the house tape rules */}
      {p.bars.map((b, i) => {
        const start = p.barStart[i];
        if (frame < start) return null;
        const q = Math.min(3, 1 + Math.floor((frame - start) / 3)) / 3;
        const up = b.c >= b.o;
        const col = up ? UP : DOWN;
        const bodyTop = y(Math.max(b.o, b.c));
        const bodyBot = y(Math.min(b.o, b.c));
        const grow = (bodyBot - bodyTop) * q;
        return (
          <React.Fragment key={i}>
            <div style={{position: 'absolute', left: x(i) - 1, top: y(b.h),
                         width: 2, height: (y(b.l) - y(b.h)) * q, background: col,
                         opacity: 0.9}} />
            <div style={{position: 'absolute', left: x(i) - bw / 2,
                         top: up ? bodyBot - grow : bodyTop,
                         width: bw, height: Math.max(2, grow), background: col,
                         boxShadow: `0 0 12px ${col}55`}} />
          </React.Fragment>
        );
      })}

      {/* resistance line — drawn only once touch 2 exists */}
      {priceLine(p.level, ACCENT, p.resistDrawAt, 'solid', 'RESISTANCE', -38, CHART.x1 - 330)}
      {tag(x(p.idx.touch1) - 60, y(p.level) - 120,
           `TOUCH 1 · ${p.eventDates.touch1}`, ACCENT, p.resistDrawAt + 6)}
      {tag(x(p.idx.touch2) - 60, y(p.level) - 190,
           `TOUCH 2 · ${p.eventDates.touch2}`, ACCENT, p.resistDrawAt + 14)}

      {/* breakout */}
      {flashAt(p.breakoutTagAt)}
      {tag(x(p.idx.breakout) - 320, y(p.bars[p.idx.breakout].h) - 200,
           `BREAKOUT · ${p.eventDates.breakout}`, '#F2F7F4', p.breakoutTagAt)}

      {/* retest */}
      {tag(x(p.idx.retest) - 140, y(p.level) + 70,
           `RETEST · ${p.eventDates.retest}`, '#FFD166', p.retestTagAt)}

      {/* trade frame — all four or none (rule 10.5). Entry == the level
       * line already on screen, so it gets a label, not a second line. */}
      {seen(p.tradeFrameAt) > 0 && (
        <div style={{position: 'absolute', left: CHART.x0 + 8, top: y(p.entry) + 8,
                     opacity: seen(p.tradeFrameAt), color: ACCENT,
                     fontFamily: FONT.mono, fontSize: 26, fontWeight: 800,
                     background: 'rgba(2,7,10,0.85)', padding: '2px 8px'}}>
          ENTRY {p.entry.toFixed(2)}
        </div>
      )}
      {priceLine(p.stop, DOWN, p.tradeFrameAt + 10, 'dashed', 'STOP', 10)}
      {priceLine(p.target, UP, p.tradeFrameAt + 20, 'dashed', 'TARGET', -38)}
      {seen(p.tradeFrameAt + 26) > 0 && (
        <div style={{position: 'absolute', left: CHART.x0 + 8, top: CHART.y1 - 90,
                     opacity: seen(p.tradeFrameAt + 26),
                     color: '#F2F7F4', background: 'rgba(34,224,126,0.16)',
                     border: `2px solid ${ACCENT}`, fontSize: 30, fontWeight: 900,
                     letterSpacing: 2, padding: '8px 14px'}}>
          R:R {p.rr.toFixed(1)}
        </div>
      )}

      {/* take profit */}
      {flashAt(p.tpAt)}
      <Sequence from={p.tpAt} durationInFrames={p.totalFrames - p.tpAt}>
        <Audio src={staticFile('audio/coin.wav')} volume={0.75} />
      </Sequence>
      {tag(x(p.idx.resolve) - 260, y(p.target) - 120,
           `TARGET HIT · ${p.eventDates.resolve} · +${p.rr.toFixed(1)}R`, UP, p.tpAt)}

      {/* reveal-side candle tones, breakout onward only (rule 10.4) */}
      {p.bars.map((b, i) =>
        i >= p.idx.breakout && p.barStart[i] < p.totalFrames - 4 ? (
          <Sequence key={`s${i}`} from={p.barStart[i]} durationInFrames={20}>
            <Audio src={staticFile(b.c >= b.o ? 'audio/candle_up.wav' : 'audio/candle_down.wav')}
                   volume={0.3} />
          </Sequence>
        ) : null
      )}

      {/* date axis */}
      {p.dateTicks.map((d) => (
        <div key={d.i} style={{position: 'absolute', left: x(d.i) - 46, top: CHART.y1 + 26,
                               color: INK, fontSize: 24, letterSpacing: 1,
                               opacity: frame >= p.barStart[d.i] ? 0.85 : 0}}>
          {d.label}
        </div>
      ))}

      {/* provenance footer, every frame */}
      <div style={{position: 'absolute', bottom: 54, left: 50, right: 50, textAlign: 'center',
                   color: INK, fontSize: 21, lineHeight: 1.5, opacity: 0.85}}>
        {p.footer}
      </div>

      <Vignette />
      <Grain opacity={0.05} />
    </AbsoluteFill>
  );
};
