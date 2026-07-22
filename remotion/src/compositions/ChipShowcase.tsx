// ChipShowcase.tsx — review card for the fully-rigged Chip character.
// variant 'sheet': static model sheet — five angles of the turnaround.
// variant 'demo': animated reel — turnaround, walk, wave, point, jump.
import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {C, FONT} from '../slides/theme';
import {Bg, Foot} from '../slides/ui';
import {FloatingBlob} from '../slides/kurz';
import {ChipRig} from '../characters/chipRig';

export const chipShowcaseSchema = z.object({
  variant: z.enum(['sheet', 'demo']),
  footer: z.string(),
  durationInFrames: z.number(),
});
export type ChipShowcaseProps = z.infer<typeof chipShowcaseSchema>;

const ANGLES: {label: string; theta: number}[] = [
  {label: 'FRONT', theta: 0},
  {label: '3/4', theta: 0.85},
  {label: 'PROFILE', theta: Math.PI / 2},
  {label: 'BACK', theta: Math.PI},
  {label: '3/4 L', theta: -0.85},
];

const Header: React.FC<{kick: string; title: string}> = ({kick, title}) => (
  <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, paddingTop: 110}}>
    <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 26, letterSpacing: 5, color: C.bg, background: C.emerald, padding: '12px 24px', borderRadius: 999}}>
      {kick}
    </div>
    <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 62, color: C.ink}}>{title}</div>
  </div>
);

const Sheet: React.FC = () => (
  <AbsoluteFill>
    <FloatingBlob size={760} x={78} y={12} hue={C.emerald} hue2={C.mint} seed={5} opacity={0.15} />
    <Header kick="MODEL SHEET" title="Chip — full turnaround." />
    <div style={{display: 'flex', justifyContent: 'center', gap: 0, marginTop: 40, flexWrap: 'wrap'}}>
      {ANGLES.slice(0, 3).map((a) => (
        <div key={a.label} style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
          <ChipRig size={330} thetaOverride={a.theta} />
          <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 24, letterSpacing: 3, color: C.muted}}>{a.label}</div>
        </div>
      ))}
    </div>
    <div style={{display: 'flex', justifyContent: 'center', gap: 60, marginTop: 24}}>
      {ANGLES.slice(3).map((a) => (
        <div key={a.label} style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
          <ChipRig size={330} thetaOverride={a.theta} />
          <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 24, letterSpacing: 3, color: C.muted}}>{a.label}</div>
        </div>
      ))}
    </div>
  </AbsoluteFill>
);

const SEGMENTS: {label: string; mode: 'turn' | 'walk' | 'wave' | 'point' | 'jump'; frames: number}[] = [
  {label: 'TURNAROUND — 360°', mode: 'turn', frames: 240},
  {label: 'WALK CYCLE', mode: 'walk', frames: 120},
  {label: 'WAVE', mode: 'wave', frames: 100},
  {label: 'POINT (chart mode)', mode: 'point', frames: 90},
  {label: 'JUMP — squash & stretch', mode: 'jump', frames: 180},
];
export const DEMO_DURATION = SEGMENTS.reduce((s, x) => s + x.frames, 0);

const DemoSegment: React.FC<{label: string; mode: 'turn' | 'walk' | 'wave' | 'point' | 'jump'}> = ({label, mode}) => {
  const frame = useCurrentFrame();
  const inOp = Math.min(1, frame / 10);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: inOp}}>
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 30}}>
        <ChipRig size={640} mode={mode} />
        <div
          style={{
            fontFamily: FONT.mono,
            fontWeight: 700,
            fontSize: 30,
            letterSpacing: 4,
            color: C.bg,
            background: C.emerald,
            padding: '14px 30px',
            borderRadius: 999,
          }}
        >
          {label}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Demo: React.FC = () => {
  let start = 0;
  return (
    <AbsoluteFill>
      <FloatingBlob size={820} x={50} y={30} hue={C.emerald} hue2={C.mint} seed={7} opacity={0.16} />
      <Header kick="RIG DEMO" title="Chip — moves & angles." />
      {SEGMENTS.map((seg) => {
        const el = (
          <Sequence key={seg.label} from={start} durationInFrames={seg.frames}>
            <DemoSegment label={seg.label} mode={seg.mode} />
          </Sequence>
        );
        start += seg.frames;
        return el;
      })}
    </AbsoluteFill>
  );
};

export const ChipShowcase: React.FC<ChipShowcaseProps> = (props) => (
  <AbsoluteFill style={{fontFamily: FONT.body}}>
    <Bg tint={C.emerald} />
    {props.variant === 'sheet' ? <Sheet /> : <Demo />}
    <AbsoluteFill style={{padding: '0 40px 22px', alignItems: 'center', justifyContent: 'flex-end', pointerEvents: 'none'}}>
      <Foot text={props.footer} />
    </AbsoluteFill>
  </AbsoluteFill>
);
