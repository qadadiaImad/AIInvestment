// CameraProbe.tsx — a THROWAWAY spike, not a deliverable.
//
// Its only job is to make one design question answerable by looking instead of
// reading: does a keyframed camera over an already-drawn chart feel cinematic,
// or does it feel like a slideshow zoom? Everything here is deliberately cheap
// — real data, real camera maths, no sound, no story.
//
// Delete this file once the Hormuz reel's own composition exists.
import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {FONT} from '../slides/theme';
import {EASE} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';
import {PatternCard, PT, type PatternData} from '../components/PatternCard';
import {CameraRig, type Shot} from '../motion/CameraRig';
import galleryFixture from '../fixtures/patterns_post/gallery.json';

export const cameraProbeSchema = z.object({durationInFrames: z.number()});
export type CameraProbeProps = z.infer<typeof cameraProbeSchema>;

export const CAMERA_PROBE_FRAMES = 240; // 8s at 30fps

const CHART_W = 1000;
const CHART_H = 880;

// The camera. x/y are the point of the chart to centre, in 0..1 of the chart's
// own box, so a shot survives the chart being resized.
const SHOTS: Shot[] = [
  {at: 0, zoom: 1.02, x: 0.5, y: 0.5},
  {at: 62, zoom: 2.15, x: 0.30, y: 0.42, ease: EASE.cruise}, // push into the left top
  {at: 96, zoom: 2.15, x: 0.30, y: 0.42}, // HOLD. A camera that never rests reads as drift.
  {at: 150, zoom: 2.05, x: 0.72, y: 0.46, ease: EASE.cruise}, // track across to the break
  {at: 178, zoom: 2.05, x: 0.72, y: 0.46},
  {at: 220, zoom: 1.02, x: 0.5, y: 0.5, ease: EASE.cruise}, // pull out to the whole story
  {at: 239, zoom: 1.06, x: 0.5, y: 0.5},
];

/** Types a line out at `cps` characters/sec, with a cursor that blinks only
 * while typing. The blink is quantised to 8-frame steps — a smoothly fading
 * cursor is the tell that no one actually looked at a terminal. */
const Typewriter: React.FC<{
  text: string;
  from: number;
  to: number;
  cps?: number;
  top: number;
}> = ({text, from, to, cps = 22, top}) => {
  const frame = useCurrentFrame();
  if (frame < from || frame > to) return null;
  const shown = Math.min(text.length, Math.floor(((frame - from) / 30) * cps));
  const typing = shown < text.length;
  const cursorOn = Math.floor((frame - from) / 8) % 2 === 0;
  const out = interpolate(frame, [to - 8, to], [1, 0], {
    easing: EASE.exit,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div
      style={{
        position: 'absolute',
        top,
        left: 70,
        right: 70,
        textAlign: 'center',
        opacity: out,
        fontFamily: FONT.mono,
        fontSize: 40,
        fontWeight: 700,
        color: '#EAFFF4',
        letterSpacing: 0.5,
        lineHeight: 1.25,
        textShadow: '0 2px 18px rgba(0,0,0,0.85)',
      }}
    >
      {text.slice(0, shown)}
      {typing && cursorOn ? <span style={{color: PT.up}}>▌</span> : null}
    </div>
  );
};

export const CameraProbe: React.FC<CameraProbeProps> = () => {
  const frame = useCurrentFrame();
  const card = (galleryFixture.chapters[0].cards as PatternData[])[0];

  return (
    <AbsoluteFill style={{backgroundColor: PT.bg}}>
      {/* the chart draws itself once, at its own size; the rig decides what
          part of it you are looking at */}
      <CameraRig
        frame={frame}
        shots={SHOTS}
        childWidth={CHART_W}
        childHeight={CHART_H}
        viewportWidth={1080}
        viewportHeight={1920}
      >
        <PatternCard data={card} width={CHART_W} height={CHART_H} variant="hero" />
      </CameraRig>

      {/* captions sit ABOVE the rig, so a push never scales the type */}
      <Typewriter text="Two tops. The same level." from={14} to={92} top={210} />
      <Typewriter text="Sellers defended it twice." from={100} to={172} top={210} />
      <Typewriter text="Then it broke." from={182} to={239} top={210} />

      <Vignette />
      <Grain opacity={0.04} />

      <div
        style={{
          position: 'absolute',
          bottom: 44,
          left: 60,
          right: 60,
          textAlign: 'center',
          fontFamily: FONT.mono,
          fontSize: 17,
          color: PT.steel,
          letterSpacing: 0.6,
        }}
      >
        CAMERA TEST · real SPY bars · no sound yet
      </div>
    </AbsoluteFill>
  );
};
