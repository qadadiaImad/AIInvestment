// ScreenInsert.tsx — perspective-map an arbitrary child composition onto an
// arbitrary convex quad in the parent frame, via a CSS matrix3d homography.
//
// Why this exists: the meme reel plays a REAL chart on a monitor that sits in
// an illustrated room at an angle. Scaling a rectangle cannot do that — the
// monitor's screen is a trapezoid in the plate, so the chart has to be mapped
// through a projective transform, not an affine one.
//
// All of the maths lives in ./screenMath.ts, which imports nothing, so it can
// be run and checked under plain node (scripts/check_screen_math.mjs). This
// file is only the layering: bloom under, insert, glass over.
//
// Two rules the maths depends on, both silent when broken:
//   * The child is laid out at its NATURAL width/height with
//     transform-origin '0 0'. The homography is expressed in the child's own
//     pixel space; any other origin shifts the result.
//   * No CSS `perspective()` anywhere in the ancestor chain. The g/h row of
//     the homography already performs the projective divide — a second CSS
//     perspective compounds it and is the likeliest cause of an insert that
//     lands off the monitor while the maths is correct.
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Quad, solveHomography, toMatrix3d} from './screenMath';

export type {Pt, Quad} from './screenMath';

export type ScreenInsertProps = {
  /** Native size the child renders at. Render big, map down — the homography
   * downscales, so oversampling here is what keeps the text crisp. */
  width: number;
  height: number;
  /** Destination quad in the parent frame: TL, TR, BR, BL. */
  quad: Quad;
  /** Screen emission colour; drives the bloom that spills onto the room. */
  glowColor?: string;
  /** 0 = panel off, 1 = full brightness. Animate to boot the monitor. */
  glow?: number;
  /** Faint angled glass highlight over the panel. 0 disables it. */
  reflection?: number;
  children: React.ReactNode;
};

export const ScreenInsert: React.FC<ScreenInsertProps> = ({
  width,
  height,
  quad,
  glowColor = '#4FD6A0',
  glow = 1,
  reflection = 0.1,
  children,
}) => {
  // Solving an 8x8 system every frame for a static quad is wasted work.
  const m = React.useMemo(() => solveHomography(width, height, quad), [width, height, quad]);
  // A degenerate or non-convex quad means "do not render" — never a fallback
  // identity transform, which would slap a full-size chart over the room.
  if (!m) return null;

  // Bloom is a blurred fill of the same quad UNDER the insert, so light appears
  // to come off the panel onto the illustrated room rather than being painted
  // on top of the chart.
  const polygon = quad.map((p) => `${p.x}px ${p.y}px`).join(', ');

  return (
    <AbsoluteFill>
      {glow > 0 ? (
        <AbsoluteFill
          style={{
            clipPath: `polygon(${polygon})`,
            background: glowColor,
            filter: 'blur(46px)',
            opacity: 0.42 * glow,
          }}
        />
      ) : null}

      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width,
          height,
          transform: toMatrix3d(m),
          transformOrigin: '0 0',
          opacity: glow,
          backfaceVisibility: 'hidden',
          overflow: 'hidden',
        }}
      >
        {children}
      </div>

      {/* Glass: one soft diagonal highlight clipped to the panel. Kept low —
          a strong reflection reads as a sticker over the chart and costs
          legibility, which is the one thing this insert exists for. */}
      {reflection > 0 ? (
        <AbsoluteFill
          style={{
            clipPath: `polygon(${polygon})`,
            background:
              'linear-gradient(112deg, rgba(255,255,255,0.16) 0%, rgba(255,255,255,0.05) 26%, rgba(255,255,255,0) 46%)',
            opacity: reflection,
            pointerEvents: 'none',
          }}
        />
      ) : null}
    </AbsoluteFill>
  );
};
