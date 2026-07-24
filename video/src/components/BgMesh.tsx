// Never a flat solid background (SKILL.md rule 5, five-layer stack).
// Source: haidrrrry/claude-remotion-skill references/motion-patterns.md §4.
import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { theme } from "../theme";

export const BgMesh: React.FC<{ hero: string }> = ({ hero }) => {
  const frame = useCurrentFrame();
  const d1 = Math.sin(frame / 55) * 50;
  const d2 = Math.cos(frame / 70) * 40;
  return (
    <AbsoluteFill style={{ background: theme.colors.bg }}>
      <div
        style={{
          position: "absolute",
          width: 1200,
          height: 1200,
          borderRadius: "50%",
          top: -450,
          left: -300 + d1,
          filter: "blur(50px)",
          background: `radial-gradient(circle, ${hero}33, transparent 62%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 900,
          height: 900,
          borderRadius: "50%",
          bottom: -400,
          right: -250 - d2,
          filter: "blur(70px)",
          background: `radial-gradient(circle, ${theme.colors.accent}22, transparent 65%)`,
        }}
      />
    </AbsoluteFill>
  );
};
