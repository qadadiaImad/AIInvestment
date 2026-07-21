import { loadFont as loadFraunces } from "@remotion/google-fonts/Fraunces";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";

const fraunces = loadFraunces("normal", { weights: ["600", "700"], subsets: ["latin"] });
const inter = loadInter("normal", { weights: ["400", "500", "600", "700"], subsets: ["latin"] });
const mono = loadMono("normal", { weights: ["600", "700", "800"], subsets: ["latin"] });

export const FONT = {
  display: fraunces.fontFamily,
  body: inter.fontFamily,
  mono: mono.fontFamily,
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
