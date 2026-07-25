// QuizWithHost.tsx — composites a generated host clip (Maya, from Grok) with a
// Remotion-rendered reel, as a screen-share inside a video call.
//
// The split is deliberate: the reel is embedded as a real video file, so the
// chart is pixel-exact and the candlestick pattern stays mathematically valid.
// Handing the reel to a generative model to "composite" reliably ends with the
// chart regenerated and the pattern silently broken.
//
// Layout is a reserved-strip screen share, not a floating corner bubble: the
// reel has content top (title/answer), middle (chart) and bottom (lesson card,
// disclaimer), so a bubble occludes something wherever it lands.
//
// Renders before the host clip exists — `hostSrc` unset draws a labeled
// placeholder tile, so the layout is reviewable ahead of the Grok round-trip.
import React from 'react';
import {AbsoluteFill, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig, interpolate, spring} from 'remotion';
import {z} from 'zod';
import {C, FONT} from '../slides/theme';
import {SPRINGS, fadeOf} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';

export const quizWithHostSchema = z.object({
  /** staticFile-relative path to the Remotion reel being presented. */
  screenSrc: z.string(),
  /** staticFile-relative path to the generated host clip. Omit/empty to draw
   * the placeholder instead — lets the layout be reviewed before the clip
   * exists. */
  hostSrc: z.string().optional(),
  /** Real length of the host clip. If it is shorter than the composition the
   * last frame holds rather than the tile going black mid-reel. */
  hostDurationInFrames: z.number().optional(),
  handle: z.string(),
  role: z.string(),
  durationInFrames: z.number(),
});
export type QuizWithHostProps = z.infer<typeof quizWithHostSchema>;

// ---------------------------------------------------------------- layout
// A 9:16 reel inside a 9:16 frame leaves no free space, so the screen card is
// scaled until it fully clears the host tile — overlapping instead would put
// the tile straight over the reel's compliance footer.
// Tile is lifted well clear of the bottom ~12% too, since the platform's
// caption/UI overlay eats that band on a Reel.
// Sized so: screen bottom (34 + 0.778*1080*16/9 ≈ 1528) < tile top (1550).
const SCREEN = {top: 34, widthPct: 0.778};
const TILE = {x: 62, w: 400, h: 240, bottom: 130};

export const QuizWithHost: React.FC<QuizWithHostProps> = (p) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();

  const screenW = width * SCREEN.widthPct;
  const screenH = screenW * (16 / 9); // the reel is itself 9:16
  const screenX = (width - screenW) / 2;

  const tileY = height - TILE.bottom - TILE.h;

  // Everything lands in the first beat — this is a wrapper, it shouldn't
  // compete with the reel it's presenting.
  const inP = spring({frame, fps, config: SPRINGS.heavy});
  const chipP = spring({frame: frame - 8, fps, config: SPRINGS.pop});

  const hostFrames = p.hostDurationInFrames ?? p.durationInFrames;

  return (
    <AbsoluteFill style={{background: C.bg, fontFamily: FONT.body}}>
      {/* studio backdrop — atmosphere only, must not compete with the screen */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at 50% 12%, ${C.emerald}0e, transparent 58%),
                       radial-gradient(ellipse at 18% 92%, ${C.amber}12, transparent 55%)`,
        }}
      />

      {/* ------------------------------------------------- shared screen */}
      <div
        style={{
          position: 'absolute',
          left: screenX,
          top: SCREEN.top,
          width: screenW,
          height: screenH,
          borderRadius: 26,
          overflow: 'hidden',
          border: `1px solid ${C.line}`,
          boxShadow: `0 30px 90px -20px rgba(0,0,0,.9), 0 0 60px ${C.emerald}14`,
          opacity: fadeOf(inP),
          transform: `translateY(${interpolate(inP, [0, 1], [22, 0])}px)`,
        }}
      >
        <OffthreadVideo src={staticFile(p.screenSrc)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </div>

      {/* --------------------------------------------------- host tile */}
      <div
        style={{
          position: 'absolute',
          left: TILE.x,
          top: tileY,
          width: TILE.w,
          height: TILE.h,
          borderRadius: 22,
          overflow: 'hidden',
          border: `1px solid ${C.line}`,
          boxShadow: '0 20px 50px -18px rgba(0,0,0,.9)',
          background: C.panel,
          opacity: fadeOf(chipP),
          transform: `translateY(${interpolate(chipP, [0, 1], [26, 0])}px)`,
        }}
      >
        {p.hostSrc ? (
          // Held on its last frame if the clip is shorter than the reel, so the
          // tile never cuts to black mid-render.
          <Sequence from={0} durationInFrames={hostFrames} layout="none">
            <OffthreadVideo
              src={staticFile(p.hostSrc)}
              style={{width: '100%', height: '100%', objectFit: 'cover'}}
            />
          </Sequence>
        ) : (
          <AbsoluteFill
            style={{
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              gap: 10,
              background: `repeating-linear-gradient(45deg, rgba(255,255,255,.03) 0 12px, transparent 12px 24px)`,
            }}
          >
            <div style={{fontFamily: FONT.mono, fontSize: 22, letterSpacing: 2, color: C.muted}}>
              HOST CLIP
            </div>
            <div style={{fontFamily: FONT.mono, fontSize: 17, color: C.muted, opacity: 0.75}}>
              drop into public/host/
            </div>
          </AbsoluteFill>
        )}
      </div>

      {/* ------------------------------------------------- handle chip */}
      <div
        style={{
          position: 'absolute',
          left: TILE.x + TILE.w + 26,
          top: tileY + TILE.h / 2 - 42,
          opacity: fadeOf(chipP),
        }}
      >
        <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 27, color: C.ink, letterSpacing: 1}}>
          {p.handle}
        </div>
        <div style={{fontFamily: FONT.mono, fontSize: 20, color: C.muted, marginTop: 8, letterSpacing: 2}}>
          {p.role.toUpperCase()}
        </div>
        <div style={{display: 'flex', alignItems: 'center', gap: 9, marginTop: 16}}>
          <div
            style={{
              width: 11,
              height: 11,
              borderRadius: 999,
              background: C.redHot,
              opacity: 0.55 + Math.sin(frame / 9) * 0.45,
            }}
          />
          <div style={{fontFamily: FONT.mono, fontSize: 18, color: C.muted, letterSpacing: 2}}>REC</div>
        </div>
      </div>

      <Grain />
      <Vignette />
    </AbsoluteFill>
  );
};
