export type Brow = "flat" | "raise" | "furrow" | "sad";
export type Eyes = "open" | "blink" | "wide" | "dead" | "sideL" | "sideR";
export type Mouth = "flat" | "open" | "frown" | "smile" | "grimace" | "o";
export type Prop = "none" | "fiddle" | "paper" | "phone" | "pointer";

export interface Arm { shoulder: number; elbow: number; wrist: number } // degrees
export interface Skin { skinFill: string; outline: string; shirtFill: string }

export interface RigParams {
  skin: Skin;
  headTurn: number; // deg, +right
  lean: number;     // deg, +right
  bob: number;      // px vertical
  brows: { l: Brow; r: Brow };
  eyes: Eyes;
  mouth: Mouth;
  sweat: boolean;
  armL: Arm;
  armR: Arm;
  prop: Prop;
}

export type DeepPartial<T> = {
  [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K];
};
export type PosePatch = DeepPartial<RigParams>;
export interface Keyframe { frame: number; patch: PosePatch }
