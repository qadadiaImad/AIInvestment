// WhyReel.tsx — the clubbillionaire recipe: one cinematic anchor clip with a
// standing gold serif question, then a machine-gun chain of single-word
// typographic cards (three alternating card styles), then back to the clip.
//
// Reverse-engineered 2026-08-02 from the owner's reference screen recording
// (13.9s: ~4s desk clip + ~12 word cards at ~0.8s + loop ender). Our anchor
// is the Maya sunset desk (habits/shot00.mp4 — practically the same shot as
// the reference's), and the card chain rides a measured beat grid when
// wordStarts/totalFrames props are supplied (scripts/audio/why_mix.py).
import React from 'react';
import {AbsoluteFill, Img, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {Grain, Vignette} from '../motion/Polish';

export const whyReelSchema = z.object({
  wordStarts: z.array(z.number()).optional(),
  enderStart: z.number().optional(),
  totalFrames: z.number().optional(),
});

const FPS = 30;
const BEAT = 0.5013; // default grid = ANDROMEDA's measured kick period
const SERIF = "'Fraunces', serif";
const GOLD = '#E8C87E';
const BROWN = '#3A2B1F';

// Reasons-you-chose-trading, habits first, FREEDOM as the closer.
const WORDS = [
  'GROWTH', 'SKILL', 'DISCIPLINE', 'CREATIVITY', 'OPPORTUNITY', 'IDENTITY',
  'CHALLENGE', 'INDEPENDENCE', 'MASTERY', 'CONTROL', 'PURPOSE', 'FREEDOM',
];

const beatsToFrames = (b: number) => Math.round(b * BEAT * FPS);
export const WHY_DEFAULTS = {
  wordStarts: WORDS.map((_, k) => beatsToFrames(8 + 2 * k)), // chain starts on the drop
  enderStart: beatsToFrames(32),
  totalFrames: beatsToFrames(36),
};

const Question: React.FC = () => {
  const frame = useCurrentFrame();
  const inp = interpolate(frame, [4, 16], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <>
      {/* the sunset sky is bright where the question sits — scrim keeps the
       * gold legible without darkening the scene */}
      <AbsoluteFill
        style={{background: 'linear-gradient(to bottom, rgba(0,0,0,0.55), rgba(0,0,0,0.25) 22%, rgba(0,0,0,0) 38%)', opacity: inp}}
      />
      <div style={{position: 'absolute', top: 170, left: 60, right: 60, textAlign: 'center', opacity: inp}}>
        <div style={{fontFamily: SERIF, fontWeight: 600, fontSize: 52, color: GOLD, letterSpacing: 1, textShadow: '0 3px 22px rgba(0,0,0,0.8)'}}>
          Why did you choose
        </div>
        <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 68, color: GOLD, letterSpacing: 2, marginTop: 6, textShadow: '0 3px 22px rgba(0,0,0,0.8)'}}>
          Trading ?
        </div>
      </div>
    </>
  );
};

/** One word card: a vector-comic illustration of the word's meaning behind
 * the type. Styles cycle: gold-on-scrim, brown-on-tan box, gold-on-brown box
 * (boxes slightly translucent so the art reads through). */
const WordCard: React.FC<{word: string; style: number; dur: number}> = ({word, style, dur}) => {
  const frame = useCurrentFrame();
  const inp = interpolate(frame, [0, 3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const drift = interpolate(frame, [0, dur], [1.06, 1.12]); // art breathes under the type
  const scale = 1.04 - 0.04 * inp;
  const boxed = style !== 0;
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile(`why/card_${word.toLowerCase()}.png`)}
          style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${drift})`}}
        />
      </AbsoluteFill>
      {/* legibility scrim, heaviest where the word sits */}
      <AbsoluteFill
        style={{background: 'radial-gradient(ellipse 90% 34% at 50% 47%, rgba(0,0,0,0.52), rgba(0,0,0,0.10) 70%, rgba(0,0,0,0) 100%)'}}
      />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <div
          style={{
            opacity: inp,
            transform: `scale(${scale})`,
            background: style === 1 ? 'rgba(180,155,133,0.94)' : style === 2 ? 'rgba(74,53,39,0.94)' : 'transparent',
            padding: boxed ? '38px 70px' : 0,
            minWidth: boxed ? 560 : undefined,
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontFamily: SERIF,
              fontWeight: 600,
              fontSize: boxed ? 54 : 72,
              color: style === 1 ? BROWN : GOLD,
              letterSpacing: 6,
              textShadow: boxed ? undefined : '0 3px 26px rgba(0,0,0,0.9)',
            }}
          >
            {word}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** Anchor/ender: Ken Burns over the composited still — the monitors carry
 * REAL charts (Yahoo bars drawn by render_terminals.py, warped on by
 * composite_anchor.py), so nothing on screen is AI-invented. */
const AnchorStill: React.FC<{from: number; to: number; dur: number}> = ({from, to, dur}) => {
  const frame = useCurrentFrame();
  const s = interpolate(frame, [0, dur], [from, to]);
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Img
        src={staticFile('why/anchor_final.png')}
        style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${s})`}}
      />
    </AbsoluteFill>
  );
};

export const WhyReel: React.FC<z.infer<typeof whyReelSchema>> = (props) => {
  const wordStarts = props.wordStarts && props.wordStarts.length === WORDS.length
    ? props.wordStarts : WHY_DEFAULTS.wordStarts;
  const enderStart = props.enderStart ?? WHY_DEFAULTS.enderStart;
  const total = props.totalFrames ?? WHY_DEFAULTS.totalFrames;
  const anchorLen = wordStarts[0];
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      <Sequence from={0} durationInFrames={anchorLen}>
        <AbsoluteFill>
          <AnchorStill from={1.0} to={1.09} dur={anchorLen} />
          <Question />
        </AbsoluteFill>
      </Sequence>
      {WORDS.map((w, k) => {
        const end = k + 1 < WORDS.length ? wordStarts[k + 1] : enderStart;
        return (
          <Sequence key={w} from={wordStarts[k]} durationInFrames={end - wordStarts[k]}>
            <WordCard word={w} style={k % 3} dur={end - wordStarts[k]} />
          </Sequence>
        );
      })}
      {/* loop closure: the same still, zoom continuing from where it left */}
      <Sequence from={enderStart} durationInFrames={total - enderStart}>
        <AbsoluteFill>
          <AnchorStill from={1.09} to={1.13} dur={total - enderStart} />
          <Question />
        </AbsoluteFill>
      </Sequence>
      <Vignette />
      <Grain opacity={0.05} />
    </AbsoluteFill>
  );
};
