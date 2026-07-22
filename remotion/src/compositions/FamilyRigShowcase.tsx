// FamilyRigShowcase.tsx — generic review card for ANY family rig: pass a
// character key; 'sheet' renders the 5-angle turnaround + action poses,
// 'demo' renders the animated move reel (incl. the signature special).
import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {C, FONT} from '../slides/theme';
import {Bg, Foot} from '../slides/ui';
import {FloatingBlob} from '../slides/kurz';
import {ChipRig} from '../characters/chipRig';
import {WattRig} from '../characters/wattRig';
import {QubitRig} from '../characters/qubitRig';
import {CapRig} from '../characters/capRig';
import {NovaRig} from '../characters/novaRig';
import {CloudyRig} from '../characters/cloudyRig';
import {CHARACTERS} from '../characters/family';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const RIGS: Record<string, React.FC<any>> = {
  chip: ChipRig,
  watt: WattRig,
  qubit: QubitRig,
  cap: CapRig,
  nova: NovaRig,
  cloudy: CloudyRig,
};

export const familyRigShowcaseSchema = z.object({
  character: z.enum(['chip', 'watt', 'qubit', 'cap', 'nova', 'cloudy']),
  variant: z.enum(['sheet', 'demo']),
  footer: z.string(),
  durationInFrames: z.number(),
});
export type FamilyRigShowcaseProps = z.infer<typeof familyRigShowcaseSchema>;

const ANGLES = [
  {label: 'FRONT', theta: 0},
  {label: '3/4', theta: 0.85},
  {label: 'PROFILE', theta: Math.PI / 2},
  {label: 'BACK', theta: Math.PI},
  {label: '3/4 L', theta: -0.85},
];

// JUMP freezes at the launch stretch (low lift — full body stays in frame);
// SPECIAL frames are hand-picked per character to catch the readable peak
// of each signature move (not a mid-dissolve/mid-spin/blink frame).
const SPECIAL_F: Record<string, number> = {chip: 20, watt: 20, qubit: 44, cap: 20, nova: 55, cloudy: 30};
const POSES = [
  {label: 'WALK', mode: 'walk', f: 8},
  {label: 'WAVE', mode: 'wave', f: 9},
  {label: 'POINT', mode: 'point', f: 30},
  {label: 'JUMP', mode: 'jump', f: 24},
  {label: 'SPECIAL', mode: 'special', f: -1},
] as const;

const SEGMENTS = [
  {label: 'TURNAROUND — 360°', mode: 'turn', frames: 240},
  {label: 'WALK', mode: 'walk', frames: 120},
  {label: 'WAVE', mode: 'wave', frames: 100},
  {label: 'POINT', mode: 'point', frames: 90},
  {label: 'JUMP', mode: 'jump', frames: 180},
  {label: 'SIGNATURE MOVE', mode: 'special', frames: 200},
] as const;
export const FAMILY_DEMO_DURATION = SEGMENTS.reduce((s, x) => s + x.frames, 0);

const Header: React.FC<{kick: string; title: string; color: string}> = ({kick, title, color}) => (
  <div style={{position: 'absolute', top: 96, left: 0, right: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14}}>
    <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 26, letterSpacing: 5, color: C.bg, background: color, padding: '12px 24px', borderRadius: 999}}>
      {kick}
    </div>
    <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 60, color: C.ink}}>{title}</div>
  </div>
);

export const FamilyRigShowcase: React.FC<FamilyRigShowcaseProps> = (props) => {
  const frame = useCurrentFrame();
  const Rig = RIGS[props.character];
  const meta = CHARACTERS.find((ch) => ch.key === props.character)!;
  const isSheet = props.variant === 'sheet';
  let segStart = 0;
  const active = SEGMENTS.find((seg) => {
    const within = frame >= segStart && frame < segStart + seg.frames;
    if (!within) segStart += seg.frames;
    return within;
  });
  return (
    <AbsoluteFill style={{fontFamily: FONT.body}}>
      <Bg tint={C.emerald} />
      <FloatingBlob size={780} x={80} y={12} hue={meta.color} hue2={C.mint} seed={5} opacity={0.15} />
      <Header kick={isSheet ? 'MODEL SHEET' : 'RIG DEMO'} title={`${meta.name} — ${isSheet ? 'full turnaround.' : 'moves & angles.'}`} color={meta.color} />
      {isSheet ? (
        <div style={{position: 'absolute', top: 300, left: 0, right: 0}}>
          <div style={{display: 'flex', justifyContent: 'center'}}>
            {ANGLES.slice(0, 3).map((a) => (
              <div key={a.label} style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
                <Rig size={320} thetaOverride={a.theta} />
                <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 23, letterSpacing: 3, color: C.muted}}>{a.label}</div>
              </div>
            ))}
          </div>
          <div style={{display: 'flex', justifyContent: 'center', gap: 56, marginTop: 6}}>
            {ANGLES.slice(3).map((a) => (
              <div key={a.label} style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
                <Rig size={320} thetaOverride={a.theta} />
                <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 23, letterSpacing: 3, color: C.muted}}>{a.label}</div>
              </div>
            ))}
          </div>
          <div style={{display: 'flex', justifyContent: 'center', gap: 4, marginTop: 8}}>
            {POSES.map((p) => (
              <div key={p.label} style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
                <Rig size={200} mode={p.mode} frameOverride={p.f === -1 ? SPECIAL_F[props.character] : p.f} />
                <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 19, letterSpacing: 2, color: meta.color}}>{p.label}</div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <>
          {(() => {
            let from = 0;
            return SEGMENTS.map((seg) => {
              const el = (
                <Sequence key={seg.label} from={from} durationInFrames={seg.frames}>
                  <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
                    <Rig size={620} mode={seg.mode} />
                  </AbsoluteFill>
                </Sequence>
              );
              from += seg.frames;
              return el;
            });
          })()}
          {active ? (
            <div style={{position: 'absolute', left: 0, right: 0, bottom: 190, display: 'flex', justifyContent: 'center'}}>
              <div
                style={{
                  fontFamily: FONT.mono,
                  fontWeight: 700,
                  fontSize: 28,
                  letterSpacing: 4,
                  color: C.bg,
                  background: meta.color,
                  padding: '13px 28px',
                  borderRadius: 999,
                }}
              >
                {active.label}
              </div>
            </div>
          ) : null}
        </>
      )}
      <AbsoluteFill style={{padding: '0 40px 22px', alignItems: 'center', justifyContent: 'flex-end', pointerEvents: 'none'}}>
        <Foot text={props.footer} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
