// Single theme object for this project — colors, easing curves, spring presets.
// Never inline a hex color or easing in a component (haidrrrry/claude-remotion-skill,
// SKILL.md non-negotiable rule 9).
//
// Palette mirrors ../../remotion/src/slides/theme.ts (`C`) — the AIInvestment brand
// tokens the character canon itself renders against — so this video layer stays
// visually consistent with the rigs it composites, without importing/duplicating
// character definitions (those come from ./characters/registry.ts instead).
import { Easing } from "remotion";

export const theme = {
  colors: {
    bg: "#0A0D12",
    bgAlt: "#11161F",
    text: "#E8EDF2",
    textDim: "#8893A4",
    // "hero" is per-character (see characters/registry.ts CHARACTERS[].color) —
    // at most one hero-colored/glowing element on screen at a time
    // (haidrrrry design-rules.md, 60/30/10 color rule).
    accent: "#7FE9C2",
  },
  fonts: {
    display: "'Fraunces', serif",
    body: "'Inter', sans-serif",
    mono: "'JetBrains Mono', monospace",
  },
  // Approved Phase 3 decision: default every entrance to spring() per the
  // third-party skill (haidrrrry SKILL.md rule 1). Roll back to interpolate()/
  // bezier per-composition if a smoke-test render looks off.
  ease: {
    out: Easing.bezier(0.16, 1, 0.3, 1), // easeOutExpo — entrances
    inOut: Easing.bezier(0.83, 0, 0.17, 1), // easeInOutQuint — moves, Ken Burns
    in: Easing.bezier(0.7, 0, 0.84, 0), // exits only
  },
  spring: {
    snappy: { damping: 14, stiffness: 160, mass: 0.6 }, // UI pops, words
    smooth: { damping: 20, stiffness: 90, mass: 1 }, // big elements, character entrances
    bouncy: { damping: 11, stiffness: 170, mass: 0.7 }, // playful accents
  },
} as const;
