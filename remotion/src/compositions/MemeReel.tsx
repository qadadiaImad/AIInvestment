// MemeReel.tsx — a rubber-hose cartoon character reacting to a REAL chart
// playing on the monitor in front of him. 1080x1920, 30fps, 510 frames (17s).
//
// Four independent layers, per references/meme-reel-pipeline.md §1 — which is
// exactly why this is composited rather than generated:
//   room plate   static illustrated wall/desk/monitor (Higgsfield, once)
//   screen       TapeChart, real IBKR bars, matrix3d-mapped onto the monitor
//   character    RubberHoseRig, pivot-rigged SVG, posed per story beat
//   camera       one intention: wide -> monitor close-up -> back out
//
// THE RAIL (brief §5). The reference reel this format comes from hooks on
// "I turned -19,168 into +123,716". We do not ship that, and softening it into
// a meme would not make it less of a returns claim. The character reacts to a
// PATTERN, not to a payout: a level that held. Every on-screen number is a
// PRICE. There is no P&L, no position, no return, and no counter of money
// anywhere in this composition or in any component it mounts.
//
// The data is the INTC failed breakout of June-July 2026 — real daily bars
// pulled from IBKR (see the fixture's `footer` for the stamp), the same window
// the ta_quiz case study uses. Nothing here authors OHLC.
import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {C, FONT} from '../slides/theme';
import {EASE, fadeOf, wiggle} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';
import {ScreenInsert} from '../components/ScreenInsert';
import type {Quad} from '../components/screenMath';
import {TapeChart} from '../components/TapeChart';
import {ToonRig} from '../characters/toonRig';
import {GROUND as TOON_GROUND, VB_H as TOON_VB_H} from '../characters/toonSkeleton';

const candleSchema = z.object({o: z.number(), h: z.number(), l: z.number(), c: z.number()});
const ptSchema = z.object({x: z.number(), y: z.number()});

export const memeReelSchema = z.object({
  /** Room plate under public/. */
  plate: z.string(),
  /** The monitor's screen corners in composition space: TL, TR, BR, BL.
   * MEASURED from the accepted plate by scripts/meme_reel/measure_screen_quad.py,
   * never guessed — the generator does not put the monitor where the prompt
   * asked, and a guessed quad is the "insert lands off the monitor" bug. */
  quad: z.array(ptSchema).length(4),
  /** Native size the chart renders at before being mapped down. Its aspect
   * should match the measured quad's, or the chart is squashed. */
  chartWidth: z.number(),
  chartHeight: z.number(),
  subject: z.string(),
  levelPrice: z.number(),
  levelLabel: z.string(),
  candles: z.array(candleSchema).min(6),
  /** Index of the bar the whole reel is about — it gets the long print. */
  storyBar: z.number(),
  captions: z.array(z.object({from: z.number(), to: z.number(), text: z.string()})),
  footer: z.string(),
  /** Path under public/ to a TRANSPARENT character performance video, animated
   * externally (Cartoon Animator / Character Animator / Moho / AE) and exported
   * as VP8/VP9 + yuva420p WebM, or ProRes 4444.
   *
   * It must be authored on a STATIC 1080x1920 canvas in the same world space as
   * the room plate — character only, NO camera move baked in. This composition
   * applies the camera to the room and the character together, so a baked-in
   * push would double up. See content/meme_reel/ANIMATION_BRIEF.md.
   *
   * When absent, the built-in ToonRig is used instead, so the reel still
   * renders and still previews the timing. */
  characterSrc: z.string().optional(),
  /** Character staging, in composition space. Tuned against the plate's floor. */
  charCenterX: z.number(),
  charFeetY: z.number(),
  charHeight: z.number(),
  durationInFrames: z.number(),
});
export type MemeReelProps = z.infer<typeof memeReelSchema>;

export const MEME_REEL_FRAMES = 510;

// ------------------------------------------------------------------ camera
// ONE camera intention (playbook §5): the room, then the screen, then back to
// the room. It is expressed as focal point + scale rather than a CSS
// transform-origin, because animating transform-origin while scaling makes the
// frame jump; solving for the translate that pins a moving focal point to the
// frame centre does not.
type Key = {f: number; v: number; ease?: (t: number) => number};
const track = (frame: number, keys: Key[]): number => {
  if (frame <= keys[0].f) return keys[0].v;
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i];
    const b = keys[i + 1];
    if (frame <= b.f) {
      return interpolate(frame, [a.f, b.f], [a.v, b.v], {
        easing: b.ease ?? EASE.cruise,
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
    }
  }
  return keys[keys.length - 1].v;
};

export const MemeReel: React.FC<MemeReelProps> = (p) => {
  const frame = useCurrentFrame();
  const quad = p.quad as unknown as Quad;

  const screenCx = (quad[0].x + quad[2].x) / 2;
  const screenCy = (quad[0].y + quad[2].y) / 2;

  // The wide framing sits slightly above centre so the character's head and
  // the monitor both live in the upper two thirds, where a phone viewer looks.
  const WIDE = {x: 540, y: 900};

  // Scale. The screen is only 417px wide in the plate, so the story bar gets a
  // genuine close-up — at 1.0 the candles are unreadable on a phone, and no
  // amount of chart polish fixes a chart nobody can see.
  const camScale = track(frame, [
    {f: 0, v: 1.0},
    {f: 70, v: 1.0},
    {f: 130, v: 1.1}, // creeps in as he notices
    {f: 196, v: 1.14},
    {f: 214, v: 2.05, ease: EASE.enter}, // cut-in to the monitor for the story bar
    {f: 250, v: 2.12},
    {f: 258, v: 2.24, ease: EASE.exit}, // emphasis hit as the close lands
    {f: 276, v: 2.05, ease: EASE.settleBack},
    {f: 296, v: 1.16, ease: EASE.enter}, // back out to his reaction
    {f: 330, v: 1.12},
    {f: 392, v: 1.06},
    {f: 452, v: 1.0, ease: EASE.cruise}, // wide for the shrug
    {f: 510, v: 1.0},
  ]);

  const camX = track(frame, [
    {f: 0, v: WIDE.x},
    {f: 196, v: WIDE.x - 40},
    {f: 214, v: screenCx, ease: EASE.enter},
    {f: 276, v: screenCx},
    {f: 296, v: WIDE.x - 30, ease: EASE.enter},
    {f: 452, v: WIDE.x, ease: EASE.cruise},
    {f: 510, v: WIDE.x},
  ]);

  const camY = track(frame, [
    {f: 0, v: WIDE.y},
    {f: 196, v: WIDE.y - 30},
    {f: 214, v: screenCy, ease: EASE.enter},
    {f: 276, v: screenCy},
    {f: 296, v: WIDE.y - 20, ease: EASE.enter},
    {f: 452, v: WIDE.y, ease: EASE.cruise},
    {f: 510, v: WIDE.y},
  ]);

  // Pin the focal point to the frame centre.
  const tx = 540 - camX * camScale;
  const ty = 960 - camY * camScale;

  // A hand-held breath on the camera so the plate never sits perfectly still.
  const camDriftX = wiggle(frame, 7, 3.2, 0.35);
  const camDriftY = wiggle(frame, 8, 2.4, 0.3);

  // ------------------------------------------------------------- the tape
  // The beat schedule. History prints fast; the story bar takes 46 frames so
  // the viewer watches it trade up through the level and settle back BELOW it,
  // which is the entire point of the reel; the aftermath prints under the
  // facepalm.
  const {appearFrames, formFrames} = React.useMemo(() => {
    const a: number[] = [];
    const f: number[] = [];
    for (let i = 0; i < p.candles.length; i++) {
      if (i < p.storyBar) {
        a.push(20 + i * 7);
        f.push(6);
      } else if (i === p.storyBar) {
        a.push(206);
        f.push(46);
      } else {
        a.push(300 + (i - p.storyBar - 1) * 22);
        f.push(9);
      }
    }
    return {appearFrames: a, formFrames: f};
  }, [p.candles.length, p.storyBar]);

  // Panel boot: the monitor wakes in the first second with a couple of
  // flickers, so the screen reads as a device rather than a hole in the wall.
  const glow = frame < 8 ? 0 : frame < 26 ? (frame % 3 === 0 ? 0.72 : 1) : 1;

  // ---------------------------------------------------------- the caption
  const caption = p.captions.find((c) => frame >= c.from && frame < c.to);
  const capP = caption
    ? interpolate(frame, [caption.from, caption.from + 9], [0, 1], {
        easing: EASE.enter,
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      }) *
      interpolate(frame, [caption.to - 8, caption.to], [1, 0], {
        easing: EASE.exit,
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;

  // charHeight is the rig's whole viewBox height in frame px; the toon rig's
  // feet sit at TOON_GROUND_FRAC of it.
  const charGroundOffset = (p.charHeight * TOON_GROUND) / TOON_VB_H;

  // The monitor close-up is a CUTAWAY: for those frames we are looking at the
  // screen, and he is not in the shot. Without this his leaning head clips into
  // the right edge of the close-up and covers the level label and the price
  // tag — the two things the whole beat exists to make legible. The camera is
  // travelling fast at both ends of the window, so the fade itself is invisible.
  // He must be back BEFORE the camera starts pulling out at 296, or the
  // pull-back plays over an empty room for half a second. By 268 he has
  // already recoiled upright, so his head is travelling away from the monitor
  // and cannot clip back into the tail of the close-up.
  const charOpacity =
    interpolate(frame, [206, 216], [1, 0], {easing: EASE.exit, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) +
    interpolate(frame, [276, 290], [0, 1], {easing: EASE.enter, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{backgroundColor: '#E9DEC7'}}>
      {/* ---------------------------------------------------- the world.
          Everything the camera moves over lives in here. No CSS perspective
          anywhere in this chain — ScreenInsert's homography does the projective
          divide itself, and a second one would push the chart off the quad. */}
      <AbsoluteFill
        style={{
          transform: `translate(${tx + camDriftX}px, ${ty + camDriftY}px) scale(${camScale})`,
          transformOrigin: '0 0',
        }}
      >
        <Img
          src={staticFile(p.plate)}
          style={{position: 'absolute', left: 0, top: 0, width: 1080, height: 1920, objectFit: 'cover'}}
        />

        <ScreenInsert
          width={p.chartWidth}
          height={p.chartHeight}
          quad={quad}
          glow={glow}
          glowColor="#3FBF8A"
          reflection={0.09}
        >
          <TapeChart
            candles={p.candles}
            appearFrames={appearFrames}
            formFrames={formFrames}
            levelPrice={p.levelPrice}
            levelLabel={p.levelLabel}
            levelInFrame={96}
            subject={p.subject}
            width={p.chartWidth}
            height={p.chartHeight}
          />
        </ScreenInsert>

        {/* Vector bezel edge over the insert — the art spec's call: one plate
            plus a drawn rim, rather than a second generated transparent asset
            that would have to stay in registration with it. */}
        <svg
          width={1080}
          height={1920}
          viewBox="0 0 1080 1920"
          style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}
        >
          <rect
            x={quad[0].x - 1}
            y={quad[0].y - 1}
            width={quad[1].x - quad[0].x + 2}
            height={quad[2].y - quad[0].y + 2}
            rx={6}
            fill="none"
            stroke="#2C2F36"
            strokeWidth={3}
          />
        </svg>

        {/* ------------------------------------------------- the character.
            Either an externally-animated transparent performance, or the
            built-in rig. Both sit INSIDE the camera transform, so the character
            is pushed and panned along with the room exactly as if he were in
            it — which is why the delivered video must not contain a camera
            move of its own. */}
        {p.characterSrc ? (
          <OffthreadVideo
            src={staticFile(p.characterSrc)}
            transparent
            style={{
              position: 'absolute',
              left: 0,
              top: 0,
              width: 1080,
              height: 1920,
              opacity: Math.min(1, charOpacity),
            }}
          />
        ) : (
          <div
            style={{
              position: 'absolute',
              left: p.charCenterX - (p.charHeight * 1700) / 2900 / 2,
              top: p.charFeetY - charGroundOffset,
              opacity: Math.min(1, charOpacity),
            }}
          >
            <ToonRig height={p.charHeight} facing="left" />
          </div>
        )}
      </AbsoluteFill>

      {/* ------------------------------------------------------- captions.
          Outside the camera transform, so type stays pinned and crisp while
          the world moves under it. */}
      {caption ? (
        <div
          style={{
            position: 'absolute',
            left: 70,
            right: 70,
            bottom: 190,
            textAlign: 'center',
            opacity: fadeOf(capP),
            transform: `translateY(${(1 - capP) * 16}px)`,
          }}
        >
          <div
            style={{
              display: 'inline-block',
              maxWidth: 880,
              padding: '16px 28px',
              borderRadius: 16,
              background: 'rgba(12,14,18,0.86)',
              border: '1px solid rgba(255,255,255,0.12)',
              fontFamily: FONT.body,
              fontWeight: 700,
              fontSize: 46,
              lineHeight: 1.24,
              color: C.ink,
              letterSpacing: -0.5,
            }}
          >
            {caption.text}
          </div>
        </div>
      ) : null}

      {/* Standard footer, every frame — the provenance stamp and the
          not-advice line are not optional decoration. It gets its own scrim
          because it lands on a wood floor, and a disclaimer nobody can read is
          not a disclaimer. */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 108,
          background: 'linear-gradient(to top, rgba(233,222,199,0.94) 40%, rgba(233,222,199,0))',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 40,
          left: 30,
          right: 30,
          textAlign: 'center',
          fontFamily: FONT.mono,
          fontSize: 17,
          lineHeight: 1.35,
          letterSpacing: -0.2,
          color: 'rgba(20,16,12,0.66)',
        }}
      >
        {p.footer}
      </div>

      <Vignette strength={0.3} />
      <Grain opacity={0.03} />
    </AbsoluteFill>
  );
};
