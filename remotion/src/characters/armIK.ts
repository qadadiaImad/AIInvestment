// armIK.ts — two-link inverse kinematics for the rubber-hose arm.
//
// Why this exists: the beats that read as "the hand lands ON something" (the
// glove covering the eyes in the facepalm, the palm planting on the desk) were
// first authored as hand-guessed shoulder/elbow angles, and the contact sheet
// showed exactly what that produces — a facepalm that punches its own nose.
// Guessing FK angles for a contact pose is unreliable; solving for them is not.
//
// Pure maths, no React or Remotion imports, so it can be run and asserted under
// plain node (scripts/check_arm_ik.mjs). "The hand reaches the target" is a
// checkable numeric claim and is checked.
//
// RIG CONVENTION (must match rubberHoseRig.tsx):
//   * SVG space, +y DOWN, angles in degrees, POSITIVE = CLOCKWISE ON SCREEN.
//   * A limb at angle 0 points DOWN (+y) from its pivot. Rotating a vector
//     (0, L) by t gives (-L*sin t, L*cos t) — so a limb at angle t points along
//     the unit vector (-sin t, cos t). At t=0 that is (0,1) = down; at t=90 it
//     is (-1,0) = screen-left, which is clockwise from down in a y-down space.

export type Vec = {x: number; y: number};

const DEG = 180 / Math.PI;
const RAD = Math.PI / 180;

/** Unit direction a limb points when rotated `deg` from its rest-down pose. */
export const limbDir = (deg: number): Vec => {
  const t = deg * RAD;
  return {x: -Math.sin(t), y: Math.cos(t)};
};

/**
 * Forward kinematics: where the wrist ends up for a given shoulder/elbow pair.
 * The elbow angle is RELATIVE to the upper arm, matching the nested <g> rig,
 * so the forearm's absolute angle is shoulder + elbow.
 */
export const armFK = (
  shoulder: Vec,
  shoulderDeg: number,
  elbowDeg: number,
  upperLen: number,
  foreLen: number,
): {elbow: Vec; wrist: Vec} => {
  const u = limbDir(shoulderDeg);
  const elbow = {x: shoulder.x + u.x * upperLen, y: shoulder.y + u.y * upperLen};
  const f = limbDir(shoulderDeg + elbowDeg);
  const wrist = {x: elbow.x + f.x * foreLen, y: elbow.y + f.y * foreLen};
  return {elbow, wrist};
};

/**
 * Inverse kinematics: the shoulder and elbow angles that put the wrist on
 * `target`. `bend` picks which of the two mirror solutions to take (+1 / -1),
 * i.e. which way the elbow points — for a rubber-hose figure both are valid
 * poses and the choice is purely which one doesn't push the elbow through the
 * torso.
 *
 * An out-of-reach target is CLAMPED to the arm's reachable annulus rather than
 * returning NaN: the arm extends as far as it can toward the target, which is
 * what a cartoon arm does and what any caller actually wants. `reached` reports
 * whether the target was literally attainable, so a caller (or a test) can tell
 * the difference between "landed on it" and "stretched at it".
 */
export const armIK = (
  shoulder: Vec,
  target: Vec,
  upperLen: number,
  foreLen: number,
  bend: 1 | -1 = 1,
): {shoulderDeg: number; elbowDeg: number; reached: boolean} => {
  const dx = target.x - shoulder.x;
  const dy = target.y - shoulder.y;
  const dRaw = Math.hypot(dx, dy);

  const dMax = upperLen + foreLen;
  const dMin = Math.abs(upperLen - foreLen);
  // Stay just inside the singular limits: exactly at full extension the
  // acos arguments hit +-1 and the elbow angle degenerates.
  const EPS = 1e-3;
  const d = Math.max(dMin + EPS, Math.min(dMax - EPS, dRaw));
  const reached = dRaw >= dMin - EPS && dRaw <= dMax + EPS;

  // Angle of the straight-line shoulder->target direction, in rig convention.
  const psi = Math.atan2(-dx, dy) * DEG;

  // Law of cosines on the triangle (shoulder, elbow, wrist).
  const cosA1 = (upperLen * upperLen + d * d - foreLen * foreLen) / (2 * upperLen * d);
  const cosA2 = (upperLen * upperLen + foreLen * foreLen - d * d) / (2 * upperLen * foreLen);
  const a1 = Math.acos(Math.max(-1, Math.min(1, cosA1))) * DEG;
  const a2 = Math.acos(Math.max(-1, Math.min(1, cosA2))) * DEG;

  return {
    shoulderDeg: psi + bend * a1,
    elbowDeg: -bend * (180 - a2),
    reached,
  };
};

/** Wrap an angle to (-180, 180] so blends between a solved pose and an
 * authored one take the short way round instead of spinning the arm. */
export const wrapDeg = (deg: number): number => {
  let d = ((deg + 180) % 360 + 360) % 360 - 180;
  if (d === -180) d = 180;
  return d;
};

/** Shortest-path blend between two angles. `t` 0..1. */
export const blendDeg = (a: number, b: number, t: number): number => a + wrapDeg(b - a) * t;
