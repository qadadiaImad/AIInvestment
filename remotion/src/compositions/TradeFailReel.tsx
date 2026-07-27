// TradeFailReel.tsx — 40s vertical reel. A character reads a textbook bullish
// setup on a real chart, takes it, is asked to call it, and is wrong.
//
// 1080x1920, 30fps, 1200 frames. Built to content/btc_reel/BUILD_SPEC.md with
// the owner's five overrides applied (see that file's reconciliation header):
// a 4s quiz window rather than 5s, an ending that states the lesson as a rule
// rather than baiting comments, cuts between character and chart rather than
// co-presence, a measured floor plane, and the generated pose drawings rather
// than the SVG rig.
//
// WHY THIS ISN'T A SECOND TradingQuiz. TradingQuiz draws the risk frame AFTER
// the outcome, as explanation. Here it has to land BEFORE the ask, because the
// question is a prediction: a viewer asked to call a trade without seeing what
// being wrong costs is guessing, and the loss then reads as bad luck instead of
// as a bounded bet that lost. So the timeline is build -> pattern -> ENTRY ->
// quiz -> wait -> fail -> lesson, and the trade frame is on screen from the
// entry beat through the very last frame.
//
// WHAT IS AND ISN'T AUTHORED HERE. Every price, level, pivot, trendline and
// outcome comes from remotion/src/fixtures/btc_reel/setup.json, produced by
// scripts/btc_reel/find_failed_setup.py scanning 250 real IBKR daily bars. This
// file owns timing, staging and prose only. Per CLAUDE.md §10.1 there is no
// arithmetic anywhere in it that could move a level or change who won.
//
// THE RAIL. IBIT is a Bitcoin ETF, labelled as such on every frame — spot BTC
// is not on the brokerage feed and the egress policy blocks every crypto API,
// so the chart is never presented as BTC/USD itself. No P&L, no returns, no
// position size. The loss is stated in R, which is a unit of the plan, not of
// money.
import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {C, FONT} from '../slides/theme';
import {EASE, fadeOf, wiggle} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';
import {ScreenInsert} from '../components/ScreenInsert';
import type {Quad} from '../components/screenMath';
import {StructureChart} from '../components/StructureChart';
import {PoseCut, poseHead, type Cut} from '../characters/poseCut';
import {whip} from '../motion/toon';
import {
  DustPuff,
  FlashCut,
  ImpactLines,
  ScreenPulse,
  ShockRing,
  SpeedLines,
  SweatBeads,
  kick,
} from '../motion/ToonFX';

const barSchema = z.object({
  d: z.string().optional(),
  o: z.number(),
  h: z.number(),
  l: z.number(),
  c: z.number(),
});
const zoneSchema = z.object({
  price: z.number(),
  touches: z.number(),
  bars: z.array(z.number()),
});

export const tradeFailReelSchema = z.object({
  plate: z.string(),
  quad: z.array(z.object({x: z.number(), y: z.number()})).length(4),
  chartWidth: z.number(),
  chartHeight: z.number(),

  symbol: z.string(),
  subject: z.string(),
  stamp: z.string(),
  bars: z.array(barSchema).min(20),
  setupBars: z.number(),
  support: zoneSchema,
  resistances: z.array(zoneSchema),
  trendline: z
    .object({m: z.number(), c: z.number(), from: z.number(), touches: z.number()})
    .nullable()
    .optional(),
  trigger: z.object({bar: z.number(), name: z.string()}),
  entry: z.number(),
  stop: z.number(),
  target: z.number(),
  risk: z.number(),
  /** Index into the reveal bars where the stop was hit. Derived in Python; a
   * payoff cannot fire on a trade that never got there. */
  slAt: z.number(),
  mfe: z.number(),
  drop: z.number(),

  /** Character staging, in composition space. Locked against the measured
   * floor plane by GroundingCheck — see ROOM in that file. */
  charCenterX: z.number(),
  charFeetY: z.number(),
  charHeight: z.number(),

  footer: z.string(),
  durationInFrames: z.number(),
});
export type TradeFailReelProps = z.infer<typeof tradeFailReelSchema>;

export const TRADE_FAIL_FRAMES = 1200;

// ------------------------------------------------------------ the beat sheet
// Eight beats summing to exactly 1200f / 40.0s. The split is deliberately
// inverted from instinct: the setup is the SMALLEST fraction of runtime and the
// tension around the decision is the largest.
const B = {
  hook: 0,
  build: 90,
  pattern: 360,
  entry: 510,
  quiz: 660,
  wait: 780, // quiz is 120f / 4.0s — the owner's override, see the spec header
  fail: 960,
  lesson: 1080,
  end: 1200,
};

/** The frame the take lands on — every part of the hit keys off this one
 * number so the drawing, the lines, the flash, the camera and the sound cannot
 * drift apart. */
const SHOCK_AT = 1014;

const COUNT_PER = 30;
const COUNT_N = 4;

// Chart layer draw-ins.
const SUPPORT_IN = 150;
const RES_IN = 198;
const TREND_IN = 246;
const PATTERN_IN = 424;
const TRADE_IN = 516;
const DECISION_IN = 466;
const OUTCOME_IN = 966;

// Bar schedule. History prints fast; the two bars the whole reel is about —
// the hammer that sweeps support and reclaims, and the bar that breaks it —
// get long prints so the viewer watches them trade rather than see them appear.
const HAMMER_IN = 366;
const HAMMER_FORM = 54;
const ENTRYBAR_IN = 432;
const BREAK_IN = 968;
const BREAK_FORM = 46;

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

// ------------------------------------------------------------- the character
// Limited animation: hold a drawing, cut on the beat. The anxious stretch
// (quiz + wait) is a rocking alternation between three poses at ~1.5s
// intervals, which is what reads as nerves rather than as a loop — a two-pose
// alternation reads as a metronome.
const CUTS: Cut[] = [
  // Density is the point. The first cut of this held each drawing for ~60
  // frames — twenty cuts across forty seconds — and that is what read as a
  // slideshow rather than as animation. Real limited animation cuts two to
  // four times as often and puts a wind-up, a smear and a settle on every one
  // of them (motion/toon.ts). Roughly one cut per second here, tightest
  // through the reaction, loosest through the quiet holds.
  {at: 0, pose: 'idle', drift: {dy: -3}},
  {at: 26, pose: 'turning', drift: {dx: -6, tilt: -0.8}},
  {at: 52, pose: 'idle', drift: {dy: -2}},
  {at: 70, pose: 'leans_a', drift: {dx: -9, tilt: -1.2}},
  // 96-252 out of shot (the structure drawing)
  {at: 252, pose: 'leans_a', drift: {dx: -7, tilt: -1}},
  {at: 286, pose: 'notices', drift: {dx: -10, tilt: -1.4}},
  {at: 318, pose: 'point', drift: {dx: -5}},
  {at: 344, pose: 'leans_b', drift: {dx: -7, tilt: -1.1}},
  // 372-430 out of shot (the hammer)
  {at: 430, pose: 'notices', drift: {dx: -11, tilt: -1.6}}, // the take, on the cut wide
  {at: 452, pose: 'crouch', drift: {dy: 6}}, // loads down — the beat before he commits
  {at: 470, pose: 'point', drift: {dx: -6}},
  {at: 492, pose: 'leans_b', drift: {dx: -6, tilt: -1}},
  // 512-570 out of shot (entry/stop/target draw)
  {at: 570, pose: 'leans_a', drift: {dx: -9, dScale: 1.02}}, // commits, on the cut wide
  {at: 596, pose: 'point', drift: {dx: -5}},
  {at: 620, pose: 'idle', drift: {dy: -1}}, // his stillest stretch, against what follows
  {at: 648, pose: 'turning', drift: {dx: 3}},
  // --- the quiz. His nerves start on the SAME frame the viewer's timer does.
  {at: 662, pose: 'crouch', drift: {dy: 6}},
  {at: 690, pose: 'leans_b', drift: {dx: 5, tilt: 1.2}},
  {at: 714, pose: 'bending', drift: {dx: -6, dScale: 1.015}},
  {at: 740, pose: 'crouch', drift: {dy: 7}},
  {at: 762, pose: 'leans_b', drift: {dx: 4, tilt: 1}},
  // --- the wait. Same vocabulary, slower rhythm, bigger amplitude: the same
  // anxiety wearing on, not a new one.
  {at: 786, pose: 'bending', drift: {dx: -7, dScale: 1.02}},
  {at: 816, pose: 'crouch', drift: {dy: 8}},
  {at: 842, pose: 'leans_b', drift: {dx: 6, tilt: 1.6}},
  // 870-908 out of shot (the bars going nowhere)
  {at: 908, pose: 'crouch', drift: {dy: 8}},
  {at: 930, pose: 'bending', drift: {dx: -6}},
  {at: 948, pose: 'leans_b', drift: {dx: 5, tilt: 1.4}},
  // 966-1014 out of shot (the break)
  // --- the reaction. Tightest cutting in the reel: four drawings in 70
  // frames. A take that holds is not a take.
  {at: 1014, pose: 'shock', drift: {dx: 30, dScale: 0.99, tilt: 3}}, // hard cut wide
  {at: 1038, pose: 'stagger', drift: {dx: 16, tilt: 2.4}},
  {at: 1062, pose: 'crouch', drift: {dy: 10}},
  {at: 1082, pose: 'facepalm', drift: {dy: 13, dScale: 0.985, tilt: 1.4}},
  // --- recalibrating. Small and linear: overshoot is surprise, and the
  // surprise is over.
  {at: 1136, pose: 'leans_a', drift: {dx: -5, tilt: -0.8}},
  {at: 1166, pose: 'turning', drift: {dx: -4}},
];

/** Frames the camera is inside the monitor and he is out of shot.
 *
 * These MUST bracket the camera moves exactly, and the fade out MUST finish
 * before the push begins. The first cut of this had him fading over the eight
 * frames AFTER the camera started diving, and the result is unmistakable in a
 * still: he is at 90% opacity while the world is already at 1.7x, so a single
 * forearm fills the frame. Fading a character out is not the same as getting
 * him out of the shot in time. */
// Every camera key below is authored so the move happens in ONE frame at
// exactly these boundaries. A six-frame ease instead leaves the camera flying
// through an empty room, because he is already cut — ten transitions of that
// is two seconds of the reel spent looking at nobody.
const CUTAWAYS: [number, number][] = [
  [96, 252],
  [372, 430],
  [512, 570],
  [870, 908], // the ambiguous bars, which he otherwise stands in front of
  [966, 1014],
];
// He is CUT, not faded. Two earlier versions of this both failed the same way
// and it is only visible in a still: any fade at all leaves him semi-present
// over a moving camera, so his pointing arm hangs across the chart as a ghost
// for a few frames. Fading a character out is not the same as cutting away
// from him. Because the CUTAWAY bounds are exactly the camera's own push and
// landing frames, a binary switch lands on the same frame as the camera cut
// and is therefore invisible — which is what limited animation does anyway.

type Caption = {from: number; to: number; text: string};

export const TradeFailReel: React.FC<TradeFailReelProps> = (p) => {
  const frame = useCurrentFrame();
  const quad = p.quad as unknown as Quad;
  const screenCx = (quad[0].x + quad[2].x) / 2;
  const screenCy = (quad[0].y + quad[2].y) / 2;
  // The focal point is pinned to the frame centre by tx = 540 - camX*scale, so
  // a wide focal point ABOVE centre translates the world down and leaves an
  // uncovered band at the top of the frame — 60px of it at y=900, visible in
  // every scale-1.0 shot. Centring it and never dropping below 1.02 covers the
  // frame with margin to spare for the hand-held drift.
  const WIDE = {x: 540, y: 960};

  const ns = p.setupBars;
  const revealCount = p.bars.length - ns;

  // ------------------------------------------------------------ bar schedule
  const {appearFrames, formFrames} = React.useMemo(() => {
    const a: number[] = [];
    const f: number[] = [];
    const histN = p.trigger.bar; // bars before the hammer
    for (let i = 0; i < p.bars.length; i++) {
      if (i < histN) {
        a.push(96 + Math.round((i * (344 - 96)) / Math.max(1, histN - 1)));
        f.push(5);
      } else if (i === p.trigger.bar) {
        a.push(HAMMER_IN);
        f.push(HAMMER_FORM);
      } else if (i < ns) {
        a.push(ENTRYBAR_IN);
        f.push(26);
      } else {
        const r = i - ns;
        if (r < p.slAt) {
          // The ambiguous bars. Stretched to ~34f each: tension needs the beats
          // slower, not faster. CANDLE_TICKS stays 3 — a slow bar is still tape.
          a.push(800 + r * 40);
          f.push(34);
        } else if (r === p.slAt) {
          a.push(BREAK_IN);
          f.push(BREAK_FORM);
        } else {
          a.push(1018 + (r - p.slAt - 1) * 7);
          f.push(8);
        }
      }
    }
    return {appearFrames: a, formFrames: f};
  }, [p.bars.length, ns, p.trigger.bar, p.slAt]);

  // ---------------------------------------------------------------- camera
  const camScaleKeys: Key[] = [
    {f: 0, v: 1.02},
    {f: 70, v: 1.05},
    {f: 95, v: 1.07}, // hold to the frame before the cut — see the note on CUTAWAYS
    {f: 96, v: 2.0, ease: EASE.enter}, // into the monitor for the structure
    {f: 251, v: 2.06},
    {f: 252, v: 1.22, ease: EASE.enter}, // back out, he starts paying attention
    {f: 356, v: 1.2},
    {f: 371, v: 1.21},
    {f: 372, v: 2.18, ease: EASE.enter}, // into the monitor for the hammer
    {f: 429, v: 2.24},
    {f: 430, v: 1.03, ease: EASE.exit}, // hard cut wide on the take
    {f: 511, v: 1.03},
    {f: 512, v: 2.1, ease: EASE.enter}, // into the monitor while entry/stop/target draw
    {f: 569, v: 2.16},
    {f: 570, v: 1.03, ease: EASE.exit}, // cut wide on the commit
    {f: 660, v: 1.04},
    {f: 869, v: 1.1, ease: EASE.cruise}, // the slow anxious creep
    {f: 870, v: 2.02, ease: EASE.enter}, // a look at the bars going nowhere
    {f: 907, v: 2.06},
    {f: 908, v: 1.12, ease: EASE.exit},
    {f: 965, v: 1.18, ease: EASE.cruise},
    {f: 966, v: 2.2, ease: EASE.enter}, // into the monitor for the break
    {f: 1013, v: 2.28},
    {f: 1014, v: 1.03, ease: EASE.exit}, // hard cut wide on the shock
    {f: 1200, v: 1.08},
  ];
  const camScale = track(frame, camScaleKeys);

  const camXKeys: Key[] = [
    {f: 0, v: WIDE.x},
    {f: 95, v: WIDE.x}, // HOLD. Without this the first segment eases from
    {f: 96, v: screenCx, ease: EASE.enter}, // frame 0 and the hook shot drifts.
    {f: 251, v: screenCx},
    {f: 252, v: WIDE.x, ease: EASE.enter},
    {f: 371, v: WIDE.x},
    {f: 372, v: screenCx, ease: EASE.enter},
    {f: 429, v: screenCx},
    {f: 430, v: WIDE.x, ease: EASE.exit},
    {f: 511, v: WIDE.x},
    {f: 512, v: screenCx, ease: EASE.enter},
    {f: 569, v: screenCx},
    {f: 570, v: WIDE.x, ease: EASE.exit},
    // Biased right through the quiz/wait so he sits toward the frame edge and
    // the monitor is not behind him.
    {f: 700, v: WIDE.x + 26},
    {f: 869, v: WIDE.x + 26},
    {f: 870, v: screenCx, ease: EASE.enter},
    {f: 907, v: screenCx},
    {f: 908, v: WIDE.x + 26, ease: EASE.exit},
    {f: 965, v: WIDE.x + 18},
    {f: 966, v: screenCx, ease: EASE.enter},
    {f: 1013, v: screenCx},
    {f: 1014, v: WIDE.x, ease: EASE.exit},
    {f: 1200, v: WIDE.x},
  ];
  const camX = track(frame, camXKeys);

  const camYKeys: Key[] = [
    {f: 0, v: WIDE.y},
    {f: 95, v: WIDE.y},
    {f: 96, v: screenCy, ease: EASE.enter},
    {f: 251, v: screenCy},
    {f: 252, v: WIDE.y, ease: EASE.enter},
    {f: 371, v: WIDE.y},
    {f: 372, v: screenCy, ease: EASE.enter},
    {f: 429, v: screenCy},
    {f: 430, v: WIDE.y, ease: EASE.exit},
    {f: 511, v: WIDE.y},
    {f: 512, v: screenCy, ease: EASE.enter},
    {f: 569, v: screenCy},
    {f: 570, v: WIDE.y, ease: EASE.exit},
    {f: 869, v: WIDE.y - 10},
    {f: 870, v: screenCy, ease: EASE.enter},
    {f: 907, v: screenCy},
    {f: 908, v: WIDE.y - 10, ease: EASE.exit},
    {f: 965, v: WIDE.y - 20},
    {f: 966, v: screenCy, ease: EASE.enter},
    {f: 1013, v: screenCy},
    {f: 1014, v: WIDE.y, ease: EASE.exit},
    {f: 1200, v: WIDE.y},
  ];
  const camY = track(frame, camYKeys);

  // WHIP. Camera velocity in composition px/frame. Every camera change here is
  // a one-frame cut, so this spikes hard on exactly those frames — which is
  // what the speed lines and the frame's own motion blur key off. Decayed over
  // three frames so the streak reads as travel rather than as a single odd
  // frame.
  const camAt = (f: number) => ({
    x: track(f, camXKeys) * track(f, camScaleKeys),
    y: track(f, camYKeys) * track(f, camScaleKeys),
  });
  const vNow = camAt(frame);
  const vPrev = camAt(frame - 1);
  const rawWhip = whip(Math.hypot(vNow.x - vPrev.x, vNow.y - vPrev.y));
  const whipK = Math.max(
    rawWhip,
    (() => {
      const a = camAt(frame - 1);
      const b = camAt(frame - 2);
      return whip(Math.hypot(a.x - b.x, a.y - b.y)) * 0.55;
    })()
  );

  const tx = 540 - camX * camScale;
  const ty = 960 - camY * camScale;
  // A hand-held breath, plus a real IMPACT on the shock cut — a decaying
  // oscillation whose frequency drops as it dies, which is what a hit does and
  // what a plain sine-times-decay does not. The frame recoils on the same
  // frames the drawn impact lines fire, so it reads as one event.
  const kk = kick(frame - SHOCK_AT, 30, 20);
  const camDriftX = wiggle(frame, 7, 3.0, 0.35) + kk.x;
  const camDriftY = wiggle(frame, 8, 2.2, 0.3) + kk.y;

  const glow = frame < 8 ? 0 : frame < 24 ? (frame % 3 === 0 ? 0.74 : 1) : 1;

  const charVisible = !CUTAWAYS.some(([a, b]) => frame >= a && frame < b);

  // ------------------------------------------------------------- the quiz
  const inQuiz = frame >= B.quiz && frame < B.wait;
  const secsLeft = Math.max(0, COUNT_N - Math.floor((frame - B.quiz) / COUNT_PER));
  const quizP = interpolate(frame, [B.quiz, B.quiz + 14], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const quizOut = interpolate(frame, [B.wait - 10, B.wait], [1, 0], {
    easing: EASE.exit,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ringP = inQuiz
    ? interpolate(frame, [B.quiz, B.wait], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})
    : 0;

  // The answer badge lands with the break, not with the timer — the whole
  // middle of this reel is the gap between committing and finding out.
  const answerP =
    interpolate(frame, [1006, 1022], [0, 1], {
      easing: EASE.enter,
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }) *
    interpolate(frame, [1088, 1106], [1, 0], {
      easing: EASE.exit,
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  const rzP = interpolate(frame, [1096, 1116], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const captions: Caption[] = [
    {from: 16, to: 88, text: `${p.symbol}, daily. Everything here is real.`},
    {from: 258, to: 350, text: `Support ${p.support.price.toFixed(2)}, held ${p.support.touches}×. Trendline rising into it.`},
    {from: 436, to: 508, text: `Then this: ${p.trigger.name.toLowerCase()}.`},
    {from: 524, to: 650, text: `Long ${p.entry.toFixed(2)}. Stop under the wick. Target 2R.`},
    {from: 800, to: 950, text: 'Four bars. It goes nowhere.'},
    {from: 1030, to: 1074, text: `Stopped. It kept going — ${Math.abs(p.drop).toFixed(0)}% lower.`},
  ];
  const caption = captions.find((c) => frame >= c.from && frame < c.to);
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

  // Bars elapsed since entry, clamped to the ambiguous stretch — this HUD only
  // runs while the trade is unresolved.
  const barsIn = Math.min(p.slAt, Math.max(0, Math.floor((frame - 800) / 40) + 1));

  // Where his head actually is on THIS frame — measured per drawing and run
  // through the same placement maths the drawing uses, so an effect anchored
  // to it inherits the drift, the boil and the squash. A fixed anchor derived
  // from the standing figure puts the sweat in empty wall the moment he bends,
  // and the head travels most of the body's height between `idle` and
  // `crouch`.
  const head = poseHead({
    frame,
    height: p.charHeight,
    footX: p.charCenterX,
    footY: p.charFeetY,
    cuts: CUTS,
    end: B.end,
    motion: 'toon',
    facing: 'left',
  }) ?? {x: p.charCenterX, y: p.charFeetY - p.charHeight * 0.84, w: p.charHeight * 0.3};

  const R = 92;
  const CIRC = 2 * Math.PI * R;

  return (
    <AbsoluteFill style={{backgroundColor: '#E9DEC7'}}>
      {/* ------------------------------------------------------- the world */}
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
          glowColor="#2FBF7A"
          reflection={0.08}
        >
          <StructureChart
            bars={p.bars}
            setupBars={ns}
            appearFrames={appearFrames}
            formFrames={formFrames}
            support={p.support}
            resistance={p.resistances[0]}
            trendline={p.trendline ?? null}
            triggerBar={p.trigger.bar}
            triggerName={p.trigger.name}
            entry={p.entry}
            stop={p.stop}
            target={p.target}
            supportIn={SUPPORT_IN}
            resistanceIn={RES_IN}
            trendIn={TREND_IN}
            patternIn={PATTERN_IN}
            tradeIn={TRADE_IN}
            decisionIn={DECISION_IN}
            outcomeIn={OUTCOME_IN}
            subject={p.subject}
            stamp={p.stamp}
            width={p.chartWidth}
            height={p.chartHeight}
          />
        </ScreenInsert>

        <svg width={1080} height={1920} viewBox="0 0 1080 1920" style={{position: 'absolute', left: 0, top: 0}}>
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

        {/* The panel throwing red light into the room as the bar breaks.
            Inside the camera transform and clipped to the monitor quad, so it
            is the screen emitting rather than a colour wash over the frame. */}
        <ScreenPulse quad={p.quad} since={frame - (BREAK_IN + BREAK_FORM - 24)} dur={30} />

        {/* The burst, BEHIND him. It opens upward and to the right — away
            from the monitor — rather than being masked off it, because a
            starburst with a hole cut in it reads as a mistake. */}
        <ImpactLines
          x={head.x}
          y={head.y}
          since={frame - SHOCK_AT}
          dur={15}
          count={11}
          r0={head.w * 0.72}
          len={head.w * 0.85}
          arc={[-Math.PI * 0.92, Math.PI * 0.18]}
        />
        <ShockRing x={head.x} y={head.y} since={frame - SHOCK_AT} dur={17} />

        <div style={{opacity: charVisible ? 1 : 0}}>
          <PoseCut
            height={p.charHeight}
            footX={p.charCenterX}
            footY={p.charFeetY}
            facing="left"
            cuts={CUTS}
            end={B.end}
            motion="toon"
          />
          {/* Dust off the floor as he staggers back. Inside the world layer so
              it is pushed and panned with the room he is standing in. */}
          <DustPuff x={p.charCenterX + 30} y={p.charFeetY} since={frame - 1040} dur={22} />
        </div>
      </AbsoluteFill>

      {/* --------------------------------------------------------- the FX.
          Frame-space, above the room and below the type. Each one is anchored
          to a beat that already exists in the story — none is here to fill a
          gap. Nothing is ever drawn over the price panel: an impact line
          across a candle would be asserting something about the data.

          `charVisible` gates every character-anchored effect, or sweat beads
          hang in mid-air through the chart close-ups. */}
      {charVisible && frame >= B.quiz && frame < 1000 ? (
        <SweatBeads
          x={head.x}
          y={head.y}
          since={frame - B.quiz}
          count={frame >= B.wait ? 3 : 2}
          scale={(head.w / 300) * 0.9}
        />
      ) : null}

      {/* THE TAKE. The flash fires on SHOCK_AT, the same frame the drawing cuts
          and the camera kicks — one event, not three. The lines are drawn back
          in the world layer, BEHIND him: the first version put them on top and
          the burst cut across his face, which reads as a bug rather than as an
          impact. */}
      <FlashCut since={frame - SHOCK_AT} frames={2} color="#FFF3E0" max={0.55} />

      {/* Speed lines over the whips, driven by the camera's own velocity — so
          they appear on exactly the frames it moves and never as decoration on
          a static shot. */}
      <SpeedLines k={whipK} seed={Math.floor(frame / 3)} />

      {/* ---------------------------------------------------------- hook */}
      {frame < 96 ? (
        <div
          style={{
            position: 'absolute',
            top: 108,
            left: 0,
            right: 0,
            textAlign: 'center',
            opacity: interpolate(frame, [4, 18, 82, 94], [0, 1, 1, 0], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <div
            style={{
              fontFamily: FONT.display,
              fontSize: 92,
              fontWeight: 700,
              color: '#0B1F16',
              lineHeight: 0.98,
              letterSpacing: -2,
              textShadow: '0 3px 0 rgba(255,255,255,.5)',
            }}
          >
            EVERY RULE
            <br />
            SAID BUY
          </div>
        </div>
      ) : null}

      {/* ---------------------------------------------------------- quiz */}
      {frame >= B.quiz && frame < B.wait + 2 ? (
        <div style={{position: 'absolute', inset: 0, opacity: quizP * quizOut}}>
          <div
            style={{
              position: 'absolute',
              top: 132,
              left: 0,
              right: 0,
              textAlign: 'center',
              fontFamily: FONT.mono,
              fontSize: 52,
              fontWeight: 700,
              color: '#0B1F16',
              letterSpacing: 1,
              textShadow: '0 3px 0 rgba(255,255,255,.55)',
            }}
          >
            BOUNCE OR BREAKDOWN?
          </div>

          {/* The ring is NEUTRAL. Tinting it with the answer colour announces
              the result before the timer ends — CLAUDE.md §10.3, leak #1. */}
          <svg width={1080} height={300} style={{position: 'absolute', top: 218, left: 0}}>
            <circle cx={540} cy={150} r={R} fill="rgba(4,16,12,.72)" stroke="rgba(255,255,255,.18)" strokeWidth={3} />
            <circle
              cx={540}
              cy={150}
              r={R}
              fill="none"
              stroke="#E8EDF2"
              strokeWidth={9}
              strokeLinecap="round"
              strokeDasharray={CIRC}
              strokeDashoffset={CIRC * ringP}
              transform="rotate(-90 540 150)"
            />
            <text
              x={540}
              y={172}
              fontFamily={FONT.mono}
              fontSize={80}
              fontWeight={700}
              fill="#E8EDF2"
              textAnchor="middle"
            >
              {secsLeft}
            </text>
          </svg>

          <div
            style={{
              position: 'absolute',
              top: 540,
              left: 0,
              right: 0,
              display: 'flex',
              justifyContent: 'center',
              gap: 26,
            }}
          >
            {['BOUNCE', 'BREAKDOWN'].map((t) => (
              <div
                key={t}
                style={{
                  padding: '18px 34px',
                  borderRadius: 14,
                  background: 'rgba(4,16,12,.78)',
                  border: '2px solid rgba(232,237,242,.30)',
                  fontFamily: FONT.mono,
                  fontSize: 38,
                  fontWeight: 700,
                  color: '#E8EDF2',
                  letterSpacing: 1.4,
                }}
              >
                {t}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* ------------------------------------------------- the open position.
          Bars elapsed, never a P&L. What makes the wait tense is that nothing
          is resolved, and a running money figure would resolve it. */}
      {frame >= B.wait && frame < 1000 ? (
        <div
          style={{
            position: 'absolute',
            top: 150,
            left: 0,
            right: 0,
            textAlign: 'center',
            opacity: interpolate(frame, [B.wait, B.wait + 12], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <span
            style={{
              display: 'inline-block',
              padding: '12px 26px',
              borderRadius: 999,
              background: 'rgba(4,16,12,.80)',
              border: '2px solid rgba(232,237,242,.24)',
              fontFamily: FONT.mono,
              fontSize: 34,
              fontWeight: 700,
              color: '#E8EDF2',
              letterSpacing: 2,
            }}
          >
            POSITION OPEN · {barsIn} {barsIn === 1 ? 'BAR' : 'BARS'} · UNRESOLVED
          </span>
        </div>
      ) : null}

      {/* --------------------------------------------------- the answer */}
      {answerP > 0 ? (
        <div
          style={{
            position: 'absolute',
            top: 146,
            left: 0,
            right: 0,
            textAlign: 'center',
            opacity: answerP,
            transform: `scale(${interpolate(answerP, [0, 1], [1.14, 1])})`,
          }}
        >
          <span
            style={{
              display: 'inline-block',
              padding: '16px 40px',
              borderRadius: 16,
              background: '#FF3B30',
              fontFamily: FONT.mono,
              fontSize: 56,
              fontWeight: 700,
              color: '#0B0304',
              letterSpacing: 2,
            }}
          >
            BREAKDOWN
          </span>
        </div>
      ) : null}

      {/* ------------------------------------------------- the R:R receipt.
          The plan, restated after it lost. Keeping the stated risk visible
          through the loss is what makes it one data point inside an edge
          rather than a wound — and R is a unit of the plan, not of money. */}
      {rzP > 0 ? (
        <div
          style={{
            position: 'absolute',
            top: 262,
            left: 0,
            right: 0,
            textAlign: 'center',
            opacity: rzP,
          }}
        >
          <span
            style={{
              display: 'inline-block',
              padding: '12px 28px',
              borderRadius: 12,
              background: 'rgba(4,16,12,.84)',
              border: '2px solid rgba(255,59,48,.5)',
              fontFamily: FONT.mono,
              fontSize: 30,
              fontWeight: 700,
              color: '#E8EDF2',
              letterSpacing: 1.6,
            }}
          >
            PLANNED −1R · BEST IT EVER GOT +{p.mfe.toFixed(2)}R
          </span>
        </div>
      ) : null}

      {/* --------------------------------------------------- the lesson.
          Stated as a rule and held to the last frame — the owner's override
          #2. Not a question to the comments. */}
      {frame >= 1104 ? (
        <div
          style={{
            position: 'absolute',
            top: 372,
            left: 56,
            right: 56,
            textAlign: 'center',
            opacity: interpolate(frame, [1104, 1126], [0, 1], {
              easing: EASE.enter,
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
            transform: `translateY(${interpolate(frame, [1104, 1130], [18, 0], {
              easing: EASE.enter,
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            })}px)`,
          }}
        >
          <div
            style={{
              padding: '26px 30px',
              borderRadius: 18,
              background: 'rgba(4,16,12,.90)',
              border: '2px solid rgba(34,224,126,.55)',
              fontFamily: FONT.body,
              fontWeight: 800,
              fontSize: 46,
              lineHeight: 1.2,
              color: '#E8EDF2',
              letterSpacing: -0.5,
            }}
          >
            A GOOD SETUP IS NOT A PREDICTION.
            <div style={{fontSize: 32, fontWeight: 600, color: '#9FD9BC', marginTop: 12, letterSpacing: 0}}>
              It is a bet with a known cost. He was wrong and still only lost 1R.
            </div>
          </div>
        </div>
      ) : null}

      {/* -------------------------------------------------------- caption */}
      {caption ? (
        <div
          style={{
            position: 'absolute',
            left: 64,
            right: 64,
            bottom: 196,
            textAlign: 'center',
            opacity: fadeOf(capP),
            transform: `translateY(${(1 - capP) * 14}px)`,
          }}
        >
          <span
            style={{
              display: 'inline-block',
              maxWidth: 900,
              padding: '15px 26px',
              borderRadius: 15,
              background: 'rgba(6,14,11,.87)',
              border: '1px solid rgba(255,255,255,.13)',
              fontFamily: FONT.body,
              fontWeight: 700,
              fontSize: 43,
              lineHeight: 1.24,
              color: C.ink,
              letterSpacing: -0.5,
            }}
          >
            {caption.text}
          </span>
        </div>
      ) : null}

      <Vignette strength={0.3} />
      <Grain opacity={0.045} />

      {/* Footer on every frame. It carries the provenance stamp and the
          not-advice line, and says the instrument is an ETF. */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 0,
          padding: '18px 40px 30px',
          background: 'linear-gradient(to top, rgba(4,10,8,.94), rgba(4,10,8,0))',
          textAlign: 'center',
          fontFamily: FONT.mono,
          fontSize: 21,
          color: '#9FB8AC',
          letterSpacing: 0.6,
          lineHeight: 1.35,
        }}
      >
        {p.footer}
      </div>

      {/* ------------------------------------------------------------ sound.
          Synthesised in scripts/audio/make_tick.py — Remotion's bundled ffmpeg
          has no highpass/lowpass, so an unfiltered tick is a beep or a hiss.
          One tick per countdown second, and one blip per REVEAL candle only:
          70 setup bars in eight seconds would be nine hits a second.
          There is NO coin here, and that is not an omission — the coin is the
          target-hit sound and this trade never reached its target. What there
          IS is an impact on the take: a swept-down sine for the body, a
          band-limited noise crack for the leading edge, and a short mid ring
          so it reads cartoon rather than as a gunshot. */}
      {Array.from({length: COUNT_N}, (_, i) => (
        <Sequence key={`tick${i}`} from={B.quiz + i * COUNT_PER} durationInFrames={COUNT_PER}>
          <Audio src={staticFile(i % 2 === 0 ? 'audio/tick.wav' : 'audio/tock.wav')} volume={0.6} />
        </Sequence>
      ))}
      {/* THE HIT. On SHOCK_AT with everything else — the drawing, the smear,
          the flash, the burst, the camera kick. A take whose sound lands even
          two frames late reads as dubbed. */}
      <Sequence from={SHOCK_AT} durationInFrames={20}>
        <Audio src={staticFile('audio/impact.wav')} volume={0.85} />
      </Sequence>
      {Array.from({length: revealCount}, (_, r) => (
        <Sequence key={`cndl${r}`} from={appearFrames[ns + r]} durationInFrames={14}>
          <Audio
            src={staticFile(p.bars[ns + r].c >= p.bars[ns + r].o ? 'audio/candle_up.wav' : 'audio/candle_down.wav')}
            volume={0.5}
          />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
