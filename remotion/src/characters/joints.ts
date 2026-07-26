// joints.ts — anatomical joint limits for the character rigs.
//
// Why this exists: the first rigs had NO limits at all. `elbowR` was authored
// across -88°..+95°, a 183° span that CROSSES ZERO — and an elbow that passes
// through zero inverts, bending the forearm backwards through the joint. On
// screen that reads exactly as "a movement a real arm could not make", which is
// what it was. Wrists had ±30° plus an additive wiggle on top, so they twisted
// past a plausible range too.
//
// A hinge joint (elbow, knee) is the important case: it is ONE-SIDED. Its range
// must sit entirely on one side of zero, so no amount of keyframe authoring or
// IK solving can flip it inside out. Ball joints (shoulder, hip) get a wide but
// finite range; the wrist gets a deliberately small one.
//
// Limits are expressed on the FINAL angle (rest + pose delta), because that is
// the angle the joint actually holds — clamping the delta alone would let a
// non-zero rest angle push the joint out of range anyway.
//
// The cost of clamping is real and accepted: an IK target outside the clamped
// range is no longer reached exactly. A hand that stops a few pixels short of
// the face is a far smaller error than an elbow bending the wrong way.

export type JointName =
  | 'shoulderL' | 'shoulderR'
  | 'elbowL' | 'elbowR'
  | 'handL' | 'handR'
  | 'hipL' | 'hipR'
  | 'kneeL' | 'kneeR'
  | 'leanChest' | 'leanHead';

/** [min, max] on the final angle, degrees, rig convention (positive = clockwise
 * on screen, limb at 0 points straight down from its pivot). */
export const JOINT_LIMITS: Record<JointName, [number, number]> = {
  // Ball joints: wide, but they cannot pass through the torso or hyperextend
  // behind the back past a shrug.
  shoulderL: [-175, 40],
  shoulderR: [-175, 40],

  // HINGES. Entirely on one side of zero so they can never invert.
  // The two arms mirror, so their ranges mirror too.
  elbowL: [0, 135],
  elbowR: [-135, 0],

  // Wrists are the joint that most obviously reads as "wrong" when overdriven,
  // and the joint with the least real range. Kept tight.
  handL: [-32, 32],
  handR: [-32, 32],

  hipL: [-55, 70],
  hipR: [-70, 55],

  // Knees bend one way only — backwards from the direction of travel.
  kneeL: [-95, 0],
  kneeR: [-95, 0],

  // Spine: a lean, not a fold in half.
  leanChest: [-25, 45],
  leanHead: [-38, 38],
};

/** Wrap to (-180, 180]. The IK solver returns angles in whatever revolution the
 * trigonometry lands in — a legal facepalm came back as +247°, which is the same
 * pose as -113° but reads as wildly out of range to a naive comparison. Clamping
 * before wrapping pinned the arm at its limit and broke the pose; the angle must
 * be normalised FIRST. */
export const wrapDeg = (deg: number): number => {
  let d = (((deg + 180) % 360) + 360) % 360 - 180;
  if (d === -180) d = 180;
  return d;
};

/** Clamp one final joint angle to its anatomical range, normalising first. */
export const clampJoint = (joint: JointName, finalDeg: number): number => {
  const [lo, hi] = JOINT_LIMITS[joint];
  const d = wrapDeg(finalDeg);
  return d < lo ? lo : d > hi ? hi : d;
};

/** True if the angle was outside its range — used by the joint-limit check to
 * report which beats were driving joints past what a body can do. */
export const violates = (joint: JointName, finalDeg: number): boolean => {
  const [lo, hi] = JOINT_LIMITS[joint];
  const d = wrapDeg(finalDeg);
  return d < lo - 1e-9 || d > hi + 1e-9;
};
