// ExplainerSceneV2.tsx — the same scene as ExplainerScene, rebuilt on the
// motion-craft library (references/animation-craft-playbook.md). Same props,
// premium motion: camera push-in with an emphasis hit when the second bar
// lands, parallax depth layers, staggered builds on house curves, data bars
// landing with clamped overshoot (facts don't wobble), caption beats on
// snappy springs with accelerating exits, grain + vignette + key glow.
// Kept separate from V1 so before/after renders stay comparable.
import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, FONT} from '../slides/theme';
import {Bg} from '../slides/ui';
import {FloatingBlob} from '../slides/kurz';
import {RIGS} from './FamilyRigShowcase';
import {explainerSceneSchema, type ExplainerSceneProps} from './ExplainerScene';
import {EASE, SPRINGS, FRAMES, stagger, fadeOf, exitFrames, cameraPushIn, DEPTH, wiggle} from '../motion/craft';
import {Grain, Vignette, KeyGlow} from '../motion/Polish';

export const explainerSceneV2Schema = explainerSceneSchema;

const WALK_END = 70;
const JUMP_AT = 330;
const BAR2_LAND = 118; // camera emphasis hit: the second (market) bar lands

const ChartV2: React.FC<{bars: ExplainerSceneProps['bars']}> = ({bars}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const max = Math.max(...bars.map((b) => b.value));
  const H = 560;
  return (
    <div style={{display: 'flex', alignItems: 'flex-end', gap: 60, height: H + 90}}>
      {bars.map((b, i) => {
        const delay = WALK_END + 18 + stagger(i, bars.length, 'dramatic') * 6;
        // data personality: confident landing, overshoot clamped (§3)
        const p = spring({frame: frame - delay, fps, config: SPRINGS.data});
        const h = Math.max(8, (b.value / max) * H * p);
        // value label pops AFTER its bar lands, on the hero spring
        const vp = spring({frame: frame - delay - 14, fps, config: SPRINGS.hero});
        return (
          <div key={b.label} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16}}>
            <div
              style={{
                fontFamily: FONT.display,
                fontWeight: 700,
                fontSize: 54,
                color: b.color,
                opacity: fadeOf(vp),
                scale: String(0.8 + 0.2 * Math.min(1, vp)),
                translate: `0px ${(1 - Math.min(1, vp)) * 18}px`,
              }}
            >
              ${b.value.toFixed(0)}
            </div>
            <div
              style={{
                width: 190,
                height: h,
                borderRadius: 24,
                background: `linear-gradient(180deg, ${b.color}, ${b.color}88)`,
                boxShadow: `0 0 40px ${b.color}44, inset 0 3px 14px rgba(255,255,255,.28)`,
              }}
            />
            <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 26, letterSpacing: 2, color: C.muted, opacity: fadeOf(p)}}>
              {b.label}
            </div>
          </div>
        );
      })}
    </div>
  );
};

const BeatV2: React.FC<{text: string; frame: number; endFrame: number}> = ({text, frame, endFrame}) => {
  const {fps} = useVideoConfig();
  const p = spring({frame, fps, config: SPRINGS.snappy});
  const s = Math.min(1, p);
  // exit: accelerate out over 70% of a card entrance, just before the next beat
  const exitStart = endFrame - exitFrames(FRAMES.card) - 2;
  const out = interpolate(frame, [exitStart, endFrame], [0, 1], {
    easing: EASE.exit,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div
      style={{
        fontFamily: FONT.body,
        fontWeight: 700,
        fontSize: 52,
        lineHeight: 1.25,
        color: C.ink,
        textAlign: 'center',
        maxWidth: 900,
        opacity: fadeOf(p) * (1 - out),
        scale: String((0.92 + 0.08 * s) * (1 - out * 0.06)),
        translate: `0px ${(1 - s) * 24 - out * 14}px`,
        textShadow: '0 6px 30px rgba(0,0,0,.6)',
      }}
    >
      {text}
    </div>
  );
};

export const ExplainerSceneV2: React.FC<ExplainerSceneProps> = (props) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const chipX = interpolate(frame, [0, WALK_END], [-360, 40], {
    easing: EASE.cruise,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const chipMode = frame < WALK_END ? 'walk' : frame >= JUMP_AT ? 'jump' : 'point';
  const beatWindows = props.beats.map((b, i) => ({...b, end: props.beats[i + 1]?.at ?? props.durationInFrames}));
  const currentBeat = [...beatWindows].reverse().find((b) => frame >= b.at);
  // ONE camera intention: slow 3% push-in, emphasis hit when bar 2 lands
  const cam = cameraPushIn(frame, props.durationInFrames, {hitFrame: BAR2_LAND});
  const camDrift = (cam - 1) * 220; // px of implied camera travel for parallax
  // header entrance: kick then title, staggered on house curves
  const kickP = spring({frame: frame - 4, fps, config: SPRINGS.pop});
  const titleP = spring({frame: frame - 10, fps, config: SPRINGS.hero});
  const Rig = RIGS[props.character ?? 'chip'];
  return (
    <AbsoluteFill style={{fontFamily: FONT.body, background: C.bg}}>
      {/* depth: background layer moves at 0.3x of camera */}
      <AbsoluteFill style={{translate: `0px ${-camDrift * DEPTH.bg}px`}}>
        <Bg tint={C.emerald} />
        <FloatingBlob size={900} x={80} y={12} hue={C.emerald} hue2={C.mint} seed={11} opacity={0.15} />
        <KeyGlow x={62} y={44} color={C.emerald} />
      </AbsoluteFill>
      {/* camera rig wraps the stage (mid+fg) */}
      <AbsoluteFill style={{scale: String(cam), transformOrigin: '50% 46%'}}>
        {/* header */}
        <div style={{position: 'absolute', top: 130 - camDrift * DEPTH.mid, left: 0, right: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16}}>
          <div
            style={{
              fontFamily: FONT.mono,
              fontWeight: 700,
              fontSize: 28,
              letterSpacing: 5,
              color: C.bg,
              background: C.emerald,
              padding: '13px 26px',
              borderRadius: 999,
              opacity: fadeOf(kickP),
              scale: String(0.85 + 0.15 * Math.min(1, kickP)),
              translate: `0px ${(1 - Math.min(1, kickP)) * -16}px`,
            }}
          >
            {props.kick}
          </div>
          <div
            style={{
              fontFamily: FONT.display,
              fontWeight: 700,
              fontSize: 72,
              color: C.ink,
              textAlign: 'center',
              maxWidth: 940,
              opacity: fadeOf(titleP),
              scale: String(0.92 + 0.08 * Math.min(1, titleP)),
              translate: `0px ${(1 - Math.min(1, titleP)) * 26}px`,
            }}
          >
            {props.title}
          </div>
        </div>
        {/* stage */}
        <div style={{position: 'absolute', right: 90, bottom: 560, translate: `0px ${wiggle(frame, 3, 2)}px`}}>
          <ChartV2 bars={props.bars} />
        </div>
        <div style={{position: 'absolute', left: chipX, bottom: 520}}>
          <Rig size={520} mode={chipMode} />
        </div>
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 600, height: 3, background: C.line}} />
        {/* caption beats */}
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 260, display: 'flex', justifyContent: 'center', padding: '0 70px'}}>
          {currentBeat ? <BeatV2 key={currentBeat.at} text={currentBeat.text} frame={frame - currentBeat.at} endFrame={currentBeat.end - currentBeat.at} /> : null}
        </div>
      </AbsoluteFill>
      {/* footer stays outside the camera (UI layer) */}
      <AbsoluteFill style={{padding: '0 40px 26px', alignItems: 'center', justifyContent: 'flex-end', pointerEvents: 'none'}}>
        <div style={{fontFamily: FONT.mono, fontSize: 19, color: C.muted, textAlign: 'center'}}>{props.footer}</div>
      </AbsoluteFill>
      <Vignette />
      <Grain />
    </AbsoluteFill>
  );
};
