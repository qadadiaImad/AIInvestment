// qubitRig.tsx — Qubit as a COMPLETE rigged character: parameterized rotation
// (full 360° turnaround), limbs, and a move set (idle / walk / wave / point /
// jump / turn / special). Everything is derived from a rotation angle theta
// and a local clock, so any scene can pose him.
//
// Unlike Chip's rectangular slab, Qubit's silhouette is a sphere — it never
// gets thinner in profile. Rotation instead reads through the orbit ring's
// tilt, the face sliding across the front, and the two superposition echoes
// swapping which one leads. Past ±90° the face hides behind a plain sphere +
// orbit ring + a small "q" marking, mirroring Chip's back panel.
//
// Signature move (special): TELEPORT. Qubit collapses into his left echo
// (fade + squash), vanishes for ~8 frames while both echoes pulse, then pops
// out of the RIGHT echo with a stretch overshoot and a brief electron-ring
// flash.
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C} from '../slides/theme';

export type RigMode = 'idle' | 'walk' | 'wave' | 'point' | 'jump' | 'turn' | 'special';

const MINT_LIGHT = '#b8f4dd';
const LIMB = C.emeraldDeep; // arm/leg lines — ties to the emerald echo
const INK = '#0d3327'; // mitt/boot stroke + pupil + mouth (spec color)
const GOLD = '#caa64a'; // wrist cuffs
const SOLE = '#0a5c3f'; // contrasting boot sole

const CX = 120;
const CY = 138;
const R = 60;
const GROUND_Y = 214;

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
  wave: boolean; // right arm in wave position
  point: boolean; // right arm extended pointing
  blink: number;
  bodyOpacity: number; // whole-rig opacity (teleport fade)
  bodyOffsetX: number; // whole-rig horizontal shift toward an echo (teleport)
  bodyScaleX: number; // sphere-only squash/stretch, horizontal
  bodyScaleY: number; // sphere-only squash/stretch, vertical
  ringFlash: number; // 0 normal .. 1 electron-ring flash
  echoBoostL: number; // extra opacity on the left superposition echo
  echoBoostR: number; // extra opacity on the right superposition echo
};

const computePose = (frame: number, mode: RigMode): Pose => {
  const blinkT = (frame + 57) % 120; // phase-shifted, matches family's Qubit phase
  const blink = blinkT < 4 ? 0.12 : blinkT < 8 ? 1 - Math.abs(6 - blinkT) * 0.22 : 1;
  const idleBob = Math.sin((frame + 52) / 22) * 6;

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
    bodyOpacity: 1,
    bodyOffsetX: 0,
    bodyScaleX: 1,
    bodyScaleY: 1,
    ringFlash: 0,
    echoBoostL: 0,
    echoBoostR: 0,
  };

  switch (mode) {
    case 'idle':
      return base;
    case 'turn':
      // one full revolution every 240 frames
      return {...base, theta: ((frame % 240) / 240) * Math.PI * 2, bob: Math.sin(frame / 20) * 3};
    case 'walk': {
      const swing = Math.sin(frame / 5.5) * 22;
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
        squash = 1 - (t / 18) * 0.16;
      } else if (t < 24) {
        squash = 0.84 + ((t - 18) / 6) * 0.34;
        lift = ((t - 18) / 6) * 24;
      } else if (t < 58) {
        const u = (t - 24) / 34;
        lift = 24 + 62 * (1 - (2 * u - 1) * (2 * u - 1));
        squash = 1.12 - u * 0.12;
      } else if (t < 66) {
        lift = Math.max(0, 24 * (1 - (t - 58) / 4));
        squash = 0.82;
      } else {
        squash = 0.82 + clamp01((t - 66) / 12) * 0.18;
      }
      const armUp = t >= 18 && t < 62 ? -150 : 0;
      return {...base, lift, squash, armL: armUp ? -armUp : 4, armR: armUp, bob: 0};
    }
    case 'special': {
      // 130-frame loop: idle lead-in (0-10) → collapse into left echo,
      // fade+squash (10-26) → vanish, both echoes pulse (26-34) → pop out of
      // the right echo, stretch overshoot + ring flash (34-54) → settle back
      // to idle (54-130).
      const LOOP = 130;
      const t = frame % LOOP;
      let bodyOpacity = 1;
      let bodyOffsetX = 0;
      let bodyScaleX = 1;
      let bodyScaleY = 1;
      let ringFlash = 0;
      let echoBoostL = 0;
      let echoBoostR = 0;
      let armL = base.armL;
      let armR = base.armR;

      if (t >= 10 && t < 26) {
        const p = (t - 10) / 16;
        const pe = p * p; // ease-in — accelerate into the collapse
        bodyOffsetX = -34 * pe;
        bodyScaleY = 1 - 0.7 * pe;
        bodyScaleX = 1 + 0.5 * pe;
        bodyOpacity = clamp01(1 - p * 1.2);
        echoBoostL = 0.6 * p;
        armL = base.armL - 14 * pe;
        armR = base.armR + 14 * pe;
      } else if (t >= 26 && t < 34) {
        bodyOpacity = 0;
        const pulse = 0.5 + 0.5 * Math.sin((t - 26) * 1.8);
        echoBoostL = 0.35 + 0.35 * pulse;
        echoBoostR = 0.35 + 0.35 * (1 - pulse);
      } else if (t >= 34 && t < 54) {
        const p = (t - 34) / 20;
        const bump = Math.sin(p * Math.PI); // 0 → peak mid-pop → 0, symmetric
        bodyOffsetX = 34 * (1 - p) - bump * 6;
        bodyScaleY = 1 + bump * 0.55;
        bodyScaleX = 1 - bump * 0.35;
        bodyOpacity = clamp01(p / 0.3);
        ringFlash = clamp01(1 - p / 0.45);
        echoBoostR = (1 - p) * 0.7;
        armL = base.armL - 10 * bump;
        armR = base.armR + 10 * bump;
      }

      return {
        ...base,
        bodyOpacity,
        bodyOffsetX,
        bodyScaleX,
        bodyScaleY,
        ringFlash,
        echoBoostL,
        echoBoostR,
        armL,
        armR,
      };
    }
  }
};

const Eye: React.FC<{cx: number; cy: number; rx: number; blink: number; look: number}> = ({cx, cy, rx, blink, look}) => (
  <g transform={`translate(${cx} ${cy}) scale(1 ${blink})`}>
    <ellipse cx="0" cy="0" rx={rx} ry={rx * 1.17} fill="#FDFEFF" />
    <circle cx={look} cy="2.5" r={rx * 0.44} fill={INK} />
    <circle cx={look + rx * 0.15} cy="0.2" r={rx * 0.14} fill="#FDFEFF" opacity="0.9" />
  </g>
);

/** Brawlhalla-proportioned mitt: mint fill, #0d3327 seams, gold wrist cuff.
 * Drawn pointing DOWN in local space; rotate the parent to aim it. `grip`:
 * 'mitt' (closed), 'open' (fingers splayed), 'point' (index out). */
const Mitt: React.FC<{x: number; y: number; grip?: 'mitt' | 'open' | 'point'; flip?: boolean}> = ({x, y, grip = 'mitt', flip = false}) => (
  <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
    <rect x="-13" y="-8" width="26" height="12" rx="5" fill={GOLD} />
    {grip === 'point' ? (
      <>
        <path d="M-12,2 Q-16,20 -4,24 Q10,27 14,16 Q16,10 12,4 Z" fill={C.mint} stroke={INK} strokeWidth="3.5" strokeLinejoin="round" />
        <rect x="6" y="10" width="22" height="11" rx="5.5" fill={C.mint} stroke={INK} strokeWidth="3.5" />
      </>
    ) : grip === 'open' ? (
      <>
        <path d="M-14,0 Q-20,18 -8,25 Q4,30 14,22 Q20,16 16,4 Z" fill={C.mint} stroke={INK} strokeWidth="3.5" strokeLinejoin="round" />
        <circle cx="-10" cy="24" r="6" fill={C.mint} stroke={INK} strokeWidth="3" />
        <circle cx="2" cy="28" r="6" fill={C.mint} stroke={INK} strokeWidth="3" />
        <circle cx="13" cy="23" r="6" fill={C.mint} stroke={INK} strokeWidth="3" />
      </>
    ) : (
      <>
        <path d="M-13,0 Q-18,16 -8,23 Q2,29 12,23 Q19,17 14,2 Z" fill={C.mint} stroke={INK} strokeWidth="3.5" strokeLinejoin="round" />
        <path d="M-2,6 L-2,22 M7,5 L8,19" stroke={INK} strokeWidth="2.5" strokeLinecap="round" fill="none" opacity="0.7" />
        <ellipse cx="-13" cy="10" rx="6" ry="8" fill={C.mint} stroke={INK} strokeWidth="3" />
      </>
    )}
  </g>
);

/** Small rounded mint shoe: a simple soft toe/heel with a contrasting sole,
 * chunky relative to the slim leg. Ankle at local (0,0). */
const Boot: React.FC<{x: number; y: number; flip?: boolean}> = ({x, y, flip = false}) => (
  <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
    <path d="M-9,-5 L-9,6 Q-9,12 -2,13 L14,13 Q21,13 20,6 Q19,0 12,-1 L7,-2 L7,-5 Q7,-9 -1,-9 Q-9,-9 -9,-5 Z" fill={C.mint} stroke={INK} strokeWidth="3" strokeLinejoin="round" />
    <path d="M-9,9 L20,9 L20,7 Q21,13 14,13 L-2,13 Q-9,12 -9,8 Z" fill={SOLE} />
  </g>
);

/** Arm: slim two-point limb from shoulder to wrist with a slight elbow bow,
 * ending in an oversized Mitt. Rotates about the shoulder. */
const Arm: React.FC<{x: number; y: number; angle: number; len?: number; grip?: 'mitt' | 'open' | 'point'; flip?: boolean}> = ({
  x,
  y,
  angle,
  len = 34,
  grip = 'mitt',
  flip = false,
}) => (
  <g transform={`rotate(${angle} ${x} ${y})`}>
    <path d={`M${x},${y} Q${x + (flip ? -7 : 7)},${y + len * 0.55} ${x},${y + len}`} fill="none" stroke={LIMB} strokeWidth="13" strokeLinecap="round" />
    <Mitt x={x} y={y + len} grip={grip} flip={flip} />
  </g>
);

/** Leg: short thick limb from hip to ankle ending in a small rounded Boot. */
const Leg: React.FC<{x: number; y: number; angle: number; len?: number; flip?: boolean}> = ({x, y, angle, len = 20, flip = false}) => (
  <g transform={`rotate(${angle} ${x} ${y})`}>
    <line x1={x} y1={y} x2={x} y2={y + len} stroke={LIMB} strokeWidth="14" strokeLinecap="round" />
    <Boot x={x} y={y + len} flip={flip} />
  </g>
);

export const QubitRig: React.FC<{size?: number; mode?: RigMode; thetaOverride?: number; speed?: number; frameOverride?: number}> = ({
  size = 240,
  mode = 'idle',
  thetaOverride,
  speed = 1,
  frameOverride,
}) => {
  const currentFrame = useCurrentFrame();
  const frame = (frameOverride ?? currentFrame) * speed;
  const pose = computePose(frame, mode);
  const theta = thetaOverride ?? pose.theta;
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  const facingFront = c > -0.12;

  // face-slide + orbit-ring tilt sell the rotation while the sphere itself
  // stays perfectly round
  const faceShift = s * 34;
  const eyeSep = 40 * (0.62 + 0.38 * Math.abs(c));
  const eyeRx = 14.5 * (0.78 + 0.22 * Math.abs(c));
  const mouthRx = 9 * (0.8 + 0.2 * Math.abs(c));
  const mouthRy = 11 * (0.8 + 0.2 * Math.abs(c));
  const ringRy = 32 * (0.45 + 0.55 * Math.abs(c));
  const ringRotate = -18 + s * 36;
  const orbitA = frame * 0.05;
  const ex = Math.cos(orbitA) * 88;
  const ey = Math.sin(orbitA) * ringRy;

  // superposition echoes: drift apart on their own clock, and lean toward
  // whichever side theta is turning away from — reading as the echoes
  // "swapping sides" mid-turnaround
  const split = Math.sin(frame / 30) * 10;
  const turnBias = s * 18;
  const echoLx = 120 - 10 - split - turnBias;
  const echoRx = 120 + 10 + split - turnBias;
  const echoLOpacity = clamp01((0.2 + pose.echoBoostL) * (1 - Math.max(0, s) * 0.5));
  const echoROpacity = clamp01((0.16 + pose.echoBoostR) * (1 - Math.max(0, -s) * 0.5));

  const legAnchorY = CY + R - 12;
  const armAnchorY = CY + 2;

  return (
    <svg width={size} height={size} viewBox="0 0 240 240">
      <ellipse
        cx="120"
        cy="220"
        rx={62 - pose.lift * 0.25 - pose.bob * 2}
        ry={9 - pose.lift * 0.04}
        fill="#000"
        opacity={(0.28 - pose.lift * 0.0015) * (0.2 + 0.8 * pose.bodyOpacity)}
      />

      {facingFront ? (
        s >= 0 ? (
          <>
            <circle cx={echoRx} cy={CY} r={R} fill={C.emerald} opacity={echoROpacity} />
            <circle cx={echoLx} cy={CY} r={R} fill={C.mint} opacity={echoLOpacity} />
          </>
        ) : (
          <>
            <circle cx={echoLx} cy={CY} r={R} fill={C.mint} opacity={echoLOpacity} />
            <circle cx={echoRx} cy={CY} r={R} fill={C.emerald} opacity={echoROpacity} />
          </>
        )
      ) : null}

      {/* whole-rig fade + slide for the teleport collapse/pop */}
      <g opacity={pose.bodyOpacity} transform={`translate(${pose.bodyOffsetX} 0)`}>
        {/* squash/stretch + jump pivot about the ground point */}
        <g transform={`translate(0 ${pose.bob - pose.lift}) translate(120 ${GROUND_Y}) scale(${2 - pose.squash} ${pose.squash}) rotate(${pose.lean}) translate(-120 -${GROUND_Y})`}>
          <Leg x={100} y={legAnchorY} angle={pose.legL} flip={s < 0.15} />
          <Leg x={140} y={legAnchorY} angle={pose.legR} />

          {/* far arm — anchored just outside the sphere so the mitt always
              hangs visibly beside the body */}
          <Arm x={CX - R - 6} y={armAnchorY} angle={pose.armL + 8} grip="mitt" flip />

          {/* sphere-only squash/stretch — the teleport "blob" effect,
              isolated from the limbs so they never distort */}
          <g transform={`translate(${CX} ${CY}) scale(${pose.bodyScaleX} ${pose.bodyScaleY}) translate(${-CX} ${-CY})`}>
            <defs>
              <radialGradient id="qubitRigBody" cx="0.38" cy="0.32" r="0.9">
                <stop offset="0" stopColor={MINT_LIGHT} />
                <stop offset="1" stopColor={C.mint} />
              </radialGradient>
            </defs>
            <circle cx={CX} cy={CY} r={R} fill="url(#qubitRigBody)" />

            {/* ring-flash backwash for the teleport pop */}
            {pose.ringFlash > 0.02 ? <circle cx={CX} cy={CY} r={R + 12} fill="#FDFEFF" opacity={pose.ringFlash * 0.35} /> : null}

            {/* orbit ring + electron */}
            <g transform={`translate(${CX} ${CY}) rotate(${ringRotate})`}>
              <ellipse cx="0" cy="0" rx="88" ry={ringRy} fill="none" stroke="#FDFEFF" strokeWidth={3 + pose.ringFlash * 4} opacity={0.35 + pose.ringFlash * 0.5} />
              <circle cx={ex} cy={ey} r={7 + pose.ringFlash * 3} fill={C.amber} />
              <circle cx={ex} cy={ey} r={11 + pose.ringFlash * 10} fill={C.amber} opacity={0.3 + pose.ringFlash * 0.4} />
            </g>

            {facingFront ? (
              <>
                <Eye cx={CX + faceShift - eyeSep / 2} cy={130} rx={eyeRx} blink={pose.blink} look={s * 4 + 1.5} />
                <Eye cx={CX + faceShift + eyeSep / 2} cy={130} rx={eyeRx} blink={pose.blink} look={s * 4 + 1.5} />
                <ellipse cx={CX + faceShift * 1.05} cy={162} rx={mouthRx} ry={mouthRy} fill={INK} />
              </>
            ) : (
              <text x={CX} y={CY + 12} textAnchor="middle" fontFamily="monospace" fontSize="34" fontWeight="700" fill={INK} opacity="0.55">
                q
              </text>
            )}
          </g>

          {/* near arm — same outside-the-edge anchoring */}
          {pose.wave ? (
            <Arm x={CX + R + 6} y={armAnchorY} angle={-148 + pose.armR} grip="open" />
          ) : pose.point ? (
            <Arm x={CX + R + 6} y={armAnchorY} angle={-96} len={42} grip="point" />
          ) : (
            <Arm x={CX + R + 6} y={armAnchorY} angle={pose.armR - 8} grip="mitt" />
          )}
        </g>
      </g>
    </svg>
  );
};
