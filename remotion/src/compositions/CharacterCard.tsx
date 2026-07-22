// CharacterCard.tsx — review/showcase cards for the AI STACK character
// family: a 'lineup' grid of the whole family, or a single-character
// portrait. 1080x1350, same palette/typography as the carousel engine.
import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {z} from 'zod';
import {C, FONT} from '../slides/theme';
import {Bg, Foot} from '../slides/ui';
import {FloatingBlob} from '../slides/kurz';
import {CHARACTERS, CHAR_COMPONENTS, type CharKey} from '../characters/family';

export const characterCardSchema = z.object({
  variant: z.enum(['lineup', 'chip', 'watt', 'qubit', 'cap', 'nova', 'cloudy']),
  footer: z.string(),
  durationInFrames: z.number(),
});
export type CharacterCardProps = z.infer<typeof characterCardSchema>;

const Pop: React.FC<{delay: number; children: React.ReactNode}> = ({delay, children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - delay, fps, config: {damping: 11, mass: 0.6, stiffness: 160}});
  const s = Math.min(1, p);
  return (
    <div style={{opacity: Math.min(1, p * 1.5), scale: String(0.8 + 0.2 * s), translate: `0px ${(1 - s) * 30}px`}}>
      {children}
    </div>
  );
};

const Lineup: React.FC = () => (
  <AbsoluteFill style={{padding: '120px 60px 120px'}}>
    <FloatingBlob size={760} x={80} y={10} hue={C.emerald} hue2={C.mint} seed={5} opacity={0.16} />
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6}}>
      <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 26, letterSpacing: 5, color: C.bg, background: C.emerald, padding: '12px 24px', borderRadius: 999}}>
        MEET THE STACK
      </div>
      <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 66, color: C.ink, marginTop: 16}}>The AI STACK family.</div>
      <div style={{fontFamily: FONT.body, fontSize: 25, color: C.inkSoft}}>One character per layer of the AI value chain.</div>
    </div>
    <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', rowGap: 26, columnGap: 12, marginTop: 40}}>
      {CHARACTERS.map((ch, i) => {
        const Comp = CHAR_COMPONENTS[ch.key];
        return (
          <Pop key={ch.key} delay={12 + i * 9}>
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2}}>
              <Comp size={272} />
              <div style={{fontFamily: FONT.mono, fontWeight: 800, fontSize: 30, color: ch.color, marginTop: 6}}>{ch.name}</div>
              <div style={{fontFamily: FONT.body, fontWeight: 600, fontSize: 21, color: C.muted}}>{ch.role}</div>
            </div>
          </Pop>
        );
      })}
    </div>
  </AbsoluteFill>
);

const Portrait: React.FC<{k: CharKey}> = ({k}) => {
  const ch = CHARACTERS.find((c) => c.key === k)!;
  const Comp = CHAR_COMPONENTS[k];
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', padding: '0 80px'}}>
      <FloatingBlob size={820} x={50} y={38} hue={ch.color} hue2={C.mint} seed={9} opacity={0.2} />
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, position: 'relative'}}>
        <Pop delay={6}>
          <Comp size={560} />
        </Pop>
        <Pop delay={26}>
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10}}>
            <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 96, color: C.ink, lineHeight: 1}}>{ch.name}</div>
            <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 27, letterSpacing: 3, color: ch.color}}>{ch.role.toUpperCase()}</div>
            <div style={{fontFamily: FONT.body, fontSize: 28, color: C.inkSoft, textAlign: 'center', maxWidth: 760, marginTop: 6}}>{ch.tagline}</div>
          </div>
        </Pop>
      </div>
    </AbsoluteFill>
  );
};

export const CharacterCard: React.FC<CharacterCardProps> = (props) => (
  <AbsoluteFill style={{fontFamily: FONT.body}}>
    <Bg tint={C.emerald} />
    {props.variant === 'lineup' ? <Lineup /> : <Portrait k={props.variant} />}
    <AbsoluteFill style={{padding: '0 40px 22px', alignItems: 'center', justifyContent: 'flex-end', pointerEvents: 'none'}}>
      <Foot text={props.footer} />
    </AbsoluteFill>
  </AbsoluteFill>
);
