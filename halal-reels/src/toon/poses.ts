import { PosePatch } from "./types";

type Entry = { patch: PosePatch; desc: string };
const P = (patch: PosePatch, desc: string): Entry => ({ patch, desc });

// Arm-angle convention (armGeom): shoulder 0=down, 90=screen-right, 180=up,
// 270=screen-left; forearm direction = shoulder + elbow. Left arm origin
// (215,360), right (325,360). Gestures must reach OUTSIDE the torso to read.
export const POSES: Record<string, Entry> = {
  rest: P({ armL: { shoulder: 20, elbow: 25 }, armR: { shoulder: 340, elbow: -25 } }, "hands resting on desk"),
  point_left: P({ armL: { shoulder: 288, elbow: 0 } }, "left arm pointing to the side"),
  point_up: P({ armR: { shoulder: 150, elbow: -20 } }, "right arm pointing up"),
  shrug: P({ armL: { shoulder: 302, elbow: -58 }, armR: { shoulder: 58, elbow: 58 } }, "both arms shrugging"),
  facepalm: P({ armR: { shoulder: 168, elbow: 34 }, headTurn: -3 }, "right hand to face"),
  present: P({ armR: { shoulder: 56, elbow: 26 }, armL: { shoulder: 20, elbow: 25 } }, "presenting to the side"),
  type: P({ armL: { shoulder: 12, elbow: 22 }, armR: { shoulder: 348, elbow: -22 } }, "typing on keyboard"),
  panic: P({ armL: { shoulder: 322, elbow: -52 }, armR: { shoulder: 38, elbow: 52 }, lean: -4 }, "arms flailing in panic"),
  lean_back: P({ lean: 8, armL: { shoulder: 18, elbow: 22 }, armR: { shoulder: 342, elbow: -22 } }, "leaning back relaxed"),
  hold_paper: P({ prop: "paper", armL: { shoulder: 6, elbow: 66 }, armR: { shoulder: 354, elbow: -66 } }, "holding a paper"),
};

export const EXPR: Record<string, Entry> = {
  deadpan: P({ brows: { l: "flat", r: "flat" }, eyes: "open", mouth: "flat" }, "deadpan"),
  smug: P({ brows: { l: "raise", r: "flat" }, eyes: "open", mouth: "smile" }, "smug"),
  dead_eyed: P({ eyes: "dead", mouth: "flat" }, "dead-eyed"),
  shocked: P({ brows: { l: "raise", r: "raise" }, eyes: "wide", mouth: "o" }, "shocked"),
  annoyed: P({ brows: { l: "furrow", r: "furrow" }, eyes: "open", mouth: "frown" }, "annoyed"),
  crying: P({ brows: { l: "sad", r: "sad" }, eyes: "dead", mouth: "frown", sweat: true }, "crying"),
};
