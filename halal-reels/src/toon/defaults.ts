import { RigParams, Skin } from "./types";

export const ANALYST: Skin = { skinFill: "#F3C9A2", outline: "#1A1A1A", shirtFill: "#37B6A6" };

// Neutral, front-facing, arms resting on the desk edge.
export const DEFAULT: RigParams = {
  skin: ANALYST,
  headTurn: 0,
  lean: 0,
  bob: 0,
  brows: { l: "flat", r: "flat" },
  eyes: "open",
  mouth: "flat",
  sweat: false,
  armL: { shoulder: 150, elbow: 40, wrist: 0 },
  armR: { shoulder: 210, elbow: -40, wrist: 0 },
  prop: "none",
};
