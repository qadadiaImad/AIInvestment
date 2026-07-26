// rubberHoseRig.tsx — a limbed rubber-hose cartoon humanoid, built as a pure
// SVG pivot rig: nested <g transform="rotate(a px py)"> groups, exactly the
// technique chipRig.tsx established (chipRig.tsx:171, :179).
//
// Why vector and not generated art: references/meme-reel-pipeline.md §3 calls
// for the character to be generated as separate transparent-background limb
// PNGs. Rubber-hose is the one style where that trade goes the other way —
// thick constant-width outlines, noodle limbs and flat fills ARE vector
// primitives, so drawing them directly removes the two failure modes the brief
// itself warns about (limbs detaching at the joints, style drifting between
// separately-generated layers) instead of merely managing them. The existing
// six rigs prove the pattern; this is the first one with arms and legs.
//
// COORDINATE CONVENTION (stated once, obeyed everywhere):
//   * Character-local SVG space, viewBox 0 0 420 440. +y is DOWN.
//   * GROUND (y=400) is the contact point between the feet; CX (x=210) is the
//     character's centre line.
//   * Angles are degrees passed straight to SVG rotate(), so POSITIVE IS
//     CLOCKWISE ON SCREEN.
//   * The rig is drawn FACING RIGHT. "Forward" (toward whatever he is looking
//     at) is therefore +x, and a positive `leanChest` leans him forward. To
//     put the monitor on his left, pass facing="left" — that mirrors the whole
//     SVG, so every pose number below stays in one intuitive frame instead of
//     flipping sign halfway through the file.
//   * Spine segments are drawn extending UP (-y) from their pivot; limb
//     segments extend DOWN (+y) from theirs, matching chipRig's Arm/Leg. Feet
//     are the exception — a foot runs along +x from the ankle, not +y.
//
// POSING IS FK-ONLY. Every limb piece, including the terminal glove and shoe,
// is drawn inside its parent joint's rotate() group at that joint's rest
// coordinates. Nothing is ever independently translated into place. That is
// the single mechanism guaranteeing a limb cannot detach or drift, and it is
// why the visual check for detached joints is cheap: if the maths were wrong
// the limb would be wrong in every frame, not intermittently.
import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {EASE, wiggle} from '../motion/craft';
import {armIK, blendDeg} from './armIK';

// ------------------------------------------------------------------ palette
const INK = '#17130F'; // one outline weight/colour system for the whole figure
const BODY = '#F3EEE4'; // off-white, never pure #FFF — it has to hold a silhouette
const GLOVE = '#FCF9F2';
const SHOE = '#1D1815';
const SHOE_SOLE = '#4A423A';
const SHORTS = '#1D1815';

const STROKE = 14; // constant limb width — never tapers with rotation
const OUTLINE = 7; // body/head outline weight

// --------------------------------------------------------------- skeleton
// Bottom-up, from GROUND. These are the spec's lengths, laid out once so the
// joints below are derived rather than hand-typed twice.
const GROUND = 400;
const CX = 210;

const PELVIS = {x: CX, y: GROUND - 164};
const CHEST = {x: CX, y: PELVIS.y - 66};
const NECK = {x: CX, y: CHEST.y - 54};
const HEAD_PIVOT = {x: CX, y: NECK.y - 12};

const SHOULDER_DX = 34;
const SHOULDER_DY = -46;
const UPPER_ARM = 60;
const FOREARM = 54;

const HIP_DX = 26;
const THIGH = 84;
const SHIN = 80;

const shoulder = (side: 1 | -1) => ({x: CHEST.x + SHOULDER_DX * side, y: CHEST.y + SHOULDER_DY});
const hip = (side: 1 | -1) => ({x: PELVIS.x + HIP_DX * side, y: PELVIS.y});

// ------------------------------------------------------------------- pose
export type Pose = {
  bob: number; // whole-rig vertical offset (breathing, jolts)
  weightShift: number; // lateral hip translate counterbalancing a lean
  leanChest: number; // deg, + = forward (toward what he's watching)
  leanHead: number; // deg, layered on top of leanChest
  gazeX: number; // pupil offset, independent of head rotation
  gazeY: number;
  blink: number; // eyelid scale-y, 1 = open
  eyeBulge: number; // bug-eye pop multiplier, 1 = neutral
  squash: number; // about the ground contact, 1 = neutral
  slouch: number; // 0..1 spine-collapse blend
  shoulderL: number; // all limb fields are deltas from the joint's rest angle
  shoulderR: number;
  elbowL: number;
  elbowR: number;
  handL: number;
  handR: number;
  hipL: number;
  hipR: number;
  kneeL: number;
  kneeR: number;
  footL: number;
  footR: number;
};

/** Rest angles, so a Pose of all zeros is a plausible standing figure. */
const REST = {
  shoulderL: 4,
  shoulderR: -4,
  elbowL: 14,
  elbowR: -14,
  handL: -6,
  handR: 6,
  hipL: 0,
  hipR: 0,
  kneeL: -6,
  kneeR: -6,
  footL: 0,
  footR: 0,
};

/** Rotate a point about a pivot by `deg`, in the rig's clockwise-positive
 * y-down convention — used to make an IK target ride a rotating parent. */
const rotateAbout = (p: {x: number; y: number}, pivot: {x: number; y: number}, deg: number) => {
  const t = (deg * Math.PI) / 180;
  const c = Math.cos(t);
  const s = Math.sin(t);
  const dx = p.x - pivot.x;
  const dy = p.y - pivot.y;
  return {x: pivot.x + dx * c - dy * s, y: pivot.y + dx * s + dy * c};
};

type Key = {f: number; v: number; ease?: (t: number) => number};

/**
 * Piecewise keyframe track. Anticipation and follow-through are expressed as
 * real keyframes — a value that moves the OPPOSITE way before the action, and
 * one that overshoots the target before settling back — rather than as a
 * post-hoc modifier. That keeps every beat's craft legible in the data: if a
 * track goes straight from rest to target with no counter-move and no
 * overshoot, the animation is wrong and you can see it by reading it.
 */
const track = (frame: number, keys: Key[]): number => {
  if (frame <= keys[0].f) return keys[0].v;
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i];
    const b = keys[i + 1];
    if (frame <= b.f) {
      return interpolate(frame, [a.f, b.f], [a.v, b.v], {
        easing: b.ease ?? EASE.enter,
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
    }
  }
  return keys[keys.length - 1].v;
};

// -------------------------------------------------------------- the beats
// 510 frames @ 30fps = 17s. The story is: idle -> notices -> leans in ->
// the pattern fails -> facepalm/slump -> shrug at camera.
//
// He is reacting to a PATTERN, never to a payout. See the brief §5: no beat
// here is keyed to a profit, and nothing in this rig knows what money is.
export const RUBBER_HOSE_BEATS = {
  idle: 0,
  notices: 70,
  leansIn: 130,
  fails: 230,
  facepalm: 300,
  shrug: 390,
  end: 510,
};

export const computeRubberHosePose = (frame: number): Pose => {
  // Breathing never stops, even under a held key pose — a frozen figure reads
  // as a still image with a chart pasted next to it.
  const breath = wiggle(frame, 0, 3.2, 0.85);
  const armDrift = wiggle(frame, 1, 4.5, 0.8);
  const legDrift = wiggle(frame, 2, 1.8, 0.6);
  const handIdle = wiggle(frame, 3, 6, 1.15);

  const leanChest = track(frame, [
    {f: 0, v: -1}, // settle-in counter-dip so frame 0 isn't a hard cut into a held pose
    {f: 6, v: 2, ease: EASE.settleBack},
    {f: 70, v: 2},
    {f: 100, v: 6, ease: EASE.settleBack}, // notices: torso follows the head turn
    {f: 130, v: 6},
    {f: 135, v: -4, ease: EASE.exit}, // ANTIC: rocks back before diving in
    // 26 deg, not the spec's 32: the torso lean and the head turn compound,
    // and at 32+26 the contact sheet showed him bent double with his head at
    // hip height. He is peering at a screen, not touching his toes.
    {f: 200, v: 26, ease: EASE.enter}, // lean-in, overshooting the 23 target
    {f: 214, v: 23, ease: EASE.settleBack}, // FOLLOW: damps back
    {f: 230, v: 23},
    {f: 233, v: 25, ease: EASE.exit}, // ANTIC: loads 2deg further forward
    {f: 248, v: -14, ease: EASE.exit}, // recoil, past the -10 target
    {f: 268, v: -6, ease: EASE.settleBack},
    {f: 300, v: -2},
    {f: 336, v: 14, ease: EASE.enter}, // facepalm droop
    {f: 372, v: 16, ease: EASE.cruise}, // FOLLOW: keeps sinking after contact
    {f: 390, v: 16},
    {f: 430, v: -6, ease: EASE.settleBack}, // straightens into the shrug
    {f: 510, v: -4},
  ]);

  const leanHead = track(frame, [
    {f: 0, v: 0},
    {f: 70, v: 0},
    {f: 76, v: -6, ease: EASE.exit}, // ANTIC: flicks AWAY first — the double-take
    {f: 94, v: 20, ease: EASE.enter}, // snaps to the screen, past the 18 target
    {f: 108, v: 18, ease: EASE.settleBack},
    {f: 130, v: 18},
    {f: 205, v: 14, ease: EASE.enter}, // peering in, on top of the torso lean
    {f: 230, v: 14},
    {f: 248, v: -18, ease: EASE.exit}, // head snaps back with the flinch
    {f: 272, v: -8, ease: EASE.settleBack},
    {f: 336, v: -22, ease: EASE.enter}, // chin drops into the hand
    {f: 390, v: -20},
    {f: 430, v: 4, ease: EASE.settleBack}, // quizzical tilt to camera
    {f: 510, v: 4},
  ]);

  const eyeBulge = track(frame, [
    {f: 0, v: 1},
    {f: 76, v: 1},
    {f: 92, v: 1.42, ease: EASE.enter}, // FOLLOW: overshoots 1.35...
    {f: 104, v: 1.35, ease: EASE.settleBack}, // ...then settles
    {f: 230, v: 1.3},
    {f: 246, v: 1.5, ease: EASE.exit}, // max at the failure
    {f: 262, v: 1.34, ease: EASE.settleBack},
    {f: 300, v: 1.28},
    {f: 336, v: 1, ease: EASE.enter}, // hidden behind the glove anyway
    {f: 430, v: 1.12, ease: EASE.settleBack},
    {f: 510, v: 1.12},
  ]);

  // Blink runs on its own cycle, suppressed through the two takes — you do not
  // blink during a double-take or a flinch.
  const blinkT = frame % 118;
  const rawBlink = blinkT < 4 ? 0.12 : blinkT < 9 ? 1 - Math.abs(7 - blinkT) * 0.2 : 1;
  const noBlink = (frame > 76 && frame < 130) || (frame > 230 && frame < 268);
  const blink = noBlink ? 1 : rawBlink;

  const squash = track(frame, [
    {f: 0, v: 1},
    {f: 130, v: 1},
    {f: 210, v: 0.94, ease: EASE.enter}, // weight settles forward
    {f: 230, v: 0.94},
    {f: 233, v: 0.9, ease: EASE.exit}, // ANTIC: loads down before the jolt
    {f: 248, v: 1.15, ease: EASE.exit}, // stretch on the jolt
    {f: 268, v: 1.0, ease: EASE.settleBack},
    {f: 336, v: 1.06, ease: EASE.enter},
    {f: 372, v: 1.08, ease: EASE.cruise}, // sag keeps deepening after the hand lands
    {f: 390, v: 1.08},
    {f: 430, v: 1.02, ease: EASE.settleBack},
    {f: 510, v: 1.02},
  ]);

  const slouch = track(frame, [
    {f: 0, v: 0},
    {f: 300, v: 0},
    {f: 336, v: 0.85, ease: EASE.enter},
    {f: 372, v: 1, ease: EASE.cruise},
    {f: 390, v: 1},
    {f: 430, v: 0.15, ease: EASE.settleBack},
    {f: 510, v: 0.15},
  ]);

  const bob = track(frame, [
    {f: 0, v: 0},
    {f: 230, v: 0},
    {f: 248, v: -10, ease: EASE.exit}, // jolt lift
    {f: 266, v: 0, ease: EASE.settleBack},
    {f: 336, v: 6, ease: EASE.enter}, // sinks into the slump
    {f: 390, v: 6},
    {f: 430, v: 0, ease: EASE.settleBack},
    {f: 510, v: 0},
  ]) + breath * (1 - slouch * 0.4);

  const weightShift = track(frame, [
    {f: 0, v: 0},
    {f: 130, v: 0},
    {f: 135, v: 6, ease: EASE.exit}, // ANTIC: hips go the other way first
    {f: 210, v: -14, ease: EASE.enter}, // counter-shift for the S-curve balance
    {f: 248, v: 4, ease: EASE.exit},
    {f: 300, v: 0, ease: EASE.settleBack},
    {f: 510, v: 0},
  ]);

  // ------------------------------------------------------------- the arms
  // Right arm is the acting arm: plants on the desk, flies up, facepalms.
  const shoulderR = track(frame, [
    {f: 0, v: 0},
    {f: 70, v: 0},
    {f: 100, v: 10, ease: EASE.settleBack}, // half-lifts on the notice
    {f: 130, v: 8},
    {f: 205, v: -70, ease: EASE.enter}, // reaches down to plant on the desk
    {f: 230, v: -70},
    {f: 236, v: -52, ease: EASE.exit}, // ANTIC: loads down before flying up
    {f: 250, v: -138, ease: EASE.exit}, // thrown up, past the -130 target
    {f: 268, v: -126, ease: EASE.settleBack},
    {f: 304, v: -170, ease: EASE.enter}, // ANTIC: lifts up/back before the drag
    {f: 340, v: -160, ease: EASE.enter}, // glove lands on the face
    {f: 390, v: -158},
    // The shrug is palms OUT at waist height with the shoulders up, not hands
    // at the ears — the previous -150 put both gloves on top of his head and
    // read as clutching his skull. The upper arm stays low; the FOREARM does
    // the turning out, which is what a shrug actually is.
    {f: 394, v: -8, ease: EASE.exit}, // ANTIC: arm drops all the way down first
    {f: 424, v: -34, ease: EASE.exit}, // pops out past the -24 target
    {f: 438, v: -24, ease: EASE.settleBack},
    {f: 510, v: -24},
  ]);

  const elbowR = track(frame, [
    {f: 0, v: 0},
    {f: 205, v: 40, ease: EASE.enter},
    {f: 230, v: 40},
    {f: 252, v: -34, ease: EASE.exit},
    {f: 272, v: -22, ease: EASE.settleBack},
    {f: 344, v: 95, ease: EASE.enter}, // folds so the glove reaches the face
    {f: 390, v: 95},
    {f: 404, v: 0, ease: EASE.exit},
    {f: 426, v: -88, ease: EASE.exit}, // forearm turns out, palm up
    {f: 440, v: -78, ease: EASE.settleBack},
    {f: 510, v: -78},
  ]);

  // ------------------------------------------------- contact poses via IK
  // Two beats are defined by the hand LANDING on something rather than by an
  // arm shape: the glove covering the eyes, and the palm planting on the desk.
  // Hand-authored angles got both wrong (the first contact sheet had him
  // punching his own nose), so these are solved, not guessed. See armIK.ts.
  const facePt = rotateAbout(
    {x: CX + 28, y: HEAD_PIVOT.y - 32}, // between the eyes, a touch low
    HEAD_PIVOT,
    leanHead // the target rides the head, so the glove tracks the face
  );
  // bend +1 sends the elbow up and BACK; bend -1 swings it across the face.
  const faceIK = armIK(shoulder(1), facePt, UPPER_ARM, FOREARM, 1);
  const plantIK = armIK(shoulder(1), {x: CX + 90, y: PELVIS.y - 26}, UPPER_ARM, FOREARM, 1);

  const facepalmW = track(frame, [
    {f: 0, v: 0},
    {f: 308, v: 0},
    {f: 344, v: 1, ease: EASE.enter},
    {f: 388, v: 1},
    {f: 402, v: 0, ease: EASE.exit},
    {f: 510, v: 0},
  ]);
  const plantW = track(frame, [
    {f: 0, v: 0},
    {f: 186, v: 0},
    {f: 208, v: 1, ease: EASE.enter},
    {f: 232, v: 1},
    {f: 240, v: 0, ease: EASE.exit},
    {f: 510, v: 0},
  ]);

  const shoulderRPosed = blendDeg(
    blendDeg(REST.shoulderR + shoulderR, plantIK.shoulderDeg, plantW),
    faceIK.shoulderDeg,
    facepalmW
  ) - REST.shoulderR;
  const elbowRPosed = blendDeg(
    blendDeg(REST.elbowR + elbowR, plantIK.elbowDeg, plantW),
    faceIK.elbowDeg,
    facepalmW
  ) - REST.elbowR;

  // Left arm is the follower: it lags the right and never leads a beat, which
  // is what stops the figure reading as a symmetrical robot.
  const shoulderL = track(frame, [
    {f: 0, v: 0},
    {f: 130, v: 0},
    {f: 212, v: -18, ease: EASE.enter},
    {f: 230, v: -18},
    {f: 239, v: -6, ease: EASE.exit},
    // The far arm flings lower than the near one, so the two gloves do not
    // stack on top of the head and the silhouette stays readable.
    {f: 253, v: -104, ease: EASE.exit},
    {f: 272, v: -92, ease: EASE.settleBack},
    {f: 340, v: -34, ease: EASE.enter}, // hangs limp through the slump
    {f: 390, v: -30},
    {f: 396, v: 6, ease: EASE.exit},
    // Mirrors the near arm outward: this side's forearm turns toward -x.
    // Offset ~3 frames behind the right shoulder (stagger, 'micro') so the two
    // arms do not pop in robotic unison.
    {f: 427, v: 34, ease: EASE.exit},
    {f: 441, v: 24, ease: EASE.settleBack},
    {f: 510, v: 24},
  ]);

  const elbowL = track(frame, [
    {f: 0, v: 0},
    {f: 230, v: 0},
    {f: 255, v: 30, ease: EASE.exit},
    {f: 275, v: 18, ease: EASE.settleBack},
    {f: 340, v: 8, ease: EASE.enter},
    {f: 390, v: 8},
    {f: 406, v: 0, ease: EASE.exit},
    {f: 429, v: 88, ease: EASE.exit},
    {f: 443, v: 78, ease: EASE.settleBack},
    {f: 510, v: 78},
  ]);

  // Hands are the loosest joints: they lag their shoulder and keep waggling
  // through every hold, so no pose is ever dead-frozen.
  const handR = track(frame, [
    {f: 0, v: 0},
    {f: 205, v: 30, ease: EASE.enter}, // flattens onto the desk
    {f: 230, v: 30},
    {f: 256, v: -26, ease: EASE.exit},
    {f: 344, v: 10, ease: EASE.enter},
    {f: 390, v: 10},
    {f: 434, v: 30, ease: EASE.settleBack}, // palm turns up
    {f: 510, v: 30},
  ]) + handIdle * 0.5;

  const handL = track(frame, [
    {f: 0, v: 0},
    {f: 230, v: 0},
    {f: 259, v: 24, ease: EASE.exit},
    {f: 340, v: -8, ease: EASE.enter},
    {f: 390, v: -8},
    {f: 437, v: -30, ease: EASE.settleBack},
    {f: 510, v: -30},
  ]) + handIdle * 0.4;

  // -------------------------------------------------------------- the legs
  const hipR = track(frame, [
    {f: 0, v: 0},
    {f: 135, v: 2, ease: EASE.exit},
    {f: 212, v: -10, ease: EASE.enter}, // front leg takes the weight
    {f: 248, v: 4, ease: EASE.exit},
    {f: 300, v: -2, ease: EASE.settleBack},
    {f: 430, v: 0, ease: EASE.settleBack},
    {f: 510, v: 0},
  ]);

  const kneeR = track(frame, [
    {f: 0, v: 0},
    {f: 216, v: 18, ease: EASE.enter},
    {f: 252, v: 4, ease: EASE.exit},
    {f: 300, v: 6, ease: EASE.settleBack},
    {f: 430, v: 2, ease: EASE.settleBack},
    {f: 510, v: 2},
  ]);

  // The trailing leg lags the pelvis and keeps swinging a few frames after it
  // stops — the follow-through the spec asks for, done as offset keyframes.
  const hipL = track(frame, [
    {f: 0, v: 0},
    {f: 140, v: -2, ease: EASE.exit},
    {f: 220, v: 6, ease: EASE.enter},
    {f: 256, v: -3, ease: EASE.exit},
    {f: 306, v: 2, ease: EASE.settleBack},
    {f: 434, v: 0, ease: EASE.settleBack},
    {f: 510, v: 0},
  ]);

  const kneeL = track(frame, [
    {f: 0, v: 0},
    {f: 224, v: -8, ease: EASE.enter},
    {f: 260, v: -2, ease: EASE.exit},
    {f: 310, v: -4, ease: EASE.settleBack},
    {f: 510, v: -2},
  ]);

  return {
    bob,
    weightShift,
    leanChest,
    leanHead,
    gazeX: track(frame, [
      {f: 0, v: 0},
      {f: 70, v: 0},
      {f: 76, v: -4, ease: EASE.exit},
      {f: 96, v: 10, ease: EASE.enter},
      {f: 230, v: 11},
      {f: 250, v: 6, ease: EASE.exit},
      {f: 336, v: 0, ease: EASE.enter},
      {f: 430, v: 0},
      {f: 510, v: 0},
    ]),
    gazeY: track(frame, [
      {f: 0, v: 2},
      {f: 96, v: 0},
      {f: 430, v: -2, ease: EASE.settleBack},
      {f: 510, v: -2},
    ]),
    blink,
    eyeBulge,
    squash,
    slouch,
    // Arms sway on their own seed and are damped once they are doing something
    // deliberate (planted, flung up, covering the face) — an idle sway riding
    // on top of a committed gesture reads as a wobble, not as life.
    shoulderL: shoulderL + armDrift * 0.5 * (1 - Math.min(1, Math.abs(shoulderL) / 90)),
    shoulderR: shoulderRPosed + armDrift * 0.6 * (1 - Math.max(facepalmW, plantW)) * (1 - Math.min(1, Math.abs(shoulderR) / 90)),
    elbowL,
    elbowR: elbowRPosed,
    handL,
    handR,
    hipL,
    hipR,
    kneeL: kneeL + legDrift * 0.3,
    kneeR: kneeR + legDrift * 0.25,
    footL: 0,
    footR: 0,
  };
};

// ------------------------------------------------------------------ pieces
/** A noodle limb segment: ONE continuous stroked path from the joint to its
 * child, bowed by a perpendicular control point so the bend reads as a smooth
 * arc. Never two straight segments meeting at a corner — that crease is the
 * thing that stops a figure being rubber-hose. */
const Hose: React.FC<{x: number; y: number; len: number; bow: number}> = ({x, y, len, bow}) => (
  <path
    d={`M${x},${y} Q${x + bow},${y + len * 0.5} ${x},${y + len}`}
    fill="none"
    stroke={INK}
    strokeWidth={STROKE}
    strokeLinecap="round"
  />
);

/** Four-fingered glove. Drawn at its wrist point inside the parent's rotate
 * group, so it can never separate from the arm. `open` splays it for the
 * palms-up shrug; `flat` presses it for the hand-on-desk plant. */
const Glove: React.FC<{x: number; y: number; variant?: 'fist' | 'open' | 'flat'}> = ({
  x,
  y,
  variant = 'fist',
}) => (
  <g transform={`translate(${x} ${y})`}>
    {variant === 'flat' ? (
      // Palm pressed onto a surface, seen from the side. Wider and with a
      // thumb, because the first pass drew a small rounded rect that read as a
      // detached white pill floating at the end of the arm.
      <>
        <path
          d="M-22,-4 Q-28,10 -16,17 L16,19 Q29,18 29,7 Q29,-3 17,-6 L-6,-11 Q-20,-13 -22,-4 Z"
          fill={GLOVE}
          stroke={INK}
          strokeWidth={OUTLINE}
          strokeLinejoin="round"
        />
        <path d="M2,-6 L1,16 M14,-3 L14,18" stroke={INK} strokeWidth={2.6} strokeLinecap="round" fill="none" opacity={0.55} />
        <ellipse cx={-19} cy={5} rx={8} ry={9} fill={GLOVE} stroke={INK} strokeWidth={OUTLINE - 2} />
      </>
    ) : variant === 'open' ? (
      // Palm-up, fingers splayed. Drawn as ONE silhouette with the fingers
      // growing out of the palm — an earlier version drew them as separate
      // circles floating above the hand, which read as soap bubbles rather
      // than as a hand. Terminal shapes never float free of what they belong
      // to, the same rule the limbs obey.
      <>
        <path
          d={`M-24,4
              Q-27,-10 -19,-14 Q-13,-17 -10,-9 L-7,-1
              L-6,-13 Q-5,-24 2,-24 Q9,-24 9,-13 L9,-2
              L12,-12 Q15,-21 21,-18 Q27,-15 24,-5 L21,4
              Q22,20 8,26 Q-6,30 -16,22 Q-24,15 -24,4 Z`}
          fill={GLOVE}
          stroke={INK}
          strokeWidth={OUTLINE}
          strokeLinejoin="round"
        />
        {/* thumb, on the near side */}
        <ellipse cx={-24} cy={12} rx={8} ry={10} fill={GLOVE} stroke={INK} strokeWidth={OUTLINE - 2} />
      </>
    ) : (
      <>
        <circle cx={0} cy={6} r={19} fill={GLOVE} stroke={INK} strokeWidth={OUTLINE} />
        {/* the three knuckle darts that make a mitt read as a glove */}
        <path d="M-9,-2 L-9,10 M0,-4 L0,12 M9,-2 L9,10" stroke={INK} strokeWidth={3} strokeLinecap="round" fill="none" opacity={0.65} />
        <ellipse cx={-17} cy={2} rx={7} ry={9} fill={GLOVE} stroke={INK} strokeWidth={OUTLINE - 2} />
      </>
    )}
  </g>
);

/** Big cartoon shoe. Runs along +x from the ankle, not +y — a foot is not a
 * hanging limb, and reusing the generic limb draw direction here is the single
 * mistake that makes a rubber-hose figure look like it is standing on stilts. */
const Shoe: React.FC<{x: number; y: number; flip?: boolean}> = ({x, y, flip = false}) => (
  <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
    <path
      d="M-16,-14 Q-18,4 -10,10 L28,10 Q42,9 41,-1 Q40,-11 26,-14 L6,-19 Q-14,-22 -16,-14 Z"
      fill={SHOE}
      stroke={INK}
      strokeWidth={OUTLINE}
      strokeLinejoin="round"
    />
    <path d="M-11,6 L40,6 Q42,10 30,10 L-9,10 Q-14,9 -11,6 Z" fill={SHOE_SOLE} />
  </g>
);

/** Bug eye: oversized white ellipse with a pupil that offsets for gaze
 * independently of head rotation, and is never clipped by the head outline. */
const Eye: React.FC<{cx: number; cy: number; r: number; blink: number; gx: number; gy: number}> = ({
  cx,
  cy,
  r,
  blink,
  gx,
  gy,
}) => (
  <g transform={`translate(${cx} ${cy}) scale(1 ${blink})`}>
    <ellipse cx={0} cy={0} rx={r} ry={r * 1.16} fill="#FFFDF8" stroke={INK} strokeWidth={5} />
    <circle cx={gx * 0.5} cy={gy * 0.5 + 1} r={r * 0.42} fill={INK} />
    <circle cx={gx * 0.5 + r * 0.14} cy={gy * 0.5 - r * 0.2} r={r * 0.13} fill="#FFFDF8" opacity={0.92} />
  </g>
);

// -------------------------------------------------------------------- rig
export type RubberHoseRigProps = {
  /** Rendered width in px; the viewBox is 420x440 so height = size * 440/420. */
  size?: number;
  /** Mirrors the whole figure. The rig is authored facing RIGHT; pass 'left'
   * when the thing he is watching is to his left. */
  facing?: 'left' | 'right';
  /** Drive the rig from an external clock instead of the timeline. */
  frameOverride?: number;
  /** Supply a pose directly, bypassing the beat timeline (used by the rig
   * contact-sheet check to render arbitrary poses). */
  poseOverride?: Partial<Pose>;
  /** Contact shadow under the feet. Off when the character stands on a plate
   * that already has its own baked shadow. */
  shadow?: boolean;
};

export const RubberHoseRig: React.FC<RubberHoseRigProps> = ({
  size = 420,
  facing = 'right',
  frameOverride,
  poseOverride,
  shadow = true,
}) => {
  const current = useCurrentFrame();
  const frame = frameOverride ?? current;
  const p = {...computeRubberHosePose(frame), ...poseOverride};

  // Slouch collapses the spine: the chest sinks and the shoulders drop. It is
  // applied as a translate on the chest group rather than as more rotation,
  // because rotating further just tips him over.
  const spineDrop = p.slouch * 14;

  const armGroup = (side: 1 | -1) => {
    const s = shoulder(side);
    const isRight = side === 1;
    const shoulderA = (isRight ? REST.shoulderR + p.shoulderR : REST.shoulderL + p.shoulderL);
    const elbowA = (isRight ? REST.elbowR + p.elbowR : REST.elbowL + p.elbowL);
    const handA = (isRight ? REST.handR + p.handR : REST.handL + p.handL);
    const elbowPt = {x: s.x, y: s.y + UPPER_ARM};
    const wristPt = {x: s.x, y: s.y + UPPER_ARM + FOREARM};
    // Glove variant is a function of the beat, so the hand reads as doing the
    // thing the pose is doing rather than being a generic mitt throughout.
    const variant: 'fist' | 'open' | 'flat' =
      frame >= 390 ? 'open' : frame >= 190 && frame < 232 && isRight ? 'flat' : 'fist';
    return (
      <g transform={`rotate(${shoulderA} ${s.x} ${s.y})`}>
        <Hose x={s.x} y={s.y} len={UPPER_ARM} bow={side * 9} />
        <g transform={`rotate(${elbowA} ${elbowPt.x} ${elbowPt.y})`}>
          <Hose x={elbowPt.x} y={elbowPt.y} len={FOREARM} bow={side * 7} />
          <g transform={`rotate(${handA} ${wristPt.x} ${wristPt.y})`}>
            <Glove x={wristPt.x} y={wristPt.y} variant={variant} />
          </g>
        </g>
      </g>
    );
  };

  const legGroup = (side: 1 | -1) => {
    const h = hip(side);
    const isRight = side === 1;
    const hipA = (isRight ? REST.hipR + p.hipR : REST.hipL + p.hipL);
    const kneeA = (isRight ? REST.kneeR + p.kneeR : REST.kneeL + p.kneeL);
    const kneePt = {x: h.x, y: h.y + THIGH};
    const anklePt = {x: h.x, y: h.y + THIGH + SHIN};
    return (
      <g transform={`rotate(${hipA} ${h.x} ${h.y})`}>
        <Hose x={h.x} y={h.y} len={THIGH} bow={side * 7} />
        <g transform={`rotate(${kneeA} ${kneePt.x} ${kneePt.y})`}>
          <Hose x={kneePt.x} y={kneePt.y} len={SHIN} bow={side * 5} />
          <Shoe x={anklePt.x} y={anklePt.y} flip={!isRight} />
        </g>
      </g>
    );
  };

  const headA = p.leanHead;

  return (
    <svg
      width={size}
      height={(size * 440) / 420}
      viewBox="0 0 420 440"
      style={{display: 'block', overflow: 'visible'}}
    >
      <g transform={facing === 'left' ? `translate(420 0) scale(-1 1)` : undefined}>
        {shadow ? (
          <ellipse
            cx={CX}
            cy={GROUND + 12}
            rx={86 - p.bob * 0.6}
            ry={11}
            fill="#000"
            opacity={0.2}
          />
        ) : null}

        {/* Whole-rig squash/stretch pivots about the ground contact, and the
            idle bob rides on top of it. */}
        <g
          transform={`translate(${p.weightShift} ${p.bob}) translate(${CX} ${GROUND}) scale(${2 - p.squash} ${p.squash}) translate(${-CX} ${-GROUND})`}
        >
          {/* far leg first so the near leg overlaps it */}
          {legGroup(-1)}
          {legGroup(1)}

          {/* shorts sit on the pelvis, under the torso */}
          <path
            d={`M${CX - 40},${PELVIS.y - 16} L${CX + 40},${PELVIS.y - 16} L${CX + 34},${PELVIS.y + 18} L${CX - 34},${PELVIS.y + 18} Z`}
            fill={SHORTS}
            stroke={INK}
            strokeWidth={OUTLINE}
            strokeLinejoin="round"
          />

          {/* far arm behind the torso */}
          <g transform={`rotate(${p.leanChest} ${PELVIS.x} ${PELVIS.y}) translate(0 ${spineDrop})`}>
            {armGroup(-1)}

            {/* Neck, drawn BEFORE the torso so the torso's outline closes over
                its base and the join reads as anatomy rather than as a pipe
                stuck on. It still rotates with the head. */}
            <g transform={`rotate(${headA * 0.55} ${HEAD_PIVOT.x} ${HEAD_PIVOT.y})`}>
              <line
                x1={CX}
                y1={NECK.y + 16}
                x2={CX}
                y2={HEAD_PIVOT.y - 6}
                stroke={INK}
                strokeWidth={STROKE + 3}
                strokeLinecap="round"
              />
            </g>

            {/* Torso: a bean, not a slab. The first contact sheet rendered this
                as a wide flat-sided capsule, which at a 32-degree lean read as
                a rotating rectangle instead of a body. Narrow shoulders, a
                wider low belly, and curved sides throughout. */}
            <path
              d={`M${CX - 33},${PELVIS.y + 10}
                  C${CX - 45},${PELVIS.y - 22} ${CX - 42},${CHEST.y + 4} ${CX - 30},${CHEST.y - 26}
                  C${CX - 24},${CHEST.y - 42} ${CX - 14},${CHEST.y - 48} ${CX},${CHEST.y - 48}
                  C${CX + 14},${CHEST.y - 48} ${CX + 24},${CHEST.y - 42} ${CX + 30},${CHEST.y - 26}
                  C${CX + 42},${CHEST.y + 4} ${CX + 45},${PELVIS.y - 22} ${CX + 33},${PELVIS.y + 10}
                  C${CX + 16},${PELVIS.y + 20} ${CX - 16},${PELVIS.y + 20} ${CX - 33},${PELVIS.y + 10} Z`}
              fill={BODY}
              stroke={INK}
              strokeWidth={OUTLINE}
              strokeLinejoin="round"
            />

            {/* head, rotating about the head pivot */}
            <g transform={`rotate(${headA} ${HEAD_PIVOT.x} ${HEAD_PIVOT.y})`}>
              <ellipse
                cx={CX}
                cy={HEAD_PIVOT.y - 32}
                rx={49}
                ry={44}
                fill={BODY}
                stroke={INK}
                strokeWidth={OUTLINE}
              />
              {/* a single hair curl — rubber-hose shorthand for a head that
                  isn't just an egg */}
              <path
                d={`M${CX + 2},${HEAD_PIVOT.y - 74} q14,-16 26,-4 q8,9 -6,13`}
                fill="none"
                stroke={INK}
                strokeWidth={OUTLINE}
                strokeLinecap="round"
              />
              <Eye
                cx={CX + 10}
                cy={HEAD_PIVOT.y - 40}
                r={16 * p.eyeBulge}
                blink={p.blink}
                gx={p.gazeX}
                gy={p.gazeY}
              />
              <Eye
                cx={CX + 40}
                cy={HEAD_PIVOT.y - 40}
                r={15 * p.eyeBulge}
                blink={p.blink}
                gx={p.gazeX}
                gy={p.gazeY}
              />
              {/* nose + mouth. The mouth opens with the eye bulge, so the take
                  reads on the whole face rather than only the eyes. */}
              <circle cx={CX + 50} cy={HEAD_PIVOT.y - 20} r={8.5} fill={INK} />
              <ellipse
                cx={CX + 28}
                cy={HEAD_PIVOT.y - 6}
                rx={9 + (p.eyeBulge - 1) * 20}
                ry={4.5 + (p.eyeBulge - 1) * 24}
                fill={INK}
              />
            </g>

            {/* near arm in front of the torso */}
            {armGroup(1)}
          </g>
        </g>
      </g>
    </svg>
  );
};
