// GrindReel.tsx — 15 AI clips, hard cuts, two-word mood text, no sound.
//
// The owner adds their own music at post time, so this render carries NO audio
// track at all — a reel with a silent track fights the platform's music
// picker; a reel with no track doesn't. Text is capped at two words per
// overlay by spec: this is a mood piece, not an argument, and it makes no
// numeric or income claims — the words are states of mind, never results.
//
// Clip order and words mirror scripts/grind/gen_clips.py (the generator is
// the source of truth for prompts; this file is the source of truth for cut
// timing). Arc: 8 clips of the grind -> 7 clips of what it's for.
import React from 'react';
import {AbsoluteFill, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {FONT} from '../slides/theme';
import {EASE} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';
import {PT} from '../components/PatternCard';

export const grindReelSchema = z.object({});

const PER = 90; // 3s per clip at 30fps
const CLIPS: {file: string; word: string | null}[] = [
  {file: 'grind/clip01.mp4', word: 'AMBITION'},
  {file: 'grind/clip02.mp4', word: null},
  {file: 'grind/clip03.mp4', word: 'STRUGGLE'},
  {file: 'grind/clip04.mp4', word: 'DISCIPLINE'},
  {file: 'grind/clip05.mp4', word: null},
  {file: 'grind/clip06.mp4', word: 'FOCUS'},
  {file: 'grind/clip07.mp4', word: null},
  {file: 'grind/clip08.mp4', word: 'PATIENCE'},
  {file: 'grind/clip09.mp4', word: 'FREEDOM'},
  {file: 'grind/clip10.mp4', word: null},
  {file: 'grind/clip11.mp4', word: null},
  {file: 'grind/clip12.mp4', word: null},
  {file: 'grind/clip13.mp4', word: null},
  {file: 'grind/clip14.mp4', word: 'PURPOSE'},
  {file: 'grind/clip15.mp4', word: 'WORTH IT'},
];

export const GRIND_FRAMES = CLIPS.length * PER; // 1350 = 45s

/** The mood word: arrives fast, tracks wide, never leaves until the cut.
 * Lower third, so it sits on the dark floor of the frame rather than across
 * her back or the skyline. */
const Word: React.FC<{word: string}> = ({word}) => {
  const frame = useCurrentFrame();
  const inp = interpolate(frame, [10, 22], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 340,
        left: 40,
        right: 40,
        textAlign: 'center',
        opacity: inp,
        transform: `translateY(${(1 - inp) * 18}px)`,
      }}
    >
      <div
        style={{
          fontFamily: FONT.mono,
          fontSize: 86,
          fontWeight: 900,
          color: '#F2F7F4',
          letterSpacing: 10,
          textShadow: '0 4px 34px rgba(0,0,0,0.95), 0 0 60px rgba(34,224,126,0.18)',
        }}
      >
        {word}
      </div>
      <div
        style={{
          margin: '16px auto 0',
          width: 64 * inp,
          height: 3,
          background: PT.ice,
          opacity: 0.85,
        }}
      />
    </div>
  );
};

export const GrindReel: React.FC = () => {
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      {CLIPS.map((c, i) => (
        <Sequence key={c.file} from={i * PER} durationInFrames={PER}>
          <AbsoluteFill>
            <OffthreadVideo
              src={staticFile(c.file)}
              muted
              style={{width: '100%', height: '100%', objectFit: 'cover'}}
            />
            {/* a breath of black at every cut — hard cuts read harder when
             * the first two frames dip */}
            <FadeIn />
            {c.word ? <Word word={c.word} /> : null}
          </AbsoluteFill>
        </Sequence>
      ))}
      <Vignette />
      <Grain opacity={0.05} />
    </AbsoluteFill>
  );
};

const FadeIn: React.FC = () => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 4], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return <AbsoluteFill style={{backgroundColor: '#000', opacity: o, pointerEvents: 'none'}} />;
};
