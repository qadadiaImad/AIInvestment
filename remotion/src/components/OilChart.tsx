// OilChart.tsx — the whole six months of Brent, drawn once, at full extent.
//
// The camera (motion/CameraRig) decides what you are looking at. This component
// therefore has exactly one rule it must never break: **its geometry does not
// depend on the frame.** A bar sits at the same pixel on frame 40 and frame
// 1300, or the camera would be flying over ground that moves under it.
//
// What DOES vary is `printedThrough` (how much of the tape exists yet) and
// `zoom`. Zoom is passed in only so that strokes and axis type can be divided
// by it: a 3x push that also triples every wick reads as a blurry image scale,
// not as a camera moving closer to a screen.
import React from 'react';
import {FONT} from '../slides/theme';
import {PT} from './PatternCard';

export type OBar = {d: string; o: number; h: number; l: number; c: number};

export type OilChartProps = {
  bars: OBar[];
  width: number;
  height: number;
  /** Fractional bar index the tape has printed up to. 3.5 = bar 3 half-formed. */
  printedThrough: number;
  /** Current camera zoom, used ONLY to keep stroke and type on-screen size. */
  zoom: number;
  /** Horizontal dashed line + label, in price space. */
  levels?: {price: number; label: string; color: string; dash?: string; opacity?: number}[];
  /** Vertical event mark at a bar index. */
  marks?: {i: number; label: string; color: string; opacity?: number}[];
  /** Boxes around a bar's own range — the pattern, drawn as a diagram.
   * `span` widens the box over following bars, which is how an inside bar gets
   * shown: the mother's box reaches across the coil so you can SEE the smaller
   * box nested inside it, rather than two boxes side by side. */
  boxes?: {i: number; span?: number; color: string; label?: string; opacity?: number}[];
  /** Shaded price band between two prices across a bar range. */
  bands?: {from: number; to: number; i0: number; i1: number; color: string; opacity?: number}[];
};

// The right gutter has to fit a price label at the WIDEST the camera ever gets,
// because labels are drawn at 1/zoom to hold their on-screen size — at zoom
// 0.72 that is a 1.39x box, and a gutter sized for zoom 1 clips it.
const PAD = {l: 18, r: 120, t: 34, b: 46};

export const oilScales = (bars: OBar[], width: number, height: number) => {
  const lo = Math.min(...bars.map((b) => b.l));
  const hi = Math.max(...bars.map((b) => b.h));
  const padP = (hi - lo) * 0.06;
  const pMin = lo - padP;
  const pMax = hi + padP;
  const plotW = width - PAD.l - PAD.r;
  const plotH = height - PAD.t - PAD.b;
  const step = plotW / bars.length;
  return {
    pMin,
    pMax,
    step,
    plotW,
    plotH,
    /** Centre of bar i. */
    x: (i: number) => PAD.l + (i + 0.5) * step,
    y: (p: number) => PAD.t + ((pMax - p) / (pMax - pMin)) * plotH,
  };
};

/** How a single bar looks when it is only partly printed.
 *
 * A forming bar is not a small bar — it is a bar whose range has not finished
 * widening and whose close has not been decided. Growing the wick out from the
 * open in both directions, and easing the last print toward the true close, is
 * what makes the tape read as live rather than as a wipe. */
const forming = (b: OBar, prog: number): OBar => {
  if (prog >= 1) return b;
  const p = Math.max(0, prog);
  const ease = p * p * (3 - 2 * p);
  return {
    d: b.d,
    o: b.o,
    h: b.o + (b.h - b.o) * p,
    l: b.o - (b.o - b.l) * p,
    c: b.o + (b.c - b.o) * ease,
  };
};

export const OilChart: React.FC<OilChartProps> = ({
  bars,
  width,
  height,
  printedThrough,
  zoom,
  levels = [],
  marks = [],
  boxes = [],
  bands = [],
}) => {
  const s = oilScales(bars, width, height);
  // Every stroke and every glyph is divided by this, so a 3x push keeps hairlines
  // hairline and keeps the axis legible at a constant on-screen size.
  const k = 1 / Math.max(0.35, zoom);
  const bodyW = Math.max(2, s.step * 0.68);

  const gridPrices: number[] = [];
  {
    const span = s.pMax - s.pMin;
    const raw = span / 7;
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const stepP = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((v) => v >= raw) ?? mag * 10;
    for (let p = Math.ceil(s.pMin / stepP) * stepP; p <= s.pMax; p += stepP) gridPrices.push(p);
  }

  const visible = bars.map((b, i) => ({b, i, prog: printedThrough - i + 1})).filter((r) => r.prog > 0);

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <defs>
        <linearGradient id="oilpanel" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={PT.panelTop} />
          <stop offset="100%" stopColor={PT.panelBot} />
        </linearGradient>
        <filter id="oilglow" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="2.4" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <rect x={0} y={0} width={width} height={height} fill="url(#oilpanel)" />

      {/* grid + right-hand price axis */}
      {gridPrices.map((p) => (
        <g key={`g${p}`}>
          <line
            x1={PAD.l}
            x2={width - PAD.r}
            y1={s.y(p)}
            y2={s.y(p)}
            stroke={PT.grid}
            strokeWidth={1 * k}
          />
          <text
            x={width - PAD.r + 10 * k}
            y={s.y(p) + 4 * k}
            fontFamily={FONT.mono}
            fontSize={17 * k}
            fill={PT.steel}
            letterSpacing={0.4 * k}
          >
            {p.toFixed(0)}
          </text>
        </g>
      ))}

      {/* shaded risk / reward bands, under everything */}
      {bands.map((bd, n) => (
        <rect
          key={`bd${n}`}
          x={s.x(bd.i0) - s.step / 2}
          y={s.y(Math.max(bd.from, bd.to))}
          width={(bd.i1 - bd.i0 + 1) * s.step}
          height={Math.abs(s.y(bd.from) - s.y(bd.to))}
          fill={bd.color}
          opacity={bd.opacity ?? 0.12}
        />
      ))}

      {/* horizontal levels — the LINE only. Its label is drawn by the caller in
       * the unscaled layer: at zoom 2.5 the right-hand gutter is a thousand
       * pixels off-screen, so a label anchored to the chart is a label nobody
       * ever sees at exactly the moment it matters most. */}
      {levels.map((lv, n) => (
        <line
          key={`lv${n}`}
          x1={PAD.l}
          x2={width - PAD.r + 130}
          y1={s.y(lv.price)}
          y2={s.y(lv.price)}
          stroke={lv.color}
          strokeWidth={2 * k}
          strokeDasharray={lv.dash ?? `${9 * k} ${7 * k}`}
          opacity={lv.opacity ?? 1}
        />
      ))}

      {/* vertical event marks */}
      {marks.map((m, n) => (
        <g key={`mk${n}`} opacity={m.opacity ?? 1}>
          <line
            x1={s.x(m.i)}
            x2={s.x(m.i)}
            y1={PAD.t}
            y2={height - PAD.b}
            stroke={m.color}
            strokeWidth={2.2 * k}
            strokeDasharray={`${6 * k} ${6 * k}`}
          />
          <g transform={`translate(${s.x(m.i)}, ${PAD.t - 6 * k})`}>
            <rect
              x={-62 * k}
              y={-26 * k}
              width={124 * k}
              height={26 * k}
              rx={4 * k}
              fill={m.color}
            />
            <text
              x={0}
              y={-8 * k}
              fontFamily={FONT.mono}
              fontSize={16 * k}
              fontWeight={800}
              fill="#0A0300"
              textAnchor="middle"
              letterSpacing={0.6 * k}
            >
              {m.label}
            </text>
          </g>
        </g>
      ))}

      {/* the tape */}
      {visible.map(({b, i, prog}) => {
        const f = forming(b, prog);
        const up = f.c >= f.o;
        const col = up ? PT.up : PT.down;
        const yO = s.y(f.o);
        const yC = s.y(f.c);
        const top = Math.min(yO, yC);
        const h = Math.max(1.6 * k, Math.abs(yC - yO));
        return (
          <g key={b.d} filter="url(#oilglow)">
            <line
              x1={s.x(i)}
              x2={s.x(i)}
              y1={s.y(f.h)}
              y2={s.y(f.l)}
              stroke={col}
              strokeWidth={Math.max(1.1, bodyW * 0.17)}
              opacity={0.95}
            />
            <rect
              x={s.x(i) - bodyW / 2}
              y={top}
              width={bodyW}
              height={h}
              fill={col}
              opacity={0.95}
              rx={Math.min(1.6, bodyW * 0.1)}
            />
          </g>
        );
      })}

      {/* pattern boxes, drawn OVER the bars they define */}
      {boxes.map((bx, n) => {
        const b = bars[bx.i];
        const span = bx.span ?? 1;
        const pad = s.step * (span > 1 ? 0.45 : 0.24);
        const x0 = s.x(bx.i) - s.step / 2 - pad;
        const w = s.step * span + pad * 2;
        return (
          <g key={`bx${n}`} opacity={bx.opacity ?? 1}>
            <rect
              x={x0}
              y={s.y(b.h) - 5 * k}
              width={w}
              height={s.y(b.l) - s.y(b.h) + 10 * k}
              fill={bx.color}
              fillOpacity={0.05}
              stroke={bx.color}
              strokeWidth={2.4 * k}
              rx={4 * k}
            />
            {bx.label ? (
              <text
                x={x0 + w / 2}
                y={s.y(b.l) + 30 * k}
                fontFamily={FONT.mono}
                fontSize={18 * k}
                fontWeight={800}
                fill={bx.color}
                textAnchor="middle"
                letterSpacing={0.8 * k}
              >
                {bx.label}
              </text>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
};
