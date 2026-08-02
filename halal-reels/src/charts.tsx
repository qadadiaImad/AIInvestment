import React from "react";
import { interpolate } from "remotion";
import { C, FONT } from "./theme";
import { clamp } from "./ui";

// Blended "merged" hero-line color -- roughly the average of the mint
// (#7FE9C2) and cyan (#49C5FF) pair colors, so the merge reads as one new
// line rather than one color simply overdrawing the other.
const MERGED_COLOR = "#8FE8E8";

// ---------------------------------------------------------------------------
// Reusable chart primitives for "two lines, one move" style explainers.
// Pure/presentational: driven entirely by props (reveal 0..1, mergeAmount
// 0..1, dial progress 0..1) so callers own all frame/timing logic via
// `interpolate(frame, ...)` and these components just render a snapshot.
// Reuse target: quiz reveals, correlation/diversification explainers, any
// "two series move together / apart" beat.
// ---------------------------------------------------------------------------

/** Min-max normalize a close-price series to 0..1 so differently-priced
 * tickers can be plotted on the same vertical band and compared by shape. */
export const normalizeSeries = (values: number[]): number[] => {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return values.map((v) => (v - min) / span);
};

export type ChartSeries = {
  id: string;
  data: number[]; // normalized 0..1, same length across series
  color: string;
  reveal: number; // 0..1 fraction of the series drawn left-to-right
  dim?: boolean; // render at reduced opacity (e.g. "already established" line)
  label?: string; // floating ticker tag at the drawn tip
};

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

// ---------------------------------------------------------------------------
// "Alive, not a screenshot" idle motion (owner spec 3): a small continuous,
// fully deterministic (frame-based sine, no Math.random/Date) low-amplitude
// wobble added to every point's value. Depends only on point index `i` and
// the caller's `liveFrame` counter -- NOT on which series it is -- so both
// lines in a pair get the exact identical wobble at each index. That keeps
// the actual plotted relationship (identical @ r=+1, mirrored @ r=-1, etc.)
// visually intact while making the chart read as continuously "breathing"
// even while `r` is held steady.
// ---------------------------------------------------------------------------
const IDLE_AMP = 0.014;
const IDLE_FREQ = 0.045;
const IDLE_PHASE_STEP = 0.22;

const idleWobble = (i: number, liveFrame: number): number =>
  IDLE_AMP * Math.sin(liveFrame * IDLE_FREQ + i * IDLE_PHASE_STEP) +
  IDLE_AMP * 0.5 * Math.sin(liveFrame * IDLE_FREQ * 2.3 - i * 0.11);

/** Build an SVG point path for one series, honoring partial (fractional)
 * reveal so the drawing edge doesn't jump discretely between data points.
 * `liveFrame`, when given, layers in the shared idle wobble above. */
const buildPoints = (
  data: number[],
  width: number,
  height: number,
  reveal: number,
  liveFrame?: number,
) => {
  const n = data.length;
  const exact = Math.max(0, Math.min(n - 1, reveal * (n - 1)));
  const lastIdx = Math.floor(exact);
  const frac = exact - lastIdx;
  const toXY = (i: number, v: number): [number, number] => {
    const wobble = liveFrame !== undefined ? idleWobble(i, liveFrame) : 0;
    const vv = Math.max(0, Math.min(1, v + wobble));
    return [(i / (n - 1)) * width, height - vv * height];
  };
  const pts: Array<[number, number]> = [];
  for (let i = 0; i <= lastIdx; i++) pts.push(toXY(i, data[i]));
  if (lastIdx < n - 1 && frac > 0) {
    const v = lerp(data[lastIdx], data[lastIdx + 1], frac);
    pts.push(toXY(lastIdx + frac, v));
  }
  return pts;
};

/** Catmull-Rom -> cubic-bezier SVG path, so the lines render as smooth
 * curves through the data points instead of jagged straight segments
 * (owner spec 2). Standard uniform Catmull-Rom conversion, deterministic. */
const buildSmoothPath = (pts: Array<[number, number]>): string => {
  if (pts.length < 2) return "";
  if (pts.length === 2) {
    return `M ${pts[0][0]},${pts[0][1]} L ${pts[1][0]},${pts[1][1]}`;
  }
  let d = `M ${pts[0][0]},${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] ?? pts[i];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[i + 2] ?? p2;
    const cp1x = p1[0] + (p2[0] - p0[0]) / 6;
    const cp1y = p1[1] + (p2[1] - p0[1]) / 6;
    const cp2x = p2[0] - (p3[0] - p1[0]) / 6;
    const cp2y = p2[1] - (p3[1] - p1[1]) / 6;
    d += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${p2[0]},${p2[1]}`;
  }
  return d;
};

/**
 * DualLineChart — draws 2-3 normalized price lines left-to-right, with
 * optional pointwise "merge" of the first two series into one glowing line
 * (mergeAmount 0..1) and a white flash overlay at the merge instant.
 */
export const DualLineChart: React.FC<{
  series: ChartSeries[];
  width: number;
  height: number;
  mergeAmount?: number; // 0=original two lines, 1=fully overlapped (series 0 & 1)
  flashAmount?: number; // 0..1 white flash opacity, peaks at the merge snap
  showLeadDot?: boolean;
  /** Frame counter driving the shared idle "breathing" wobble + glow/dot
   * pulse (owner spec 3: never fully frozen, even mid-hold). Omit for a
   * static render (e.g. non-demo callers). */
  liveFrame?: number;
}> = ({ series, width, height, mergeAmount = 0, flashAmount = 0, showLeadDot = true, liveFrame }) => {
  // Pointwise average of series[0] & series[1] for the merge pull.
  const avg =
    mergeAmount > 0 && series.length >= 2
      ? series[0].data.map((v, i) => (v + series[1].data[i]) / 2)
      : null;

  const merged = series.map((s, idx) => {
    if (avg && (idx === 0 || idx === 1) && mergeAmount > 0) {
      return { ...s, data: s.data.map((v, i) => lerp(v, avg[i], mergeAmount)) };
    }
    return s;
  });

  // Once the merge is well underway, fade the two original strokes and let a
  // single blended "hero" line (mint+cyan average) take over on top -- this
  // is what sells "two lines becoming one," rather than the top series simply
  // painting over the other.
  const heroOpacity = avg ? interpolate(mergeAmount, [0.7, 1], [0, 1], clamp) : 0;
  const originalOpacity = avg ? interpolate(mergeAmount, [0.7, 1], [1, 0.12], clamp) : 1;

  return (
    <div style={{ position: "relative", width, height }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ overflow: "visible" }}>
        <defs>
          {merged.map((s, idx) => {
            // Gentle continuous glow-pulse (owner spec 3): blur radius
            // breathes a few px around its base value, per-line phase offset
            // so the two lines don't pulse in perfect lockstep.
            const glowPulse =
              liveFrame !== undefined ? 3 * Math.sin(liveFrame * 0.05 + idx * 2.1) : 0;
            return (
              <filter key={`glow-${s.id}`} id={`glow-${s.id}`} x="-60%" y="-60%" width="220%" height="220%">
                <feGaussianBlur stdDeviation={Math.max(4, 10 + glowPulse)} result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            );
          })}
          <filter id="glow-hero" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur
              stdDeviation={Math.max(6, 14 + (liveFrame !== undefined ? 4 * Math.sin(liveFrame * 0.045) : 0))}
              result="blur"
            />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* faint baseline grid */}
        {[0.25, 0.5, 0.75].map((f) => (
          <line
            key={f}
            x1={0}
            x2={width}
            y1={height * f}
            y2={height * f}
            stroke={C.line}
            strokeWidth={1}
          />
        ))}

        {merged.map((s, idx) => {
          const pts = buildPoints(s.data, width, height, s.reveal, liveFrame);
          if (pts.length < 2) return null;
          const pathD = buildSmoothPath(pts);
          const [lx, ly] = pts[pts.length - 1];
          const fadeForMerge = idx === 0 || idx === 1 ? originalOpacity : 1;
          // Subtle continuous opacity breathing on top of the merge fade, so
          // the stroke itself never sits at one flat static value.
          const opacityPulse =
            liveFrame !== undefined ? 1 + 0.08 * Math.sin(liveFrame * 0.06 + idx * 2.6) : 1;
          const fullyDrawn = s.reveal >= 1;
          const dotPulse = liveFrame !== undefined ? Math.sin(liveFrame * 0.12 + idx * 1.7) : 0;
          return (
            <g key={s.id} opacity={(s.dim ? 0.35 : 1) * fadeForMerge * opacityPulse}>
              <path
                d={pathD}
                fill="none"
                stroke={s.color}
                strokeWidth={mergeAmount > 0.6 ? 10 : 7}
                strokeLinecap="round"
                strokeLinejoin="round"
                filter={`url(#glow-${s.id})`}
              />
              {showLeadDot && s.reveal > 0 && !fullyDrawn ? (
                <circle cx={lx} cy={ly} r={12} fill={s.color} filter={`url(#glow-${s.id})`} />
              ) : null}
              {showLeadDot && fullyDrawn ? (
                <circle
                  cx={lx}
                  cy={ly}
                  r={9 + 3 * dotPulse}
                  fill={s.color}
                  opacity={0.75 + 0.25 * dotPulse}
                  filter={`url(#glow-${s.id})`}
                />
              ) : null}
            </g>
          );
        })}

        {avg && heroOpacity > 0
          ? (() => {
              const revealHero = Math.max(series[0].reveal, series[1].reveal);
              const heroDim = series[0].dim || series[1].dim;
              const pts = buildPoints(avg, width, height, revealHero, liveFrame);
              if (pts.length < 2) return null;
              const pathD = buildSmoothPath(pts);
              return (
                <path
                  d={pathD}
                  fill="none"
                  stroke={MERGED_COLOR}
                  strokeWidth={13}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  opacity={heroOpacity * (heroDim ? 0.35 : 1)}
                  filter="url(#glow-hero)"
                />
              );
            })()
          : null}
      </svg>

      {/* floating ticker tags at each line's current tip -- staggered per
          series index so two lines converging in value don't collide. */}
      {merged.map((s, idx) => {
        if (!s.label || s.reveal <= 0) return null;
        const pts = buildPoints(s.data, width, height, s.reveal, liveFrame);
        if (!pts.length) return null;
        const [lx, ly] = pts[pts.length - 1];
        const stagger = (idx - (merged.length - 1) / 2) * 32;
        return (
          <div
            key={`tag-${s.id}`}
            style={{
              position: "absolute",
              left: Math.min(width - 10, lx + 16),
              top: Math.max(0, ly - 22 + stagger),
              fontFamily: FONT.mono,
              fontWeight: 800,
              fontSize: 26,
              letterSpacing: 1,
              color: s.color,
              opacity: s.dim ? 0.4 : 1,
              textShadow: "0 2px 10px rgba(0,0,0,.85)",
              whiteSpace: "nowrap",
            }}
          >
            {s.label}
          </div>
        );
      })}

      {/* Local glow pulse at the merge instant (the full-frame snap flash
          itself is rendered by the calling scene, e.g. CorrelationReel's
          MergeScene, so it reads as a true screen-wide flash). */}
      {flashAmount > 0 ? (
        <div
          style={{
            position: "absolute",
            inset: -60,
            borderRadius: "50%",
            background: `radial-gradient(circle, #fff ${flashAmount * 40}%, transparent 70%)`,
            opacity: flashAmount,
            pointerEvents: "none",
          }}
        />
      ) : null}
    </div>
  );
};

// ---------------------------------------------------------------------------
// SyncDial — semicircular gauge + needle + numeric readout. Animates from 0
// to a target correlation reading (expressed as a -100..100 percent value).
// Green zone hugs +100 (moving together); the rest of the arc reads neutral.
// ---------------------------------------------------------------------------
export const SyncDial: React.FC<{
  progress: number; // 0..1 animation progress toward `target`
  target: number; // -100..100
  size?: number;
  label?: string;
  min?: number;
  max?: number;
}> = ({ progress, target, size = 240, label = "SYNC", min = -20, max = 100 }) => {
  const value = target * progress;
  const span = max - min;
  const clampedTarget = Math.max(min, Math.min(max, target));
  const isHot = clampedTarget >= 60; // "moving together" zone

  const w = size;
  const h = size * 0.62;
  const cx = w / 2;
  const cy = h - 6;
  const R = w / 2 - 18;
  const strokeW = Math.max(14, size * 0.075);

  const angleForValue = (v: number) => {
    const t = Math.max(0, Math.min(1, (v - min) / span));
    return Math.PI - t * Math.PI; // PI (left, =min) .. 0 (right, =max)
  };

  const arcPoint = (angle: number, r: number) => [cx + Math.cos(angle) * r, cy - Math.sin(angle) * r];

  const describeArc = (a0: number, a1: number, r: number) => {
    const [x0, y0] = arcPoint(a0, r);
    const [x1, y1] = arcPoint(a1, r);
    const large = Math.abs(a0 - a1) > Math.PI ? 1 : 0;
    return `M ${x0} ${y0} A ${r} ${r} 0 ${large} 0 ${x1} ${y1}`;
  };

  const needleAngle = angleForValue(value);
  const [nx, ny] = arcPoint(needleAngle, R - strokeW / 2 - 2);

  const hotStart = angleForValue(60);
  const hotEnd = angleForValue(max);
  const neutralStart = angleForValue(min);
  const neutralEnd = hotStart;

  const needleColor = value >= 60 ? C.mint : C.muted;
  const readout = `${value >= 0 ? "" : "-"}${Math.abs(Math.round(value))}%`;

  return (
    <div style={{ width: w, height: h + 60, position: "relative" }}>
      <svg width={w} height={h + 4} viewBox={`0 0 ${w} ${h + 4}`} style={{ overflow: "visible" }}>
        <path d={describeArc(neutralStart, neutralEnd, R)} stroke={C.panel} strokeWidth={strokeW} fill="none" strokeLinecap="round" />
        <path d={describeArc(hotStart, hotEnd, R)} stroke={`${C.emerald}55`} strokeWidth={strokeW} fill="none" strokeLinecap="round" />
        <path
          d={describeArc(neutralStart, needleAngle, R)}
          stroke={isHot ? C.emerald : C.amber}
          strokeWidth={strokeW}
          fill="none"
          strokeLinecap="round"
        />
        <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={needleColor} strokeWidth={5} strokeLinecap="round" />
        <circle cx={cx} cy={cy} r={9} fill={needleColor} />
      </svg>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: h - 4,
          textAlign: "center",
        }}
      >
        <div style={{ fontFamily: FONT.mono, fontWeight: 800, fontSize: size * 0.19, color: isHot ? C.mint : C.ink, letterSpacing: -1 }}>
          {readout}
        </div>
        <div style={{ fontFamily: FONT.mono, fontWeight: 700, fontSize: size * 0.075, letterSpacing: 3, color: C.muted, marginTop: 2 }}>
          {label}
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// CorrelationScale — horizontal −1..+1 meter with a glowing marker. Used for
// the definition beat (sweeping demo across the whole range) and for the
// illustrative 0 / −1 scenarios (settling at the relevant point). The real
// 0.89 example uses the semicircular SyncDial instead (see CorrelationReel).
// Pure/presentational: caller drives `value` via interpolate(frame, ...).
// ---------------------------------------------------------------------------
export const CorrelationScale: React.FC<{
  value: number; // -1..1, current marker position
  width?: number;
  valueLabel?: string; // override readout text, e.g. "0.89"
  /** Extra labeled reference ticks on the track (e.g. "real" data points),
   * distinct from the fixed -1/0/+1 ticks. Self-highlights (bigger, brighter
   * label) whenever the live `value` sweeps close to it, so it visibly lights
   * up as the marker passes through -- no separate "active" prop needed. */
  extraTicks?: Array<{ value: number; label: string; color?: string }>;
  /** Frame counter for the marker's continuous idle glow pulse (owner spec
   * 3: the balance marker gently pulses/glows while held). Omit for static. */
  liveFrame?: number;
}> = ({ value, width = 860, valueLabel, extraTicks, liveFrame }) => {
  const v = Math.max(-1, Math.min(1, value));
  const trackY = 90;
  const pad = 26;
  const usable = width - pad * 2;
  const xFor = (t: number) => pad + ((t + 1) / 2) * usable;
  const markerX = xFor(v);
  const markerColor = v > 0.25 ? C.mint : v < -0.25 ? C.amber : C.muted;
  const readout = valueLabel ?? (v >= 0 ? `+${v.toFixed(2)}` : v.toFixed(2));
  const markerPulse = liveFrame !== undefined ? Math.sin(liveFrame * 0.07) : 0;

  const extraRow = extraTicks && extraTicks.length > 0;

  return (
    <div style={{ position: "relative", width, height: trackY + 70 + (extraRow ? 40 : 0) }}>
      <svg width={width} height={trackY + 30} viewBox={`0 0 ${width} ${trackY + 30}`} style={{ overflow: "visible" }}>
        <defs>
          <filter id="glow-scale-marker" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation={Math.max(4, 8 + 3 * markerPulse)} result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* base track */}
        <line x1={pad} x2={width - pad} y1={trackY} y2={trackY} stroke={C.line} strokeWidth={10} strokeLinecap="round" />
        {/* filled segment from the 0-mark to the marker, colored by sign */}
        <line
          x1={xFor(0)}
          x2={markerX}
          y1={trackY}
          y2={trackY}
          stroke={markerColor}
          strokeWidth={10}
          strokeLinecap="round"
          opacity={0.85}
        />
        {/* tick marks at -1, 0, +1 */}
        {[-1, 0, 1].map((t) => (
          <line key={t} x1={xFor(t)} x2={xFor(t)} y1={trackY - 20} y2={trackY + 20} stroke={C.muted} strokeWidth={3} />
        ))}
        {/* extra reference ticks (e.g. "real" data points) -- glow brighter
            whenever the live marker sweeps close to them. */}
        {extraTicks?.map((et) => {
          const tx = xFor(Math.max(-1, Math.min(1, et.value)));
          const active = Math.abs(v - et.value) < 0.03;
          const col = et.color ?? C.mint;
          return (
            <g key={et.label}>
              <line
                x1={tx}
                x2={tx}
                y1={trackY - (active ? 32 : 26)}
                y2={trackY + (active ? 32 : 26)}
                stroke={col}
                strokeWidth={active ? 5 : 3}
                opacity={active ? 1 : 0.6}
              />
              <circle cx={tx} cy={trackY} r={active ? 9 : 5} fill={col} opacity={active ? 0.95 : 0.55} />
            </g>
          );
        })}
        <circle
          cx={markerX}
          cy={trackY}
          r={17 + 2 * markerPulse}
          fill={markerColor}
          stroke={C.bg}
          strokeWidth={4}
          filter="url(#glow-scale-marker)"
        />
        <circle
          cx={markerX}
          cy={trackY}
          r={30 + 7 * Math.max(0, markerPulse)}
          fill="none"
          stroke={markerColor}
          strokeWidth={2}
          opacity={0.3 + 0.2 * Math.max(0, markerPulse)}
        />
      </svg>

      {/* readout above the marker */}
      <div
        style={{
          position: "absolute",
          left: markerX,
          top: 0,
          translate: "-50% 0px",
          fontFamily: FONT.mono,
          fontWeight: 800,
          fontSize: 38,
          color: markerColor,
          whiteSpace: "nowrap",
          textShadow: "0 2px 14px rgba(0,0,0,.7)",
        }}
      >
        {readout}
      </div>

      {/* end labels below the track */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: trackY + 34,
          width,
          display: "flex",
          justifyContent: "space-between",
          fontFamily: FONT.mono,
          fontSize: 20,
          fontWeight: 700,
          letterSpacing: 0.5,
        }}
      >
        <span style={{ color: C.amber }}>−1 · move OPPOSITE</span>
        <span style={{ color: C.muted }}>0 · unrelated</span>
        <span style={{ color: C.mint }}>+1 · move TOGETHER</span>
      </div>

      {/* extra reference-tick labels, one row below the end labels -- e.g.
          "AMAT · LRCX (real) 0.89" pinned under its tick, brightening when
          the live marker sweeps close to it (mirrors the tick glow above). */}
      {extraTicks?.map((et) => {
        const tx = xFor(Math.max(-1, Math.min(1, et.value)));
        const active = Math.abs(v - et.value) < 0.03;
        const col = et.color ?? C.mint;
        return (
          <div
            key={et.label}
            style={{
              position: "absolute",
              left: tx,
              top: trackY + 62,
              translate: "-50% 0px",
              fontFamily: FONT.mono,
              fontSize: active ? 21 : 18,
              fontWeight: active ? 800 : 600,
              color: col,
              opacity: active ? 1 : 0.65,
              whiteSpace: "nowrap",
              textShadow: active ? "0 2px 12px rgba(0,0,0,.8)" : "none",
              transition: "none",
            }}
          >
            {et.label}
          </div>
        );
      })}
    </div>
  );
};

export { clamp };

// ---- SemisReel charts ------------------------------------------------------

/** Candlestick free-fall. Down candles use C.red (data, not decoration).
 * `reveal` 0..1 draws candles left->right; `dropPct` shows the headline % . */
export const CrashChart: React.FC<{
  candles: { o: number; h: number; l: number; c: number }[];
  reveal: number; dropPct: number; width: number; height: number;
}> = ({ candles, reveal, dropPct, width, height }) => {
  const n = candles.length;
  const shown = Math.max(0, Math.min(n, Math.floor(reveal * n)));
  const cw = (width / n) * 0.62;
  const yOf = (v: number) => height - v * height;
  return (
    <svg width={width} height={height} style={{ overflow: "visible" }}>
      {candles.slice(0, shown).map((k, i) => {
        const x = (i + 0.5) * (width / n);
        const down = k.c <= k.o;
        const col = down ? C.redHot : C.emerald;
        const bodyTop = yOf(Math.max(k.o, k.c));
        const bodyBot = yOf(Math.min(k.o, k.c));
        return (
          <g key={i}>
            <line x1={x} x2={x} y1={yOf(k.h)} y2={yOf(k.l)} stroke={col} strokeWidth={2} />
            <rect x={x - cw / 2} y={bodyTop} width={cw} height={Math.max(2, bodyBot - bodyTop)} fill={col} rx={2} />
          </g>
        );
      })}
      <text x={width} y={28} textAnchor="end" fontFamily={FONT.mono} fontWeight={800}
        fontSize={64} fill={C.redHot}>{dropPct.toFixed(1)}%</text>
    </svg>
  );
};

/** Capital rotating from an amber "chips" node (left) to a mint "healthcare"
 * node (right). `t` 0..1 drives particle travel + node glow swap. */
export const RotationFlow: React.FC<{ t: number; width: number; height: number }> = ({ t, width, height }) => {
  const cy = height / 2;
  const lx = width * 0.2, rx = width * 0.8;
  const dots = Array.from({ length: 14 }, (_, i) => {
    const phase = (i / 14 + t) % 1;
    const x = lx + (rx - lx) * phase;
    const y = cy + Math.sin(phase * Math.PI * 2 + i) * 40;
    return { x, y, o: Math.sin(phase * Math.PI) };
  });
  return (
    <svg width={width} height={height} style={{ overflow: "visible" }}>
      <circle cx={lx} cy={cy} r={54} fill="none" stroke={C.amber} strokeWidth={3} opacity={1 - t * 0.6} />
      <circle cx={rx} cy={cy} r={54} fill="none" stroke={C.mint} strokeWidth={3} opacity={0.4 + t * 0.6} />
      {dots.map((d, i) => (
        <circle key={i} cx={d.x} cy={d.y} r={7} fill={d.x < (lx + rx) / 2 ? C.amber : C.mint} opacity={d.o} />
      ))}
      <text x={lx} y={cy + 100} textAnchor="middle" fontFamily={FONT.mono} fontWeight={700} fontSize={26} fill={C.amber}>CHIPS</text>
      <text x={rx} y={cy + 100} textAnchor="middle" fontFamily={FONT.mono} fontWeight={700} fontSize={26} fill={C.mint}>HEALTHCARE</text>
    </svg>
  );
};
