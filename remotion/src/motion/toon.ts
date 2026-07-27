// toon.ts — the cartoon-animation grammar, as maths.
//
// WHY THIS EXISTS. The first cut of the pose-cut character read as a
// slideshow: hold a drawing for two seconds, cut, hold the next. That is
// technically limited animation and it is not what limited animation looks
// like. What was missing is not more drawings — it is everything that happens
// AROUND a drawing:
//
//   * a pose winds up before it moves (anticipation),
//   * it overshoots its target and settles back (follow-through),
//   * it squashes and stretches while it travels, preserving volume,
//   * the frame between two poses is a SMEAR, not a cut,
//   * and a held drawing is never actually held — it breathes, drifts, and
//     settles in three sub-beats rather than drifting linearly for 60 frames.
//
// Every function here is deterministic in `frame`, so a render is
// reproducible, and none of them know anything about the chart or the story —
// they are the vocabulary, and the composition writes the sentences.
//
// The load-bearing idea is VOLUME PRESERVATION. A cartoon body that scales up
// on one axis must scale down on the other, or it reads as a picture being
// resized rather than as a body absorbing a force. `squash()` returns the pair
// and guarantees sx*sy ~= 1, which is the single difference between "animated"
// and "zoomed".
import {Easing, interpolate} from 'remotion';
import {EASE} from './craft';

export type SquashPair = {sx: number; sy: number};

/**
 * Volume-preserving squash/stretch.
 *
 * `amount` > 0 stretches vertically (and narrows horizontally) — a body
 * launching, a take reaching up. `amount` < 0 squashes vertically (and widens)
 * — a landing, an impact, a slump.
 *
 * The inverse is exact rather than approximated because a body that gains area
 * while it deforms reads as a balloon inflating, which is a different (and
 * usually wrong) character note.
 */
export const squash = (amount: number): SquashPair => {
  const sy = 1 + amount;
  return {sx: 1 / sy, sy};
};

/**
 * The three-part cut: ANTICIPATION -> ACTION -> SETTLE, as a single 0..1
 * "action progress" that dips negative before it rises.
 *
 * Returned in the range about -0.18 .. 1.06:
 *   frames 0..a      wind up the OPPOSITE way (this is the part everyone skips)
 *   frames a..a+b    travel, fast
 *   frames a+b..end  overshoot ~6% and settle
 *
 * Multiply any channel by this — position, tilt, scale — and that channel
 * inherits the grammar for free.
 */
export const actionCurve = (since: number, anticipation = 4, action = 7, settle = 9): number => {
  if (since < 0) return 0;
  if (since < anticipation) {
    // A quick dip against the direction of travel, easing OUT so the wind-up
    // decelerates into the release — a linear wind-up reads mechanical.
    return interpolate(since, [0, anticipation], [0, -0.18], {
      easing: EASE.exit,
      extrapolateRight: 'clamp',
    });
  }
  if (since < anticipation + action) {
    return interpolate(since, [anticipation, anticipation + action], [-0.18, 1.06], {
      easing: Easing.bezier(0.2, 0.85, 0.4, 1),
      extrapolateRight: 'clamp',
    });
  }
  return interpolate(since, [anticipation + action, anticipation + action + settle], [1.06, 1], {
    easing: EASE.settleBack,
    extrapolateRight: 'clamp',
  });
};

/**
 * The SMEAR. On the two frames either side of a cut, a cartoon does not draw
 * the character — it draws the blur of the character getting there. Returns a
 * horizontal stretch, a vertical pinch and an opacity, all 1/1/1 outside the
 * smear window so it costs nothing when it is not firing.
 *
 * `strength` is normally the size of the change being covered: a cut from idle
 * to shock smears hard, a cut from idle to turning barely smears at all.
 * Feeding it a constant is the giveaway that a smear was bolted on rather than
 * derived from the motion.
 */
export const smear = (
  since: number,
  strength = 1,
  frames = 2
): {sx: number; sy: number; blur: number; opacity: number} => {
  if (since < 0 || since >= frames) return {sx: 1, sy: 1, blur: 0, opacity: 1};
  const t = 1 - since / frames; // 1 on the cut frame, decaying
  const k = Math.max(0, Math.min(1.6, strength)) * t;
  return {
    sx: 1 + k * 0.42,
    sy: 1 - k * 0.16,
    blur: k * 7,
    // Never fully transparent: a smear is a fast drawing, not a ghost.
    opacity: 1 - k * 0.28,
  };
};

/**
 * How big a change a given cut is, 0..1.6 — used to drive `smear` so the
 * smear is a consequence of the motion rather than a decoration on it.
 * Distance is in whatever units the caller uses (px of drift, degrees of tilt,
 * change in silhouette width), normalised by `full`.
 */
export const cutEnergy = (distance: number, full = 260): number =>
  Math.max(0, Math.min(1.6, Math.abs(distance) / full));

/**
 * A held pose in three sub-beats instead of one linear drift.
 *
 * A 60-frame hold that eases from A to B across all 60 frames reads as a slow
 * zoom on a still. Real held poses ARRIVE (fast), then have a small secondary
 * MOVE partway through — a weight shift, a head turn — and then SETTLE. This
 * returns 0..1 with that shape, so `drift * holdCurve(...)` is alive without
 * any extra drawings.
 */
export const holdCurve = (since: number, hold: number): number => {
  const a = Math.min(14, hold * 0.28); // arrival
  const m = hold * 0.62; // the secondary move lands here
  if (since <= a) {
    return interpolate(since, [0, a], [0, 0.72], {easing: EASE.enter, extrapolateRight: 'clamp'});
  }
  if (since <= m) {
    // a slight recoil off the arrival — this is the beat that reads as breath
    return interpolate(since, [a, m], [0.72, 0.62], {easing: EASE.cruise, extrapolateRight: 'clamp'});
  }
  return interpolate(since, [m, hold], [0.62, 1], {easing: EASE.cruise, extrapolateRight: 'clamp'});
};

/**
 * A 2-frame vertical bob at `bpm`-ish rate, phase-locked to the frame so two
 * characters (or two holds) never breathe in lockstep. Amplitude in px.
 */
export const bob = (frame: number, seed: number, amp: number, period: number): number =>
  Math.sin((frame + seed * 13.13) / period) * amp;

/**
 * BOIL. Two-frame drawing vibration, the thing that makes a hand-drawn hold
 * feel drawn rather than photographed. Deliberately quantised to 2s (the same
 * drawing held for two frames) rather than continuous — a continuous jitter
 * reads as a rendering fault, a 2-frame boil reads as animation.
 */
export const boil = (frame: number, seed: number, amp = 1.2): {x: number; y: number} => {
  const s = Math.floor(frame / 2) + seed * 7;
  return {
    x: (((s * 9301 + 49297) % 233280) / 233280 - 0.5) * 2 * amp,
    y: (((s * 4177 + 10151) % 233280) / 233280 - 0.5) * 2 * amp,
  };
};

/**
 * IMPACT. A decaying oscillation for hits — the shock take, the camera kick,
 * a slam. Returns roughly +/-1, dying over `dur` frames. Frequency is high at
 * the start and drops, which is what a real impact does and what a plain
 * `sin * decay` does not.
 */
export const impact = (since: number, dur = 18): number => {
  if (since < 0 || since > dur) return 0;
  const t = since / dur;
  const decay = Math.pow(1 - t, 2.1);
  return Math.sin(since * (1.5 - t * 0.75)) * decay;
};

/**
 * A whip-pan's motion blur, as a 0..1 intensity. Feed it the camera's
 * per-frame travel in composition px; it engages only above a threshold so
 * ordinary drifts stay crisp.
 */
export const whip = (pxPerFrame: number, threshold = 90, full = 900): number =>
  Math.max(0, Math.min(1, (Math.abs(pxPerFrame) - threshold) / (full - threshold)));
