// Standard character/element entrance: opacity + translateY + scale, spring-driven.
// Phase 3 decision: default to spring() per haidrrrry/claude-remotion-skill
// motion-patterns.md §1 (SKILL.md rule 1 — "every entrance prefers spring()").
// Roll back to interpolate()/bezier (../../../remotion/src/motion/craft.ts EASE)
// per-composition if a smoke-test render looks worse than the existing approach.
import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";

export const Entrance: React.FC<{
  delay?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ delay = 0, children, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: theme.spring.smooth });
  return (
    <div
      style={{
        opacity: p,
        transform: `translateY(${interpolate(p, [0, 1], [40, 0])}px) scale(${interpolate(
          p,
          [0, 1],
          [0.94, 1]
        )})`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
