// Polish.tsx — the finish layers from the playbook (§5): film grain,
// vignette, and key-glow lighting. These three kill the "flat CSS" look;
// every shipped scene should mount <Grain/> and <Vignette/> last.
import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';

/** Subtle animated film grain: SVG feTurbulence, seed re-rolled every 2
 * frames so the noise lives, at ~3.5% opacity. Mount LAST (above content). */
export const Grain: React.FC<{opacity?: number}> = ({opacity = 0.035}) => {
  const frame = useCurrentFrame();
  const seed = Math.floor(frame / 2) % 1000;
  return (
    <AbsoluteFill style={{pointerEvents: 'none', mixBlendMode: 'overlay', opacity}}>
      <svg width="100%" height="100%">
        <filter id={`grain-${seed}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={seed} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grain-${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};

/** Soft vignette pulling the eye to center. Mount above content, below Grain. */
export const Vignette: React.FC<{strength?: number}> = ({strength = 0.42}) => (
  <AbsoluteFill
    style={{
      pointerEvents: 'none',
      background: `radial-gradient(ellipse 78% 68% at 50% 46%, transparent 58%, rgba(0,0,0,${strength}) 100%)`,
    }}
  />
);

/** Warm key glow behind the subject — one per scene, positioned in %. */
export const KeyGlow: React.FC<{x?: number; y?: number; color?: string; size?: number; opacity?: number}> = ({
  x = 50,
  y = 42,
  color = '#34D399',
  size = 900,
  opacity = 0.14,
}) => {
  const frame = useCurrentFrame();
  const breathe = 1 + Math.sin(frame / 46) * 0.05;
  return (
    <div
      style={{
        position: 'absolute',
        left: `${x}%`,
        top: `${y}%`,
        width: size * breathe,
        height: size * breathe,
        translate: '-50% -50%',
        borderRadius: '50%',
        background: `radial-gradient(circle, ${color}, transparent 65%)`,
        opacity,
        pointerEvents: 'none',
      }}
    />
  );
};
