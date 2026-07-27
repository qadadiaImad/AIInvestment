// ToonFX.tsx — the drawn effects a cartoon reaction needs and a chart does not
// supply: impact lines, sweat beads, dust, and the one-frame flash.
//
// These are the things whose absence the owner named. They are NOT decoration
// bolted onto the timeline: each one is anchored to a beat that already exists
// in the story, and each one is drawn (hard vector shapes, flat fills, no
// gradients or particles) so it sits in the same world as the character rather
// than looking like a video-editor preset dropped on top.
//
// Three rules they all follow:
//   1. SHORT. Nothing here runs longer than ~20 frames. A cartoon effect that
//      outstays the hit it punctuates reads as a screensaver.
//   2. DETERMINISTIC. Every random is seeded off the index, so renders match.
//   3. NEVER ON THE CHART. They live in the room layer, above the character
//      and below the type. No effect is ever allowed over the price panel —
//      an "impact" drawn across a candle would be asserting something about
//      the data, and the data says what it says on its own.
import React from 'react';
import {interpolate} from 'remotion';
import {EASE} from './craft';
import {impact} from './toon';

/** Radiating impact lines — the shock take. Drawn from a ring outward so the
 * centre stays clear of the character's face. */
export const ImpactLines: React.FC<{
  x: number;
  y: number;
  since: number;
  dur?: number;
  count?: number;
  color?: string;
  r0?: number;
  len?: number;
  /** Radiate over an ARC rather than a full circle. The burst here has to stay
   * off the monitor — a line drawn across a candle is asserting something
   * about the data — so it opens upward and away from the screen instead of
   * being masked, which would read as a burst someone had cut a hole in. */
  arc?: [number, number];
}> = ({
  x,
  y,
  since,
  dur = 14,
  count = 14,
  color = '#1B1208',
  r0 = 210,
  len = 190,
  arc = [0, Math.PI * 2],
}) => {
  if (since < 0 || since > dur) return null;
  const t = since / dur;
  // Fast out, then gone. The lines never travel back inward.
  const grow = interpolate(t, [0, 1], [0, 1], {easing: EASE.exit});
  const op = interpolate(t, [0, 0.25, 1], [0, 0.9, 0]);
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
      {Array.from({length: count}, (_, i) => {
        const a = arc[0] + ((i + 0.5) / count) * (arc[1] - arc[0]);
        // Alternating lengths — a perfectly even starburst reads as a logo.
        const l = len * (i % 2 === 0 ? 1 : 0.62);
        const ir = r0 + grow * 64;
        const or = ir + l * grow;
        return (
          <line
            key={i}
            x1={x + Math.cos(a) * ir}
            y1={y + Math.sin(a) * ir}
            x2={x + Math.cos(a) * or}
            y2={y + Math.sin(a) * or}
            stroke={color}
            strokeWidth={i % 2 === 0 ? 9 : 5}
            strokeLinecap="round"
            opacity={op}
          />
        );
      })}
    </svg>
  );
};

/** Sweat beads — the anxious wait. They pop out from the head, hang, then fly
 * off. Classic, funny, and the cheapest possible read of "he is nervous". */
export const SweatBeads: React.FC<{
  x: number;
  y: number;
  since: number;
  count?: number;
  scale?: number;
}> = ({x, y, since, count = 3, scale = 1}) => {
  const CYCLE = 46;
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
      {Array.from({length: count}, (_, i) => {
        const phase = (since + i * 17) % CYCLE;
        if (phase > 26) return null;
        const p = phase / 26;
        // side of the head, alternating, with a fixed lean
        const dir = i % 2 === 0 ? -1 : 1;
        const ox = dir * (78 + i * 9) * scale;
        const oy = -14 - i * 26 * scale;
        // pop out, hang, then fly
        const out = interpolate(p, [0, 0.28], [0, 1], {easing: EASE.settleBack, extrapolateRight: 'clamp'});
        const fly = interpolate(p, [0.55, 1], [0, 1], {easing: EASE.exit, extrapolateLeft: 'clamp'});
        const bx = x + ox + dir * 40 * fly;
        const by = y + oy - 26 * fly;
        const op = interpolate(p, [0, 0.15, 0.7, 1], [0, 1, 1, 0]);
        const s = (0.7 + 0.3 * out) * scale;
        return (
          <g key={i} opacity={op} transform={`translate(${bx} ${by}) scale(${s * out})`}>
            {/* teardrop: round bottom, pointed top, leaning the way it flies */}
            <path
              d={`M0 -26 C 11 -8, 17 2, 17 10 A 17 17 0 1 1 -17 10 C -17 2, -11 -8, 0 -26 Z`}
              fill="#8FD3F4"
              stroke="#1B1208"
              strokeWidth={4}
              transform={`rotate(${dir * 16})`}
            />
            <ellipse cx={-5} cy={7} rx={4} ry={6} fill="#EAF7FF" opacity={0.9} />
          </g>
        );
      })}
    </svg>
  );
};

/** ONE sweat drop, gliding slowly down the head, on a loop.
 *
 * The owner's note on the bead version: exaggerated. Three drops popping off
 * the skull is a gag; one drop crawling down the temple is DREAD, and dread is
 * the emotion this beat actually carries. So: it beads up near the temple,
 * slides down slowly — gathering a little size as it goes, the way a real drop
 * collects — flattens out at the jaw, and after a beat another one forms.
 * Nothing flies anywhere.
 *
 * `x`/`y` are the head centre and `w` its width, both from the measured
 * per-pose head anchor, so the drop stays on the skull through every cut. */
export const SweatSlide: React.FC<{
  x: number;
  y: number;
  w: number;
  since: number;
}> = ({x, y, w, since}) => {
  if (since < 0) return null;
  const CYCLE = 132; // ~4.4s — slow is the point
  const t = (since % CYCLE) / CYCLE;

  // phases: bead up 0-.09 · glide .09-.72 · flatten+fade .72-.85 · rest
  if (t > 0.85) return null;
  const beadIn = interpolate(t, [0, 0.09], [0, 1], {
    easing: EASE.settleBack,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const glide = interpolate(t, [0.09, 0.72], [0, 1], {
    // starts hesitant, gains a little speed — a drop breaking surface tension
    easing: EASE.cruise,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fade = interpolate(t, [0.72, 0.85], [1, 0], {
    easing: EASE.exit,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Path: down the temple, bowing slightly outward over the cheekbone and
  // back in toward the jaw. Quadratic in glide, in units of head width.
  const px = x + w * 0.28 + w * (0.10 * Math.sin(glide * Math.PI)) * 0.6;
  const py = y - w * 0.18 + w * 0.62 * glide;
  const size = w * 0.085 * (0.8 + 0.25 * glide) * beadIn; // gathers as it slides
  const squish = 1 + 0.35 * (1 - fade); // flattens as it dies at the jaw

  return (
    <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
      <g opacity={Math.min(beadIn, fade)} transform={`translate(${px} ${py}) scale(${size / 20})`}>
        <path
          d={`M0 -22 C 8.5 -7, 13.5 1, 13.5 ${8 * squish} A 13.5 ${13.5 * squish} 0 1 1 -13.5 ${8 * squish} C -13.5 1, -8.5 -7, 0 -22 Z`}
          fill="#8FD3F4"
          stroke="#12262E"
          strokeWidth={3}
        />
        <ellipse cx={-4} cy={5} rx={3.2} ry={5} fill="#EAF7FF" opacity={0.9} />
      </g>
    </svg>
  );
};

/** Three short surprise flicks beside the head — the manga "!!" without the
 * glyph. Small on purpose: in the corner-cam format there is no room for a
 * full radial burst that stays off the chart, and three flicks read the same
 * beat at a tenth the ink. */
export const ShockFlicks: React.FC<{
  x: number;
  y: number;
  since: number;
  size?: number;
  color?: string;
}> = ({x, y, since, size = 60, color = '#EAFFF4'}) => {
  const DUR = 13;
  if (since < 0 || since > DUR) return null;
  const t = since / DUR;
  const grow = interpolate(t, [0, 0.45], [0, 1], {easing: EASE.settleBack, extrapolateRight: 'clamp'});
  const op = interpolate(t, [0, 0.15, 0.75, 1], [0, 1, 1, 0]);
  const angles = [-0.35, -0.95, -1.55]; // up-and-outward fan
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
      {angles.map((a, i) => {
        const l = size * (i === 1 ? 1 : 0.72);
        const r0 = size * 0.55 + grow * size * 0.3;
        return (
          <line
            key={i}
            x1={x + Math.cos(a) * r0}
            y1={y + Math.sin(a) * r0}
            x2={x + Math.cos(a) * (r0 + l * grow)}
            y2={y + Math.sin(a) * (r0 + l * grow)}
            stroke={color}
            strokeWidth={7 - i}
            strokeLinecap="round"
            opacity={op}
            style={{filter: `drop-shadow(0 0 6px ${color})`}}
          />
        );
      })}
    </svg>
  );
};

/** Dust puff at the feet — the stagger. Two expanding, fading rings of blobs. */
export const DustPuff: React.FC<{x: number; y: number; since: number; dur?: number}> = ({
  x,
  y,
  since,
  dur = 20,
}) => {
  if (since < 0 || since > dur) return null;
  const t = since / dur;
  const op = interpolate(t, [0, 0.2, 1], [0, 0.55, 0]);
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
      {Array.from({length: 7}, (_, i) => {
        const dir = i < 4 ? -1 : 1;
        const k = (i % 4) + 1;
        const travel = interpolate(t, [0, 1], [0, 1], {easing: EASE.exit});
        const cx = x + dir * (26 + k * 34) * travel;
        const cy = y - 6 - k * 7 * travel;
        const r = (13 + k * 5) * (0.5 + travel * 0.9);
        return <circle key={i} cx={cx} cy={cy} r={r} fill="#C6B49A" opacity={op} />;
      })}
    </svg>
  );
};

/** The one-frame flash. Reel grammar: on a hard cut to the worst moment, a
 * single bright frame sells the hit better than any transition. Kept to 1-2
 * frames — three is a strobe and reads as a fault. */
export const FlashCut: React.FC<{since: number; frames?: number; color?: string; max?: number}> = ({
  since,
  frames = 2,
  color = '#FFFFFF',
  max = 0.72,
}) => {
  if (since < 0 || since >= frames) return null;
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: color,
        opacity: max * (1 - since / frames),
        pointerEvents: 'none',
      }}
    />
  );
};

/** Directional speed lines — laid over a whip so the cut has velocity rather
 * than just being sudden. `k` is the whip intensity, 0..1. */
export const SpeedLines: React.FC<{k: number; seed?: number; color?: string}> = ({
  k,
  seed = 0,
  color = 'rgba(20,14,8,0.5)',
}) => {
  if (k <= 0.02) return null;
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
      {Array.from({length: 20}, (_, i) => {
        const r = ((i * 9301 + seed * 49297) % 233280) / 233280;
        const y = r * 1920;
        const w = 180 + r * 620;
        const x0 = ((i * 7919 + seed * 104729) % 1080) - w * 0.3;
        return (
          <rect
            key={i}
            x={x0}
            y={y}
            width={w * k}
            height={2 + (i % 3)}
            fill={color}
            opacity={k * 0.75}
          />
        );
      })}
    </svg>
  );
};

/** A drawn shock-ring: one expanding outline, used with ImpactLines so the hit
 * has a shape as well as rays. */
export const ShockRing: React.FC<{x: number; y: number; since: number; dur?: number; color?: string}> = ({
  x,
  y,
  since,
  dur = 16,
  color = '#1B1208',
}) => {
  if (since < 0 || since > dur) return null;
  const t = since / dur;
  const r = interpolate(t, [0, 1], [90, 420], {easing: EASE.exit});
  const op = interpolate(t, [0, 0.18, 1], [0, 0.5, 0]);
  const sw = interpolate(t, [0, 1], [14, 2]);
  return (
    <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
      <circle cx={x} cy={y} r={r} fill="none" stroke={color} strokeWidth={sw} opacity={op} />
    </svg>
  );
};

/** Screen-emission pulse: the monitor throwing light into the room when a bar
 * breaks. Anchored to the monitor quad, not the frame, so it reads as the
 * panel and not as a filter. */
export const ScreenPulse: React.FC<{
  quad: {x: number; y: number}[];
  since: number;
  dur?: number;
  color?: string;
}> = ({quad, since, dur = 22, color = '#FF3B30'}) => {
  if (since < 0 || since > dur) return null;
  const op = interpolate(since / dur, [0, 0.12, 1], [0, 0.5, 0]);
  const polygon = quad.map((p) => `${p.x}px ${p.y}px`).join(', ');
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        clipPath: `polygon(${polygon})`,
        background: color,
        filter: 'blur(58px)',
        opacity: op,
        pointerEvents: 'none',
      }}
    />
  );
};

/** Impact-driven camera kick, in px. Exported here so a composition applies
 * exactly the same decay to the frame that the FX use for their hit. */
export const kick = (since: number, amp = 26, dur = 18): {x: number; y: number} => ({
  x: impact(since, dur) * amp,
  y: impact(since - 1, dur) * amp * 0.7,
});
