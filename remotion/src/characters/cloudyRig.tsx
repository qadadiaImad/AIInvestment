// cloudyRig.tsx — Cloudy as a COMPLETE rigged character: parameterized
// rotation (full 360° turnaround with faux-3D side extrusion), limbs, and a
// move set (idle / walk / wave / point / jump / turn / special). Everything
// is derived from a rotation angle theta and a local clock, so any scene can
// pose him.
//
// Cloudy is vapor, not machinery: he FLOATS. His "walk" is a gliding drift
// (stronger bob, trailing dangled legs, slight lean into travel) rather than
// a stepping gait, and his "jump" is an updraft float (slow rise, hang,
// gentle sink — no hard squash landing). His signature move is DATA RAIN:
// staggered emerald droplets fall from his base while the server-light strip
// chases in sequence and he wiggles contentedly.
//
// Faux-3D model: the three cloud lobes + base slab are treated as a rounded
// paper-toy fold. cos(theta) drives the apparent width (lobes pulled toward
// the vertical centerline as they narrow), sin(theta) drives the side
// extrusion slab and how far the face slides across the front. Past ±90° the
// face + light strip hide and a plain back panel with a small exhaust-fan
// detail shows — matching chipRig's turnaround treatment.
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C} from '../slides/theme';

export type RigMode = 'idle' | 'walk' | 'wave' | 'point' | 'jump' | 'turn' | 'special';

const MITT_FILL = '#d7dfe8';
const MITT_STROKE = '#5c6b7e';
const CUFF_GOLD = '#caa64a';
const LIMB_COLOR = '#7c8fa5';
const BOOT_FILL = '#7c8fa5';
const BOOT_STROKE = '#4a5768';
const BOOT_SOLE = '#3f4a58';
const SLAB_COLOR = '#6f8299';
const STRIP_BG = '#5c6b7e';
const PUPIL = '#2a3646';

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

/** All pose state the SVG needs, derived per-frame by the mode logic. */
type Pose = {
  theta: number; // rotation around vertical axis, radians (0 = facing camera)
  bob: number; // vertical float offset
  lift: number; // updraft height (positive = up)
  squash: number; // ~1 always — Cloudy is vapor, no hard squash/stretch
  lean: number; // body tilt degrees (travel lean / contented wiggle)
  legL: number; // leg pendulum swing degrees
  legR: number;
  armL: number; // arm swing degrees relative to hanging
  armR: number;
  wave: boolean; // right arm in wave position (armR = wave phase instead)
  point: boolean; // right arm extended pointing
  special: boolean; // data-rain signature move active
  blink: number;
};

const computeCloudyPose = (frame: number, mode: RigMode): Pose => {
  const blinkT = (frame + 101) % 120; // phase-shifted so the family never blinks in unison
  const blink = blinkT < 4 ? 0.12 : blinkT < 8 ? 1 - Math.abs(6 - blinkT) * 0.22 : 1;
  const floatBob = Math.sin(frame / 26) * 6;

  const base: Pose = {
    theta: 0,
    bob: floatBob,
    lift: 0,
    squash: 1,
    lean: 0,
    legL: Math.sin(frame / 18) * 10,
    legR: Math.sin(frame / 18 + 1.1) * 9,
    armL: Math.sin(frame / 24) * 5,
    armR: -Math.sin(frame / 24) * 5,
    wave: false,
    point: false,
    special: false,
    blink,
  };

  switch (mode) {
    case 'idle':
      return base;
    case 'turn':
      // one full revolution every 240 frames; legs keep dangling throughout
      return {...base, theta: ((frame % 240) / 240) * Math.PI * 2, bob: Math.sin(frame / 20) * 4};
    case 'walk': {
      // gliding drift, not a stepping gait: stronger bob, legs trailing
      // loosely behind, body tilted into the direction of travel
      const trail = Math.sin(frame / 9) * 12;
      return {
        ...base,
        theta: 0.24,
        bob: Math.sin(frame / 10) * 10 - 4,
        lean: 4,
        legL: 24 + trail,
        legR: 20 + Math.sin(frame / 9 + 0.7) * 12,
        armL: -6 + Math.sin(frame / 10) * 6,
        armR: 6 - Math.sin(frame / 10) * 6,
      };
    }
    case 'wave':
      return {...base, wave: true, armR: Math.sin(frame / 6) * 28};
    case 'point':
      return {...base, theta: 0.2, point: true, armL: 2};
    case 'jump': {
      // updraft float: slow rise -> hang -> gentle sink, eased with sine —
      // no anticipation crouch, no hard landing squash (he's vapor)
      const t = frame % 140;
      let lift = 0;
      if (t < 40) {
        const u = t / 40;
        lift = ((1 - Math.cos(Math.PI * u)) / 2) * 68;
      } else if (t < 95) {
        lift = 68 + Math.sin(((t - 40) / 55) * Math.PI * 2) * 4;
      } else {
        const u = (t - 95) / 45;
        lift = 68 * (1 - (1 - Math.cos(Math.PI * u)) / 2);
      }
      const squash = 1 + Math.sin(frame / 10) * 0.015;
      const armRaise = clamp01(lift / 68) * -18;
      return {
        ...base,
        lift,
        squash,
        bob: 0,
        armL: armRaise + Math.sin(frame / 16) * 4,
        armR: -armRaise - Math.sin(frame / 16) * 4,
        legL: Math.sin(frame / 14) * 14,
        legR: Math.sin(frame / 14 + 1.2) * 13,
      };
    }
    case 'special':
      // DATA RAIN: contented side-to-side wiggle while droplets fall and
      // the light strip chases (droplets + chase computed in the component,
      // where per-particle staggering is easiest to lay out)
      return {
        ...base,
        special: true,
        lean: Math.sin(frame / 8) * 5,
        legL: Math.sin(frame / 16) * 8,
        legR: Math.sin(frame / 16 + 1) * 7,
      };
  }
};

const Eye: React.FC<{cx: number; cy: number; rx: number; blink: number; look: number}> = ({cx, cy, rx, blink, look}) => (
  <g transform={`translate(${cx} ${cy}) scale(1 ${blink})`}>
    <ellipse cx="0" cy="0" rx={rx} ry={rx * 1.17} fill="#FDFEFF" />
    <circle cx={look} cy="2.5" r={rx * 0.44} fill={PUPIL} />
    <circle cx={look + rx * 0.15} cy="0.2" r={rx * 0.14} fill="#FDFEFF" opacity="0.9" />
  </g>
);

/** Brawlhalla-proportioned mitt: an oversized rounded hand — puffy light
 * grey with a slate-blue stroke and a gold wrist cuff. Drawn pointing DOWN
 * in local space; rotate the parent to aim it. `grip`: 'mitt' (closed),
 * 'open' (fingers splayed), 'point' (index out). */
const Mitt: React.FC<{x: number; y: number; grip?: 'mitt' | 'open' | 'point'; flip?: boolean}> = ({x, y, grip = 'mitt', flip = false}) => (
  <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
    {/* cuff */}
    <rect x="-13" y="-8" width="26" height="12" rx="5" fill={CUFF_GOLD} />
    {grip === 'point' ? (
      <>
        <path d="M-12,2 Q-16,20 -4,24 Q10,27 14,16 Q16,10 12,4 Z" fill={MITT_FILL} stroke={MITT_STROKE} strokeWidth="3.5" strokeLinejoin="round" />
        <rect x="6" y="10" width="22" height="11" rx="5.5" fill={MITT_FILL} stroke={MITT_STROKE} strokeWidth="3.5" />
      </>
    ) : grip === 'open' ? (
      <>
        <path d="M-14,0 Q-20,18 -8,25 Q4,30 14,22 Q20,16 16,4 Z" fill={MITT_FILL} stroke={MITT_STROKE} strokeWidth="3.5" strokeLinejoin="round" />
        <circle cx="-10" cy="24" r="6" fill={MITT_FILL} stroke={MITT_STROKE} strokeWidth="3" />
        <circle cx="2" cy="28" r="6" fill={MITT_FILL} stroke={MITT_STROKE} strokeWidth="3" />
        <circle cx="13" cy="23" r="6" fill={MITT_FILL} stroke={MITT_STROKE} strokeWidth="3" />
      </>
    ) : (
      <>
        <path d="M-13,0 Q-18,16 -8,23 Q2,29 12,23 Q19,17 14,2 Z" fill={MITT_FILL} stroke={MITT_STROKE} strokeWidth="3.5" strokeLinejoin="round" />
        {/* finger seams */}
        <path d="M-2,6 L-2,22 M7,5 L8,19" stroke={MITT_STROKE} strokeWidth="2.5" strokeLinecap="round" fill="none" opacity="0.7" />
        {/* thumb */}
        <ellipse cx="-13" cy="10" rx="6" ry="8" fill={MITT_FILL} stroke={MITT_STROKE} strokeWidth="3" />
      </>
    )}
  </g>
);

/** Chunky boot: big rounded toe, heel, contrasting sole. Drawn with the
 * ankle at local (0,0), sole resting ~15px below. */
const Boot: React.FC<{x: number; y: number; flip?: boolean}> = ({x, y, flip = false}) => (
  <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
    <path
      d="M-11,-6 L-11,8 Q-11,14 -4,15 L18,15 Q26,15 25,7 Q24,0 16,-1 L9,-2 L9,-6 Q9,-11 -1,-11 Q-11,-11 -11,-6 Z"
      fill={BOOT_FILL}
      stroke={BOOT_STROKE}
      strokeWidth="3"
      strokeLinejoin="round"
    />
    <path d="M-11,12 L25,12 L25,10 Q26,15 18,15 L-4,15 Q-11,14 -11,9 Z" fill={BOOT_SOLE} />
  </g>
);

/** Arm: slim two-point limb from shoulder to wrist with a slight elbow bow,
 * ending in an oversized Mitt. Rotates about the shoulder. */
const Arm: React.FC<{x: number; y: number; angle: number; len?: number; grip?: 'mitt' | 'open' | 'point'; flip?: boolean}> = ({
  x,
  y,
  angle,
  len = 30,
  grip = 'mitt',
  flip = false,
}) => (
  <g transform={`rotate(${angle} ${x} ${y})`}>
    <path d={`M${x},${y} Q${x + (flip ? -6 : 6)},${y + len * 0.55} ${x},${y + len}`} fill="none" stroke={LIMB_COLOR} strokeWidth="12" strokeLinecap="round" />
    <Mitt x={x} y={y + len} grip={grip} flip={flip} />
  </g>
);

/** Leg: short thick limb from hip to ankle ending in a chunky Boot. Cloudy's
 * legs never plant — they dangle and pendulum-swing, even when idle. */
const Leg: React.FC<{x: number; y: number; angle: number; len?: number; flip?: boolean}> = ({x, y, angle, len = 16, flip = false}) => (
  <g transform={`rotate(${angle} ${x} ${y})`}>
    <line x1={x} y1={y} x2={x} y2={y + len} stroke={LIMB_COLOR} strokeWidth="13" strokeLinecap="round" />
    <Boot x={x} y={y + len} flip={flip} />
  </g>
);

export const CloudyRig: React.FC<{size?: number; mode?: RigMode; thetaOverride?: number; speed?: number; frameOverride?: number}> = ({
  size = 240,
  mode = 'idle',
  thetaOverride,
  speed = 1,
  frameOverride,
}) => {
  const currentFrame = useCurrentFrame();
  const frame = (frameOverride ?? currentFrame) * speed;
  const pose = computeCloudyPose(frame, mode);
  const theta = thetaOverride ?? pose.theta;
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  const facingFront = c > -0.12;

  // ------- cloud-body geometry under rotation -------
  // Three lobes + a base slab, paper-toy folded: cos(theta) narrows the
  // apparent width and pulls each lobe toward the vertical centerline,
  // sin(theta) drives the side-extrusion slab and how far the face/strip
  // slide across the front, matching chipRig's turnaround treatment.
  const wf = 0.68 + 0.32 * Math.abs(c); // width factor
  const faceShift = s * 22;
  const groundY = 214;

  const lobe = (cx0: number, cy0: number, r: number) => ({
    cx: 120 + (cx0 - 120) * wf,
    cy: cy0,
    rx: r * wf,
    ry: r,
  });
  const lobeL = lobe(86, 130, 44);
  const lobeM = lobe(132, 106, 52);
  const lobeR = lobe(168, 142, 38);

  const baseW = 150 * wf;
  const baseX = 120 - baseW / 2;

  const stripW = 76 * wf;
  const stripX = 120 - stripW / 2 + faceShift * 0.4;

  const eyeSep = 42 * (0.62 + 0.38 * Math.abs(c));
  const eyeCy = 124;

  const halfW = 84 * wf;
  const slabW = 22 * Math.abs(s);
  const slabX = s > 0 ? 120 - halfW - slabW + 4 : 120 + halfW - 4;

  const hipLx = baseX + baseW * 0.35;
  const hipRx = baseX + baseW * 0.65;
  const shoulderXL = baseX - 6;
  const shoulderXR = baseX + baseW + 6;
  const shoulderY = 158;

  // server light strip: gentle ambient shimmer normally, sequential chase
  // during the DATA RAIN special move
  const lightColors = [C.emerald, C.amber, C.redHot];
  const chaseIdx = Math.floor(frame / 6) % lightColors.length;
  const lights = lightColors.map((col, i) => ({
    col,
    on: pose.special ? i === chaseIdx : Math.sin(frame / 10 + i * 2.1) > -0.2,
  }));

  // DATA RAIN droplets — 7 tiny emerald drops raining from the base in
  // staggered loops, only during the special move
  const DROP_N = 7;
  const drops = pose.special
    ? Array.from({length: DROP_N}).map((_, i) => {
        const period = 46;
        const t = (frame + i * 7) % period;
        const u = t / period;
        const x = 92 + i * 9;
        const y = 186 + u * 48;
        const o = u < 0.15 ? u / 0.15 : u > 0.8 ? (1 - u) / 0.2 : 1;
        return {x, y, o};
      })
    : [];

  const fanSpin = frame * 6;
  const fanCx = 120 + faceShift * 0.5;

  return (
    <svg width={size} height={size} viewBox="0 0 240 240">
      <ellipse cx="120" cy="220" rx={62 - pose.lift * 0.25 - pose.bob * 2} ry={9 - pose.lift * 0.04} fill="#000" opacity={0.28 - pose.lift * 0.0015} />
      {/* soft float bob + updraft lift + gentle lean/wiggle, pivoting about the ground point */}
      <g transform={`translate(0 ${pose.bob - pose.lift}) translate(120 ${groundY}) scale(${2 - pose.squash} ${pose.squash}) rotate(${pose.lean}) translate(-120 -${groundY})`}>
        {/* legs — short, always dangling, pendulum swing */}
        <Leg x={hipLx} y={182} angle={pose.legL} len={16} flip={s < 0.15} />
        <Leg x={hipRx} y={182} angle={pose.legR} len={16} />

        {/* far arm — anchored just outside the cloud silhouette */}
        <Arm x={shoulderXL} y={shoulderY} angle={pose.armL + 8} len={30} grip="mitt" flip />

        {/* faux-3D depth slab */}
        {slabW > 1.5 ? <rect x={slabX} y="66" width={slabW} height="104" rx="16" fill={SLAB_COLOR} /> : null}

        {/* puffy three-lobe cloud body */}
        <defs>
          <linearGradient id="cloudyRigBody" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#b6c5d6" />
            <stop offset="1" stopColor="#8fa2b8" />
          </linearGradient>
        </defs>
        <g fill="url(#cloudyRigBody)">
          <ellipse cx={lobeL.cx} cy={lobeL.cy} rx={lobeL.rx} ry={lobeL.ry} />
          <ellipse cx={lobeM.cx} cy={lobeM.cy} rx={lobeM.rx} ry={lobeM.ry} />
          <ellipse cx={lobeR.cx} cy={lobeR.cy} rx={lobeR.rx} ry={lobeR.ry} />
          <rect x={baseX} y="130" width={baseW} height="52" rx="22" />
        </g>

        {facingFront ? (
          <>
            {/* server light strip — hidden on the back view */}
            <rect x={stripX} y="160" width={stripW} height="16" rx="8" fill={STRIP_BG} />
            {lights.map((l, i) => (
              <circle key={i} cx={stripX + stripW * (0.18 + i * 0.32)} cy="168" r="5" fill={l.col} opacity={l.on ? 1 : 0.25} />
            ))}
            <Eye cx={120 + faceShift - eyeSep / 2} cy={eyeCy} rx={13.5} blink={pose.blink} look={s * 4} />
            <Eye cx={120 + faceShift + eyeSep / 2} cy={eyeCy} rx={13.5} blink={pose.blink} look={s * 4} />
            <path
              d={`M${120 + faceShift - 13},146 Q${120 + faceShift},156 ${120 + faceShift + 13},146`}
              fill="none"
              stroke={PUPIL}
              strokeWidth="5"
              strokeLinecap="round"
            />
          </>
        ) : (
          <g>
            {/* back view: plain cloud, no face, no light strip — just a
                small spinning exhaust-fan detail */}
            <circle cx={fanCx} cy="140" r="17" fill={SLAB_COLOR} opacity="0.9" />
            <g transform={`rotate(${fanSpin} ${fanCx} 140)`} stroke="#4a5768" strokeWidth="4" strokeLinecap="round">
              <line x1={fanCx} y1="128" x2={fanCx} y2="152" />
              <line x1={fanCx - 12} y1="140" x2={fanCx + 12} y2="140" />
            </g>
            <circle cx={fanCx} cy="140" r="4" fill={PUPIL} />
          </g>
        )}

        {/* DATA RAIN droplets */}
        {drops.map((d, i) => (
          <ellipse key={i} cx={d.x} cy={d.y} rx="3.2" ry="5.5" fill={C.emerald} opacity={d.o} />
        ))}

        {/* near arm — anchored just outside the cloud silhouette */}
        {pose.wave ? (
          <Arm x={shoulderXR} y={shoulderY} angle={-148 + pose.armR} len={30} grip="open" />
        ) : pose.point ? (
          <Arm x={shoulderXR} y={shoulderY} angle={-96} len={38} grip="point" />
        ) : (
          <Arm x={shoulderXR} y={shoulderY} angle={pose.armR - 8} len={30} grip="mitt" />
        )}
      </g>
    </svg>
  );
};
