// wattRig.tsx — Watt as a COMPLETE rigged character: parameterized rotation
// (full 360° turnaround with faux-3D side extrusion), limbs, and a move set
// (idle / walk / wave / point / jump / turn / special). Mirrors chipRig.tsx's
// architecture exactly — a pure computePose(frame, mode) function feeding a
// single SVG tree — so the two rigs drop into the same registry.
//
// Body: the chunky rounded lightning-bolt silhouette from family.tsx
// (gradient #F2C05C → C.amber, #c9821f stroke), kept as a single static path
// that is horizontally squished about its center to fake the turn rotation
// (same trick chipRig uses on its body rect). Legs tuck in close under the
// bolt's lower point and stay short so the tail still reads as a bolt tip,
// not a torso. Signature move: ZIP — an anticipation lean-back, an explosive
// ~40px horizontal dash with trailing amber motion streaks and spark
// pulses, then a damped overshoot wobble before it settles.
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C} from '../slides/theme';

export type RigMode = 'idle' | 'walk' | 'wave' | 'point' | 'jump' | 'turn' | 'special';

const AMBER_LIGHT = '#F2C05C';
const AMBER_DEEP = C.amber; // #E0A23B
const AMBER_STROKE = '#c9821f';
const AMBER_SIDE = '#a8650f';
const GOLD_CUFF = '#caa64a';
const INKFACE = '#10141c';

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

// Static bolt silhouette, centered on x=120, spanning y=60..194 — the same
// chunky zigzag as WattChar in family.tsx, rescaled to leave headroom below
// for legs/boots before the y=214 ground line.
const BOLT_W0 = 82;
const BOLT_PATH =
  'M100,66 Q96,60 105,60 L152,60 Q161,60 157,67 L135,110 L151,110 Q159,110 153,117 L93,187 Q86,194 83,186 Q81,183 83,179 L103,134 L88,134 Q79,134 83,127 Z';

/** All pose state the SVG needs, derived per-frame by the mode logic. */
type Pose = {
  theta: number; // rotation around vertical axis, radians (0 = facing camera)
  bob: number; // vertical idle offset
  lift: number; // jump height (positive = up)
  squash: number; // 1 = neutral; <1 squashed, >1 stretched (about the ground)
  lean: number; // lean degrees
  jitter: number; // tiny crackling twitch added on top of lean, every mode
  legL: number; // leg swing degrees
  legR: number;
  armL: number; // arm swing degrees relative to hanging
  armR: number;
  wave: boolean; // right arm in wave position
  point: boolean; // right arm extended pointing
  blink: number;
  dashX: number; // ZIP horizontal displacement
  streak: number; // ZIP motion-streak / spark-burst intensity, 0..1
};

const computeWattPose = (frame: number, mode: RigMode): Pose => {
  // phase-shifted so Watt never blinks in sync with the rest of the family
  const blinkT = (frame + 31) % 120;
  const blink = blinkT < 4 ? 0.12 : blinkT < 8 ? 1 - Math.abs(6 - blinkT) * 0.22 : 1;
  const idleBob = Math.sin(frame / 18) * 5;
  // small always-on crackle — quick, jittery, never fully still
  const jitter = Math.sin(frame * 1.3) * 0.5 + Math.sin(frame * 2.7) * 0.35;

  const base: Pose = {
    theta: 0,
    bob: idleBob,
    lift: 0,
    squash: 1,
    lean: 0,
    jitter,
    legL: 0,
    legR: 0,
    armL: Math.sin(frame / 18) * 5,
    armR: -Math.sin(frame / 18) * 5,
    wave: false,
    point: false,
    blink,
    dashX: 0,
    streak: 0,
  };

  switch (mode) {
    case 'idle':
      return base;
    case 'turn':
      // one full revolution every 240 frames
      return {...base, theta: ((frame % 240) / 240) * Math.PI * 2, bob: Math.sin(frame / 20) * 3};
    case 'walk': {
      const swing = Math.sin(frame / 5.5) * 20;
      return {
        ...base,
        theta: 0.3,
        bob: Math.abs(Math.sin(frame / 5.5)) * -5,
        lean: 4,
        legL: swing,
        legR: -swing,
        armL: -swing * 0.7,
        armR: swing * 0.7,
      };
    }
    case 'wave': {
      return {...base, wave: true, armR: Math.sin(frame / 6) * 28};
    }
    case 'point': {
      return {...base, theta: 0.25, point: true, armL: 2};
    }
    case 'jump': {
      // 90-frame loop: crouch → launch → hang → land → settle
      const t = frame % 90;
      let lift = 0;
      let squash = 1;
      if (t < 18) {
        squash = 1 - (t / 18) * 0.16; // anticipation crouch
      } else if (t < 24) {
        squash = 0.84 + ((t - 18) / 6) * 0.34; // launch stretch to 1.18
        lift = ((t - 18) / 6) * 24;
      } else if (t < 58) {
        const u = (t - 24) / 34; // parabolic flight
        lift = 24 + 58 * (1 - (2 * u - 1) * (2 * u - 1));
        squash = 1.12 - u * 0.12;
      } else if (t < 66) {
        lift = Math.max(0, 24 * (1 - (t - 58) / 4));
        squash = 0.82; // landing squash
      } else {
        squash = 0.82 + clamp01((t - 66) / 12) * 0.18;
      }
      const armUp = t >= 18 && t < 62 ? -150 : 0;
      return {...base, lift, squash, armL: armUp ? -armUp : 4, armR: armUp, bob: 0};
    }
    case 'special': {
      // ZIP — 70-frame loop: anticipation lean-back → explosive dash →
      // damped overshoot wobble → ease back to rest.
      const t = frame % 70;
      let dashX = 0;
      let lean = 0;
      let squash = 1;
      let streak = 0;
      let legL = 0;
      let legR = 0;
      let armL = base.armL;
      let armR = base.armR;
      if (t < 14) {
        // anticipation: coil back before the shot
        const u = t / 14;
        lean = -10 * u;
        squash = 1 - 0.08 * u;
        legL = 6 * u;
        legR = 6 * u;
        armL = -6 * u;
        armR = -6 * u;
      } else if (t < 24) {
        // the dash itself — fast ease-out shot sideways
        const u = (t - 14) / 10;
        const ease = 1 - Math.pow(1 - u, 3);
        dashX = 40 * ease;
        lean = 6 * (1 - u);
        squash = 1 + 0.06 * (1 - u);
        legL = 6 - 24 * u;
        legR = 6 - 18 * u;
        armL = -6 - 14 * u;
        armR = -6 - 14 * u;
        streak = clamp01(u * 3);
      } else if (t < 34) {
        // damped overshoot wobble on the stop
        const u = (t - 24) / 10;
        const decay = 1 - u;
        const wobble = Math.sin(u * Math.PI * 2.5) * 10 * decay;
        dashX = 40 + wobble;
        lean = wobble * 0.4;
        squash = 1 + Math.sin(u * Math.PI * 2.5) * 0.03 * decay;
        legL = -18 * decay;
        legR = -12 * decay;
        armL = -20 * decay;
        armR = -20 * decay;
        streak = clamp01(decay * 0.8);
      } else {
        // ease back to rest so the loop closes cleanly
        const u = clamp01((t - 34) / 36);
        const ease2 = 1 - Math.pow(1 - u, 3);
        dashX = 40 * (1 - ease2);
      }
      return {...base, dashX, lean, squash, legL, legR, armL, armR, streak};
    }
  }
};

const Eye: React.FC<{cx: number; cy: number; rx: number; blink: number; look: number}> = ({cx, cy, rx, blink, look}) => (
  <g transform={`translate(${cx} ${cy}) scale(1 ${blink})`}>
    <ellipse cx="0" cy="0" rx={rx} ry={rx * 1.17} fill="#FDFEFF" />
    <circle cx={look} cy="2.5" r={rx * 0.44} fill={INKFACE} />
    <circle cx={look + rx * 0.15} cy="0.2" r={rx * 0.14} fill="#FDFEFF" opacity="0.9" />
  </g>
);

const Smile: React.FC<{x: number; y: number; w?: number}> = ({x, y, w = 24}) => (
  <path d={`M${x - w / 2},${y} Q${x},${y + 11} ${x + w / 2},${y}`} fill="none" stroke={INKFACE} strokeWidth="4.5" strokeLinecap="round" />
);

/** Brawlhalla-proportioned mitt: an oversized rounded hand with finger
 * seams, a thumb, and a gold wrist cuff. Drawn pointing DOWN in local
 * space; rotate the parent to aim it. `grip`: 'mitt' (closed), 'open'
 * (fingers splayed), 'point' (index out). */
const Mitt: React.FC<{x: number; y: number; grip?: 'mitt' | 'open' | 'point'; flip?: boolean}> = ({x, y, grip = 'mitt', flip = false}) => (
  <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
    {/* cuff */}
    <rect x="-13" y="-8" width="26" height="12" rx="5" fill={GOLD_CUFF} />
    {grip === 'point' ? (
      <>
        <path d="M-12,2 Q-16,20 -4,24 Q10,27 14,16 Q16,10 12,4 Z" fill={AMBER_DEEP} stroke={AMBER_STROKE} strokeWidth="3.5" strokeLinejoin="round" />
        <rect x="6" y="10" width="22" height="11" rx="5.5" fill={AMBER_DEEP} stroke={AMBER_STROKE} strokeWidth="3.5" />
      </>
    ) : grip === 'open' ? (
      <>
        <path d="M-14,0 Q-20,18 -8,25 Q4,30 14,22 Q20,16 16,4 Z" fill={AMBER_DEEP} stroke={AMBER_STROKE} strokeWidth="3.5" strokeLinejoin="round" />
        <circle cx="-10" cy="24" r="6" fill={AMBER_DEEP} stroke={AMBER_STROKE} strokeWidth="3" />
        <circle cx="2" cy="28" r="6" fill={AMBER_DEEP} stroke={AMBER_STROKE} strokeWidth="3" />
        <circle cx="13" cy="23" r="6" fill={AMBER_DEEP} stroke={AMBER_STROKE} strokeWidth="3" />
      </>
    ) : (
      <>
        <path d="M-13,0 Q-18,16 -8,23 Q2,29 12,23 Q19,17 14,2 Z" fill={AMBER_DEEP} stroke={AMBER_STROKE} strokeWidth="3.5" strokeLinejoin="round" />
        {/* finger seams */}
        <path d="M-2,6 L-2,22 M7,5 L8,19" stroke={AMBER_STROKE} strokeWidth="2.5" strokeLinecap="round" fill="none" opacity="0.7" />
        {/* thumb */}
        <ellipse cx="-13" cy="10" rx="6" ry="8" fill={AMBER_DEEP} stroke={AMBER_STROKE} strokeWidth="3" />
      </>
    )}
  </g>
);

/** Chunky sneaker-boot: big rounded toe, heel, dark contrasting sole. */
const Boot: React.FC<{x: number; y: number; flip?: boolean}> = ({x, y, flip = false}) => (
  <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
    <path d="M-11,-6 L-11,8 Q-11,14 -4,15 L18,15 Q26,15 25,7 Q24,0 16,-1 L9,-2 L9,-6 Q9,-11 -1,-11 Q-11,-11 -11,-6 Z" fill={AMBER_DEEP} stroke={AMBER_STROKE} strokeWidth="3" strokeLinejoin="round" />
    <path d="M-11,12 L25,12 L25,10 Q26,15 18,15 L-4,15 Q-11,14 -11,9 Z" fill={AMBER_STROKE} />
  </g>
);

/** Arm: slim two-point limb from shoulder to wrist with a slight elbow
 * bow, ending in an oversized Mitt. Rotates about the shoulder. */
const Arm: React.FC<{x: number; y: number; angle: number; len?: number; grip?: 'mitt' | 'open' | 'point'; flip?: boolean}> = ({
  x,
  y,
  angle,
  len = 36,
  grip = 'mitt',
  flip = false,
}) => (
  <g transform={`rotate(${angle} ${x} ${y})`}>
    <path d={`M${x},${y} Q${x + (flip ? -7 : 7)},${y + len * 0.55} ${x},${y + len}`} fill="none" stroke={AMBER_STROKE} strokeWidth="13" strokeLinecap="round" />
    <Mitt x={x} y={y + len} grip={grip} flip={flip} />
  </g>
);

/** Leg: short thick limb from hip to ankle ending in a chunky Boot — kept
 * short so the pair tucks under the bolt's point without widening it into
 * a torso silhouette. */
const Leg: React.FC<{x: number; y: number; angle: number; len?: number; flip?: boolean}> = ({x, y, angle, len = 16, flip = false}) => (
  <g transform={`rotate(${angle} ${x} ${y})`}>
    <line x1={x} y1={y} x2={x} y2={y + len} stroke={AMBER_STROKE} strokeWidth="13" strokeLinecap="round" />
    <Boot x={x} y={y + len} flip={flip} />
  </g>
);

export const WattRig: React.FC<{size?: number; mode?: RigMode; thetaOverride?: number; speed?: number; frameOverride?: number}> = ({
  size = 240,
  mode = 'idle',
  thetaOverride,
  speed = 1,
  frameOverride,
}) => {
  const currentFrame = useCurrentFrame();
  const frame = (frameOverride ?? currentFrame) * speed;
  const pose = computeWattPose(frame, mode);
  const theta = thetaOverride ?? pose.theta;
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  const facingFront = c > -0.12;

  // body geometry under rotation — the static bolt path is horizontally
  // squished about its own center to fake the turn, same trick chipRig
  // plays on its body rect.
  const bodyW = BOLT_W0 * (0.68 + 0.32 * Math.abs(c));
  const bodyX = 120 - bodyW / 2;
  const bodyScaleX = bodyW / BOLT_W0;
  const slabW = 16 * Math.abs(s);
  const faceShift = s * 20;
  const eyeSep = 26 * (0.78 + 0.22 * Math.abs(c));
  const eyeRx = 10.5 * (0.8 + 0.2 * Math.abs(c));
  const sparkPulse = 0.4 + Math.abs(Math.sin(frame / 11)) * 0.6;
  const groundY = 214;
  const hipY = 190;

  return (
    <svg width={size} height={size} viewBox="0 0 240 240">
      <ellipse
        cx={120 + pose.dashX * 0.6}
        cy="220"
        rx={62 - pose.lift * 0.25 - pose.bob * 2}
        ry={9 - pose.lift * 0.04}
        fill="#000"
        opacity={0.28 - pose.lift * 0.0015}
      />
      {/* dash translate + squash/stretch + jump pivot about the ground point */}
      <g
        transform={`translate(${pose.dashX} ${pose.bob - pose.lift}) translate(120 ${groundY}) scale(${2 - pose.squash} ${pose.squash}) rotate(${
          pose.lean + pose.jitter
        }) translate(-120 -${groundY})`}
      >
        {/* ZIP motion streaks — trail behind the current position, only
            visible mid-dash/wobble */}
        {[1, 2, 3].map((i) => (
          <rect
            key={i}
            x={120 - i * 18 - 14}
            y={96}
            width={26 - i * 3}
            height={94}
            rx={13}
            fill={AMBER_LIGHT}
            opacity={pose.streak * (0.42 / i)}
          />
        ))}

        {/* legs — tucked close together under the bolt's lower point */}
        <Leg x={108} y={hipY} angle={pose.legL} flip={s < 0.15} />
        <Leg x={128} y={hipY} angle={pose.legR} />

        {/* far arm — anchored just OUTSIDE the body edge so the big mitt
            always hangs visibly beside the body */}
        <Arm x={bodyX - 5} y={122} angle={pose.armL + 8} grip="mitt" flip />

        {/* side extrusion slab (the faux-3D depth edge) */}
        {slabW > 1.5 ? (
          <rect x={s > 0 ? bodyX - slabW + 3 : bodyX + bodyW - 3} y={70} width={slabW} height={118} rx={10} fill={AMBER_SIDE} />
        ) : null}

        {/* ambient crackle — free-floating sparks near the body, pulsing;
            brighten during the ZIP dash */}
        <g stroke={AMBER_DEEP} strokeWidth="5" strokeLinecap="round" opacity={Math.max(sparkPulse, pose.streak)}>
          <path d="M188,80 L200,80 M194,74 L194,86" />
          <path d="M46,108 L56,108 M51,103 L51,113" />
          <path d="M182,154 L192,154" />
        </g>

        {/* body — static bolt path, squished about x=120 to fake rotation */}
        <defs>
          <linearGradient id="wattRigBody" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={AMBER_LIGHT} />
            <stop offset="1" stopColor={AMBER_DEEP} />
          </linearGradient>
        </defs>
        <g transform={`translate(120 0) scale(${bodyScaleX} 1) translate(-120 0)`}>
          <path d={BOLT_PATH} fill="url(#wattRigBody)" stroke={AMBER_STROKE} strokeWidth="4" strokeLinejoin="round" />
          {!facingFront ? <path d={BOLT_PATH} fill={AMBER_SIDE} opacity="0.55" /> : null}
        </g>

        {facingFront ? (
          <>
            {/* face slides across the head as he turns */}
            <Eye cx={120 + faceShift - eyeSep / 2} cy={84} rx={eyeRx} blink={pose.blink} look={s * 4 - 2} />
            <Eye cx={120 + faceShift + eyeSep / 2} cy={84} rx={eyeRx} blink={pose.blink} look={s * 4 - 2} />
            <Smile x={120 + faceShift * 1.05} y={110} w={22} />
          </>
        ) : (
          <>
            {/* back panel: plain darker bolt (drawn above) + battery sticker */}
            <rect x="100" y="66" width="40" height="26" rx="6" fill="#FDFEFF" opacity="0.85" />
            <rect x="136" y="74" width="6" height="10" rx="2" fill="#FDFEFF" opacity="0.85" />
            {[0, 1, 2].map((i) => (
              <rect key={i} x={104 + i * 11} y={70} width={8} height={18} rx={2} fill={AMBER_DEEP} opacity={sparkPulse} />
            ))}
          </>
        )}

        {/* near arm — same outside-the-edge anchoring */}
        {pose.wave ? (
          <Arm x={bodyX + bodyW + 5} y={122} angle={-148 + pose.armR} grip="open" />
        ) : pose.point ? (
          <Arm x={bodyX + bodyW + 5} y={122} angle={-96} len={42} grip="point" />
        ) : (
          <Arm x={bodyX + bodyW + 5} y={122} angle={pose.armR - 8} grip="mitt" />
        )}
      </g>
    </svg>
  );
};
