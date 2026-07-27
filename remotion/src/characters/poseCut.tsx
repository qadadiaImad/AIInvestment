// poseCut.tsx — the character as POSE-TO-POSE limited animation.
//
// WHY THIS REPLACES THE RIG.
//
// A cutout rig moves rigid PNG pieces by rotating them about pivots. That is
// what it does, and it is why it reads mechanical: the hand is a stamp that
// SPINS rather than a hand that turns, the elbow is a hinge between two tubes
// rather than an arm that bends, and the torso is one unchanging drawing for
// all 510 frames, so the body never reacts to anything. No amount of better
// pivots, joint limits or IK removes that — it is the technique, not a bug in
// this instance of it.
//
// The generated key-pose sheet already solves it. In each drawn pose the arm is
// one continuous silhouette from sleeve to fingers, the elbow CURVES, the belly
// reshapes on the lean and the shirt stretches on the take. Everything deforms,
// because it was drawn that way.
//
// So: hold a drawing, cut to the next drawing on the beat. That is limited
// animation — South Park, Cyanide & Happiness, and most meme reels — and it
// reads as a deliberate style rather than as a puppet, precisely because
// nothing rotates.
//
// THE ONE PROBLEM IT INTRODUCES is registration. Cut between drawings that are
// not aligned and the character jumps every time. Two fixes, both computed
// rather than eyeballed by scripts/meme_reel/pose_anchors.py:
//   * every pose is placed by its GROUND CONTACT — the bottom of the ink and
//     the horizontal centre of only the ink near that bottom, i.e. the feet.
//     Aligning on the bounding box would sink a pose that throws its arms up
//     and slide one that reaches sideways.
//   * every pose carries a scale correction to a common body height, so he
//     cannot grow or shrink across a cut.
//
// LIFE WITHOUT ROTATION. A held drawing is dead, so each pose gets a breath
// (a sub-percent scale about the feet) and each CUT gets a snap — the drawing
// arrives ~6% large and settles. That is where limited animation puts its
// anticipation and follow-through: on the whole drawing, not on joints.
import React from 'react';
import {Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {EASE, wiggle} from '../motion/craft';
import anchors from '../fixtures/meme_reel/pose_anchors.json';

type Anchor = {w: number; h: number; anchor: number[]; ink_h: number; scale: number};
const A = anchors as unknown as Record<string, Anchor>;

/** Reference body height the per-pose scale corrections normalise to. */
const REF_INK = 686;

export type PoseName =
  | 'idle' | 'turning' | 'notices' | 'bending' | 'leans_a' | 'point' | 'reach'
  | 'leans_b' | 'crouch' | 'shock' | 'stagger' | 'facepalm' | 'shrug';

/** The cut sheet. Each entry is the frame the drawing CUTS IN on; it holds
 * until the next one. Keyed to the same beats as the chart. */
// NOTE: the pose files were renamed to what the drawings ACTUALLY are. The
// extractor orders blobs by row then x, and the sheet put a large hero figure
// beside two rows of smaller ones — so the sort mislabelled six of the seven,
// and the first render cut to a shock take during the idle beat. Verified
// against a labelled contact sheet, not against the sort order.
export type Cut = {
  at: number;
  pose: PoseName;
  /** WHOLE-DRAWING MOTION while this pose is held.
   *
   * This is the second source of smoothness, and the safe one. Moving, scaling
   * or tilting the ENTIRE drawing never articulates it — the figure stays
   * internally coherent, which is exactly what rotating its parts destroyed.
   * Real limited animation leans on this hard: a held pose drifts toward what
   * it is reacting to, settles back after a hit, sinks through a slump.
   *
   * dx/dy are travel in frame px from the cut to the end of the hold, dScale a
   * multiplier, tilt a whole-body lean in degrees about the feet.
   */
  drift?: {dx?: number; dy?: number; dScale?: number; tilt?: number};
};

export const POSE_CUTS: Cut[] = [
  // STAGED BACK FROM THE SCREEN. He used to bend over the desk with his head
  // beside the monitor, which buried the chart — the one thing the reel exists
  // to show. The bending/reaching poses are mostly out; he now works from a
  // distance and INDICATES the screen with `point` instead of crowding it.
  // His frustration is carried by the take, the stagger, the facepalm and the
  // shrug, none of which need him close to anything.
  //
  // Drifts are small for the same reason: a big -x drift walks him back onto
  // the monitor over the course of a hold.
  {at: 0, pose: 'idle', drift: {dy: -2}},
  {at: 58, pose: 'turning', drift: {dx: -6}}, // BREAKDOWN — head starts round
  {at: 80, pose: 'notices', drift: {dx: -8, tilt: -1}},
  {at: 122, pose: 'point', drift: {dx: -5}}, // indicates the level, from across the room
  {at: 176, pose: 'bending', drift: {dx: -10, dScale: 1.02}}, // one brief lean in
  {at: 204, pose: 'point', drift: {dx: -5}}, // points again as the story bar prints
  {at: 246, pose: 'crouch', drift: {dy: 6}}, // BREAKDOWN — loads down before the take
  {at: 258, pose: 'shock', drift: {dx: 40, dScale: 0.99, tilt: 3}},
  {at: 288, pose: 'stagger', drift: {dx: 16, tilt: 2}}, // BREAKDOWN — the settle
  {at: 316, pose: 'facepalm', drift: {dy: 14, dScale: 0.985, tilt: 1.5}},
  {at: 396, pose: 'shrug', drift: {dy: -4, tilt: -1}},
];

export const poseAt = (
  frame: number,
  cuts: Cut[] = POSE_CUTS,
  end = 510
): {cut: Cut; since: number; hold: number} => {
  let idx = 0;
  for (let i = 0; i < cuts.length; i++) if (frame >= cuts[i].at) idx = i;
  const cur = cuts[idx];
  const next = cuts[idx + 1];
  return {cut: cur, since: frame - cur.at, hold: (next ? next.at : end) - cur.at};
};

export type PoseCutProps = {
  /** The character's ink height in frame pixels — his actual on-screen size,
   * independent of how big any one drawing's canvas happens to be. */
  height?: number;
  /** Where his feet touch the floor, in the parent's coordinate space. */
  footX: number;
  footY: number;
  facing?: 'left' | 'right';
  frameOverride?: number;
  poseOverride?: PoseName;
  shadow?: boolean;
  /** This reel's own cut sheet. POSE_CUTS is keyed to MemeReel's 510-frame
   * beats, so a second reel with different beats has to bring its own or the
   * character performs the wrong story. Additive: omitting it is unchanged. */
  cuts?: Cut[];
  /** Frame the last pose is held until — only used to size that final hold's
   * drift. Defaults to MemeReel's length. */
  end?: number;
};

export const PoseCut: React.FC<PoseCutProps> = ({
  height = 900,
  footX,
  footY,
  facing = 'right',
  frameOverride,
  poseOverride,
  shadow = true,
  cuts,
  end,
}) => {
  const current = useCurrentFrame();
  const frame = frameOverride ?? current;
  const {cut, since, hold} = poseAt(frame, cuts ?? POSE_CUTS, end ?? 510);
  const name = poseOverride ?? cut.pose;
  const a = A[name];
  if (!a) return null;

  // Global scale maps the reference body height onto the requested pixel
  // height; the per-pose correction then equalises the drawings to each other.
  const scale = (height / REF_INK) * a.scale;

  // THE SNAP. The drawing cuts in ~6% large and settles over 7 frames. This is
  // the anticipation/follow-through of limited animation — applied to the whole
  // pose, because there are no joints to apply it to.
  const snap = poseOverride
    ? 1
    : interpolate(since, [0, 7], [1.06, 1], {
        easing: EASE.settleBack,
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });

  // THE BREATH. Sub-percent, about the feet, so a held drawing is never a
  // frozen still. Seeded off the pose so two poses do not breathe in lockstep.
  const breath = poseOverride ? 0 : wiggle(frame, name.length, 0.006, 0.5);

  // THE DRIFT. Eased across the whole hold, so the pose is never static and is
  // always travelling toward or away from the thing it is reacting to.
  const d = poseOverride ? 0 : interpolate(since, [0, Math.max(1, hold)], [0, 1], {
    easing: EASE.cruise,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const dr = cut.drift ?? {};
  const dx = (dr.dx ?? 0) * d;
  const dy = (dr.dy ?? 0) * d;
  const tilt = (dr.tilt ?? 0) * d;
  const driftScale = 1 + ((dr.dScale ?? 1) - 1) * d;

  const s = scale * snap * driftScale * (1 + breath);
  const w = a.w * s;
  const h = a.h * s;
  // Place the drawing so its GROUND CONTACT lands exactly on (footX, footY).
  const left = footX + dx - a.anchor[0] * w;
  const top = footY + dy - a.anchor[1] * h;

  return (
    <>
      {shadow ? (
        <div
          style={{
            position: 'absolute',
            left: footX + dx - height * 0.19,
            top: footY + dy - height * 0.022,
            width: height * 0.38,
            height: height * 0.045,
            borderRadius: '50%',
            background: 'rgba(0,0,0,0.17)',
            filter: 'blur(3px)',
          }}
        />
      ) : null}
      <Img
        src={staticFile(`meme_reel/poses/${name}.png`)}
        style={{
          position: 'absolute',
          left,
          top,
          width: w,
          height: h,
          // The tilt pivots about the FEET, so a lean never lifts him off the
          // floor — same reason the rig's squash pivoted about the pelvis.
          transform: `${facing === 'left' ? 'scaleX(-1) ' : ''}rotate(${facing === 'left' ? -tilt : tilt}deg)`,
          transformOrigin: `${a.anchor[0] * 100}% ${a.anchor[1] * 100}%`,
        }}
      />
    </>
  );
};
