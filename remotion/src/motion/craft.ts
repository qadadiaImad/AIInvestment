// craft.ts — the motion-craft library implementing
// references/animation-craft-playbook.md. This is our AE graph editor:
// house easing curves, frame-band timing, stagger choreography, the
// anticipation->action->settle grammar, smears, follow-through, and
// camera/parallax math. Every scene should build motion from these
// primitives instead of ad-hoc springs so the whole channel moves with one
// consistent hand.
import {Easing, interpolate, spring} from 'remotion';

// ---------------------------------------------------------------- easing
// House curves (playbook §2). Entrances decelerate, exits accelerate,
// nothing spatial is ever linear.
export const EASE = {
  /** MD3 Emphasized — every entrance. */
  enter: Easing.bezier(0.05, 0.7, 0.1, 1),
  /** MD3 Accelerate — every exit. */
  exit: Easing.bezier(0.3, 0, 1, 1),
  /** Canonical easeOutBack — bounce-settle without a spring. */
  settleBack: Easing.bezier(0.175, 0.885, 0.32, 1.275),
  /** Long drifts and camera moves. */
  cruise: Easing.bezier(0.4, 0, 0.2, 1),
};

// House spring configs (playbook §2): personality by damping/stiffness/mass.
export const SPRINGS = {
  /** UI chips, pills, cards. */
  pop: {damping: 12, stiffness: 170, mass: 0.6},
  /** Big numbers, hero elements. */
  hero: {damping: 10, stiffness: 130, mass: 0.7},
  /** Large slabs, charts — heavier, no jitter. */
  heavy: {damping: 14, stiffness: 90, mass: 1.1},
  /** Captions, small labels — quick, tight. */
  snappy: {damping: 16, stiffness: 220, mass: 0.5},
  /** Data landing confidently: overshoot clamped (premium 0%). */
  data: {damping: 18, stiffness: 120, mass: 1, overshootClamping: true as const},
};

// ---------------------------------------------------------------- timing
// Frame bands at 30fps (playbook §3).
export const FRAMES = {
  micro: 3,
  card: 8,
  modal: 10,
  transition: 14,
  reveal: 24,
  fadeBeat: 20,
  counter: 60,
  highlight: 15,
};

/** Exits run at ~70% of the matching entrance duration. */
export const exitFrames = (enterFrames: number) => Math.round(enterFrames * 0.7);

/**
 * Stagger choreography (playbook §3): per-item delay by flavor, with the
 * TOTAL clamped to <=15f — per-item delay shrinks as count grows.
 */
export const stagger = (
  index: number,
  count: number,
  flavor: 'micro' | 'standard' | 'dramatic' | 'wave' = 'standard',
): number => {
  const per = {micro: 1, standard: 2.5, dramatic: 5, wave: 1.5}[flavor];
  const total = per * Math.max(0, count - 1);
  const scale = total > 15 ? 15 / total : 1;
  return Math.round(index * per * scale);
};

// ------------------------------------------------- entrance/exit recipes
type Frame = number;
type Fps = number;

/**
 * Standard entrance: spring progress 0..1 with house personality.
 * Usage: const p = enterSpring(frame, fps, delay, 'pop');
 * opacity: Math.min(1, p * 1.4); translate/scale from p.
 */
export const enterSpring = (
  frame: Frame,
  fps: Fps,
  delay = 0,
  personality: keyof typeof SPRINGS = 'pop',
): number => spring({frame: frame - delay, fps, config: SPRINGS[personality]});

/**
 * The full anticipation -> action -> settle grammar (playbook §4) as a
 * single scalar: returns scale-like value that dips to `anticipation`
 * (default 0.97) for ~2f, springs up with overshoot, settles to 1.
 */
export const anticipatePop = (
  frame: Frame,
  fps: Fps,
  delay = 0,
  {anticipation = 0.97, personality = 'pop' as keyof typeof SPRINGS} = {},
): number => {
  const f = frame - delay;
  if (f <= 2) return anticipation; // 2-frame counter-move dip
  // spring overshoots past 1 on its own -> scale briefly exceeds 1, then settles
  const p = spring({frame: f - 2, fps, config: SPRINGS[personality]});
  return anticipation + (1 - anticipation) * p;
};

/** Entrance opacity from a spring progress — reaches 1 early so the motion
 * finishes visible. */
export const fadeOf = (p: number) => Math.min(1, p * 1.4);

/** Standard exit progress: 0 (visible) -> 1 (gone), accelerating. */
export const exitProgress = (frame: Frame, start: Frame, durInFrames: number): number =>
  interpolate(frame, [start, start + durInFrames], [0, 1], {
    easing: EASE.exit,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

// ------------------------------------------------------ polish helpers
/**
 * Smear (playbook §5): given per-frame velocity in px, returns the stretch
 * factor along the motion vector. >20px/f engages, capped at 1.6, meant for
 * 1-2 frame bursts.
 */
export const smearScale = (velocityPxPerFrame: number): number => {
  const v = Math.abs(velocityPxPerFrame);
  if (v < 20) return 1;
  return Math.min(1.6, 1 + (v - 20) / 60);
};

/**
 * Follow-through (playbook §5): appendages lag the driver by `lagFrames`
 * and keep moving after it stops. Call with a function that evaluates the
 * driver value at an arbitrary frame.
 */
export const followThrough = (
  driverAt: (frame: number) => number,
  frame: Frame,
  lagFrames = 3,
  overshootGain = 1.25,
): number => {
  // the appendage tracks a delayed copy of the driver, plus amplified
  // momentum so it keeps traveling after the driver stops
  const lagged = driverAt(frame - lagFrames);
  const momentum = (lagged - driverAt(frame - lagFrames - 1)) * (overshootGain - 1) * 4;
  return lagged + momentum;
};

/**
 * Ambient wiggle — the code analog of AE's wiggle(): layered
 * incommensurate sines, deterministic per seed. Amplitude in px.
 */
export const wiggle = (frame: Frame, seed = 0, amp = 3, speed = 1): number => {
  const t = (frame + seed * 37.7) * speed;
  return (Math.sin(t / 17) * 0.55 + Math.sin(t / 7.3 + 1.7) * 0.3 + Math.sin(t / 2.9 + 4.1) * 0.15) * amp;
};

// ------------------------------------------------------ camera & depth
/**
 * Camera intention (playbook §5): ONE per scene. Returns the scale for a
 * slow push-in across the whole scene (default 3%), optionally with a fast
 * emphasis hit at `hitFrame` (+8% over 5f, settling back to the cruise).
 */
export const cameraPushIn = (
  frame: Frame,
  sceneDurationInFrames: number,
  {base = 0.03, hitFrame, hitAmount = 0.08}: {base?: number; hitFrame?: number; hitAmount?: number} = {},
): number => {
  const cruise = interpolate(frame, [0, sceneDurationInFrames], [1, 1 + base], {
    easing: EASE.cruise,
    extrapolateRight: 'clamp',
  });
  if (hitFrame === undefined || frame < hitFrame) return cruise;
  const hit = interpolate(frame, [hitFrame, hitFrame + 5, hitFrame + 30], [0, hitAmount, hitAmount * 0.55], {
    easing: EASE.enter,
    extrapolateRight: 'clamp',
  });
  return cruise + hit;
};

/** Parallax depth factors (fake 3D): multiply any camera delta by these. */
export const DEPTH = {bg: 0.3, mid: 0.6, fg: 1};

/**
 * Parallax offset for a layer: given the camera's translate delta (px) and
 * the layer's depth, the layer's own translate.
 */
export const parallax = (cameraDeltaPx: number, depth: keyof typeof DEPTH): number =>
  cameraDeltaPx * DEPTH[depth];
