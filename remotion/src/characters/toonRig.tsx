// toonRig.tsx — the character: generated art on a cutout rig, with the feet
// nailed to the floor.
//
// Why the art is generated rather than drawn in code: rubberHoseRig.tsx draws
// its limbs as constant-width stroked paths, and the target look needs a
// TAPERED brush outline with volume. That is the wrong primitive, not a matter
// of effort. The art is generated once as sheets, cut by
// scripts/meme_reel/extract_limbs.py, and rigged here.
//
// WHAT CHANGED IN v2, and why it is the difference between "poses" and
// "movement":
//
//   THE FEET ARE PINNED. v1 wrapped the entire figure — legs included — in
//   `translate(weightShift, bob)`, so every breath lifted the feet off the floor
//   and every weight shift slid them sideways: 16px of vertical hover and 13px
//   of skate across the reel (scripts/check_foot_plant.mjs). A standing figure's
//   feet do not move; the body moves OVER them. Now the pelvis moves and each
//   leg SOLVES to a fixed floor position with the same two-link IK the arms use.
//   Foot drift is zero by construction, because the foot position is an input.
//
//   THE FEET STAY FLAT. The shoe used to inherit the shin's rotation, so it
//   pitched like a ski whenever the knee bent. It is now counter-rotated by the
//   accumulated hip+knee angle, keeping its sole parallel to the floor.
//
//   THE KNEE IS NEVER STRAIGHT. The hip rests at 95.5% of full leg extension
//   (toonSkeleton.LEG_REST). A fully extended two-link chain is the singular
//   case for IK — the solution flips there and the knee snaps.
//
//   NEAR AND FAR ARE DIFFERENTIATED. One drawing still serves both sides — the
//   honest limitation of a single-view parts sheet — but the far side is tinted
//   and stands in a different place, so the two no longer read as one shape
//   stamped twice.
//
// Everything else is reused unchanged: the pose engine (computeRubberHosePose),
// the contact-pose IK (armIK), and the anatomical clamps (joints.ts).
import React from 'react';
import {staticFile, useCurrentFrame} from 'remotion';
import {computeRubberHosePose, type Pose} from './rubberHoseRig';
import {armIK} from './armIK';
import {clampJoint} from './joints';
import {
  CX,
  GROUND,
  HIP_DX,
  HIP_Y,
  NECK_Y,
  P,
  SHIN_BONE,
  SHOULDER_DX,
  SHOULDER_Y,
  STANCE,
  THIGH_BONE,
  VB_H,
  VB_W,
  boneLen,
  type Part,
} from './toonSkeleton';

const src = (p: Part) => staticFile(`meme_reel/char2/${p.file}`);

// ------------------------------------------------------------------- swaps
const HEADS = ['neutral', 'curious', 'shock', 'weary', 'wince', 'blink'] as const;
export type Expression = (typeof HEADS)[number];

/** Which face is on at a given frame. The reference reel gets most of its read
 * from the FACE — a shocked take with a neutral face is just a man waving. */
export const expressionAt = (frame: number): Expression => {
  if (frame < 76) return 'neutral';
  if (frame < 232) return 'curious';
  if (frame < 302) return 'shock';
  return 'weary';
};

/** Hand swap set. Cutout hands are swapped, never deformed. Each pose carries
 * its OWN wrist pivot because the drawings sit in different orientations — a
 * shared pivot leaves the pointing hand hanging off the end of the arm. */
export type HandPose = 'relaxed' | 'flat' | 'splay' | 'palmup';
// PENDING REGENERATION. The swap sheet was drawn at a different scale from the
// body (its hands are ~2x too big) and its wrist pivots were GUESSED, not
// measured — which is exactly why hands read as detached blobs floating beside
// the arm. Until that sheet is redrawn to match this body with the wrist at a
// known point, every pose uses the one hand that came from the VALIDATED parts
// sheet. A correct single hand beats four wrong ones.
export const HAND_POSES: Record<HandPose, Part> = {
  relaxed: {file: 'hand.png', w: 195, h: 280, px: 0.5, py: 0.06},
  flat: {file: 'hand.png', w: 195, h: 280, px: 0.5, py: 0.06},
  splay: {file: 'hand.png', w: 195, h: 280, px: 0.5, py: 0.06},
  palmup: {file: 'hand.png', w: 195, h: 280, px: 0.5, py: 0.06},
};

export const handPoseAt = (frame: number): HandPose => {
  if (frame < 200) return 'relaxed';
  if (frame < 232) return 'flat';
  if (frame < 302) return 'splay';
  if (frame < 396) return 'relaxed';
  return 'palmup';
};

// ------------------------------------------------------------------ pieces
const Piece: React.FC<{
  part: Part;
  jx: number;
  jy: number;
  angle: number;
  children?: React.ReactNode;
}> = ({part, jx, jy, angle, children}) => {
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
        preserveAspectRatio="none"
      />
      {children}
    </g>
  );
};

/** Rest angles — the same values the vector rig uses, so an identical Pose
 * reads the same on both rigs. */
const REST = {
  shoulderL: 4,
  shoulderR: -4,
  elbowL: 14,
  elbowR: -14,
  handL: -6,
  handR: 6,
};

export type ToonRigProps = {
  /** Rendered height in frame pixels — the whole viewBox. */
  height?: number;
  facing?: 'left' | 'right';
  frameOverride?: number;
  poseOverride?: Partial<Pose>;
  shadow?: boolean;
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

  // ------------------------------------------------------------ the pelvis
  // ONLY the pelvis and everything above it move. The feet do not.
  const GAIN = 2.2;
  const pelvisX = CX + p.weightShift * GAIN;
  const pelvisY = HIP_Y + p.bob * GAIN;

  // -------------------------------------------------------------- the legs
  // Each leg solves from its (moving) hip down to its (fixed) floor position.
  const leg = (which: 'near' | 'far') => {
    const isNear = which === 'near';
    const hip = {x: pelvisX + HIP_DX * (isNear ? 1 : -1), y: pelvisY};
    const ankle = STANCE[which];

    // bend +1 puts the knee forward, which is the only way a knee goes.
    const ik = armIK(hip, ankle, THIGH_BONE, SHIN_BONE, 1);
    const hipA = clampJoint(isNear ? 'hipR' : 'hipL', ik.shoulderDeg);
    const kneeA = clampJoint(isNear ? 'kneeR' : 'kneeL', ik.elbowDeg);

    const kneePt = {x: hip.x, y: hip.y + THIGH_BONE};
    const anklePt = {x: hip.x, y: hip.y + THIGH_BONE + SHIN_BONE};

    return (
      <g style={isNear ? undefined : {filter: 'brightness(0.93)'}}>
        <Piece part={P.thigh} jx={hip.x} jy={hip.y} angle={hipA}>
          <Piece part={P.shin} jx={kneePt.x} jy={kneePt.y} angle={kneeA}>
            {/* Counter-rotated by the accumulated leg angle so the sole stays
                parallel to the floor instead of pitching like a ski. */}
            <Piece part={P.foot} jx={anklePt.x} jy={anklePt.y} angle={-(hipA + kneeA)} />
          </Piece>
        </Piece>
      </g>
    );
  };

  // -------------------------------------------------------------- the arms
  // Drawn in pelvis-local space, so they ride the lean and the squash.
  const arm = (which: 'near' | 'far') => {
    const isNear = which === 'near';
    const sx = SHOULDER_DX * (isNear ? 1 : -1);
    const sy = SHOULDER_Y - HIP_Y;

    const shoulderA = clampJoint(
      isNear ? 'shoulderR' : 'shoulderL',
      isNear ? REST.shoulderR + p.shoulderR : REST.shoulderL + p.shoulderL
    );
    const elbowA = clampJoint(
      isNear ? 'elbowR' : 'elbowL',
      isNear ? REST.elbowR + p.elbowR : REST.elbowL + p.elbowL
    );
    const handA = clampJoint(
      isNear ? 'handR' : 'handL',
      isNear ? REST.handR + p.handR : REST.handL + p.handL
    );

    const elbowY = sy + boneLen(P.upperArm);
    const wristY = elbowY + boneLen(P.forearm);

    return (
      <g style={isNear ? undefined : {filter: 'brightness(0.93)'}}>
        <Piece part={P.upperArm} jx={sx} jy={sy} angle={shoulderA}>
          <Piece part={P.forearm} jx={sx} jy={elbowY} angle={elbowA}>
            <Piece part={HAND_POSES[handPose]} jx={sx} jy={wristY} angle={handA} />
          </Piece>
        </Piece>
      </g>
    );
  };

  const leanChest = clampJoint('leanChest', p.leanChest);
  const leanHead = clampJoint('leanHead', p.leanHead);
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
          <ellipse cx={CX + 10} cy={GROUND + 26} rx={380} ry={36} fill="#000" opacity={0.16} />
        ) : null}

        {/* far leg, then near leg — both solved to the floor, never translated */}
        {leg('far')}
        {leg('near')}

        {/* Everything from the pelvis up. The squash pivots about the PELVIS,
            not the ground, so it can never drag the planted feet sideways. */}
        <g
          transform={`translate(${pelvisX} ${pelvisY}) scale(${2 - p.squash} ${p.squash}) rotate(${leanChest}) translate(0 ${spineDrop})`}
        >
          {arm('far')}

          <Piece part={P.torso} jx={0} jy={0} angle={0} />

          <Piece
            part={{...P.head, file: `head_${expression}.png`}}
            jx={0}
            jy={NECK_Y - HIP_Y}
            angle={leanHead}
          />

          {arm('near')}
        </g>
      </g>
    </svg>
  );
};
