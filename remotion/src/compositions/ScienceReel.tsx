// ScienceReel.tsx — "they call it gambling" on the habits-reel engine.
// Part 1 (~28%): the accusations, cold white type with a RED glow. Pivot
// flash. Part 2 (~72%): the actual sciences, type flipped to the house
// GREEN glow — the color flip IS the argument. Dark-phonk aesthetic
// (owner's call for this piece; the no-neon rule stays for motivational
// reels). Silent render on the beat-ready 1.7s grid — owner adds an
// Instagram phonk sound; cutStarts/totalFrames props allow re-timing to a
// measured track grid like HabitsReel.
//
// Assets + prompts: scripts/science_reel/gen_assets.py (source of truth).
// Spec: docs/superpowers/specs/2026-08-02-science-reel-design.md
import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {FONT} from '../slides/theme';
import {EASE} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';

export const scienceReelSchema = z.object({
  cutStarts: z.array(z.number()).optional(),
  totalFrames: z.number().optional(),
});

const UNIT = 51; // 1.7s at 30fps = 3 beats at ~106 BPM
const RED = 'rgba(255,59,48,0.35)';
const GREEN = 'rgba(34,224,126,0.30)';

type Shot = {
  file: string;
  kind: 'img' | 'vid';
  units: number;
  word: string | null;
  accuse?: boolean; // part-1 red treatment
  flash?: boolean;  // 2-frame white flash on this shot's cut
};

const SHOTS: Shot[] = [
  {file: 'science/shot00.mp4', kind: 'vid', units: 2, word: "“TRADING ISN'T A REAL SCIENCE”", accuse: true},
  {file: 'science/shot01.png', kind: 'img', units: 1, word: '“IT’S JUST GAMBLING”', accuse: true},
  {file: 'science/shot02.png', kind: 'img', units: 1, word: '“IT’S PURE LUCK”', accuse: true},
  {file: 'science/shot03.png', kind: 'img', units: 1, word: '“IT’S UNETHICAL”', accuse: true},
  {file: 'science/shot04.png', kind: 'img', units: 1, word: "HERE'S THE ACTUAL SCIENCE", flash: true},
  {file: 'science/shot05.png', kind: 'img', units: 1, word: 'PROBABILITY'},
  {file: 'science/shot06.png', kind: 'img', units: 1, word: 'STATISTICS'},
  {file: 'science/shot07.png', kind: 'img', units: 1, word: 'STOCHASTIC CALCULUS'},
  {file: 'science/shot08.mp4', kind: 'vid', units: 2, word: 'RANDOM WALKS'},
  {file: 'science/shot09.png', kind: 'img', units: 1, word: 'COMPUTER SCIENCE'},
  {file: 'science/shot10.png', kind: 'img', units: 1, word: 'ALGORITHMS'},
  {file: 'science/shot11.png', kind: 'img', units: 1, word: 'GAME THEORY'},
  {file: 'science/shot12.png', kind: 'img', units: 1, word: 'MACHINE LEARNING'},
  {file: 'science/shot13.png', kind: 'img', units: 1, word: 'BEHAVIORAL SCIENCE'},
  {file: 'science/shot14.mp4', kind: 'vid', units: 1, word: "IT'S NOT LUCK. IT'S MATH.", flash: true},
  {file: 'science/shot15.mp4', kind: 'vid', units: 1, word: 'STUDY THE SCIENCE.'},
];

export const SCIENCE_FRAMES = SHOTS.reduce((n, s) => n + s.units * UNIT, 0); // 918 = 30.6s

const KenBurns: React.FC<{src: string; index: number; frames: number}> = ({src, index, frames}) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [0, frames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const push = index % 2 === 0;
  const scale = push ? 1.05 + 0.09 * t : 1.14 - 0.09 * t;
  const panX = (index % 4 < 2 ? 1 : -1) * 14 * t;
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Img
        src={staticFile(src)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${scale}) translateX(${panX}px)`,
        }}
      />
    </AbsoluteFill>
  );
};

const Word: React.FC<{word: string; accuse?: boolean}> = ({word, accuse}) => {
  const frame = useCurrentFrame();
  const inp = interpolate(frame, [3, 12], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const long = word.length > 14;
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 340,
        left: 50,
        right: 50,
        textAlign: 'center',
        opacity: inp,
        transform: `translateY(${(1 - inp) * 18}px)`,
      }}
    >
      <div
        style={{
          fontFamily: FONT.mono,
          fontSize: long ? 58 : 74,
          fontWeight: 900,
          lineHeight: 1.25,
          color: accuse ? '#EDEFF2' : '#F2F7F4',
          letterSpacing: long ? 4 : 8,
          textShadow: `0 4px 34px rgba(0,0,0,0.95), 0 0 60px ${accuse ? RED : GREEN}`,
        }}
      >
        {word}
      </div>
      <div
        style={{
          margin: '14px auto 0',
          width: 64 * inp,
          height: 3,
          background: accuse ? '#FF3B30' : '#22E07E',
          opacity: 0.85,
        }}
      />
    </div>
  );
};

const CutDip: React.FC = () => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 4], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return <AbsoluteFill style={{backgroundColor: '#000', opacity: o, pointerEvents: 'none'}} />;
};

/** 2-frame white pop on the pivot and the closer — the "chain" transition. */
const Flash: React.FC = () => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 2, 5], [0.9, 0.5, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return <AbsoluteFill style={{backgroundColor: '#fff', opacity: o, pointerEvents: 'none'}} />;
};

export const ScienceReel: React.FC<z.infer<typeof scienceReelSchema>> = ({cutStarts, totalFrames}) => {
  const defaults: number[] = [];
  let acc = 0;
  for (const s of SHOTS) {
    defaults.push(acc);
    acc += s.units * UNIT;
  }
  const starts = cutStarts && cutStarts.length === SHOTS.length ? cutStarts : defaults;
  const total = totalFrames ?? SCIENCE_FRAMES;
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      {SHOTS.map((s, i) => {
        const start = starts[i];
        const dur = (i + 1 < starts.length ? starts[i + 1] : total) - start;
        return (
          <Sequence key={s.file} from={start} durationInFrames={dur}>
            <AbsoluteFill>
              {s.kind === 'vid' ? (
                <OffthreadVideo
                  src={staticFile(s.file)}
                  muted
                  style={{width: '100%', height: '100%', objectFit: 'cover'}}
                />
              ) : (
                <KenBurns src={s.file} index={i} frames={dur} />
              )}
              {s.flash ? <Flash /> : <CutDip />}
              {s.word ? <Word word={s.word} accuse={s.accuse} /> : null}
            </AbsoluteFill>
          </Sequence>
        );
      })}
      <Vignette />
      <Grain opacity={0.06} />
    </AbsoluteFill>
  );
};
