// Fonts are bundled locally via @fontsource (Remotion's recommended offline
// path) instead of @remotion/google-fonts: sandboxed/CI renderers can't reach
// fonts.gstatic.com, and local woff2 makes renders deterministic everywhere.
import "@fontsource/fraunces/600.css";
import "@fontsource/fraunces/700.css";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/jetbrains-mono/600.css";
import "@fontsource/jetbrains-mono/700.css";
import "@fontsource/jetbrains-mono/800.css";

export const FONT = {
  display: "'Fraunces', serif",
  body: "'Inter', sans-serif",
  mono: "'JetBrains Mono', monospace",
};

export const C = {
  bg: "#0A0D12",
  ink: "#E8EDF2",
  inkSoft: "#D7DEE8",
  muted: "#8893A4",
  emerald: "#34D399",
  emeraldDeep: "#10B981",
  mint: "#7FE9C2",
  amber: "#E0A23B",
  red: "#C25E5E",
  redHot: "#E0524D",
  panel: "rgba(255,255,255,.05)",
  line: "rgba(255,255,255,.14)",
};

export const NOT_FATWA = "Computed methodology result — not a fatwa · not financial advice";
