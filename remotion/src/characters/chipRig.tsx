// chipRig.tsx — Chip as a COMPLETE rigged character: parameterized rotation
// (full 360° turnaround with faux-3D side extrusion), limbs, and a move set
// (idle / walk / wave / point / jump / turn). Everything is derived from a
// rotation angle theta and a local clock, so any scene can pose him.
//
// Faux-3D model: the body is treated as a rounded slab. cos(theta) drives
// the apparent width, sin(theta) drives which side face (extrusion) shows
// and how far the face features slide across the front. Past ±90° the face
// hides and the back panel (vents + serial sticker) shows. It reads as a
// paper-toy rotation — the 2D cousin of a 3D turnaround, native to the
// flat Kurzgesagt-inspired language.
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C} from '../slides/theme';

export type ChipMode = 'idle' | 'walk' | 'wave' | 'point' | 'jump' | 'turn';

const EMERALD_DARK = '#0a8f66';
const EMERALD_SIDE = '#087a57';
const PIN_GOLD = '#caa64a';
const INKFACE = '#10141c';

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

/** All pose state the SVG needs, derived per-frame by the mode logic. */
type Pose = {
  theta: number; // rotation around vertical axis, radians (0 = facing camera)
  bob: number; // vertical idle offset
  lift: number; // jump height (positive = up)
  squash: number; // 1 = neutral; <1 squashed, >1 stretched (about the ground)
  lean: number; // forward lean degrees (walk)
  legL: number; // leg swing degrees
  legR: number;
  armL: number; // arm swing degrees relative to hanging
  armR: number;
  wave: boolean; // right arm in wave position (armR = wave phase instead)
  point: boolean; // right arm extended pointing
  blink: number;
};

const computeChipPose = (frame: number, mode: ChipMode): Pose => {
  const blinkT = frame % 120;
  const blink = blinkT < 4 ? 0.12 : blinkT < 8 ? 1 - Math.abs(6 - blinkT) * 0.22 : 1;
  const idleBob = Math.sin(frame / 22) * 4;

  const base: Pose = {
    theta: 0,
    bob: idleBob,
    lift: 0,
    squash: 1,
    lean: 0,
    legL: 0,
    legR: 0,
    armL: Math.sin(frame / 22) * 4,
    armR: -Math.sin(frame / 22) * 4,
    wave: false,
    point: false,
    blink,
  };

  switch (mode) {
    case 'idle':
      return base;
    case 'turn':
      // one full revolution every 240 frames
      return {...base, theta: ((frame % 240) / 240) * Math.PI * 2, bob: Math.sin(frame / 20) * 3};
    case 'walk': {
      const swing = Math.sin(frame / 5.5) * 24;
      return {
        ...base,
        theta: 0.35, // slight 3/4 so the walk reads
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
        lift = 24 + 62 * (1 - (2 * u - 1) * (2 * u - 1));
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
  }
};

const Eye: React.FC<{cx: number; cy: number; rx: number; blink: number; look: number}> = ({cx, cy, rx, blink, look}) => (
  <g transform={`translate(${cx} ${cy}) scale(1 ${blink})`}>
    <ellipse cx="0" cy="0" rx={rx} ry={rx * 1.17} fill="#FDFEFF" />
    <circle cx={look} cy="2.5" r={rx * 0.44} fill={INKFACE} />
    <circle cx={look + rx * 0.15} cy="0.2" r={rx * 0.14} fill="#FDFEFF" opacity="0.9" />
  </g>
);

/** Brawlhalla-proportioned mitt: an oversized rounded hand with two finger
 * bumps, a thumb, and a gold wrist cuff (echoes the chip pins). Drawn
 * pointing DOWN in local space; rotate the parent to aim it. `grip`:
 * 'mitt' (closed), 'open' (fingers splayed), 'point' (index out). */
const Mitt: React.FC<{x: number; y: number; grip?: 'mitt' | 'open' | 'point'; flip?: boolean}> = ({x, y, grip = 'mitt', flip = false}) => (
  <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
    {/* cuff */}
    <rect x="-13" y="-8" width="26" height="12" rx="5" fill={PIN_GOLD} />
    {grip === 'point' ? (
      <>
        <path d="M-12,2 Q-16,20 -4,24 Q10,27 14,16 Q16,10 12,4 Z" fill={C.emerald} stroke={EMERALD_DARK} strokeWidth="3.5" strokeLinejoin="round" />
        <rect x="6" y="10" width="22" height="11" rx="5.5" fill={C.emerald} stroke={EMERALD_DARK} strokeWidth="3.5" />
      </>
    ) : grip === 'open' ? (
      <>
        <path d="M-14,0 Q-20,18 -8,25 Q4,30 14,22 Q20,16 16,4 Z" fill={C.emerald} stroke={EMERALD_DARK} strokeWidth="3.5" strokeLinejoin="round" />
        <circle cx="-10" cy="24" r="6" fill={C.emerald} stroke={EMERALD_DARK} strokeWidth="3" />
        <circle cx="2" cy="28" r="6" fill={C.emerald} stroke={EMERALD_DARK} strokeWidth="3" />
        <circle cx="13" cy="23" r="6" fill={C.emerald} stroke={EMERALD_DARK} strokeWidth="3" />
      </>
    ) : (
      <>
        <path d="M-13,0 Q-18,16 -8,23 Q2,29 12,23 Q19,17 14,2 Z" fill={C.emerald} stroke={EMERALD_DARK} strokeWidth="3.5" strokeLinejoin="round" />
        {/* finger seams */}
        <path d="M-2,6 L-2,22 M7,5 L8,19" stroke={EMERALD_DARK} strokeWidth="2.5" strokeLinecap="round" fill="none" opacity="0.7" />
        {/* thumb */}
        <ellipse cx="-13" cy="10" rx="6" ry="8" fill={C.emerald} stroke={EMERALD_DARK} strokeWidth="3" />
      </>
    )}
  </g>
);

/** Chunky boot: big rounded toe, heel, contrasting sole. Drawn with the
 * ankle at local (0,0), sole resting ~15px below. */
const Boot: React.FC<{x: number; y: number; flip?: boolean}> = ({x, y, flip = false}) => (
  <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
    <path d="M-11,-6 L-11,8 Q-11,14 -4,15 L18,15 Q26,15 25,7 Q24,0 16,-1 L9,-2 L9,-6 Q9,-11 -1,-11 Q-11,-11 -11,-6 Z" fill={EMERALD_DARK} stroke="#065c42" strokeWidth="3" strokeLinejoin="round" />
    <path d="M-11,12 L25,12 L25,10 Q26,15 18,15 L-4,15 Q-11,14 -11,9 Z" fill="#065c42" />
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
    <path d={`M${x},${y} Q${x + (flip ? -7 : 7)},${y + len * 0.55} ${x},${y + len}`} fill="none" stroke={EMERALD_DARK} strokeWidth="13" strokeLinecap="round" />
    <Mitt x={x} y={y + len} grip={grip} flip={flip} />
  </g>
);

/** Leg: short thick limb from hip to ankle ending in a chunky Boot. */
const Leg: React.FC<{x: number; y: number; angle: number; len?: number; flip?: boolean}> = ({x, y, angle, len = 20, flip = false}) => (
  <g transform={`rotate(${angle} ${x} ${y})`}>
    <line x1={x} y1={y} x2={x} y2={y + len} stroke={EMERALD_DARK} strokeWidth="14" strokeLinecap="round" />
    <Boot x={x} y={y + len} flip={flip} />
  </g>
);

export const ChipRig: React.FC<{size?: number; mode?: ChipMode; thetaOverride?: number; speed?: number; frameOverride?: number}> = ({
  size = 240,
  mode = 'idle',
  thetaOverride,
  speed = 1,
  frameOverride,
}) => {
  const currentFrame = useCurrentFrame();
  const frame = (frameOverride ?? currentFrame) * speed;
  const pose = computeChipPose(frame, mode);
  const theta = thetaOverride ?? pose.theta;
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  const facingFront = c > -0.12;

  // body geometry under rotation
  const W0 = 124;
  const bodyW = W0 * (0.68 + 0.32 * Math.abs(c));
  const bodyX = 120 - bodyW / 2;
  const slabW = 20 * Math.abs(s);
  const faceShift = s * 30;
  const eyeSep = 46 * (0.62 + 0.38 * Math.abs(c));
  const eyeRx = 14.5 * (0.78 + 0.22 * Math.abs(c));
  const antennaGlow = 0.55 + Math.sin(frame / 14) * 0.35;
  const groundY = 214;

  return (
    <svg width={size} height={size} viewBox="0 0 240 240">
      <ellipse cx="120" cy="220" rx={62 - pose.lift * 0.25 - pose.bob * 2} ry={9 - pose.lift * 0.04} fill="#000" opacity={0.28 - pose.lift * 0.0015} />
      {/* squash/stretch + jump pivot about the ground point */}
      <g transform={`translate(0 ${pose.bob - pose.lift}) translate(120 ${groundY}) scale(${2 - pose.squash} ${pose.squash}) rotate(${pose.lean}) translate(-120 -${groundY})`}>
        {/* legs + chunky boots; front-facing stance points the boots
            outward, a turned/walking pose points both toes with the facing */}
        <Leg x={100} y={184} angle={pose.legL} flip={s < 0.15} />
        <Leg x={140} y={184} angle={pose.legR} />

        {/* far arm — anchored just OUTSIDE the body edge so the big mitt
            always hangs visibly beside the body, Brawlhalla-style */}
        <Arm x={bodyX - 5} y={140} angle={pose.armL + 8} grip="mitt" flip />

        {/* side extrusion slab (the faux-3D depth edge) */}
        {slabW > 1.5 ? (
          <rect
            x={s > 0 ? bodyX - slabW + 3 : bodyX + bodyW - 3}
            y={72}
            width={slabW}
            height={130}
            rx={12}
            fill={EMERALD_SIDE}
          />
        ) : null}

        {/* antenna */}
        <line x1={120 + s * 10} y1="72" x2={120 + s * 14} y2="44" stroke={C.emeraldDeep} strokeWidth="7" strokeLinecap="round" />
        <circle cx={120 + s * 14} cy="38" r="9" fill={C.mint} opacity={antennaGlow} />
        <circle cx={120 + s * 14} cy="38" r="4.5" fill="#FDFEFF" opacity={antennaGlow} />

        {/* body */}
        <defs>
          <linearGradient id="chipRigBody" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={C.emerald} />
            <stop offset="1" stopColor={C.emeraldDeep} />
          </linearGradient>
        </defs>
        <rect x={bodyX} y="70" width={bodyW} height="132" rx="26" fill="url(#chipRigBody)" />

        {/* side pins fade out as we rotate away from front */}
        <g fill={PIN_GOLD} opacity={clamp01(1 - Math.abs(s) * 1.4)}>
          {[96, 126, 156].map((y) => (
            <React.Fragment key={y}>
              <rect x={bodyX - 14} y={y} width="18" height="12" rx="4" />
              <rect x={bodyX + bodyW - 4} y={y} width="18" height="12" rx="4" />
            </React.Fragment>
          ))}
        </g>

        {facingFront ? (
          <>
            {/* circuit traces */}
            <g stroke="#FDFEFF" strokeWidth="3.5" opacity={0.28 * clamp01(c + 0.4)} fill="none" strokeLinecap="round">
              <path d={`M${bodyX + 16},178 L${bodyX + 36},178 L${bodyX + 36},166`} />
              <path d={`M${bodyX + bodyW - 16},178 L${bodyX + bodyW - 34},178 L${bodyX + bodyW - 34},168`} />
            </g>
            {/* face slides across the front as he turns */}
            <Eye cx={120 + faceShift - eyeSep / 2} cy={118} rx={eyeRx} blink={pose.blink} look={s * 4 + 1.5} />
            <Eye cx={120 + faceShift + eyeSep / 2} cy={118} rx={eyeRx} blink={pose.blink} look={s * 4 + 1.5} />
            <path
              d={`M${120 + faceShift * 1.05 - 17},152 Q${120 + faceShift * 1.05},166 ${120 + faceShift * 1.05 + 17},152`}
              fill="none"
              stroke={INKFACE}
              strokeWidth="5"
              strokeLinecap="round"
            />
          </>
        ) : (
          <>
            {/* back panel: vents + serial sticker */}
            <g stroke="#0c7c59" strokeWidth="6" strokeLinecap="round" opacity="0.75">
              <line x1={102} y1="96" x2={138} y2="96" />
              <line x1={102} y1="112" x2={138} y2="112" />
              <line x1={102} y1="128" x2={138} y2="128" />
            </g>
            <rect x={98} y="150" width="44" height="26" rx="6" fill="#FDFEFF" opacity="0.85" />
            <text x={120} y="168" textAnchor="middle" fontFamily="monospace" fontSize="13" fontWeight="700" fill={EMERALD_SIDE}>
              AI·STK
            </text>
          </>
        )}

        {/* near arm — same outside-the-edge anchoring */}
        {pose.wave ? (
          <Arm x={bodyX + bodyW + 5} y={140} angle={-148 + pose.armR} grip="open" />
        ) : pose.point ? (
          <Arm x={bodyX + bodyW + 5} y={140} angle={-96} len={42} grip="point" />
        ) : (
          <Arm x={bodyX + bodyW + 5} y={140} angle={pose.armR - 8} grip="mitt" />
        )}
      </g>
    </svg>
  );
};
