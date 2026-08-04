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

/**
 * TEMPERAMENT. Two characters should not move the same way.
 *
 * A two-hander's cast needs distinct PHYSICAL vocabularies, not just
 * distinct lines — otherwise the same recoil-and-lean grammar plays on a
 * seventy-year-old veteran and an over-eager junior and they read as one
 * puppet wearing two costumes. Sol is economical: he arrives slower,
 * undershoots the recoil, settles once. Rex is jumpy: faster in,
 * overshoots, takes an extra beat to stop wobbling.
 *
 * Applied automatically from which character the drawing is, so no beat
 * data has to carry it.
 */
export type Temper = 'calm' | 'eager';

const TEMPER: Record<Temper, {
  amp: number; recoil: number; anticipation: number; action: number; settle: number;
}> = {
  calm:  {amp: 0.82, recoil: 0.70, anticipation: 5, action: 11, settle: 14},
  eager: {amp: 1.16, recoil: 1.25, anticipation: 3, action: 7,  settle: 9},
};

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
export const moveXform = (m: Move, since: number,
                          temper: Temper = 'eager'): Xform => {
  const T = TEMPER[temper];
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

  const p = actionCurve(t, T.anticipation, T.action + 2, T.settle);
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
  turn: Turn, since: number, fromX: number, fromY: number,
  temper: Temper = 'eager'
): Xform => {
  const t = since - turn.at;
  if (t < 0) return NO_XFORM;
  const T = TEMPER[temper];
  // No upper bound: once he has turned he STAYS turned. Snapping the
  // lean away after a fixed window undoes the whole point — the head
  // would whip round and then drift back as if nothing had happened.
  const p = actionCurve(t, T.anticipation - 1, T.action - 1, T.settle);
  const vx = turn.tx - fromX, vy = turn.ty - fromY;
  const len = Math.max(1, Math.hypot(vx, vy));
  const ux = vx / len, uy = vy / len;
  const sm = smear(t - 4, 1.3, 3);
  // A STARTLE on top of the turn: a short shove back AWAY from whatever
  // just appeared, decaying out. Turning toward a thing is "he looked";
  // recoiling first and then turning is "he was surprised by it", which
  // is the beat when someone pops into the room uninvited.
  const recoil = impact(t - 3, 15) * -22 * T.recoil;
  // FORESHORTENING. A body rotating away from camera gets narrower, and
  // that width change is most of what sells a turn — lean and tilt alone
  // read as leaning, not turning. The squeeze peaks with the whip and
  // eases back to about 96%, so the settled pose is fractionally turned
  // rather than snapping back to a flat front-on width. Vertical scale
  // rises to hold volume, the same rule squash() enforces.
  const shorten = interpolate(t, [0, 5, 11, 22], [1, 0.86, 0.94, 0.96], {
    easing: EASE.cruise, extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  return {
    // Amplitudes are deliberately large. With no drawn head-turn frames
    // the whole read has to come from the body's lean, the tilt and the
    // smear; at 7deg it was invisible on screen.
    dx: ux * (56 * T.amp * p + recoil), dy: uy * (26 * T.amp * p + recoil * 0.4),
    sx: sm.sx * shorten, sy: sm.sy * (1 + (1 - shorten) * 0.55),
    rot: ux * (12 * T.amp * p + recoil * 0.18),
    opacity: sm.opacity, blur: sm.blur,
  };
};

/**
 * IDLE. What a held drawing does when nothing is happening.
 *
 * `boil` was doing this job and it is the wrong tool here: it is a
 * 2-frame random offset, which on a large clean vector figure does not
 * read as hand-drawn media, it reads as the picture VIBRATING. Owner's
 * note exactly. A body at rest instead has a slow breath — chest rises,
 * a little vertical scale, volume preserved — and an even slower weight
 * shift from foot to foot. Both are continuous sinusoids at frequencies
 * far below the flicker threshold, seeded per character so two figures
 * never breathe in lockstep.
 *
 * Amplitudes are in fractions of the figure's height, so a close-up and
 * a wide shot breathe by the same visible amount.
 */
export const idle = (frame: number, seed: number, h: number,
                     temper: Temper = 'calm'): Xform => {
  const p = seed * 7.13;
  // TEMPER APPLIES HERE TOO. This used to be one curve for everybody, so
  // the old man and the over-eager junior stood still in exactly the same
  // way — which is half of why Rex read as the less alive of the two even
  // on beats where his mouth WAS articulating. An eager kid breathes
  // faster, shifts weight more often and can't keep his shoulders
  // still; a veteran is economical.
  const t = temper === 'eager'
    ? {breath: 17.4, sway: 44.0, amp: 1.55, rot: 1.7, bob: 1.45}
    : {breath: 21.2, sway: 61.0, amp: 1.00, rot: 1.0, bob: 1.00};
  const breath = Math.sin((frame + p) / t.breath);
  const sway = Math.sin((frame + p * 1.7) / t.sway);
  // a second, slower sway on the eager curve so the motion doesn't read
  // as one clean sine — a metronome is as dead as a freeze, just busier
  const drift = temper === 'eager'
    ? Math.sin((frame + p * 2.9) / 97.0) * 0.45 : 0;
  const rise = 1 + breath * 0.0055 * t.bob;
  return {
    dx: (sway + drift) * h * 0.004 * t.amp,
    dy: -breath * h * 0.0022 * t.bob,
    sx: 1 / rise,               // volume preserving, as squash() requires
    sy: rise,
    rot: (sway + drift * 0.6) * 0.28 * t.rot,
    opacity: 1, blur: 0,
  };
};

/** Fold every move + turn active on this frame into one transform. */
export const interactXform = (
  since: number,
  moves: Move[] | undefined,
  turns: Turn[] | undefined,
  headX: number,
  headY: number,
  temper: Temper = 'eager'
): Xform => {
  let out = NO_XFORM;
  for (const m of moves ?? []) out = compose(out, moveXform(m, since, temper));
  for (const tn of turns ?? []) {
    out = compose(out, turnXform(tn, since, headX, headY, temper));
  }
  return out;
};
