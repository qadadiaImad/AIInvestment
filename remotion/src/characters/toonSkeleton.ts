// toonSkeleton.ts — the character's parts table and derived joint positions.
//
// Pure data and arithmetic, no React and no Remotion, so the rig and the
// checking scripts read the SAME numbers instead of each keeping their own copy
// and drifting apart.
//
// All measurements are the output of scripts/meme_reel/extract_limbs.py on
// content/meme_reel/character/*.png — see manifest_*.json in
// remotion/public/meme_reel/char2/.

export type Part = {
  file: string;
  w: number;
  h: number;
  /** Joint position inside the image, normalised 0..1. */
  px: number;
  py: number;
  /** Where this part's CHILD joint sits, normalised down its own height.
   * Deliberately short of 1 so the child's cap overlaps and hides the seam. */
  childY?: number;
  /** Draw scale relative to the sheet. */
  s?: number;
};

export const P: Record<string, Part> = {
  // Measured by extract_limbs.py and GATED by validate_parts.py — the previous
  // sheet failed three proportion checks (hand 98% of the forearm, thigh 62% as
  // wide as the torso) and could not assemble into a body no matter how it was
  // rigged. This one passes all six.
  //
  // The two parts that hang UPWARD from a pivot at their BOTTOM: the head on
  // its neck stub, the torso on its belt.
  //
  // The head comes from the EXPRESSION sheet, not this parts sheet, so it is
  // scaled to match this body's head size (556/631).
  head: {file: 'head_neutral.png', w: 530, h: 631, px: 0.598, py: 0.955, s: 0.88},
  torso: {file: 'torso.png', w: 579, h: 617, px: 0.5, py: 0.90, childY: 0.03},
  upperArm: {file: 'upper_arm.png', w: 215, h: 659, px: 0.5, py: 0.04, childY: 0.95},
  forearm: {file: 'forearm.png', w: 199, h: 538, px: 0.5, py: 0.05, childY: 0.95},
  hand: {file: 'hand.png', w: 195, h: 280, px: 0.5, py: 0.06},
  thigh: {file: 'thigh.png', w: 247, h: 609, px: 0.5, py: 0.04, childY: 0.95},
  shin: {file: 'shin.png', w: 191, h: 536, px: 0.5, py: 0.04, childY: 0.95},
  foot: {file: 'foot.png', w: 281, h: 208, px: 0.38, py: 0.14},
};

/** Ink length from a part's own joint to where its child attaches.
 * Absolute, because the torso's bone runs UPWARD from its joint while every
 * limb runs downward. */
export const boneLen = (p: Part) => Math.abs(((p.childY ?? 1) - p.py) * p.h * (p.s ?? 1));

// ------------------------------------------------------------- the skeleton
export const VB_W = 1700;
export const VB_H = 2900;
export const CX = 850;
export const GROUND = 2620;

export const THIGH_BONE = boneLen(P.thigh);
export const SHIN_BONE = boneLen(P.shin);
/** Full leg extension. The hip is deliberately placed CLOSER than this so the
 * knee is never straight — a fully extended two-link chain is the singular case
 * for IK, where the solution flips and the knee snaps. */
export const LEG_REACH = THIGH_BONE + SHIN_BONE;
export const LEG_REST = LEG_REACH * 0.955;

export const ANKLE_Y = GROUND - (1 - P.foot.py) * P.foot.h * (P.foot.s ?? 1);
export const HIP_Y = ANKLE_Y - LEG_REST;
export const TORSO_TOP_Y = HIP_Y - boneLen(P.torso);
export const NECK_Y = TORSO_TOP_Y + 104;
export const SHOULDER_Y = TORSO_TOP_Y + 96;

export const HIP_DX = 118;
export const SHOULDER_DX = 176;

/**
 * WHERE THE FEET ARE NAILED TO THE FLOOR.
 *
 * These are fixed world positions, not offsets from the hip. The whole point of
 * the rig's second version is that the pelvis moves and the legs solve to reach
 * these — rather than the previous version, which translated the entire figure
 * (legs included) and made the feet skate 13px sideways and hover 16px off the
 * floor across the reel. See scripts/check_foot_plant.mjs.
 *
 * Slightly staggered and tucked inside the hips, which is how a person actually
 * stands; feet directly under the hip joints reads as a mannequin.
 */
export const STANCE: Record<'near' | 'far', {x: number; y: number}> = {
  near: {x: CX + 104, y: ANKLE_Y},
  far: {x: CX - 92, y: ANKLE_Y},
};

/** Top of the character's ink, so a caller can size him in real frame pixels. */
export const INK_TOP = NECK_Y - P.head.py * P.head.h * (P.head.s ?? 1);
export const INK_HEIGHT = GROUND - INK_TOP;
