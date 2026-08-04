// interact.ts — the grammar for two characters sharing a space.
//
// WHY THIS EXISTS. toon.ts animates a drawing; nothing animated the
// RELATIONSHIP between two drawings. Sol and Rex were each staged as an
// independent picture that happened to be on screen at the same time:
// no consistent sides, no eyelines, no arrivals — a character simply
// existed or did not, by a cut. The owner's note: "instead of putting
// each one image unrelated to other", they should speak to each other,
// leave, arrive somewhere else, and be LOOKED at when they do.
//
// Three primitives cover almost all of that:
//
//   * a STAGE, so left is always left and the eyeline geometry holds,
//   * MOVES, so a character arrives and leaves under cartoon physics
//     (wind up, travel fast, overshoot, settle) rather than appearing,
//   * a TURN, so the other character's head follows them when they do.
//
// Everything is deterministic in `frame` and composes with the shot
// reframing, so a punch-in during an entrance still reads correctly.
import {interpolate} from 'remotion';
import {EASE} from './craft';
import {actionCurve, cutEnergy, impact, smear} from './toon';

export const STAGE_W = 1080;
export const STAGE_H = 1920;

/** Where a character lives on the stage. Keeping each character on a
 * fixed side is what makes two drawings read as one room: the audience
 * builds the geometry once and every later cut reuses it. Crossing the
 * line is then a deliberate event rather than an accident. */
export type Side = 'L' | 'R';
export const SIDE_X: Record<Side, number> = {L: 300, R: 790};

export type MoveKind =
  | 'inL' | 'inR' | 'inT' | 'inB' | 'pop'
  | 'outL' | 'outR' | 'outT' | 'outB' | 'vanish';

/** A character arriving or leaving. `at` is a frame offset inside the beat. */
export type Move = {at: number; kind: MoveKind};

/** A head/body turn toward a direction, in stage coordinates. `tx`/`ty`
 * is the point being looked at; the character leans and rotates toward
 * it with a smear on the fast part. */
export type Turn = {at: number; tx: number; ty: number};

export type Xform = {
  dx: number; dy: number;
  sx: number; sy: number;
  rot: number;
  opacity: number;
  blur: number;
};

export const NO_XFORM: Xform = {dx: 0, dy: 0, sx: 1, sy: 1, rot: 0, opacity: 1, blur: 0};

const TRAVEL: Record<string, [number, number]> = {
  L: [-STAGE_W * 0.85, 0],
  R: [STAGE_W * 0.85, 0],
  T: [0, -STAGE_H * 0.7],
  B: [0, STAGE_H * 0.7],
};

const compose = (a: Xform, b: Xform): Xform => ({
  dx: a.dx + b.dx, dy: a.dy + b.dy,
  sx: a.sx * b.sx, sy: a.sy * b.sy,
  rot: a.rot + b.rot,
  opacity: a.opacity * b.opacity,
  blur: Math.max(a.blur, b.blur),
});

/**
 * One move's contribution. Entrances run the action curve BACKWARDS onto
 * the offset — the character is off stage at p=0 and home at p=1 — so
 * they inherit the wind-up and the overshoot for free: an entrance that
 * merely slides in at constant speed is the thing that reads as a
 * PowerPoint transition.
 *
 * `pop`/`vanish` are the spatially-teleporting pair the owner asked for:
 * a squash-and-burst rather than a slide, because a character appearing
 * somewhere they were not needs to look like an event, not a fade.
 */
export const moveXform = (m: Move, since: number): Xform => {
  const t = since - m.at;
  const isOut = m.kind.startsWith('out') || m.kind === 'vanish';
  const dir = m.kind.replace(/^(in|out)/, '');
  const travel = TRAVEL[dir] ?? [0, 0];

  if (m.kind === 'pop' || m.kind === 'vanish') {
    // 0 -> 1 over 12 frames; a pop lands hard and rebounds, a vanish
    // stretches up and blinks out.
    const p = interpolate(t, [0, 12], [0, 1], {
      easing: EASE.exit, extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    });
    const k = m.kind === 'pop' ? p : 1 - p;
    if (m.kind === 'pop' && t < 0) return {...NO_XFORM, opacity: 0, sx: 0.2, sy: 0.2};
    if (m.kind === 'vanish' && t > 12) return {...NO_XFORM, opacity: 0, sx: 0.2, sy: 0.2};
    // overshoot on the way in: 1.18 then settle
    const bounce = m.kind === 'pop' ? 1 + 0.22 * impact(t, 16) : 1;
    const s = (0.2 + 0.8 * k) * bounce;
    return {
      dx: 0, dy: (1 - k) * 40 * (m.kind === 'pop' ? 1 : -1),
      sx: s * (m.kind === 'vanish' ? 1 - 0.5 * (1 - k) : 1),
      sy: s * (m.kind === 'vanish' ? 1 + 0.6 * (1 - k) : 1),
      rot: 0, opacity: Math.min(1, k * 1.8), blur: 0,
    };
  }

  const p = actionCurve(t, 4, 9, 11);
  const q = isOut ? p : 1 - p;                 // 1 = off stage, 0 = home
  const sm = smear(t - 4, cutEnergy(Math.abs(travel[0]) + Math.abs(travel[1]), 900), 3);
  if (!isOut && t < 0) return {...NO_XFORM, dx: travel[0], dy: travel[1], opacity: 0};
  if (isOut && t > 24) return {...NO_XFORM, dx: travel[0], dy: travel[1], opacity: 0};
  return {
    dx: travel[0] * q, dy: travel[1] * q,
    sx: sm.sx, sy: sm.sy, rot: 0,
    // Fade only across the last sliver of travel; a character that
    // dissolves while still on stage reads as a ghost, not an exit.
    opacity: Math.min(1, (1 - Math.max(0, q - 0.75) / 0.25)) * sm.opacity,
    blur: sm.blur,
  };
};

/**
 * The TURN. A drawn head turn needs new artwork; what sells it on a
 * static drawing is the motion around it — wind up the opposite way,
 * whip across with a smear, overshoot, settle — plus a lean and a tilt
 * toward the target. Two frames of that reads as "he looked", which is
 * all this beat needs.
 *
 * `from` is the character's own head position, so the lean is toward the
 * target rather than a fixed direction.
 */
export const turnXform = (
  turn: Turn, since: number, fromX: number, fromY: number
): Xform => {
  const t = since - turn.at;
  if (t < 0) return NO_XFORM;
  // No upper bound: once he has turned he STAYS turned. Snapping the
  // lean away after a fixed window undoes the whole point — the head
  // would whip round and then drift back as if nothing had happened.
  const p = actionCurve(t, 4, 6, 10);
  const vx = turn.tx - fromX, vy = turn.ty - fromY;
  const len = Math.max(1, Math.hypot(vx, vy));
  const ux = vx / len, uy = vy / len;
  const sm = smear(t - 4, 1.3, 3);
  return {
    // Amplitudes are deliberately large. With no drawn head-turn frames
    // the whole read has to come from the body's lean, the tilt and the
    // smear; at 7deg it was invisible on screen.
    dx: ux * 56 * p, dy: uy * 26 * p,
    sx: sm.sx, sy: sm.sy,
    rot: ux * 12 * p,
    opacity: sm.opacity, blur: sm.blur,
  };
};

/** Fold every move + turn active on this frame into one transform. */
export const interactXform = (
  since: number,
  moves: Move[] | undefined,
  turns: Turn[] | undefined,
  headX: number,
  headY: number
): Xform => {
  let out = NO_XFORM;
  for (const m of moves ?? []) out = compose(out, moveXform(m, since));
  for (const tn of turns ?? []) out = compose(out, turnXform(tn, since, headX, headY));
  return out;
};
