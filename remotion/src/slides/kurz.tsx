// kurz.tsx — Kurzgesagt-INSPIRED motion primitives for the animated-carousel
// slide engine (KurzSlide.tsx). Flat-vector educational cuteness (rounded
// geometric shapes, saturated accents on our deep ground, gentle constant
// motion), built entirely from our own theme.ts palette + basic SVG/div
// shapes — no mascots, no traced trade dress. Every primitive animates
// continuously off useCurrentFrame so nothing on a slide is ever static.
import React from 'react';
import {interpolate, random, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, FONT} from './theme';
import {clamp, pop} from './ui';

// ---------------------------------------------------------------------------
// FloatingBlob — a large soft rounded blob: slow sine drift + gentle rotate,
// two-stop gradient fill, blurred edge for softness. Configurable hue/size/xy
// so callers can drop several behind text/motifs as ambient "life".
// ---------------------------------------------------------------------------
export const FloatingBlob: React.FC<{
  size?: number;
  x?: number; // center, % of slide width
  y?: number; // center, % of slide height
  hue?: string;
  hue2?: string;
  seed?: number; // phase offset so multiple blobs don't sync
  opacity?: number;
  blur?: number;
}> = ({size = 560, x = 50, y = 50, hue = C.emerald, hue2 = C.mint, seed = 0, opacity = 0.32, blur = 60}) => {
  const frame = useCurrentFrame();
  const t = frame + seed * 41;
  const driftX = Math.sin(t / 96) * 26;
  const driftY = Math.cos(t / 118) * 20;
  const rotate = Math.sin(t / 150) * 12 + seed * 7;
  // asymmetric radii give the organic "blob" silhouette; drift very slowly
  // over an even slower cycle so it never reads as pulsing.
  const wob = Math.sin(t / 210) * 6;
  const radius = `${42 + wob}% ${58 - wob}% ${63 + wob}% ${37 - wob}% / ${41 - wob}% ${44 + wob}% ${56 - wob}% ${59 + wob}%`;
  return (
    <div
      style={{
        position: 'absolute',
        left: `${x}%`,
        top: `${y}%`,
        width: size,
        height: size,
        translate: `${-size / 2 + driftX}px ${-size / 2 + driftY}px`,
        rotate: `${rotate}deg`,
        borderRadius: radius,
        background: `linear-gradient(135deg, ${hue}, ${hue2})`,
        opacity,
        filter: `blur(${blur}px)`,
        pointerEvents: 'none',
      }}
    />
  );
};

// ---------------------------------------------------------------------------
// OrbitDots — n small dots orbiting a shared center, staggered phase per dot,
// with a slow breathing radius so the ring never feels mechanical.
// ---------------------------------------------------------------------------
export const OrbitDots: React.FC<{
  n?: number;
  radius?: number;
  dotSize?: number;
  colors?: string[];
  speed?: number; // radians/frame multiplier
  x?: number; // center, % of container width
  y?: number; // center, % of container height
}> = ({n = 6, radius = 150, dotSize = 16, colors = [C.emerald, C.mint, C.amber], speed = 1, x = 50, y = 50}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{position: 'absolute', left: `${x}%`, top: `${y}%`, width: 0, height: 0, pointerEvents: 'none'}}>
      {new Array(n).fill(0).map((_, i) => {
        const phase = (i / n) * Math.PI * 2;
        const angle = frame * 0.018 * speed + phase;
        const breathe = 1 + Math.sin(frame / 40 + i) * 0.08;
        const r = radius * breathe;
        const cx = Math.cos(angle) * r;
        const cy = Math.sin(angle) * r * 0.86; // slight ellipse for depth
        const s = dotSize * (0.8 + 0.2 * Math.sin(frame / 22 + i * 2));
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: cx,
              top: cy,
              width: s,
              height: s,
              translate: `${-s / 2}px ${-s / 2}px`,
              borderRadius: '50%',
              background: colors[i % colors.length],
              boxShadow: `0 0 ${s}px ${colors[i % colors.length]}88`,
            }}
          />
        );
      })}
    </div>
  );
};

// ---------------------------------------------------------------------------
// BouncyCounter — huge Fraunces number that springs up with overshoot while
// counting to `value`. Optional prefix ('+') / suffix ('%').
// ---------------------------------------------------------------------------
export const BouncyCounter: React.FC<{
  value: number;
  prefix?: string;
  suffix?: string;
  delay?: number;
  fontSize?: number;
  color?: string;
  countFrames?: number;
}> = ({value, prefix = '', suffix = '', delay = 0, fontSize = 172, color = C.ink, countFrames = 46}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const entrance = spring({frame: frame - delay, fps, config: {damping: 9, mass: 0.7, stiffness: 130}});
  const countP = interpolate(frame, [delay, delay + countFrames], [0, 1], {...clamp, easing: pop});
  const shown = Math.round(countP * value);
  // subtle continuous life after landing: gentle breathing scale.
  const settledT = Math.max(0, frame - (delay + countFrames + 10));
  const breathe = 1 + Math.sin(settledT / 34) * 0.012;
  return (
    <div
      style={{
        fontFamily: FONT.display,
        fontWeight: 700,
        fontSize,
        lineHeight: 1,
        letterSpacing: -3,
        color,
        opacity: Math.min(1, entrance * 1.6),
        scale: String(Math.min(1.15, entrance) * breathe),
        textShadow: '0 10px 46px rgba(0,0,0,.5)',
      }}
    >
      {prefix}
      {shown}
      {suffix}
    </div>
  );
};

// ---------------------------------------------------------------------------
// MetricPill — rounded pill: label + value + a small emerald check badge.
// Pops in with spring, staggered via `delay`.
// ---------------------------------------------------------------------------
export const MetricPill: React.FC<{
  label: string;
  value: string;
  delay?: number;
}> = ({label, value, delay = 0}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - delay, fps, config: {damping: 11, mass: 0.6, stiffness: 160}});
  const bob = Math.sin((frame - delay) / 50) * 3; // gentle life once settled
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 18,
        opacity: Math.min(1, p * 1.5),
        scale: String(Math.min(1, p)),
        translate: `0px ${(1 - Math.min(1, p)) * 24 + bob}px`,
        background: C.panel,
        border: `1.5px solid ${C.line}`,
        borderRadius: 999,
        padding: '18px 26px',
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          flex: '0 0 auto',
          borderRadius: '50%',
          background: `${C.emerald}26`,
          border: `2px solid ${C.emerald}`,
          color: C.emerald,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 22,
          fontWeight: 800,
          fontFamily: FONT.mono,
        }}
      >
        ✓
      </div>
      <div>
        <div style={{fontFamily: FONT.body, fontWeight: 500, fontSize: 24, color: C.muted}}>{label}</div>
        <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 30, color: C.ink, marginTop: 2}}>{value}</div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// IconMotif — three hand-drawn-feeling flat-vector motifs built from basic
// shapes, ~400px, each with a looping idle animation. Own visual identity:
// our palette (theme.ts), rounded geometry, no borrowed trade dress.
// ---------------------------------------------------------------------------

const BeamsMotif: React.FC<{size: number}> = ({size}) => {
  const frame = useCurrentFrame();
  const pulse = (i: number) => 0.55 + 0.45 * ((Math.sin(frame / 26 + i * 1.3) + 1) / 2);
  const flow = (frame * 2.4) % 40;
  const arcs = [
    {d: 'M 60 210 Q 200 60 340 130', color: C.emerald},
    {d: 'M 50 250 Q 200 130 350 210', color: C.mint},
    {d: 'M 70 290 Q 200 200 330 280', color: C.amber},
  ];
  return (
    <svg width={size} height={size} viewBox="0 0 400 400">
      {/* central node the beams emanate from */}
      <g style={{transformOrigin: '200px 200px', rotate: `${Math.sin(frame / 90) * 4}deg`}}>
        <circle cx="200" cy="200" r="46" fill={C.panel} stroke={C.emerald} strokeWidth="4" />
        <circle cx="200" cy="200" r="20" fill={C.emerald} opacity={0.9} />
        {arcs.map((a, i) => (
          <path
            key={i}
            d={a.d}
            fill="none"
            stroke={a.color}
            strokeWidth={10}
            strokeLinecap="round"
            opacity={pulse(i)}
            strokeDasharray="26 14"
            strokeDashoffset={-flow - i * 8}
          />
        ))}
      </g>
    </svg>
  );
};

const PrismMotif: React.FC<{size: number}> = ({size}) => {
  const frame = useCurrentFrame();
  const fan = Math.sin(frame / 45) * 8;
  const rays = [
    {angle: -26 + fan, color: C.redHot},
    {angle: -10 + fan * 0.7, color: C.amber},
    {angle: 8 + fan * 0.5, color: C.emerald},
    {angle: 24 + fan, color: C.mint},
  ];
  return (
    <svg width={size} height={size} viewBox="0 0 400 400">
      {/* incoming beam */}
      <line x1="30" y1="200" x2="176" y2="200" stroke={C.ink} strokeWidth="8" strokeLinecap="round" opacity="0.85" />
      {/* prism */}
      <polygon points="176,120 176,280 300,200" fill={C.panel} stroke={C.ink} strokeWidth="4" opacity="0.9" />
      {/* refracted fan of colored rays */}
      <g style={{transformOrigin: '260px 200px'}}>
        {rays.map((r, i) => {
          const rad = (r.angle * Math.PI) / 180;
          const len = 130;
          const x2 = 260 + Math.cos(rad) * len;
          const y2 = 200 + Math.sin(rad) * len;
          return (
            <line
              key={i}
              x1="260"
              y1="200"
              x2={x2}
              y2={y2}
              stroke={r.color}
              strokeWidth="8"
              strokeLinecap="round"
              opacity={0.5 + 0.5 * ((Math.sin(frame / 20 + i) + 1) / 2)}
            />
          );
        })}
      </g>
    </svg>
  );
};

const StackMotif: React.FC<{size: number}> = ({size}) => {
  const frame = useCurrentFrame();
  const layers = [
    {y: 260, w: 220, color: C.emeraldDeep},
    {y: 200, w: 190, color: C.emerald},
    {y: 140, w: 160, color: C.mint},
  ];
  return (
    <svg width={size} height={size} viewBox="0 0 400 400">
      {layers.map((l, i) => {
        const bob = Math.sin(frame / 44 + i * 1.1) * 6;
        const x = 200 - l.w / 2;
        return (
          <rect
            key={i}
            x={x}
            y={l.y + bob}
            width={l.w}
            height={46}
            rx={16}
            fill={l.color}
            opacity={0.92}
            stroke="#00000022"
            strokeWidth="2"
          />
        );
      })}
      <OrbitDotsSvg frame={frame} />
    </svg>
  );
};

// small helper: a handful of orbiting dots drawn directly as SVG circles
// (kept local to StackMotif so the motif file is a single self-contained
// unit; the standalone <OrbitDots> above is the div-based general primitive
// used elsewhere on the slide).
const OrbitDotsSvg: React.FC<{frame: number}> = ({frame}) => {
  const n = 5;
  const colors = [C.amber, C.mint, C.emerald];
  return (
    <>
      {new Array(n).fill(0).map((_, i) => {
        const angle = frame * 0.02 + (i / n) * Math.PI * 2;
        const r = 150;
        const cx = 200 + Math.cos(angle) * r;
        const cy = 100 + Math.sin(angle) * r * 0.4;
        return <circle key={i} cx={cx} cy={cy} r={6} fill={colors[i % colors.length]} opacity={0.75} />;
      })}
    </>
  );
};

export const IconMotif: React.FC<{kind: 'beams' | 'prism' | 'stack'; size?: number}> = ({kind, size = 400}) => {
  if (kind === 'beams') return <BeamsMotif size={size} />;
  if (kind === 'prism') return <PrismMotif size={size} />;
  return <StackMotif size={size} />;
};

// ---------------------------------------------------------------------------
// small utility export used by KurzSlide for deterministic "randomized but
// stable" jitter, matching the ui.tsx Bg mote pattern (remotion's `random`).
// ---------------------------------------------------------------------------
export const stableJitter = (seed: string) => random(seed) * 2 - 1;
