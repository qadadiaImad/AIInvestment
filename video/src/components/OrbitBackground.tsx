// Real company logos orbiting a TSM center mark — replaces the earlier
// matplotlib dot-graph (kept as a static image, this is a live animated
// Remotion/SVG layer instead: slow ring rotation + per-tile idle breathing +
// spokes that draw in on entrance). Logo source: ../data/orbitLogos.ts.
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { ORBIT_LOGOS, CATEGORY_COLOR } from "../data/orbitLogos";
import { theme } from "../theme";

const CENTER = { xFrac: 0.5, yFrac: 0.4 };
const RING_RADIUS_FRAC = 0.27; // of frame width
const TILE = 108;

const LogoTile: React.FC<{
  logo: (typeof ORBIT_LOGOS)[number];
  x: number;
  y: number;
  frame: number;
  delay: number;
}> = ({ logo, x, y, frame, delay }) => {
  const local = frame - delay;
  const enter = interpolate(local, [0, 18], [0, 1], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const breathe = 1 + Math.sin((frame + delay * 7) / 30) * 0.03;
  const ring = CATEGORY_COLOR[logo.category];

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: `translate(-50%, -50%) scale(${enter * breathe})`,
        opacity: enter,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 10,
      }}
    >
      <div
        style={{
          width: TILE,
          height: TILE,
          borderRadius: 26,
          background: "#11161F",
          border: `2px solid ${ring}`,
          boxShadow: `0 0 30px ${ring}33`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {logo.path ? (
          <svg width={TILE * 0.52} height={TILE * 0.52} viewBox="0 0 24 24">
            <path d={logo.path} fill={theme.colors.text} />
          </svg>
        ) : (
          <div
            style={{
              fontFamily: theme.fonts.display,
              fontWeight: 700,
              fontSize: 26,
              color: theme.colors.text,
            }}
          >
            {logo.title}
          </div>
        )}
      </div>
      <div
        style={{
          fontFamily: theme.fonts.mono,
          fontWeight: 700,
          fontSize: 18,
          letterSpacing: "0.04em",
          color: theme.colors.textDim,
        }}
      >
        {logo.ticker}
      </div>
    </div>
  );
};

export const OrbitBackground: React.FC<{ heroColor: string }> = ({ heroColor }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const cx = width * CENTER.xFrac;
  const cy = height * CENTER.yFrac;
  const radius = width * RING_RADIUS_FRAC;

  // Whole ring drifts very slowly — "alive" background without distracting
  // from the character/captions in front of it.
  const drift = interpolate(frame, [0, 900], [0, Math.PI / 8], { easing: theme.ease.inOut });

  const n = ORBIT_LOGOS.length;
  const positions = ORBIT_LOGOS.map((logo, i) => {
    const theta = -Math.PI / 2 + (2 * Math.PI * i) / n + drift;
    return {
      logo,
      x: cx + radius * Math.cos(theta),
      y: cy + radius * Math.sin(theta) * 0.62, // flatten into an ellipse, more room top/bottom
      delay: 6 + i * 5,
    };
  });

  const spokeLen = interpolate(frame, [0, 24], [0, 1], {
    easing: theme.ease.out,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {positions.map(({ x, y }, i) => (
          <line
            key={i}
            x1={cx}
            y1={cy}
            x2={cx + (x - cx) * spokeLen}
            y2={cy + (y - cy) * spokeLen}
            stroke="#2A3340"
            strokeWidth={1.5}
            opacity={0.8}
          />
        ))}
      </svg>

      <div
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          transform: "translate(-50%, -50%)",
          width: 156,
          height: 156,
          borderRadius: "50%",
          background: theme.colors.text,
          boxShadow: `0 0 60px ${heroColor}55, 0 0 120px ${heroColor}22`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            fontFamily: theme.fonts.display,
            fontWeight: 700,
            fontSize: 40,
            color: theme.colors.bg,
          }}
        >
          TSM
        </div>
      </div>

      {positions.map(({ logo, x, y, delay }) => (
        <LogoTile key={logo.ticker} logo={logo} x={x} y={y} frame={frame} delay={delay} />
      ))}
    </>
  );
};
