// capRig.tsx — Cap as a COMPLETE rigged character: parameterized rotation
// (full 360° turnaround with faux-3D side extrusion), limbs, and a move set
// (idle / walk / wave / point / jump / turn / special). Mirrors chipRig.tsx's
// architecture exactly — a pure computePose(frame, mode) function feeding one
// useCurrentFrame() call — but reskinned as the Capitol-dome mascot: off-white
// dome + cupola + waving flag over a column pedestal, cream white-glove mitts
// with navy cuffs, navy formal boots, and a dignified side-to-side WADDLE walk.
//
// Faux-3D model: the dome+pedestal assembly is treated as a rounded slab.
// cos(theta) drives the apparent width, sin(theta) drives which side face
// (extrusion) shows and how far the face features slide across the front.
// Past ±90° the face hides and a plain back panel (no face, small "PUBLIC
// RECORD" plaque, flag still flying) shows instead.
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C} from '../slides/theme';

export type RigMode = 'idle' | 'walk' | 'wave' | 'point' | 'jump' | 'turn' | 'special';

const NAVY = '#1c2c55';
const NAVY_DEEP = '#13203f';
const CREAM = '#F7F3E8';
const SOLE = '#7d8ba0';
const DOME_SHADOW = '#cfd9e4';
const DOME_SIDE = '#aebccb';
const BASE_COLOR = '#b9c6d4';
const BASE_SIDE = '#9fb0c2';
const COLUMN_COLOR = '#aebccb';
const INKFACE = '#22304a';
const RED = C.redHot;

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const lerp = (a: number, b: number, u: number) => a + (b - a) * u;
const smoothstep = (a: number, b: number, t: number) => {
  const u = clamp01((t - a) / (b - a));
  return u * u * (3 - 2 * u);
};
/** Damped-cosine spring: 0 → overshoots past 1 → settles at 1. Used for the
 * FILED chip's pop-up. */
const springOvershoot = (u: number) => 1 - Math.exp(-8 * u) * Math.cos(12 * u);

/** All pose state the SVG needs, derived per-frame by the mode logic. */
type Pose = {
  theta: number; // rotation around vertical axis, radians (0 = facing camera)
  bob: number; // vertical idle offset
  lift: number; // jump height (positive = up)
  squash: number; // 1 = neutral; <1 squashed, >1 stretched (about the ground)
  lean: number; // side rock / lean degrees, rotated about the ground point
  legL: number; // leg swing degrees
  legR: number;
  armL: number; // arm swing degrees relative to hanging
  armR: number;
  wave: boolean; // right arm in wave position
  point: boolean; // right arm extended pointing
  blink: number;
  stampAngle: number; // special: near-arm angle while raising/slamming the stamp
  filedScale: number; // special: FILED chip pop scale
  filedOpacity: number; // special: FILED chip opacity
  filedY: number; // special: FILED chip vertical settle offset
};

const computeCapPose = (frame: number, mode: RigMode): Pose => {
  const blinkT = (frame + 83) % 120; // phase-shifted from Chip, matches family.tsx's Cap phase
  const blink = blinkT < 4 ? 0.12 : blinkT < 8 ? 1 - Math.abs(6 - blinkT) * 0.22 : 1;
  const idleBob = Math.sin(frame / 24) * 3;

  const base: Pose = {
    theta: 0,
    bob: idleBob,
    lift: 0,
    squash: 1,
    lean: 0,
    legL: 0,
    legR: 0,
    armL: Math.sin(frame / 24) * 4,
    armR: -Math.sin(frame / 24) * 4,
    wave: false,
    point: false,
    blink,
    stampAngle: -6,
    filedScale: 0,
    filedOpacity: 0,
    filedY: 0,
  };

  switch (mode) {
    case 'idle':
      return base;
    case 'turn':
      // one full revolution every 240 frames
      return {...base, theta: ((frame % 240) / 240) * Math.PI * 2, bob: Math.sin(frame / 22) * 3};
    case 'walk': {
      // dignified WADDLE: short-legged step swing plus a whole-body rock
      // (rotate about the ground point) synced to the same stride phase.
      const swing = Math.sin(frame / 5.5) * 20;
      const rock = Math.sin(frame / 5.5) * 6;
      return {
        ...base,
        theta: 0.18,
        bob: Math.abs(Math.sin(frame / 5.5)) * -4,
        lean: rock,
        legL: swing,
        legR: -swing,
        armL: -swing * 0.6,
        armR: swing * 0.6,
      };
    }
    case 'wave': {
      return {...base, wave: true, armR: Math.sin(frame / 6) * 26};
    }
    case 'point': {
      return {...base, theta: 0.22, point: true, armL: 2};
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
        lift = ((t - 18) / 6) * 22;
      } else if (t < 58) {
        const u = (t - 24) / 34; // parabolic flight
        lift = 22 + 58 * (1 - (2 * u - 1) * (2 * u - 1));
        squash = 1.1 - u * 0.1;
      } else if (t < 66) {
        lift = Math.max(0, 22 * (1 - (t - 58) / 4));
        squash = 0.83; // landing squash
      } else {
        squash = 0.83 + clamp01((t - 66) / 12) * 0.17;
      }
      const armUp = t >= 18 && t < 62 ? -150 : 0;
      return {...base, lift, squash, armL: armUp ? -armUp : 4, armR: armUp, bob: 0};
    }
    case 'special': {
      // STAMP: raise → slam (body dip/squash) → FILED chip pops with a
      // spring overshoot beside him → holds → fades. 100-frame loop.
      const t = frame % 100;
      let stampAngle = -6;
      let squash = 1;
      let liftUp = 0;

      if (t < 18) {
        const u = smoothstep(0, 18, t);
        stampAngle = lerp(-6, -150, u); // raise the stamp overhead
        liftUp = u * 5;
        squash = lerp(1, 1.06, u);
      } else if (t < 26) {
        const u = smoothstep(18, 26, t);
        stampAngle = lerp(-150, 30, u); // slam down
        liftUp = lerp(5, 0, u);
        squash = lerp(1.06, 0.8, u); // impact squash + body dip
      } else if (t < 34) {
        const u = smoothstep(26, 34, t);
        stampAngle = lerp(30, -6, u); // recoil back to rest
        squash = lerp(0.8, 1, u);
      }

      let filedScale = 0;
      let filedOpacity = 0;
      let filedY = 8;
      if (t >= 26 && t < 38) {
        const u = clamp01((t - 26) / 12);
        filedScale = springOvershoot(u);
        filedOpacity = clamp01(u * 2);
        filedY = 8 * (1 - u);
      } else if (t >= 38 && t < 70) {
        filedScale = 1;
        filedOpacity = 1;
        filedY = 0;
      } else if (t >= 70 && t < 88) {
        const u = clamp01((t - 70) / 18);
        filedScale = 1;
        filedOpacity = 1 - u;
        filedY = -u * 6;
      }

      return {...base, bob: idleBob - liftUp, squash, stampAngle, filedScale, filedOpacity, filedY};
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

/** Brawlhalla-proportioned mitt: cream white glove with navy stroke seams,
 * a thumb, and a navy wrist cuff. Drawn pointing DOWN in local space; rotate
 * the parent to aim it. `grip`: 'mitt'/'stamp' (closed fist — 'stamp' just
 * marks the hand as holding a prop drawn by the caller), 'open' (splayed for
 * the wave), 'point' (index out, for chart scenes). */
const Mitt: React.FC<{x: number; y: number; grip?: 'mitt' | 'open' | 'point' | 'stamp'; flip?: boolean}> = ({x, y, grip = 'mitt', flip = false}) => (
  <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
    {/* cuff */}
    <rect x="-13" y="-8" width="26" height="12" rx="5" fill={NAVY} />
    {grip === 'point' ? (
      <>
        <path d="M-12,2 Q-16,20 -4,24 Q10,27 14,16 Q16,10 12,4 Z" fill={CREAM} stroke={NAVY} strokeWidth="3.5" strokeLinejoin="round" />
        <rect x="6" y="10" width="22" height="11" rx="5.5" fill={CREAM} stroke={NAVY} strokeWidth="3.5" />
      </>
    ) : grip === 'open' ? (
      <>
        <path d="M-14,0 Q-20,18 -8,25 Q4,30 14,22 Q20,16 16,4 Z" fill={CREAM} stroke={NAVY} strokeWidth="3.5" strokeLinejoin="round" />
        <circle cx="-10" cy="24" r="6" fill={CREAM} stroke={NAVY} strokeWidth="3" />
        <circle cx="2" cy="28" r="6" fill={CREAM} stroke={NAVY} strokeWidth="3" />
        <circle cx="13" cy="23" r="6" fill={CREAM} stroke={NAVY} strokeWidth="3" />
      </>
    ) : (
      <>
        <path d="M-13,0 Q-18,16 -8,23 Q2,29 12,23 Q19,17 14,2 Z" fill={CREAM} stroke={NAVY} strokeWidth="3.5" strokeLinejoin="round" />
        {/* finger seams */}
        <path d="M-2,6 L-2,22 M7,5 L8,19" stroke={NAVY} strokeWidth="2.5" strokeLinecap="round" fill="none" opacity="0.6" />
        {/* thumb */}
        <ellipse cx="-13" cy="10" rx="6" ry="8" fill={CREAM} stroke={NAVY} strokeWidth="3" />
      </>
    )}
  </g>
);

/** Chunky navy formal boot: rounded toe, heel, contrasting lighter sole. */
const Boot: React.FC<{x: number; y: number; flip?: boolean}> = ({x, y, flip = false}) => (
  <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
    <path d="M-11,-6 L-11,8 Q-11,14 -4,15 L18,15 Q26,15 25,7 Q24,0 16,-1 L9,-2 L9,-6 Q9,-11 -1,-11 Q-11,-11 -11,-6 Z" fill={NAVY} stroke={NAVY_DEEP} strokeWidth="3" strokeLinejoin="round" />
    <path d="M-11,12 L25,12 L25,10 Q26,15 18,15 L-4,15 Q-11,14 -11,9 Z" fill={SOLE} />
  </g>
);

/** Arm: slim two-point limb from shoulder to wrist with a slight elbow bow,
 * ending in an oversized Mitt. Rotates about the shoulder. */
const Arm: React.FC<{x: number; y: number; angle: number; len?: number; grip?: 'mitt' | 'open' | 'point' | 'stamp'; flip?: boolean}> = ({
  x,
  y,
  angle,
  len = 36,
  grip = 'mitt',
  flip = false,
}) => (
  <g transform={`rotate(${angle} ${x} ${y})`}>
    <path d={`M${x},${y} Q${x + (flip ? -7 : 7)},${y + len * 0.55} ${x},${y + len}`} fill="none" stroke={NAVY} strokeWidth="13" strokeLinecap="round" />
    <Mitt x={x} y={y + len} grip={grip} flip={flip} />
  </g>
);

/** Leg: short thick limb from hip to ankle ending in a chunky Boot. */
const Leg: React.FC<{x: number; y: number; angle: number; len?: number; flip?: boolean}> = ({x, y, angle, len = 20, flip = false}) => (
  <g transform={`rotate(${angle} ${x} ${y})`}>
    <line x1={x} y1={y} x2={x} y2={y + len} stroke={NAVY} strokeWidth="14" strokeLinecap="round" />
    <Boot x={x} y={y + len} flip={flip} />
  </g>
);

export const CapRig: React.FC<{size?: number; mode?: RigMode; thetaOverride?: number; speed?: number; frameOverride?: number}> = ({
  size = 240,
  mode = 'idle',
  thetaOverride,
  speed = 1,
  frameOverride,
}) => {
  const currentFrame = useCurrentFrame();
  const frame = (frameOverride ?? currentFrame) * speed;
  const pose = computeCapPose(frame, mode);
  const theta = thetaOverride ?? pose.theta;
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  const facingFront = c > -0.12;

  // ------- dome + pedestal geometry under rotation -------
  // The dome+cupola is the HEAD equivalent; a narrower column PEDESTAL below
  // it is the TORSO — arms attach to the pedestal shoulders, outside its
  // silhouette, so both mitts always read clearly beside the body.
  const DOME_W0 = 112;
  const domeW = DOME_W0 * (0.68 + 0.32 * Math.abs(c));
  const domeX = 120 - domeW / 2;
  const BASE_W0 = 100;
  const baseW = BASE_W0 * (0.7 + 0.3 * Math.abs(c));
  const baseX = 120 - baseW / 2;
  const slabW = 16 * Math.abs(s);
  const faceShift = s * 20;
  const domeShift = s * 8;
  const eyeSep = 38 * (0.62 + 0.38 * Math.abs(c));
  const eyeRx = 12.5 * (0.78 + 0.22 * Math.abs(c));
  const flagWave = Math.sin(frame / 16) * 4;
  const groundY = 214;
  const shoulderY = 164;
  const domeBaseY = 176; // arc bottom / pedestal top
  const domeApexY = domeBaseY - 74;

  // near (right) arm — normally hangs; in special mode it raises/slams the
  // stamp, so its transform + prop position are shared between the Arm and
  // the stamp prop drawn in its grip.
  const nearArmAngle = mode === 'special' ? pose.stampAngle : pose.wave ? -148 + pose.armR : pose.point ? -96 : pose.armR - 9;
  const nearArmLen = mode === 'point' ? 40 : 32;
  const nearArmX = baseX + baseW + 4;
  const nearArmGrip: 'mitt' | 'open' | 'point' | 'stamp' = pose.wave ? 'open' : pose.point ? 'point' : mode === 'special' ? 'stamp' : 'mitt';

  return (
    <svg width={size} height={size} viewBox="0 0 240 240">
      <ellipse cx="120" cy="220" rx={60 - pose.lift * 0.25 - pose.bob * 2} ry={9 - pose.lift * 0.04} fill="#000" opacity={0.28 - pose.lift * 0.0015} />
      {/* squash/stretch + waddle rock + jump pivot about the ground point */}
      <g transform={`translate(0 ${pose.bob - pose.lift}) translate(120 ${groundY}) scale(${2 - pose.squash} ${pose.squash}) rotate(${pose.lean}) translate(-120 -${groundY})`}>
        {/* legs + navy boots */}
        <Leg x={104} y={180} angle={pose.legL} len={18} flip={s < 0.15} />
        <Leg x={136} y={180} angle={pose.legR} len={18} />

        {/* far arm — anchored at the pedestal shoulder, outside its edge */}
        <Arm x={baseX - 4} y={shoulderY} angle={pose.armL + 9} len={32} grip="mitt" flip />

        {/* faux-3D depth slabs for dome + pedestal */}
        {slabW > 1.5 ? (
          <>
            <rect x={s > 0 ? domeX - slabW + 3 : domeX + domeW - 3} y={domeApexY} width={slabW} height={domeBaseY - domeApexY} rx={9} fill={DOME_SIDE} />
            <rect x={s > 0 ? baseX - slabW * 0.8 + 3 : baseX + baseW - 3} y={150} width={slabW * 0.8} height={42} rx={7} fill={BASE_SIDE} />
          </>
        ) : null}

        {/* flag pole + waving flag, always flying regardless of facing */}
        <line x1={120 + domeShift} y1="24" x2={120 + domeShift} y2={domeApexY + 4} stroke="#9aa7b5" strokeWidth="5" strokeLinecap="round" />
        <path
          d={`M${123 + domeShift},26 Q${138 + domeShift + flagWave},30 ${152 + domeShift},27 L${152 + domeShift},45 Q${138 + domeShift + flagWave},48 ${123 + domeShift},44 Z`}
          fill={RED}
        />
        <rect x={123 + domeShift} y="26" width="29" height="7" fill={NAVY} />

        <defs>
          <linearGradient id="capRigDome" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#FDFEFF" />
            <stop offset="1" stopColor={DOME_SHADOW} />
          </linearGradient>
        </defs>

        {/* pedestal (torso equivalent) first, dome over it */}
        <rect x={baseX} y={domeBaseY} width={baseW} height="16" rx="7" fill={BASE_COLOR} />
        {facingFront ? (
          <g stroke={COLUMN_COLOR} strokeWidth="6" strokeLinecap="round" opacity="0.85">
            <line x1={baseX + baseW * 0.16} y1="150" x2={baseX + baseW * 0.16} y2={domeBaseY} />
            <line x1={baseX + baseW * 0.39} y1="146" x2={baseX + baseW * 0.39} y2={domeBaseY} />
            <line x1={baseX + baseW * 0.61} y1="146" x2={baseX + baseW * 0.61} y2={domeBaseY} />
            <line x1={baseX + baseW * 0.84} y1="150" x2={baseX + baseW * 0.84} y2={domeBaseY} />
          </g>
        ) : (
          <g>
            <rect x="92" y="152" width="56" height="22" rx="6" fill="#FDFEFF" opacity="0.9" />
            <text x="120" y="167" textAnchor="middle" fontFamily="monospace" fontSize="8.5" fontWeight="700" fill={NAVY} letterSpacing="0.5">
              PUBLIC RECORD
            </text>
          </g>
        )}

        {/* dome + cupola */}
        <path d={`M${domeX},${domeBaseY} A ${domeW / 2},74 0 0 1 ${domeX + domeW},${domeBaseY} Z`} fill="url(#capRigDome)" />
        <line x1={120 + domeShift} y1={domeApexY - 4} x2={120 + domeShift} y2={domeApexY} stroke={DOME_SHADOW} strokeWidth="6" strokeLinecap="round" />
        <rect x={106 + domeShift} y={domeApexY - 22} width="28" height="18" rx="6" fill={DOME_SHADOW} opacity={clamp01(1 - Math.abs(s) * 1.2)} />

        {facingFront ? (
          <>
            {/* face slides across the dome as he turns */}
            <Eye cx={120 + faceShift - eyeSep / 2} cy={140} rx={eyeRx} blink={pose.blink} look={s * 4 + 1.5} />
            <Eye cx={120 + faceShift + eyeSep / 2} cy={140} rx={eyeRx} blink={pose.blink} look={s * 4 + 1.5} />
            <path
              d={`M${120 + faceShift * 1.05 - 14},160 Q${120 + faceShift * 1.05},170 ${120 + faceShift * 1.05 + 14},160`}
              fill="none"
              stroke={INKFACE}
              strokeWidth="4.5"
              strokeLinecap="round"
            />
            {/* little bowtie */}
            <path d={`M${112 + faceShift},170 L${120 + faceShift},175 L${112 + faceShift},180 Z`} fill={RED} />
            <path d={`M${128 + faceShift},170 L${120 + faceShift},175 L${128 + faceShift},180 Z`} fill={RED} />
            <circle cx={120 + faceShift} cy="175" r="2.6" fill="#8c2f2c" />
          </>
        ) : null}

        {/* near arm — pedestal shoulder, outside its edge; carries the stamp
            prop in special mode */}
        <Arm x={nearArmX} y={shoulderY} angle={nearArmAngle} len={nearArmLen} grip={nearArmGrip} />
        {mode === 'special' ? (
          <g transform={`rotate(${nearArmAngle} ${nearArmX} ${shoulderY})`}>
            {/* rubber stamp: dark handle block + red ink pad, resting in the
                fist at the end of the arm */}
            <rect x={nearArmX - 9} y={shoulderY + nearArmLen - 30} width="18" height="16" rx="4" fill={NAVY_DEEP} stroke={NAVY} strokeWidth="2" />
            <rect x={nearArmX - 11} y={shoulderY + nearArmLen - 16} width="22" height="8" rx="3" fill={RED} />
          </g>
        ) : null}
      </g>

      {/* FILED chip — pops up beside him on impact, independent of the body
          squash so its own spring stays crisp, then fades. */}
      {mode === 'special' && pose.filedOpacity > 0.001 ? (
        <g transform={`translate(178 ${142 + pose.filedY}) scale(${pose.filedScale})`} opacity={pose.filedOpacity}>
          <rect x="-34" y="-16" width="68" height="32" rx="10" fill="#FDFEFF" stroke={RED} strokeWidth="3.5" />
          <text x="0" y="6" textAnchor="middle" fontFamily="monospace" fontSize="15" fontWeight="800" fill={RED} letterSpacing="1">
            FILED
          </text>
        </g>
      ) : null}
    </svg>
  );
};
