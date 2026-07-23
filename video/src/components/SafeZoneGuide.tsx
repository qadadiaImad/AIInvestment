// Dev-only 9:16 safe-zone overlay — critical content must stay inside the middle
// ~75% vertically (platform UI covers top/bottom).
// Source: haidrrrry/claude-remotion-skill references/design-rules.md,
// "9:16 safe zone: critical text inside the middle ~75% vertically".
// Render only while composing/reviewing; never ship it burned into a delivered video.
import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";

export const SafeZoneGuide: React.FC<{ enabled?: boolean }> = ({ enabled = false }) => {
  const { height } = useVideoConfig();
  if (!enabled) return null;
  const margin = height * 0.125; // 75% middle band => 12.5% top + 12.5% bottom
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 0,
          height: margin,
          background: "repeating-linear-gradient(45deg, rgba(255,0,80,.18) 0 8px, transparent 8px 16px)",
          borderBottom: "1px dashed rgba(255,0,80,.6)",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 0,
          height: margin,
          background: "repeating-linear-gradient(45deg, rgba(255,0,80,.18) 0 8px, transparent 8px 16px)",
          borderTop: "1px dashed rgba(255,0,80,.6)",
        }}
      />
    </AbsoluteFill>
  );
};
