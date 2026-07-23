// Color grade overlay — unifies mismatched layers into one look. Renders above
// content, below grain/vignette (../../../remotion/src/motion/Polish.tsx, reused
// as-is rather than duplicated — it's already self-contained: react + remotion only).
// Source: haidrrrry/claude-remotion-skill references/motion-patterns.md §5.
import React from "react";
import { AbsoluteFill } from "remotion";

export const Grade: React.FC<{ hero: string; opacity?: number }> = ({ hero, opacity = 0.18 }) => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <AbsoluteFill style={{ backgroundColor: hero, mixBlendMode: "soft-light", opacity }} />
    <AbsoluteFill
      style={{
        background:
          "linear-gradient(180deg, rgba(0,0,0,0.10), transparent 28%, transparent 72%, rgba(0,0,0,0.2))",
      }}
    />
  </AbsoluteFill>
);
