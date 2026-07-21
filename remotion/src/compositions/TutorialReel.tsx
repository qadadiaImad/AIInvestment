// TutorialReel.tsx — narrated product-walkthrough reel: a screen recording of
// the live app inside a browser-chrome frame, callout chips pointing at the
// feature being narrated, a persistent brand header, a Karim PIP (photo,
// gentle breathing scale), and the shared disclaimer footer. Follows the
// same schema-driven idiom as SlideStoryReel.tsx (props -> zod schema ->
// parameterized composition) and reuses the slides/ brand system (theme.ts,
// ui.tsx: Bg/Head) plus components/DisclaimerFooter.tsx for the footer.
import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  Series,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import type {Callout, TutorialProps, TutorialScene} from '../slides/tutorialProps';
import {C, FONT} from '../slides/theme';
import {Bg, Head, clamp, inOut, pop} from '../slides/ui';
import {DisclaimerFooter} from '../components/DisclaimerFooter';

const PAD = 84;
const HEADER_H = 96; // approx rendered height of the Head chip row
const HEADER_GAP = 40;
const FRAME_TOP = PAD + HEADER_H + HEADER_GAP;
const FRAME_HEIGHT_PCT = 0.78; // "fills ~78% height"
const FRAME_SIDE_PAD = 56;
const CROSSFADE_FRAMES = 12;
const BROWSER_URL = 'highreturnethicalscreen.vercel.app';

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** Browser-chrome card: rounded, top bar with three traffic-light dots
 * (mapped onto the existing red/amber/emerald theme colors) + a readable
 * URL pill, subtle border/shadow. */
const BrowserChrome: React.FC<{height: number; children: React.ReactNode}> = ({height, children}) => (
  <div
    style={{
      position: 'relative',
      width: '100%',
      height,
      borderRadius: 28,
      overflow: 'hidden',
      background: '#000',
      border: `2px solid ${C.line}`,
      boxShadow: '0 30px 90px rgba(0,0,0,.55)',
    }}
  >
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: 56,
        zIndex: 2,
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '0 18px',
        background: 'rgba(12,15,20,.94)',
        borderBottom: `1px solid ${C.line}`,
      }}
    >
      <div style={{width: 12, height: 12, borderRadius: 6, background: C.red}} />
      <div style={{width: 12, height: 12, borderRadius: 6, background: C.amber}} />
      <div style={{width: 12, height: 12, borderRadius: 6, background: C.emerald}} />
      <div style={{flex: 1, display: 'flex', justifyContent: 'center'}}>
        <span
          style={{
            fontFamily: FONT.mono,
            fontWeight: 600,
            fontSize: 18,
            letterSpacing: 0.5,
            color: C.inkSoft,
            background: C.panel,
            border: `1px solid ${C.line}`,
            borderRadius: 999,
            padding: '6px 18px',
          }}
        >
          {BROWSER_URL}
        </span>
      </div>
    </div>
    <div style={{position: 'absolute', top: 56, left: 0, right: 0, bottom: 0, overflow: 'hidden'}}>
      {children}
    </div>
  </div>
);

/** Callout chip: fades in at `atFrame` (relative to the scene), stays for
 * the rest of the scene, with a soft pulsing ring behind it anchored at
 * (x, y) — fractional coordinates within the browser-chrome frame. */
const CalloutChip: React.FC<{callout: Callout; frame: number; tone: 'emerald' | 'amber'}> = ({
  callout,
  frame,
  tone,
}) => {
  const t = frame - callout.atFrame;
  if (t < 0) return null;
  const p = interpolate(t, [0, 10], [0, 1], {...clamp, easing: pop});
  const color = tone === 'emerald' ? C.emerald : C.amber;
  const pulse = (Math.sin(t * 0.16) + 1) / 2; // slow breathing 0..1
  return (
    <div
      style={{
        position: 'absolute',
        left: `${callout.x * 100}%`,
        top: `${callout.y * 100}%`,
        translate: '-50% -50%',
        opacity: p,
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: -14 - pulse * 10,
          borderRadius: 999,
          border: `2px solid ${color}`,
          opacity: 0.45 - pulse * 0.25,
        }}
      />
      <div
        style={{
          position: 'relative',
          fontFamily: FONT.mono,
          fontWeight: 700,
          fontSize: 22,
          letterSpacing: 0.3,
          whiteSpace: 'nowrap',
          color: C.bg,
          background: color,
          padding: '10px 20px',
          borderRadius: 999,
          boxShadow: '0 10px 26px rgba(0,0,0,.4)',
          scale: String(0.88 + 0.12 * p),
        }}
      >
        {callout.text}
      </div>
    </div>
  );
};

/** One scene: the capture (with an optional slow ken-burns zoom toward a
 * focal point) inside the browser-chrome frame, plus its callouts. Fades
 * 12 frames in/out at the scene boundary — the "crossfade" against the
 * persistent header/footer/background. */
const SceneView: React.FC<{scene: TutorialScene; frameHeight: number}> = ({scene, frameHeight}) => {
  const frame = useCurrentFrame();
  const dur = scene.durationInFrames;
  const fadeIn = interpolate(frame, [0, CROSSFADE_FRAMES], [0, 1], clamp);
  const fadeOut = interpolate(frame, [dur - CROSSFADE_FRAMES, dur], [1, 0], clamp);
  const opacity = Math.min(fadeIn, fadeOut);

  const zp = interpolate(frame, [0, dur], [0, 1], {...clamp, easing: inOut});
  const scale = scene.zoom ? lerp(scene.zoom.from.scale, scene.zoom.to.scale, zp) : 1;
  const originX = scene.zoom ? lerp(scene.zoom.from.x, scene.zoom.to.x, zp) * 100 : 50;
  const originY = scene.zoom ? lerp(scene.zoom.from.y, scene.zoom.to.y, zp) * 100 : 50;

  return (
    <AbsoluteFill style={{opacity, alignItems: 'center'}}>
      <div style={{width: '100%'}}>
        <BrowserChrome height={frameHeight}>
          <OffthreadVideo
            src={staticFile(scene.src)}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              transform: `scale(${scale})`,
              transformOrigin: `${originX}% ${originY}%`,
            }}
          />
          {scene.callouts.map((callout, i) => (
            <CalloutChip
              key={`${callout.text}-${i}`}
              callout={callout}
              frame={frame}
              tone={i % 2 === 0 ? 'emerald' : 'amber'}
            />
          ))}
        </BrowserChrome>
      </div>
    </AbsoluteFill>
  );
};

/** Karim PIP: a static photo in a rounded frame, bottom-right, with a very
 * subtle slow breathing scale (1.0 -> 1.03 -> 1.0 over 300+300 frames) so
 * it feels alive without pulling attention off the capture. */
const KarimPip: React.FC<{src: string}> = ({src}) => {
  const frame = useCurrentFrame();
  // cos(0)=1 -> breathe=1.0; cos(pi) at frame=300 -> breathe=1.03; cos(2pi) at
  // frame=600 -> back to 1.0. i.e. 300 frames up, 300 frames down, alternating.
  const breathe = 1.0 + 0.015 * (1 - Math.cos((frame / 300) * Math.PI));
  return (
    <div
      style={{
        position: 'absolute',
        right: 40,
        bottom: 40,
        width: '22%',
        aspectRatio: '9 / 16',
        borderRadius: 24,
        overflow: 'hidden',
        border: `3px solid ${C.line}`,
        boxShadow: '0 16px 50px rgba(0,0,0,.5)',
        transform: `scale(${breathe})`,
        transformOrigin: 'bottom right',
      }}
    >
      <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    </div>
  );
};

export const TutorialReel: React.FC<TutorialProps> = (props) => {
  const totalFrames = props.scenes.reduce((sum, s) => sum + s.durationInFrames, 0);
  const frameHeight = Math.round(1920 * FRAME_HEIGHT_PCT);

  return (
    <AbsoluteFill style={{fontFamily: FONT.body}}>
      <Bg tint={C.emerald} />

      <AbsoluteFill style={{padding: PAD, bottom: 'auto', height: 'auto'}}>
        <Head tk={props.title} sub="" badge={{text: props.badge, color: C.emerald}} />
      </AbsoluteFill>

      <AbsoluteFill
        style={{
          top: FRAME_TOP,
          bottom: 'auto',
          height: frameHeight,
          left: FRAME_SIDE_PAD,
          right: FRAME_SIDE_PAD,
        }}
      >
        <Series>
          {props.scenes.map((scene) => (
            <Series.Sequence key={scene.id} durationInFrames={scene.durationInFrames} name={scene.id}>
              <SceneView scene={scene} frameHeight={frameHeight} />
            </Series.Sequence>
          ))}
        </Series>
      </AbsoluteFill>

      <KarimPip src={props.karimSrc} />

      <Sequence from={0} durationInFrames={totalFrames} layout="none" name="Footer">
        <DisclaimerFooter text={props.disclaimer} />
      </Sequence>

      {props.audioSrc ? <Audio src={staticFile(props.audioSrc)} /> : null}
    </AbsoluteFill>
  );
};
