// toonRig.tsx — the same puppet, drawn with GENERATED ART instead of
// hand-authored vector shapes.
//
// Why this exists: rubberHoseRig.tsx draws its limbs as constant-width stroked
// paths (`<path stroke strokeWidth={14}>`). That is the wrong primitive for the
// target look — a real toon limb has a TAPERED brush outline and visible volume
// (thick at the hip, hairline at the ankle), which a constant stroke cannot
// express at any level of effort. So the art is generated once as a parts
// sheet, cut into per-limb PNGs by scripts/meme_reel/extract_limbs.py, and
// rigged here.
//
// EVERYTHING ELSE IS REUSED. The pose engine (computeRubberHosePose) and the
// contact-pose IK (armIK) are imported unchanged from the vector rig — this
// file only swaps what gets drawn inside each joint's rotate() group. The beat
// timing, anticipation/follow-through, and the facepalm/desk-plant IK targets
// are the same code that was already reviewed and checked.
//
// PROPORTIONS COME FROM THE ART, NOT FROM A SKELETON GUESS. Bone lengths are
// derived from each part PNG's own pixel height, so the figure is shaped like
// the drawing. The reference look is extremely leggy with a small torso; that
// falls out of the art automatically instead of being re-guessed here.
//
// JOINT SEAMS are the known failure mode of cutout rigs. Two mitigations, both
// structural rather than cosmetic:
//   * each part's pivot sits slightly INSIDE its ink (PIVOT_Y ≈ 0.05), so the
//     rounded cap of the child overlaps the parent's end and there is no gap to
//     see at any rotation;
//   * children are nested inside their parent's <g>, so SVG paint order draws
//     them ON TOP of the joint automatically.
import React from 'react';
import {staticFile, useCurrentFrame} from 'remotion';
import {computeRubberHosePose, type Pose} from './rubberHoseRig';
import {clampJoint} from './joints';

// ---------------------------------------------------------------- the parts
// Intrinsic pixel size of each extracted PNG, and where its joint sits inside
// it, normalised 0..1. These mirror remotion/public/meme_reel/char/manifest.json;
// the pivots are hand-tuned from it because "top-centre of the ink bbox" is the
// right default for a hanging limb but wrong for a head (which hangs UP from a
// neck) and for a foot (whose ankle is at its upper-LEFT).
type Part = {
  file: string;
  w: number;
  h: number;
  /** Joint position inside the image, normalised. */
  px: number;
  py: number;
  /** Where this part's CHILD joint sits, normalised down its own height.
   * Slightly less than 1 so the child overlaps and hides the seam. */
  childY?: number;
  /** Draw scale relative to the sheet. The parts arrive at one another's
   * scale except the hand, which the generator drew as a large splayed hand. */
  s?: number;
};

/** The four interchangeable heads. Generated as ONE sheet so they share
 * framing, size and neck position exactly — a head swapped in from a different
 * generation jumps on the cut, which is the whole reason they were not just
 * generated one at a time. Their pivot is the NECK STUB, not the top of the
 * ink: a head hangs up from its neck. */
const HEADS = ['neutral', 'curious', 'shock', 'weary', 'wince', 'blink'] as const;
export type Expression = (typeof HEADS)[number];

/** Which face is on at a given frame. The reference reel gets most of its read
 * from the FACE, not the body — a shocked take with a neutral face is just a
 * man waving. */
/** Hand swap set. Each pose is a different drawing with its OWN wrist position,
 * so the pivot has to travel with the file — a shared pivot would leave the
 * pointing hand hanging off the end of the arm. */
export type HandPose = 'relaxed' | 'flat' | 'splay' | 'palmup';
export const HAND_POSES: Record<HandPose, {file: string; w: number; h: number; px: number; py: number; s?: number}> = {
  relaxed: {file: 'hand_relaxed.png', w: 413, h: 619, px: 0.50, py: 0.04, s: 0.62},
  flat: {file: 'hand_flat.png', w: 573, h: 533, px: 0.80, py: 0.10, s: 0.62},
  splay: {file: 'hand_splay.png', w: 635, h: 538, px: 0.68, py: 0.90, s: 0.62},
  palmup: {file: 'hand_palmup.png', w: 659, h: 434, px: 0.12, py: 0.35, s: 0.62},
};

/** Which hand is on at a given frame — keyed to the same beats as the face. */
export const handPoseAt = (frame: number): HandPose => {
  if (frame < 200) return 'relaxed';
  if (frame < 232) return 'flat';   // planted on the desk
  if (frame < 302) return 'splay';  // the recoil
  if (frame < 396) return 'relaxed';
  return 'palmup';                  // the shrug
};

export const expressionAt = (frame: number): Expression => {
  if (frame < 76) return 'neutral';
  if (frame < 232) return 'curious';
  if (frame < 302) return 'shock';
  return 'weary';
};

const P: Record<string, Part> = {
  // Dimensions and pivots are the measured output of extract_limbs.py on
  // content/meme_reel/character/*.png — see manifest_*.json in char2/.
  // Only the two that hang UPWARD from their joint are hand-corrected: the head
  // pivots on its neck stub and the torso on its belt, both at the BOTTOM.
  head: {file: 'head_neutral.png', w: 530, h: 631, px: 0.598, py: 0.955},
  torso: {file: 'torso.png', w: 665, h: 608, px: 0.5, py: 0.90, childY: 0.03},
  upperArm: {file: 'upper_arm.png', w: 245, h: 595, px: 0.5, py: 0.04, childY: 0.95},
  forearm: {file: 'forearm.png', w: 225, h: 369, px: 0.5, py: 0.05, childY: 0.95},
  hand: {file: 'hand_relaxed.png', w: 413, h: 619, px: 0.5, py: 0.04, s: 0.62},
  thigh: {file: 'thigh.png', w: 415, h: 623, px: 0.5, py: 0.04, childY: 0.95},
  shin: {file: 'shin.png', w: 351, h: 598, px: 0.5, py: 0.04, childY: 0.95},
  foot: {file: 'shoe.png', w: 357, h: 232, px: 0.30, py: 0.12},
};

const src = (p: Part) => staticFile(`meme_reel/char2/${p.file}`);

/** Ink length from a part's own joint to where its child attaches.
 * Absolute, because the torso is the one part whose bone runs UPWARD from its
 * joint (it hangs off the pelvis and the shoulders are above it) while every
 * limb runs downward — signing this caught out the first assembly, which put
 * the head and both arms below the hip. */
const boneLen = (p: Part) => Math.abs(((p.childY ?? 1) - p.py) * p.h * (p.s ?? 1));

// ------------------------------------------------------------- the skeleton
// Built bottom-up in ART UNITS, so every number below is a real pixel distance
// in the generated drawing rather than an invented one.
const VB_W = 1700;
const VB_H = 2900;
const CX = 850;
const GROUND = 2620;

const ANKLE_Y = GROUND - (1 - P.foot.py) * P.foot.h;
const KNEE_Y = ANKLE_Y - boneLen(P.shin);
const HIP_Y = KNEE_Y - boneLen(P.thigh);
const TORSO_TOP_Y = HIP_Y - boneLen(P.torso);
const NECK_Y = TORSO_TOP_Y + 104;

const HIP_DX = 200;
const SHOULDER_DX = 205;
const SHOULDER_Y = TORSO_TOP_Y + 96;

/** The rig's full ink height, so a caller can size it in real frame pixels. */
export const TOON_INK_TOP = NECK_Y - P.head.py * P.head.h;
export const TOON_INK_HEIGHT = GROUND - TOON_INK_TOP;
/** Fraction of the rendered height at which the feet sit — the composition
 * needs this to stand him on a floor line. */
export const TOON_GROUND_FRAC = (GROUND - 0) / VB_H;

/**
 * One part, placed so its own joint lands exactly on (jx, jy) and rotated about
 * that joint. `flipX` mirrors a part in place — used so the far arm/leg do not
 * read as an identical stamp of the near one.
 */
const Piece: React.FC<{
  part: Part;
  jx: number;
  jy: number;
  angle: number;
  opacity?: number;
  children?: React.ReactNode;
}> = ({part, jx, jy, angle, opacity = 1, children}) => {
  const w = part.w * (part.s ?? 1);
  const h = part.h * (part.s ?? 1);
  return (
    <g transform={`rotate(${angle} ${jx} ${jy})`}>
      <image
        href={src(part)}
        x={jx - part.px * w}
        y={jy - part.py * h}
        width={w}
        height={h}
        opacity={opacity}
        preserveAspectRatio="none"
      />
      {children}
    </g>
  );
};

/** Rest angles — same values the vector rig uses, so an identical Pose reads
 * the same on both rigs. */
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
};

export type ToonRigProps = {
  /** Rendered height in frame pixels (the whole viewBox, feet at
   * TOON_GROUND_FRAC of it). */
  height?: number;
  facing?: 'left' | 'right';
  frameOverride?: number;
  poseOverride?: Partial<Pose>;
  shadow?: boolean;
  /** Force a face, bypassing the beat timeline (used by the contact sheet). */
  expressionOverride?: Expression;
};

export const ToonRig: React.FC<ToonRigProps> = ({
  height = 1400,
  facing = 'right',
  frameOverride,
  poseOverride,
  shadow = true,
  expressionOverride,
}) => {
  const current = useCurrentFrame();
  const frame = frameOverride ?? current;
  const p = {...computeRubberHosePose(frame), ...poseOverride};
  const expression = expressionOverride ?? expressionAt(frame);
  const handPose = handPoseAt(frame);

  const width = (height * VB_W) / VB_H;

  const arm = (side: 1 | -1) => {
    const isR = side === 1;
    const sx = CX + SHOULDER_DX * side;
    // Every joint is clamped to what a body can actually do. Without this the
    // elbow crosses zero and inverts — see joints.ts.
    const shoulderA = clampJoint(isR ? 'shoulderR' : 'shoulderL', isR ? REST.shoulderR + p.shoulderR : REST.shoulderL + p.shoulderL);
    const elbowA = clampJoint(isR ? 'elbowR' : 'elbowL', isR ? REST.elbowR + p.elbowR : REST.elbowL + p.elbowL);
    const handA = clampJoint(isR ? 'handR' : 'handL', isR ? REST.handR + p.handR : REST.handL + p.handL);
    const elbowY = SHOULDER_Y + boneLen(P.upperArm);
    const wristY = elbowY + boneLen(P.forearm);
    // The far side is TINTED darker, not made transparent. Using opacity here
    // let the torso show through the far arm wherever they crossed — the art is
    // opaque and has to stay opaque; only its value should change.
    return (
      <g style={isR ? undefined : {filter: 'brightness(0.86)'}}>
        <Piece part={P.upperArm} jx={sx} jy={SHOULDER_Y} angle={shoulderA}>
          <Piece part={P.forearm} jx={sx} jy={elbowY} angle={elbowA}>
            <Piece part={{...P.hand, ...HAND_POSES[handPose]}} jx={sx} jy={wristY} angle={handA} />
          </Piece>
        </Piece>
      </g>
    );
  };

  const leg = (side: 1 | -1) => {
    const isR = side === 1;
    const hx = CX + HIP_DX * side;
    const hipA = clampJoint(isR ? 'hipR' : 'hipL', isR ? REST.hipR + p.hipR : REST.hipL + p.hipL);
    const kneeA = clampJoint(isR ? 'kneeR' : 'kneeL', isR ? REST.kneeR + p.kneeR : REST.kneeL + p.kneeL);
    const kneeY = HIP_Y + boneLen(P.thigh);
    const ankleY = kneeY + boneLen(P.shin);
    return (
      <g style={isR ? undefined : {filter: 'brightness(0.86)'}}>
        <Piece part={P.thigh} jx={hx} jy={HIP_Y} angle={hipA}>
          <Piece part={P.shin} jx={hx} jy={kneeY} angle={kneeA}>
            <Piece part={P.foot} jx={hx} jy={ankleY} angle={0} />
          </Piece>
        </Piece>
      </g>
    );
  };

  const spineDrop = p.slouch * 26;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${VB_W} ${VB_H}`}
      style={{display: 'block', overflow: 'visible'}}
    >
      <g transform={facing === 'left' ? `translate(${VB_W} 0) scale(-1 1)` : undefined}>
        {shadow ? (
          <ellipse cx={CX} cy={GROUND + 26} rx={330 - p.bob * 1.2} ry={34} fill="#000" opacity={0.17} />
        ) : null}

        <g
          transform={`translate(${p.weightShift * 2.2} ${p.bob * 2.2}) translate(${CX} ${GROUND}) scale(${2 - p.squash} ${p.squash}) translate(${-CX} ${-GROUND})`}
        >
          {leg(-1)}
          {leg(1)}

          <g transform={`rotate(${clampJoint('leanChest', p.leanChest)} ${CX} ${HIP_Y}) translate(0 ${spineDrop})`}>
            {arm(-1)}

            <Piece part={P.torso} jx={CX} jy={HIP_Y} angle={0} />

            <Piece part={{...P.head, file: `head_${expression}.png`}} jx={CX} jy={NECK_Y} angle={clampJoint('leanHead', p.leanHead)} />

            {arm(1)}
          </g>
        </g>
      </g>
    </svg>
  );
};
