// HabitsReel.tsx — 10 real-aesthetic stills + 4 videos on a fixed 1.7s beat
// grid. Silent by design (owner adds a trending sound in the platform app;
// a reel with no audio track doesn't fight the platform's music picker).
//
// The mechanic: hook text on frame one, one idea per cut, a wordless rain
// video as the mid-reel pattern interrupt, and an ender that visually matches
// the hook shot so replays loop seamlessly. Stills carry a Ken Burns push
// (alternating direction) so nothing reads static; videos hold 1–2 units as
// the slower breathing moments. Words are habits and states of mind, never
// income claims (house rule 10.6).
//
// Assets + prompts: scripts/habits/gen_assets.py (source of truth for shots).
// Spec: docs/superpowers/specs/2026-08-02-habits-reel-design.md
import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {FONT} from '../slides/theme';
import {EASE} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';
import {PT} from '../components/PatternCard';

// cutStarts/totalFrames re-time the cuts to a real track's measured kick grid
// (scripts/audio/mix_playlist.py emits them); omitted -> the built-in 1.7s grid.
export const habitsReelSchema = z.object({
  cutStarts: z.array(z.number()).optional(),
  totalFrames: z.number().optional(),
});

const UNIT = 51; // 1.7s at 30fps = 3 beats at ~106 BPM

type Shot = {
  file: string;
  kind: 'img' | 'vid';
  units: number;
  word: string | null;
  centered?: boolean; // hook/ender words sit mid-frame; habit words lower third
};

const SHOTS: Shot[] = [
  // Cold open: the one Maya cameo — the doubt the whole reel answers.
  {file: 'habits/shot00.mp4', kind: 'vid', units: 2, word: "THEY SAY YOU DON'T HAVE THE TALENT FOR TRADING", centered: true},
  {file: 'habits/shot01.mp4', kind: 'vid', units: 2, word: 'TALENT LOSES TO ROUTINE', centered: true},
  {file: 'habits/shot02.png', kind: 'img', units: 1, word: 'WAKE EARLY'},
  {file: 'habits/shot03.png', kind: 'img', units: 1, word: 'TRAIN'},
  {file: 'habits/shot04.png', kind: 'img', units: 1, word: 'STUDY'},
  {file: 'habits/shot05.png', kind: 'img', units: 1, word: 'PLAN'},
  {file: 'habits/shot06.png', kind: 'img', units: 1, word: 'EXECUTE'},
  {file: 'habits/shot07.png', kind: 'img', units: 1, word: 'RISK SMALL'},
  {file: 'habits/shot08.mp4', kind: 'vid', units: 2, word: null}, // the interrupt
  {file: 'habits/shot09.png', kind: 'img', units: 1, word: 'JOURNAL EVERYTHING'},
  {file: 'habits/shot10.png', kind: 'img', units: 1, word: 'PATIENCE'},
  {file: 'habits/shot11.png', kind: 'img', units: 1, word: 'IT COMPOUNDS'},
  {file: 'habits/shot12.mp4', kind: 'vid', units: 1, word: 'FREEDOM'},
  {file: 'habits/shot13.png', kind: 'img', units: 1, word: 'WORTH IT'},
  {file: 'habits/shot14.mp4', kind: 'vid', units: 1, word: 'SAME HABITS. TOMORROW.', centered: true},
];

export const HABITS_FRAMES = SHOTS.reduce((n, s) => n + s.units * UNIT, 0); // 816 = 27.2s

/** Ken Burns: slow push, direction alternating per shot so consecutive stills
 * never drift the same way. Scale stays >= 1.05 to cover the pan. */
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

/** One idea per cut. Cuts are 1.7s, so the word lands fast (frames 3–12). */
const Word: React.FC<{word: string; centered?: boolean}> = ({word, centered}) => {
  const frame = useCurrentFrame();
  const inp = interpolate(frame, [3, 12], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const long = word.length > 12;
  return (
    <div
      style={{
        position: 'absolute',
        left: 50,
        right: 50,
        textAlign: 'center',
        ...(centered
          ? {top: '50%', transform: `translateY(calc(-50% + ${(1 - inp) * 18}px))`}
          : {bottom: 340, transform: `translateY(${(1 - inp) * 18}px)`}),
        opacity: inp,
      }}
    >
      <div
        style={{
          fontFamily: FONT.mono,
          fontSize: centered ? (long ? 58 : 84) : long ? 62 : 78,
          fontWeight: 900,
          lineHeight: 1.25,
          color: '#F2F7F4',
          letterSpacing: long ? 4 : 9,
          textShadow: '0 4px 34px rgba(0,0,0,0.95), 0 0 60px rgba(34,224,126,0.18)',
        }}
      >
        {word}
      </div>
      <div
        style={{
          margin: '14px auto 0',
          width: 64 * inp,
          height: 3,
          background: PT.ice,
          opacity: 0.85,
        }}
      />
    </div>
  );
};

/** A breath of black at every cut — hard cuts read harder when the first
 * frames dip. */
const CutDip: React.FC = () => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 4], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return <AbsoluteFill style={{backgroundColor: '#000', opacity: o, pointerEvents: 'none'}} />;
};

export const HabitsReel: React.FC<z.infer<typeof habitsReelSchema>> = ({cutStarts, totalFrames}) => {
  const defaults: number[] = [];
  let acc = 0;
  for (const s of SHOTS) {
    defaults.push(acc);
    acc += s.units * UNIT;
  }
  const starts = cutStarts && cutStarts.length === SHOTS.length ? cutStarts : defaults;
  const total = totalFrames ?? HABITS_FRAMES;
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
              <CutDip />
              {s.word ? <Word word={s.word} centered={s.centered} /> : null}
            </AbsoluteFill>
          </Sequence>
        );
      })}
      <Vignette />
      <Grain opacity={0.06} />
    </AbsoluteFill>
  );
};
