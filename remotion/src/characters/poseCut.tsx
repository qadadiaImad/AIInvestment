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

export type PoseName = 'idle' | 'notices' | 'leans_a' | 'leans_b' | 'shock' | 'facepalm' | 'shrug';

/** The cut sheet. Each entry is the frame the drawing CUTS IN on; it holds
 * until the next one. Keyed to the same beats as the chart. */
// NOTE: the pose files were renamed to what the drawings ACTUALLY are. The
// extractor orders blobs by row then x, and the sheet put a large hero figure
// beside two rows of smaller ones — so the sort mislabelled six of the seven,
// and the first render cut to a shock take during the idle beat. Verified
// against a labelled contact sheet, not against the sort order.
export const POSE_CUTS: {at: number; pose: PoseName}[] = [
  {at: 0, pose: 'idle'},
  {at: 78, pose: 'notices'}, // head up, hand half-raised
  {at: 150, pose: 'leans_a'}, // bends toward the screen
  {at: 206, pose: 'leans_b'}, // in closer, reaching
  {at: 236, pose: 'shock'}, // the level fails
  {at: 304, pose: 'facepalm'},
  {at: 396, pose: 'shrug'},
];

export const poseAt = (frame: number): {pose: PoseName; since: number} => {
  let cur = POSE_CUTS[0];
  for (const c of POSE_CUTS) if (frame >= c.at) cur = c;
  return {pose: cur.pose, since: frame - cur.at};
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
};

export const PoseCut: React.FC<PoseCutProps> = ({
  height = 900,
  footX,
  footY,
  facing = 'right',
  frameOverride,
  poseOverride,
  shadow = true,
}) => {
  const current = useCurrentFrame();
  const frame = frameOverride ?? current;
  const {pose, since} = poseAt(frame);
  const name = poseOverride ?? pose;
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

  const s = scale * snap * (1 + breath);
  const w = a.w * s;
  const h = a.h * s;
  // Place the drawing so its GROUND CONTACT lands exactly on (footX, footY).
  const left = footX - a.anchor[0] * w;
  const top = footY - a.anchor[1] * h;

  return (
    <>
      {shadow ? (
        <div
          style={{
            position: 'absolute',
            left: footX - height * 0.19,
            top: footY - height * 0.022,
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
          transform: facing === 'left' ? 'scaleX(-1)' : undefined,
          transformOrigin: `${a.anchor[0] * 100}% ${a.anchor[1] * 100}%`,
        }}
      />
    </>
  );
};
