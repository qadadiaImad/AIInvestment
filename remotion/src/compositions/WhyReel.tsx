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
import {AbsoluteFill, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
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
const TAN = '#B49B85';
const BROWN = '#3A2B1F';
const BOX_BROWN = '#4A3527';

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
    <div style={{position: 'absolute', top: 170, left: 60, right: 60, textAlign: 'center', opacity: inp}}>
      <div style={{fontFamily: SERIF, fontWeight: 600, fontSize: 52, color: GOLD, letterSpacing: 1}}>
        Why did you choose
      </div>
      <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 68, color: GOLD, letterSpacing: 2, marginTop: 6}}>
        Trading ?
      </div>
    </div>
  );
};

/** One word card. Styles cycle: gold-on-black, brown-on-tan box, gold-on-brown box. */
const WordCard: React.FC<{word: string; style: number}> = ({word, style}) => {
  const frame = useCurrentFrame();
  const inp = interpolate(frame, [0, 3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const scale = 1.04 - 0.04 * inp;
  const boxed = style !== 0;
  return (
    <AbsoluteFill style={{backgroundColor: '#000', alignItems: 'center', justifyContent: 'center'}}>
      <div
        style={{
          opacity: inp,
          transform: `scale(${scale})`,
          background: style === 1 ? TAN : style === 2 ? BOX_BROWN : 'transparent',
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
          }}
        >
          {word}
        </div>
      </div>
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
          <OffthreadVideo
            src={staticFile('habits/shot00.mp4')}
            muted
            style={{width: '100%', height: '100%', objectFit: 'cover'}}
          />
          <Question />
        </AbsoluteFill>
      </Sequence>
      {WORDS.map((w, k) => {
        const end = k + 1 < WORDS.length ? wordStarts[k + 1] : enderStart;
        return (
          <Sequence key={w} from={wordStarts[k]} durationInFrames={end - wordStarts[k]}>
            <WordCard word={w} style={k % 3} />
          </Sequence>
        );
      })}
      {/* loop closure: the SAME clip continues from where the anchor left it */}
      <Sequence from={enderStart} durationInFrames={total - enderStart}>
        <AbsoluteFill>
          <OffthreadVideo
            src={staticFile('habits/shot00.mp4')}
            muted
            startFrom={anchorLen}
            style={{width: '100%', height: '100%', objectFit: 'cover'}}
          />
          <Question />
        </AbsoluteFill>
      </Sequence>
      <Vignette />
      <Grain opacity={0.05} />
    </AbsoluteFill>
  );
};
