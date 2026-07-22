// novaRig.tsx — Nova as a COMPLETE rigged character: parameterized rotation
// (full 360° turnaround with faux-3D side extrusion), limbs, and a move set
// (idle / walk / wave / point / jump / turn / special). Everything is derived
// from a rotation angle theta and a local clock, so any scene can pose her.
//
// Nova's silhouette (from family.tsx) is a single dark app-icon panel with a
// chat-bubble tail and twinkling amber sparkles — there is no separate head,
// so the rig treats the whole panel as one faux-3D slab (the chip rig's
// head-rotation math, applied to the panel instead of a head+torso stack).
// Past ±90° the face and tail hide and a single big centered sparkle marks
// the back, matching the requested turnaround.
//
// Signature move — LAUNCH: a quick 360° spin-in-place (reusing the turn
// mechanics compressed into ~28 frames), then a satisfied smile pop and a
// 6-point sparkle burst that scales out radially and fades.
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C} from '../slides/theme';

export type RigMode = 'idle' | 'walk' | 'wave' | 'point' | 'jump' | 'turn' | 'special';

const NAVY_FILL = '#131b2a';
const EMERALD_LINE = C.emerald;
const GOLD = '#caa64a';
const INKFACE = '#0b1020';
const LIMB = '#1f2942';

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

/** All pose state the SVG needs, derived per-frame by the mode logic. */
type Pose = {
  theta: number; // rotation around vertical axis, radians (0 = facing camera)
  bob: number; // vertical idle offset
  lift: number; // jump/hop height (positive = up)
  squash: number; // 1 = neutral; <1 squashed, >1 stretched (about the ground)
  lean: number; // forward lean degrees (walk)
  legL: number; // leg swing degrees
  legR: number;
  armL: number; // arm swing degrees relative to hanging
  armR: number;
  wave: boolean; // right arm in wave position (armR = wave phase instead)
  point: boolean; // right arm extended pointing
  blink: number;
  burstT: number; // -1 = no LAUNCH burst; else 0..1 progress of the sparkle burst
  smileBig: boolean; // satisfied smile pop (LAUNCH finale)
};

const computeNovaPose = (frame: number, mode: RigMode): Pose => {
  const blinkT = (frame + 19) % 120; // unique phase — never blinks with her siblings
  const blink = blinkT < 4 ? 0.12 : blinkT < 8 ? 1 - Math.abs(6 - blinkT) * 0.22 : 1;
  const idleBob = Math.sin((frame + 104) / 22) * 4;

  const base: Pose = {
    theta: 0,
    bob: idleBob,
    lift: 0,
    squash: 1,
    lean: 0,
    legL: 0,
    legR: 0,
    armL: Math.sin((frame + 104) / 22) * 4,
    armR: -Math.sin((frame + 104) / 22) * 4,
    wave: false,
    point: false,
    blink,
    burstT: -1,
    smileBig: false,
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
    case 'special': {
      // LAUNCH: spin-in-place (0-28) → anticipation pop (28-34) → sparkle
      // burst (34-78) → settle back to idle (78-100), then loops.
      const t = frame % 100;
      if (t < 28) {
        const theta = (t / 28) * Math.PI * 2;
        const wiggle = Math.sin(t / 2.6) * 10; // tucked-arm spin blur
        return {...base, theta, bob: 0, squash: 1 - Math.sin((t / 28) * Math.PI) * 0.05, armL: wiggle, armR: -wiggle};
      }
      if (t < 34) {
        const u = (t - 28) / 6;
        return {...base, theta: 0, bob: 0, lift: u * 10, squash: 1 + u * 0.12, armL: 150 * u, armR: -150 * u, smileBig: u > 0.3};
      }
      if (t < 78) {
        const v = (t - 34) / 44;
        const eased = 1 - (1 - v) * (1 - v);
        return {...base, theta: 0, bob: 0, lift: 10 * (1 - v), squash: 1.12 - v * 0.12, armL: 150, armR: -150, burstT: eased, smileBig: v < 0.85};
      }
      const w = (t - 78) / 22;
      return {...base, theta: 0, bob: idleBob * w, lift: 0, squash: 1, armL: 150 * (1 - w), armR: -150 * (1 - w)};
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

const Smile: React.FC<{x: number; y: number; w?: number; open?: boolean}> = ({x, y, w = 30, open = false}) =>
  open ? (
    <ellipse cx={x} cy={y + 3} rx="10" ry="12" fill={INKFACE} />
  ) : (
    <path d={`M${x - w / 2},${y} Q${x},${y + 13} ${x + w / 2},${y}`} fill="none" stroke={INKFACE} strokeWidth="5" strokeLinecap="round" />
  );

/** Brawlhalla-proportioned mitt: dark-navy hand with an emerald outline
 * (matching Nova's panel border) and a gold wrist cuff. Drawn pointing DOWN
 * in local space; rotate the parent to aim it. `grip`: 'mitt' (closed),
 * 'open' (fingers splayed / cheering), 'point' (index out). */
const Mitt: React.FC<{x: number; y: number; grip?: 'mitt' | 'open' | 'point'; flip?: boolean}> = ({x, y, grip = 'mitt', flip = false}) => (
  <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
    {/* cuff */}
    <rect x="-13" y="-8" width="26" height="12" rx="5" fill={GOLD} />
    {grip === 'point' ? (
      <>
        <path d="M-12,2 Q-16,20 -4,24 Q10,27 14,16 Q16,10 12,4 Z" fill={NAVY_FILL} stroke={EMERALD_LINE} strokeWidth="3.5" strokeLinejoin="round" />
        <rect x="6" y="10" width="22" height="11" rx="5.5" fill={NAVY_FILL} stroke={EMERALD_LINE} strokeWidth="3.5" />
      </>
    ) : grip === 'open' ? (
      <>
        <path d="M-14,0 Q-20,18 -8,25 Q4,30 14,22 Q20,16 16,4 Z" fill={NAVY_FILL} stroke={EMERALD_LINE} strokeWidth="3.5" strokeLinejoin="round" />
        <circle cx="-10" cy="24" r="6" fill={NAVY_FILL} stroke={EMERALD_LINE} strokeWidth="3" />
        <circle cx="2" cy="28" r="6" fill={NAVY_FILL} stroke={EMERALD_LINE} strokeWidth="3" />
        <circle cx="13" cy="23" r="6" fill={NAVY_FILL} stroke={EMERALD_LINE} strokeWidth="3" />
      </>
    ) : (
      <>
        <path d="M-13,0 Q-18,16 -8,23 Q2,29 12,23 Q19,17 14,2 Z" fill={NAVY_FILL} stroke={EMERALD_LINE} strokeWidth="3.5" strokeLinejoin="round" />
        {/* finger seams */}
        <path d="M-2,6 L-2,22 M7,5 L8,19" stroke={EMERALD_LINE} strokeWidth="2.5" strokeLinecap="round" fill="none" opacity="0.7" />
        {/* thumb */}
        <ellipse cx="-13" cy="10" rx="6" ry="8" fill={NAVY_FILL} stroke={EMERALD_LINE} strokeWidth="3" />
      </>
    )}
  </g>
);

/** Chunky boot: dark navy body, thin emerald sole glow. Drawn with the
 * ankle at local (0,0), sole resting ~15px below. */
const Boot: React.FC<{x: number; y: number; flip?: boolean}> = ({x, y, flip = false}) => (
  <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
    <path d="M-11,-6 L-11,8 Q-11,14 -4,15 L18,15 Q26,15 25,7 Q24,0 16,-1 L9,-2 L9,-6 Q9,-11 -1,-11 Q-11,-11 -11,-6 Z" fill={NAVY_FILL} stroke="#0a0f1a" strokeWidth="3" strokeLinejoin="round" />
    <path d="M-11,12 L25,12 L25,10 Q26,15 18,15 L-4,15 Q-11,14 -11,9 Z" fill={EMERALD_LINE} opacity="0.85" />
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
    <path d={`M${x},${y} Q${x + (flip ? -7 : 7)},${y + len * 0.55} ${x},${y + len}`} fill="none" stroke={LIMB} strokeWidth="13" strokeLinecap="round" />
    <Mitt x={x} y={y + len} grip={grip} flip={flip} />
  </g>
);

/** Leg: short thick limb from hip to ankle ending in a chunky Boot. */
const Leg: React.FC<{x: number; y: number; angle: number; len?: number; flip?: boolean}> = ({x, y, angle, len = 20, flip = false}) => (
  <g transform={`rotate(${angle} ${x} ${y})`}>
    <line x1={x} y1={y} x2={x} y2={y + len} stroke={LIMB} strokeWidth="14" strokeLinecap="round" />
    <Boot x={x} y={y + len} flip={flip} />
  </g>
);

export const NovaRig: React.FC<{size?: number; mode?: RigMode; thetaOverride?: number; speed?: number; frameOverride?: number}> = ({
  size = 240,
  mode = 'idle',
  thetaOverride,
  speed = 1,
  frameOverride,
}) => {
  const currentFrame = useCurrentFrame();
  const frame = (frameOverride ?? currentFrame) * speed;
  const pose = computeNovaPose(frame, mode);
  const theta = thetaOverride ?? pose.theta;
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  const facingFront = c > -0.12;
  const cheer = mode === 'special' && Math.abs(pose.armR) > 5;

  // ------- panel geometry under rotation -------
  // Nova has no separate head — the whole rounded app-icon panel is the
  // faux-3D slab. cos(theta) drives the apparent width, sin(theta) drives
  // the side extrusion + face/tail slide. Past ~90° the face and chat tail
  // hide and a single big sparkle marks the back (the turnaround spec).
  const PANEL_W0 = 116;
  const panelW = PANEL_W0 * (0.68 + 0.32 * Math.abs(c));
  const panelX = 120 - panelW / 2;
  const panelY = 64;
  const panelH = 120;
  const slabW = 16 * Math.abs(s);
  const faceShift = s * 22;
  const eyeSep = 44 * (0.62 + 0.38 * Math.abs(c));
  const eyeRx = 14 * (0.78 + 0.22 * Math.abs(c));
  const twinkle = 0.5 + Math.sin(frame / 9) * 0.5;
  const groundY = 214;
  const shoulderY = panelY + 42;
  const hipY = panelY + panelH - 16;
  const tailOpacity = clamp01((c + 0.12) / 0.35);

  const star = (cx: number, cy: number, r: number, o: number) => (
    <path
      d={`M${cx},${cy - r} Q${cx + r * 0.22},${cy - r * 0.22} ${cx + r},${cy} Q${cx + r * 0.22},${cy + r * 0.22} ${cx},${cy + r} Q${cx - r * 0.22},${cy + r * 0.22} ${cx - r},${cy} Q${cx - r * 0.22},${cy - r * 0.22} ${cx},${cy - r} Z`}
      fill={C.amber}
      opacity={o}
    />
  );

  return (
    <svg width={size} height={size} viewBox="0 0 240 240">
      <ellipse cx="120" cy="220" rx={62 - pose.lift * 0.25 - pose.bob * 2} ry={9 - pose.lift * 0.04} fill="#000" opacity={0.28 - pose.lift * 0.0015} />
      {/* squash/stretch + jump pivot about the ground point */}
      <g transform={`translate(0 ${pose.bob - pose.lift}) translate(120 ${groundY}) scale(${2 - pose.squash} ${pose.squash}) rotate(${pose.lean}) translate(-120 -${groundY})`}>
        {/* legs + chunky boots */}
        <Leg x={100} y={hipY} angle={pose.legL} len={18} flip={s < 0.15} />
        <Leg x={140} y={hipY} angle={pose.legR} len={18} />

        {/* far arm — anchored just outside the panel edge */}
        <Arm x={panelX - 4} y={shoulderY} angle={pose.armL + 9} len={32} grip={cheer ? 'open' : 'mitt'} flip />

        {/* faux-3D depth slab for the panel */}
        {slabW > 1.5 ? <rect x={s > 0 ? panelX - slabW + 3 : panelX + panelW - 3} y={panelY} width={slabW} height={panelH} rx="26" fill="#0c1220" /> : null}

        <defs>
          <linearGradient id="novaRigBody" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#233047" />
            <stop offset="1" stopColor={NAVY_FILL} />
          </linearGradient>
        </defs>

        {/* body: the rounded app-icon panel */}
        <rect x={panelX} y={panelY} width={panelW} height={panelH} rx="32" fill="url(#novaRigBody)" stroke={C.emerald} strokeWidth="4" />

        {/* chat tail — bottom-left, hides past profile */}
        {facingFront ? (
          <path
            d={`M${panelX + panelW * 0.2},${panelY + panelH - 4} L${panelX + panelW * (14 / 120)},${panelY + panelH + 22} L${panelX + panelW * (46 / 120)},${panelY + panelH} Z`}
            fill={NAVY_FILL}
            stroke={C.emerald}
            strokeWidth="4"
            strokeLinejoin="round"
            opacity={tailOpacity}
          />
        ) : null}

        {/* ambient sparkles up front; one big centered sparkle on the back */}
        {facingFront ? (
          <>
            {star(panelX + panelW + 6, panelY - 6, 15, twinkle)}
            {star(panelX - 12, panelY + 40, 8, 1 - twinkle * 0.6)}
            {star(panelX + panelW + 8, panelY + 78, 6.5, 0.4 + twinkle * 0.5)}
          </>
        ) : (
          star(120, panelY + panelH / 2, 32, 0.75 + twinkle * 0.25)
        )}

        {facingFront ? (
          <>
            <Eye cx={120 + faceShift - eyeSep / 2} cy={panelY + 52} rx={eyeRx} blink={pose.blink} look={s * 4 + 2} />
            <Eye cx={120 + faceShift + eyeSep / 2} cy={panelY + 52} rx={eyeRx} blink={pose.blink} look={s * 4 + 2} />
            <Smile x={120 + faceShift * 1.05} y={panelY + 86} w={pose.smileBig ? 24 : 30} open={pose.smileBig} />
          </>
        ) : null}

        {/* LAUNCH finale: 6-point sparkle burst, scales out radially + fades */}
        {mode === 'special' && pose.burstT >= 0
          ? Array.from({length: 6}).map((_, i) => {
              const ang = (i / 6) * Math.PI * 2 + 0.35;
              const dist = 18 + pose.burstT * 76;
              const bx = 120 + Math.cos(ang) * dist;
              const by = panelY + 50 + Math.sin(ang) * dist * 0.82;
              const r = 13 - pose.burstT * 5;
              const op = Math.max(0, 1 - pose.burstT);
              return <React.Fragment key={i}>{star(bx, by, r, op)}</React.Fragment>;
            })
          : null}

        {/* near arm — torso shoulder, outside its edge */}
        {pose.wave ? (
          <Arm x={panelX + panelW + 4} y={shoulderY} angle={-148 + pose.armR} len={32} grip="open" />
        ) : pose.point ? (
          <Arm x={panelX + panelW + 4} y={shoulderY} angle={-96} len={40} grip="point" />
        ) : (
          <Arm x={panelX + panelW + 4} y={shoulderY} angle={pose.armR - 9} len={32} grip={cheer ? 'open' : 'mitt'} />
        )}
      </g>
    </svg>
  );
};
