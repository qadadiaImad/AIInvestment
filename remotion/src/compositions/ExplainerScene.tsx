// ExplainerScene.tsx — proof-of-concept for character-driven explainer
// movies: Chip walks on stage, stops beside a live-data chart, points at
// each bar while caption beats pop, then celebrates with a jump. 9:16 reel
// canvas. The scene pattern (enter → point → beat captions → react) is the
// building block for full cartoon explainers.
import React from 'react';
import {AbsoluteFill, interpolate, Sequence, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {z} from 'zod';
import {C, FONT} from '../slides/theme';
import {Bg, Foot} from '../slides/ui';
import {FloatingBlob} from '../slides/kurz';
import {ChipRig} from '../characters/chipRig';

export const explainerSceneSchema = z.object({
  kick: z.string(),
  title: z.string(),
  bars: z.array(z.object({label: z.string(), value: z.number(), color: z.string()})).length(2),
  beats: z.array(z.object({text: z.string(), at: z.number()})).min(1).max(4),
  footer: z.string(),
  durationInFrames: z.number(),
});
export type ExplainerSceneProps = z.infer<typeof explainerSceneSchema>;

const WALK_END = 70; // Chip reaches his mark
const JUMP_AT = 330; // celebration

const Chart: React.FC<{bars: ExplainerSceneProps['bars']}> = ({bars}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const max = Math.max(...bars.map((b) => b.value));
  const H = 560;
  return (
    <div style={{display: 'flex', alignItems: 'flex-end', gap: 60, height: H + 90}}>
      {bars.map((b, i) => {
        const p = spring({frame: frame - (WALK_END + 18 + i * 30), fps, config: {damping: 13, mass: 0.8, stiffness: 100}});
        const h = Math.max(8, (b.value / max) * H * Math.min(1, p));
        return (
          <div key={b.label} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16}}>
            <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 54, color: b.color, opacity: Math.min(1, p * 1.3)}}>
              ${b.value.toFixed(0)}
            </div>
            <div
              style={{
                width: 190,
                height: h,
                borderRadius: 24,
                background: `linear-gradient(180deg, ${b.color}, ${b.color}88)`,
                boxShadow: `0 0 40px ${b.color}44`,
              }}
            />
            <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 26, letterSpacing: 2, color: C.muted}}>{b.label}</div>
          </div>
        );
      })}
    </div>
  );
};

const Beat: React.FC<{text: string}> = ({text}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame, fps, config: {damping: 12, mass: 0.6, stiffness: 170}});
  const s = Math.min(1, p);
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
        opacity: Math.min(1, p * 1.4),
        scale: String(0.9 + 0.1 * s),
        translate: `0px ${(1 - s) * 26}px`,
        textShadow: '0 6px 30px rgba(0,0,0,.6)',
      }}
    >
      {text}
    </div>
  );
};

export const ExplainerScene: React.FC<ExplainerSceneProps> = (props) => {
  const frame = useCurrentFrame();
  // Chip enters from off-screen left, walks to his mark, then presents.
  const chipX = interpolate(frame, [0, WALK_END], [-360, 40], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const chipMode = frame < WALK_END ? 'walk' : frame >= JUMP_AT ? 'jump' : 'point';
  const currentBeat = [...props.beats].reverse().find((b) => frame >= b.at);
  return (
    <AbsoluteFill style={{fontFamily: FONT.body}}>
      <Bg tint={C.emerald} />
      <FloatingBlob size={900} x={80} y={12} hue={C.emerald} hue2={C.mint} seed={11} opacity={0.15} />
      {/* header — absolutely positioned: the Bg layer is in-flow/full-size,
          so any in-flow sibling would be pushed below the canvas */}
      <div style={{position: 'absolute', top: 130, left: 0, right: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16}}>
        <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 28, letterSpacing: 5, color: C.bg, background: C.emerald, padding: '13px 26px', borderRadius: 999}}>
          {props.kick}
        </div>
        <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 72, color: C.ink, textAlign: 'center', maxWidth: 940}}>{props.title}</div>
      </div>
      {/* stage: chart right, Chip left on a shared ground line */}
      <div style={{position: 'absolute', right: 90, bottom: 560}}>
        <Chart bars={props.bars} />
      </div>
      <div style={{position: 'absolute', left: chipX, bottom: 520}}>
        <ChipRig size={520} mode={chipMode} />
      </div>
      {/* ground line */}
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 600, height: 3, background: C.line}} />
      {/* caption beats */}
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 260, display: 'flex', justifyContent: 'center', padding: '0 70px'}}>
        {currentBeat ? (
          <Sequence key={currentBeat.at} from={currentBeat.at} layout="none">
            <Beat text={currentBeat.text} />
          </Sequence>
        ) : null}
      </div>
      <AbsoluteFill style={{padding: '0 40px 26px', alignItems: 'center', justifyContent: 'flex-end', pointerEvents: 'none'}}>
        <Foot text={props.footer} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
