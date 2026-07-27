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
import {actionCurve, bob, boil, cutEnergy, holdCurve, smear, squash} from '../motion/toon';
import anchors from '../fixtures/meme_reel/pose_anchors.json';
import heads from '../fixtures/meme_reel/head_anchors.json';

type Anchor = {w: number; h: number; anchor: number[]; ink_h: number; scale: number};
const A = anchors as unknown as Record<string, Anchor>;

/** Measured head position per drawing — scripts/meme_reel/head_anchors.py. */
type Head = {head: number[]; head_w: number};
const HEADS = heads as unknown as Record<string, Head>;

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
  /** Per-cut multiplier on the derived smear/squash energy. The geometry-only
   * derivation treats every large silhouette change as a large EVENT — but a
   * quiet "he points at the level" swaps in the widest drawing of the sheet
   * and is not a take. Grade the cut editorially: ~0.6 for quiet swaps that
   * happen to move a lot of ink, >1 only for genuine hits. */
  energy?: number;
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
  /**
   * `'cut'` (default) is the original behaviour: hold a drawing, snap 6% on
   * arrival, drift linearly across the hold. `'toon'` adds the grammar that
   * behaviour is missing — anticipation before every cut, volume-preserving
   * squash and stretch through it, a smear on the cut frames sized by how big
   * the change is, a three-sub-beat hold instead of a linear drift, and a
   * two-frame drawing boil so a held pose is drawn rather than photographed.
   *
   * Opt-in, because `'cut'` is what MemeReel shipped with and re-timing a
   * finished reel is not a side effect a new prop should have.
   */
  motion?: 'cut' | 'toon';
  /** Per-pose energy multiplier for the toon smear/squash, 0..1.6. Reaction
   * beats want a hard smear; a quiet weight shift wants almost none. */
  energy?: number;
};

export type PoseLayout = {
  name: PoseName;
  a: Anchor;
  left: number;
  top: number;
  w: number;
  h: number;
  tilt: number;
  sq: {sx: number; sy: number};
  sm: {sx: number; sy: number; blur: number; opacity: number};
  dx: number;
  dy: number;
  bx: number;
};

export type LayoutArgs = {
  frame: number;
  height: number;
  footX: number;
  footY: number;
  cuts?: Cut[];
  end?: number;
  poseOverride?: PoseName;
  motion?: 'cut' | 'toon';
  energy?: number;
};

/**
 * Everything about where and how big the drawing is, in one place.
 *
 * Extracted so `poseHead()` can report the head's real position WITHOUT
 * re-deriving the placement. Anything that anchors to the character - sweat,
 * an impact burst, a bubble - has to move with the drift, the boil, the breath
 * and the squash, and a second copy of that maths is a second copy that goes
 * stale the first time one of them changes.
 */
export const poseLayout = ({
  frame,
  height,
  footX,
  footY,
  cuts,
  end,
  poseOverride,
  motion = 'cut',
  energy = 1,
}: LayoutArgs): PoseLayout | null => {
  const sheet = cuts ?? POSE_CUTS;
  const {cut, since, hold} = poseAt(frame, sheet, end ?? 510);
  const name = poseOverride ?? cut.pose;
  const a = A[name];
  if (!a) return null;

  const toon = motion === 'toon' && !poseOverride;

  // Global scale maps the reference body height onto the requested pixel
  // height; the per-pose correction then equalises the drawings to each other.
  const scale = (height / REF_INK) * a.scale;

  const dr = cut.drift ?? {};

  // ------------------------------------------------------------ 'toon'
  // How big THIS cut is, derived from how much the silhouette and the drift
  // change across it - so the smear and the squash are consequences of the
  // motion instead of a constant sprinkled on every cut. A constant is the
  // giveaway that a smear was bolted on.
  const prev = sheet[sheet.findIndex((c) => c.at === cut.at) - 1];
  const prevA = prev ? A[prev.pose] : undefined;
  const widthDelta = prevA ? Math.abs(a.w * a.scale - prevA.w * prevA.scale) * (height / REF_INK) : 0;
  const driftDelta = Math.abs(dr.dx ?? 0) + Math.abs(dr.dy ?? 0) + Math.abs(dr.tilt ?? 0) * 12;
  const nrg = toon ? cutEnergy(widthDelta + driftDelta * 2.2) * energy * (cut.energy ?? 1) : 0;

  const sm = toon ? smear(since, nrg, 2) : {sx: 1, sy: 1, blur: 0, opacity: 1};

  // ANTICIPATION -> ACTION -> SETTLE, as one curve every channel below is
  // multiplied by, so the whole drawing inherits the grammar. The old path
  // eased a 6% snap down, which has no wind-up at all - and the wind-up is the
  // part that reads as animation.
  const act = toon ? actionCurve(since, 3, 6, 9) : 1;

  // Volume-preserving squash on arrival: he stretches through the travel and
  // squashes as he lands, then settles. Scaling both axes together (what the
  // 'cut' path does) reads as a picture being resized.
  const sq = toon ? squash((act - 1) * 0.085 * (0.5 + nrg)) : {sx: 1, sy: 1};

  // THE SNAP. Kept for 'cut'; under 'toon' the action curve does this job.
  const snap =
    poseOverride || toon
      ? 1
      : interpolate(since, [0, 7], [1.06, 1], {
          easing: EASE.settleBack,
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });

  // THE BREATH. Sub-percent, about the feet, so a held drawing is never a
  // frozen still. Seeded off the pose so two poses do not breathe in lockstep.
  const breath = poseOverride ? 0 : wiggle(frame, name.length, 0.006, 0.5);

  // THE DRIFT. Under 'toon' the hold is three sub-beats - arrive, small
  // secondary move, settle - instead of one 60-frame linear ease, which reads
  // as a slow zoom on a still.
  const d = poseOverride
    ? 0
    : toon
      ? holdCurve(since, Math.max(1, hold))
      : interpolate(since, [0, Math.max(1, hold)], [0, 1], {
          easing: EASE.cruise,
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
  // The travel carries the action curve, so a cut LAUNCHES rather than easing
  // away from where it was.
  const travel = toon ? d * Math.max(0, act) : d;
  const dx = (dr.dx ?? 0) * travel;
  const dy = (dr.dy ?? 0) * travel;
  const tilt = (dr.tilt ?? 0) * travel + (toon ? bob(frame, name.length, 0.35, 41) : 0);
  const driftScale = 1 + ((dr.dScale ?? 1) - 1) * travel;

  // BOIL - the 2-frame drawing vibration that makes a hold feel drawn. Scaled
  // with the character so it is the same visual amount at any size.
  const bl = toon ? boil(frame, name.length, height * 0.0016) : {x: 0, y: 0};
  // A slow vertical breath on top, so the quiet holds are never truly still.
  const by = toon ? bob(frame, name.length + 3, height * 0.004, 34) : 0;

  const s = scale * snap * driftScale * (1 + breath);
  const w = a.w * s;
  const h = a.h * s;
  // Place the drawing so its GROUND CONTACT lands exactly on (footX, footY).
  return {
    name,
    a,
    w,
    h,
    tilt,
    sq,
    sm,
    dx,
    dy,
    bx: bl.x,
    left: footX + dx + bl.x - a.anchor[0] * w,
    top: footY + dy + by + bl.y - a.anchor[1] * h,
  };
};

/**
 * Where the character's HEAD is, in the parent's coordinate space, plus how
 * wide it is so an effect can be sized to him rather than to the frame.
 *
 * The head moves further between these drawings than anything else does -
 * x=0.29 of the box in `stagger` against x=0.78 in `leans_a`, and most of the
 * body's height between `idle` and `crouch`. Anchoring an effect to a single
 * standing head position leaves it hanging in empty wall the moment he bends,
 * so the position per drawing is MEASURED by scripts/meme_reel/head_anchors.py
 * and read back here.
 */
export const poseHead = (
  args: LayoutArgs & {facing?: 'left' | 'right'}
): {x: number; y: number; w: number} | null => {
  const L = poseLayout(args);
  if (!L) return null;
  const hd = HEADS[L.name];
  if (!hd) return null;
  const [hx, hy] = hd.head;
  // facing="left" mirrors the drawing about the FOOT anchor, so the head
  // reflects across it too - a head drawn right-of-centre ends up left of him.
  const x =
    args.facing === 'left'
      ? L.left + (2 * L.a.anchor[0] - hx) * L.w
      : L.left + hx * L.w;
  return {x, y: L.top + hy * L.h, w: hd.head_w * L.w};
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
  motion = 'cut',
  energy = 1,
}) => {
  const current = useCurrentFrame();
  const frame = frameOverride ?? current;
  const L = poseLayout({frame, height, footX, footY, cuts, end, poseOverride, motion, energy});
  if (!L) return null;
  const {name, a, left, top, w, h, tilt, sq, sm, dx, dy, bx} = L;

  return (
    <>
      {shadow ? (
        <div
          style={{
            position: 'absolute',
            left: footX + dx + bx - height * 0.19,
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
          // Order matters. Everything pivots about the FEET, so a lean, a
          // squash or a smear never lifts him off the floor — same reason the
          // rig's squash pivoted about the pelvis. The smear's horizontal
          // stretch is applied in the drawing's own space (before the mirror),
          // so a left-facing character smears the way he is travelling.
          transform:
            `${facing === 'left' ? 'scaleX(-1) ' : ''}` +
            `rotate(${facing === 'left' ? -tilt : tilt}deg) ` +
            `scale(${sq.sx * sm.sx}, ${sq.sy * sm.sy})`,
          transformOrigin: `${a.anchor[0] * 100}% ${a.anchor[1] * 100}%`,
          filter: sm.blur > 0.05 ? `blur(${sm.blur.toFixed(2)}px)` : undefined,
          opacity: sm.opacity,
        }}
      />
    </>
  );
};
