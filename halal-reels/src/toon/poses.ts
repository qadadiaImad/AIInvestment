import { PosePatch } from "./types";

type Entry = { patch: PosePatch; desc: string };
const P = (patch: PosePatch, desc: string): Entry => ({ patch, desc });

export const POSES: Record<string, Entry> = {
  rest: P({ armL: { shoulder: 150, elbow: 40 }, armR: { shoulder: 210, elbow: -40 } }, "hands resting on desk"),
  point_left: P({ armR: { shoulder: 300, elbow: 10, wrist: 0 } }, "right arm pointing left"),
  point_up: P({ armR: { shoulder: 350, elbow: -10 } }, "right arm pointing up"),
  shrug: P({ armL: { shoulder: 120, elbow: -70 }, armR: { shoulder: 240, elbow: 70 } }, "both arms shrugging"),
  facepalm: P({ armR: { shoulder: 15, elbow: 150 }, headTurn: -3 }, "right hand to face"),
  present: P({ armR: { shoulder: 250, elbow: 30 }, armL: { shoulder: 110, elbow: -30 } }, "presenting to the side"),
  type: P({ armL: { shoulder: 165, elbow: 35 }, armR: { shoulder: 195, elbow: -35 } }, "typing on keyboard"),
  panic: P({ armL: { shoulder: 100, elbow: -90 }, armR: { shoulder: 260, elbow: 90 }, lean: -4 }, "arms flailing in panic"),
  lean_back: P({ lean: 8, armR: { shoulder: 210, elbow: -60 } }, "leaning back relaxed"),
  hold_paper: P({ prop: "paper", armR: { shoulder: 235, elbow: 20 } }, "holding a paper"),
};

export const EXPR: Record<string, Entry> = {
  deadpan: P({ brows: { l: "flat", r: "flat" }, eyes: "open", mouth: "flat" }, "deadpan"),
  smug: P({ brows: { l: "raise", r: "flat" }, eyes: "open", mouth: "smile" }, "smug"),
  dead_eyed: P({ eyes: "dead", mouth: "flat" }, "dead-eyed"),
  shocked: P({ brows: { l: "raise", r: "raise" }, eyes: "wide", mouth: "o" }, "shocked"),
  annoyed: P({ brows: { l: "furrow", r: "furrow" }, eyes: "open", mouth: "frown" }, "annoyed"),
  crying: P({ brows: { l: "sad", r: "sad" }, eyes: "dead", mouth: "frown", sweat: true }, "crying"),
};
