// HormuzReel.tsx — "What moves the price of oil", told on one chart.
//
// The whole reel is a single 125-bar Brent chart that never moves. What moves
// is the camera, and what changes is how much of the tape has printed. That is
// the entire trick: a cut here is a camera arriving somewhere, not a new slide.
//
// Every number on screen comes from scripts/oil_reel/ — the composition does no
// arithmetic on prices, so the caption and the candle cannot disagree
// (CLAUDE.md 10.1). The trade shows entry, stop, target and R together or not
// at all (10.5), and it ends on the base rate rather than on the winner (10.6).
import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, random, staticFile, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {FONT} from '../slides/theme';
import {EASE} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';
import {PT} from '../components/PatternCard';
import {OilChart, oilScales, type OBar} from '../components/OilChart';
import {CameraRig, cameraAt, type Shot} from '../motion/CameraRig';
import fx from '../fixtures/oil_reel/hormuz.json';

export const hormuzSchema = z.object({});
export type HormuzProps = z.infer<typeof hormuzSchema>;

export const HORMUZ_FRAMES = 2220; // 74s at 30fps

const W = 1080;
const H = 1920;
const CHART_W = 2100;
// Tall on purpose. The price axis spans $65-$126 over six months; at a square
// aspect, quiet February is a 6-dollar smear four pixels high and the opening
// seven seconds have nothing to look at. Stretching the axis gives the calm
// somewhere to live without touching the geometry the camera flies over.
const CHART_H = 2000;

const BARS = fx.bars as OBar[];
const S = oilScales(BARS, CHART_W, CHART_H);
const GAP = fx.shock.firstSessionIndex;
const P = fx.pattern;
const T = fx.trade;
const BR = fx.baseRate;
const AF = fx.aftermath;
// The confirmation act: the same pattern after a DIFFERENT crisis (July), and
// the quiet-vs-crisis split. Both computed by scripts/oil_reel/, never here.
const J = fx.july as NonNullable<typeof fx.july>;
const SP = fx.split;

/** A camera target expressed the way the story thinks: "bar 22, at $85". */
const at = (i: number, price: number) => ({x: S.x(i) / CHART_W, y: S.y(price) / CHART_H});

// ------------------------------------------------------------------ beats
// Six acts. The camera arrives somewhere slightly BEFORE the bar it is there
// to watch prints — anticipation is what separates a camera operator who knows
// what is coming from a zoom that reacts late.
const SHOTS: Shot[] = [
  {at: 0, zoom: 4.65, ...at(3.5, 68.6)}, // start CLOSER — the 7s drift to the next mark is visible motion from frame 1
  {at: 210, zoom: 3.8, ...at(GAP - 1, 71.5), ease: EASE.cruise}, // drift right over quiet Feb
  {at: 246, zoom: 3.8, ...at(GAP - 1, 71.5)}, // settle on the last calm bar
  // Wide enough to hold BOTH Friday's bar and Monday's. A gap is the empty
  // space between two bars; framed on the second bar alone there is no gap on
  // screen at all, just a big green candle while the caption claims a gap.
  {at: 330, zoom: 2.2, ...at(GAP - 0.4, 75.5), ease: EASE.cruise},
  {at: 580, zoom: 2.2, ...at(GAP - 0.4, 75.5)}, // HOLD: mark, gap, and caption all live here
  {at: 640, zoom: 4.0, ...at(GAP, 80.3), ease: EASE.cruise}, // now into the upper wick — the trap
  {at: 700, zoom: 4.0, ...at(GAP, 80.3)},
  // THE LOGIC ACT: step back from the trap and think. The camera easing out
  // to a mid-wide while the voice explains is the visual grammar of
  // reflection — a lecture beat needs a contemplative frame, not a push.
  {at: 790, zoom: 2.7, ...at(GAP + 1, 78.5), ease: EASE.cruise},
  {at: 1010, zoom: 2.7, ...at(GAP + 1, 78.5)}, // hold through 'crisis picks direction'
  {at: 1020, zoom: 3.9, ...at(P.mother + 0.5, 81.5), ease: EASE.cruise},
  {at: 1100, zoom: 4.9, ...at(P.inside, 82.4), ease: EASE.cruise}, // tight on the coil
  {at: 1160, zoom: 4.9, ...at(P.inside, 82.4)},
  {at: 1220, zoom: 3.5, ...at(P.trigger, 86.5), ease: EASE.cruise}, // out far enough for the frame
  {at: 1300, zoom: 3.5, ...at(P.trigger, 88)}, // HOLD on the plan, before the outcome
  {at: 1360, zoom: 2.0, ...at(P.trigger + 2, 98), ease: EASE.cruise}, // pull-out REVEALS the target
  {at: 1410, zoom: 2.0, ...at(P.trigger + 2, 98)},
  // the camera opens as the tape races — the six-month round trip lands in one move
  {at: 1510, zoom: 0.515, x: 0.5, y: 0.5, ease: EASE.cruise},
  {at: 1735, zoom: 0.515, x: 0.5, y: 0.5}, // hold wide: 17 fires, 24%
  // THE CONFIRMATION ACT: fly BACK across the chart to July — same pattern,
  // different crisis. The return journey itself is the argument.
  {at: 1810, zoom: 2.4, ...at(J.trigger, 90), ease: EASE.cruise},
  {at: 1960, zoom: 2.4, ...at(J.trigger, 90)},
  {at: 2030, zoom: 0.515, x: 0.5, y: 0.5, ease: EASE.cruise}, // wide for the honest split
  {at: 2219, zoom: 0.535, x: 0.5, y: 0.5},
];

/** How much tape exists, per frame. Same keyframe shape as the camera. */
const PRINT: {at: number; i: number}[] = [
  {at: 0, i: 9}, // frame 0 is the thumbnail: it needs a chart, not an empty panel
  {at: 210, i: GAP - 1}, // February prints out slowly under the opening lines
  {at: 365, i: GAP - 1},
  {at: 415, i: GAP}, // the gap bar
  {at: 670, i: GAP},
  // the tape WAITS through the logic act — nothing new prints while the
  // method is being explained, so the explanation can't peek at the future
  {at: 1020, i: GAP},
  {at: 1030, i: P.mother},
  {at: 1090, i: P.inside},
  {at: 1170, i: P.trigger},
  // HOLD the tape here. The plan has to exist on screen BEFORE the outcome
  // does, or the reel is just showing a chart that already went up.
  {at: 1305, i: P.trigger},
  {at: 1395, i: T.tpBar as number}, // two sessions to the target
  // HOLD again. "Target in two sessions" has to be TRUE on screen while it is
  // being claimed — fifteen extra bars already printed makes it a lie.
  {at: 1468, i: T.tpBar as number},
  {at: 1554, i: BARS.length - 1}, // then the rest of the year, in a rush
];

const printedAt = (f: number) => {
  if (f <= PRINT[0].at) return PRINT[0].i;
  const last = PRINT[PRINT.length - 1];
  if (f >= last.at) return last.i;
  let k = 0;
  for (let n = 0; n < PRINT.length - 1; n++) if (f >= PRINT[n].at) k = n;
  const a = PRINT[k];
  const b = PRINT[k + 1];
  return a.i + (b.i - a.i) * ((f - a.at) / Math.max(1, b.at - a.at));
};

// ---------------------------------------------------------------- captions
type Cap = {
  from: number;
  to: number;
  text: string;
  sub?: string;
  big?: boolean;
  /** Fully composited from its first frame — no typewriter. The opening
   * caption must survive as a static share-image (frame 0 IS the thumbnail),
   * so it cannot spend its first second half-typed. */
  instant?: boolean;
  /** Keyboard SFX under this caption. Only the number-dense lines get keys —
   * research: clicks under every line fight the narration's own rhythm. */
  keys?: boolean;
};

/** Numbers and day-words pop in accent green, connective words stay ink.
 * One emphasis system, applied by pattern — never by eye, so a new caption
 * can't forget it. */
const RICH = /(\$?\d[\d,.]*%?|SATURDAY|MONDAY|FRIDAY)/g;
// split() uses the global regex; the membership test uses an ANCHORED copy —
// testing with a /g/ regex is stateful (lastIndex advances) and alternates
// true/false on identical inputs.
const RICH_TEST = /^(\$?\d[\d,.]*%?|SATURDAY|MONDAY|FRIDAY)$/;
const renderRich = (s: string, base: string): React.ReactNode[] =>
  s.split(RICH).map((part, i) =>
    RICH_TEST.test(part) ? (
      <span key={i} style={{color: PT.ice}}>
        {part}
      </span>
    ) : (
      <span key={i} style={{color: base}}>
        {part}
      </span>
    )
  );

const CAPS: Cap[] = [
  // instant: frame 0 is the thumbnail — hook fully composited, no ramp
  {from: 0, to: 130, text: '20.9 MILLION BARRELS A DAY', big: true, instant: true},
  {from: 142, to: 232, text: 'A FIFTH OF THE WORLD’S OIL', sub: 'THROUGH ONE STRAIT', keys: true},
  {from: 246, to: 350, text: 'FRIDAY 27 FEB', sub: `BRENT CLOSED $${fx.shock.prevClose}`, keys: true},
  {from: 362, to: 452, text: 'SATURDAY. MARKETS SHUT.'},
  {
    from: 464,
    to: 586,
    text: `MONDAY GAPPED $${Math.abs(fx.shock.gapPts)}`,
    sub: `+${fx.shock.gapPct}% BEFORE A SINGLE TRADE`,
    keys: true,
  },
  {
    from: 598,
    to: 690,
    text: `IT SPIKED TO $${fx.shock.spikeHigh}`,
    sub: `THEN CLOSED $${fx.shock.spikeGiveback} LOWER`,
    keys: true,
  },
  // ---- the logic act: WHY wait — the method in two sentences ----------
  {from: 775, to: 852, text: 'NO CHASING. NO PREDICTING.'},
  {
    from: 864,
    to: 948,
    text: 'THE CRISIS PICKS THE DIRECTION',
    sub: 'A FIFTH OF WORLD SUPPLY HAS A REASON TO MOVE',
  },
  {
    from: 956,
    to: 1100,
    text: 'THE PATTERN PICKS THE MOMENT',
    sub: 'AND THE PRICE WHERE YOU’RE WRONG',
  },
  {from: 1122, to: 1216, text: 'INSIDE BAR', sub: 'THE WHOLE DAY FITS INSIDE THE ONE BEFORE'},
  {
    from: 1228,
    to: 1336,
    text: 'A CLOSE ABOVE THE RANGE',
    sub: `ENTRY $${T.entry} · STOP $${T.stop} · TARGET $${T.target}`,
    keys: true,
  },
  {from: 1360, to: 1462, text: 'TARGET IN TWO SESSIONS', sub: `2R · ${T.tpDate}`},
  {
    from: 1474,
    to: 1560,
    text: `$${AF.peakHigh} IN APRIL. $${AF.troughLow} BY JULY.`,
    sub: 'THE WAR PREMIUM DID NOT LAST',
    keys: true,
  },
  {
    from: 1572,
    to: 1740,
    text: `THAT SETUP FIRED ${BR.n} TIMES`,
    sub: `IT REACHED TARGET ${BR.wins} TIMES`,
    big: true,
    keys: true,
  },
  // ---- the confirmation act: the OTHER crisis, same pattern -------------
  {
    from: 1755,
    to: 1995,
    text: 'IT HAPPENED AGAIN',
    sub: `${J.shockDate.slice(5)}: +${J.shockPct}% SHOCK · SAME PATTERN · TARGET ${J.tpDate}`,
    keys: true,
  },
  // ---- the close: crisis-conditioned record + the WHY. Owner's call:
  // the final section is chart-and-voice only, so this caption carries the
  // numbers (still fixture-owned) and the mechanism in one card.
  {
    from: 2010,
    to: 2219,
    text: `AFTER A SHOCK: ${SP.crisis.wins} OF ${SP.crisis.n}`,
    sub: 'THE MARKET LEANS ONE WAY · SMALL SAMPLE',
    big: true,
    keys: true,
  },
];

/** One typed line. The cursor blink is quantised to 8-frame steps — a smoothly
 * fading cursor is the tell that nobody looked at a real terminal. */
const Caption: React.FC<{cap: Cap; frame: number}> = ({cap, frame}) => {
  if (frame < cap.from || frame > cap.to) return null;
  // 42cps: a caption that takes 1.5s to finish typing is stealing attention
  // from the voice that is already past it. instant-mode captions skip the
  // typewriter entirely (the hook must be complete on frame 0).
  const cps = 42;
  const shown = cap.instant
    ? cap.text.length
    : Math.min(cap.text.length, Math.floor(((frame - cap.from) / 30) * cps));
  const typing = shown < cap.text.length || (cap.instant === true && frame < cap.from + 60);
  const cursorOn = Math.floor((frame - cap.from) / 8) % 2 === 0;
  const doneAt = cap.instant ? cap.from : cap.from + (cap.text.length / cps) * 30;
  const subIn = interpolate(frame, [doneAt + 4, doneAt + 16], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const out = interpolate(frame, [cap.to - 9, cap.to], [1, 0], {
    easing: EASE.exit,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const rise = cap.instant
    ? 0
    : interpolate(frame, [cap.from, cap.from + 10], [14, 0], {
        easing: EASE.enter,
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });

  return (
    <div
      style={{
        position: 'absolute',
        top: 196,
        left: 56,
        right: 56,
        textAlign: 'center',
        opacity: out,
        transform: `translateY(${rise}px)`,
      }}
    >
      <div
        style={{
          fontFamily: FONT.mono,
          fontSize: cap.big ? 62 : 50,
          fontWeight: 800,
          color: '#EAFFF4',
          lineHeight: 1.12,
          letterSpacing: -0.5,
          textShadow: '0 3px 26px rgba(0,0,0,0.92)',
        }}
      >
        {renderRich(cap.text.slice(0, shown), '#EAFFF4')}
        {/* zero-width so the cursor can never change the line-wrap — it cost
         * frame 0 a widowed word once */}
        {typing && cursorOn ? (
          <span style={{display: 'inline-block', width: 0, overflow: 'visible', color: PT.up}}>
            &#9612;
          </span>
        ) : null}
      </div>
      {cap.sub ? (
        <div
          style={{
            marginTop: 14,
            opacity: subIn,
            transform: `translateY(${(1 - subIn) * 8}px)`,
            fontFamily: FONT.mono,
            fontSize: 27,
            fontWeight: 700,
            color: PT.ice,
            letterSpacing: 1.4,
            textShadow: '0 2px 18px rgba(0,0,0,0.9)',
          }}
        >
          {cap.sub}
        </div>
      ) : null}
    </div>
  );
};

// ------------------------------------------------------------------ sound
/** Keyswitches — only under the number-dense captions (keys: true), a short
 * burst per phrase rather than a click per character. Clicks under every line
 * fight the narration's own rhythm; under the number lines they read as data
 * being entered, which is the point of the terminal aesthetic. */
const keystrokes = () => {
  const out: {f: number; src: string}[] = [];
  const files = ['key_click.wav', 'key_click2.wav', 'key_click3.wav'];
  CAPS.forEach((cap, ci) => {
    if (!cap.keys) return;
    const n = Math.min(5, Math.ceil(cap.text.length / 6));
    for (let i = 0; i < n; i++) {
      const f = Math.round(cap.from + i * 4);
      if (f < HORMUZ_FRAMES) out.push({f, src: files[(ci + i) % 3]});
    }
  });
  return out;
};
const KEYS = keystrokes();

/** Camera moves that deserve air, taken from the shot list rather than typed
 * out again — a whoosh that drifts off its move is worse than no whoosh. */
const AIR = SHOTS.slice(1)
  .map((s, i) => ({s, prev: SHOTS[i]}))
  .filter(({s, prev}) => Math.abs(s.zoom - prev.zoom) > 0.35)
  .map(({s, prev}) => ({
    f: Math.max(0, prev.at - 4),
    src: s.zoom > prev.zoom ? 'whoosh_in.wav' : 'whoosh_out.wav',
  }));

const CANDLE_HITS = [
  {f: 415, up: true}, // the gap bar
  {f: 1030, up: true}, // mother
  {f: 1090, up: false}, // the coil
  {f: 1170, up: true}, // trigger
];

const SHOCK_F = 366; // the mark lands, the desk kicks, the sting hits — one frame
const COIN_F = 1395; // the bar that reaches the target
const JULY_COIN_F = 1965; // 'target again' — the July confirmation pays

export const HormuzReel: React.FC<HormuzProps> = () => {
  const frame = useCurrentFrame();
  const cam = cameraAt(frame, SHOTS);
  const printed = printedAt(frame);

  // The shock knocks the whole frame, captions included — a camera bolted to a
  // desk when something lands on it. Decays inside 18 frames; a shake that
  // outlives its cause reads as a rendering fault.
  const shakeT = (frame - SHOCK_F) / 18;
  const shake =
    frame >= SHOCK_F && shakeT < 1
      ? (() => {
          const amp = (1 - shakeT) ** 2 * 17;
          return {
            x: (random(`sx${frame}`) - 0.5) * 2 * amp,
            y: (random(`sy${frame}`) - 0.5) * 2 * amp,
          };
        })()
      : {x: 0, y: 0};

  const markIn = interpolate(frame, [SHOCK_F, SHOCK_F + 10], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const motherIn = interpolate(frame, [1040, 1056], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const insideIn = interpolate(frame, [1102, 1118], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const levelIn = interpolate(frame, [1150, 1170], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  // All four legs of the trade land together — a target with no stop shows the
  // upside and hides what being wrong cost (CLAUDE.md 10.5). The target line is
  // off the top of frame at this zoom; the pull-out at 1030 is what reveals it.
  const tradeIn = interpolate(frame, [1240, 1264], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Annotations are scaffolding for the beat that needs them. Left up, the
  // shock mark and the pattern boxes clutter the final wide shot with a
  // diagram of something the reel finished explaining twenty seconds ago.
  const annoOut = interpolate(frame, [1450, 1516], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  // The 28 FEB rule has done its work once the pattern is being drawn. Left at
  // full strength it runs a dashed red line straight through the caption.
  const markFade = interpolate(frame, [1000, 1060], [1, 0.28], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // The March trade frame leaves before July's arrives — two overlapping
  // trade frames at once asserts nothing except clutter.
  const marchOut = interpolate(frame, [1720, 1760], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const marchOp = tradeIn * marchOut;
  const julyOp =
    interpolate(frame, [1760, 1790], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) *
    interpolate(frame, [1990, 2030], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  const levels = [
    {
      price: P.motherHigh,
      label: `$${P.motherHigh}`,
      color: PT.level,
      opacity: levelIn * (1 - tradeIn) * annoOut,
    },
    ...(marchOp > 0
      ? [
          {price: T.entry, label: 'ENTRY', color: PT.ink, opacity: marchOp, dash: '0'},
          {price: T.stop, label: 'STOP', color: PT.down, opacity: marchOp},
          {price: T.target, label: 'TARGET', color: PT.up, opacity: marchOp},
        ]
      : []),
    ...(julyOp > 0
      ? [
          {price: J.entry, label: 'ENTRY', color: PT.ink, opacity: julyOp, dash: '0'},
          {price: J.stop, label: 'STOP', color: PT.down, opacity: julyOp},
          {price: J.target, label: 'TARGET', color: PT.up, opacity: julyOp},
        ]
      : []),
  ];

  // The bands stop where the trade stopped. Running them to the right edge
  // paints a hundred bars the trade was never in as if it held them.
  const bandEnd = Math.min(BARS.length - 1, (T.tpBar as number) + 2);
  const jBandEnd = Math.min(BARS.length - 1, (J.tpBar as number) + 1);
  const bands = [
    ...(marchOp > 0
      ? [
          {from: T.entry, to: T.stop, i0: P.trigger, i1: bandEnd, color: PT.down, opacity: 0.17 * marchOp},
          {from: T.entry, to: T.target, i0: P.trigger, i1: bandEnd, color: PT.up, opacity: 0.14 * marchOp},
        ]
      : []),
    ...(julyOp > 0
      ? [
          {from: J.entry, to: J.stop, i0: J.trigger, i1: jBandEnd, color: PT.down, opacity: 0.17 * julyOp},
          {from: J.entry, to: J.target, i0: J.trigger, i1: jBandEnd, color: PT.up, opacity: 0.14 * julyOp},
        ]
      : []),
  ];

  // Chrome (header + footer) leaves for the close — the last card is chart,
  // caption and voice, nothing else.
  const chromeOut = interpolate(frame, [1712, 1748], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  /** Project a price onto the screen through the same camera the chart uses,
   * so a label pinned here sits exactly on its dashed line at any zoom. */
  const screenY = (price: number) =>
    H / 2 - cam.y * CHART_H * cam.zoom + S.y(price) * cam.zoom;

  return (
    <AbsoluteFill style={{backgroundColor: PT.bg}}>
      <div style={{position: 'absolute', inset: 0, transform: `translate(${shake.x}px, ${shake.y}px)`}}>
        <CameraRig
          frame={frame}
          shots={SHOTS}
          childWidth={CHART_W}
          childHeight={CHART_H}
          viewportWidth={W}
          viewportHeight={H}
        >
          <OilChart
            bars={BARS}
            width={CHART_W}
            height={CHART_H}
            printedThrough={printed}
            zoom={cam.zoom}
            levels={levels}
            marks={[
              ...(markIn * annoOut * markFade > 0
                ? [{i: GAP, label: '28 FEB', color: PT.down, opacity: markIn * annoOut * markFade}]
                : []),
              ...(julyOp > 0
                ? [{i: J.shockIdx, label: '13 JUL', color: PT.down, opacity: julyOp}]
                : []),
            ]}
            boxes={[
              ...(motherIn * annoOut > 0
                ? [{i: P.mother, span: 2, color: PT.trendline, label: 'RANGE', opacity: motherIn * annoOut}]
                : []),
              ...(insideIn * annoOut > 0
                ? [{i: P.inside, color: PT.level, label: 'INSIDE', opacity: insideIn * annoOut}]
                : []),
              // July draws the SAME diagram — the visual rhyme is the proof
              ...(julyOp > 0
                ? [
                    {i: J.mother, span: 2, color: PT.trendline, label: 'RANGE', opacity: julyOp},
                    {i: J.inside, color: PT.level, label: 'INSIDE', opacity: julyOp},
                  ]
                : []),
            ]}
            bands={bands}
          />
        </CameraRig>

        {/* Level labels, pinned to the right edge of the SCREEN rather than to
         * the chart. They ride the camera vertically and never scale, so at a
         * 3x push they are the same size they are at the wide. */}
        {levels
          .map((lv) => ({lv, y: screenY(lv.price)}))
          .filter(({lv, y}) => (lv.opacity ?? 1) > 0.02 && y > 250 && y < 1720)
          .map(({lv, y}, i) => (
            <div
              key={`ll${i}`}
              style={{
                position: 'absolute',
                right: 22,
                top: y - 17,
                height: 34,
                padding: '0 13px',
                display: 'flex',
                alignItems: 'center',
                borderRadius: 5,
                background: PT.bg,
                border: `1.6px solid ${lv.color}`,
                opacity: lv.opacity ?? 1,
                fontFamily: FONT.mono,
                fontSize: 21,
                fontWeight: 800,
                color: lv.color,
                letterSpacing: 1,
                boxShadow: '0 2px 16px rgba(0,0,0,0.8)',
              }}
            >
              {lv.label}
            </div>
          ))}

        {/* captions ride above the rig, so a 3x push never scales the type */}
        {CAPS.map((c, i) => (
          <Caption key={i} cap={c} frame={frame} />
        ))}

        {/* The 24%% overlay is gone by owner's call — the FIRED-17 caption
         * carries the honest count, and from that beat on the lower screen is
         * chart only. */}
      </div>

      <Vignette />
      <Grain opacity={0.045} />

      {/* header — on for the whole story, steps off for the close */}
      <div
        style={{
          opacity: chromeOut,
          position: 'absolute',
          top: 62,
          left: 56,
          right: 56,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          fontFamily: FONT.mono,
        }}
      >
        <div style={{fontSize: 30, fontWeight: 900, color: PT.ink, letterSpacing: 1.2}}>
          BRENT CRUDE
        </div>
        <div style={{fontSize: 22, fontWeight: 700, color: PT.steel, letterSpacing: 1.6}}>
          {BARS[0].d} &rarr; {BARS[BARS.length - 1].d}
        </div>
      </div>

      {/* footer — real data, named source, snapshot time (CLAUDE.md 10.6);
          burned in for 67 of 74 seconds, fades for the clean close */}
      <div
        style={{
          opacity: chromeOut,
          position: 'absolute',
          bottom: 42,
          left: 56,
          right: 56,
          textAlign: 'center',
          fontFamily: FONT.mono,
          fontSize: 15,
          lineHeight: 1.55,
          color: PT.steel,
          letterSpacing: 0.4,
        }}
      >
        REAL DAILY BARS &middot; BRENT FRONT-MONTH (BZ=F) &middot; YAHOO FINANCE &middot; SNAPSHOT{' '}
        {String(fx.provenance.bars_retrieved_at).slice(0, 10)}
        <br />
        TRANSIT VOLUME: U.S. EIA WORLD OIL TRANSIT CHOKEPOINTS &middot; NOT INVESTMENT ADVICE
      </div>

      {/* ---------------------------------------------------------- audio
       * Every cue is derived from the same constant the picture uses — the
       * caption list, the shot list, the print keyframes — so a retimed beat
       * moves its sound with it. A cue typed out by hand drifts the first
       * time a number changes, and two frames of drift reads as dubbed. */}

      {/* keyswitches under the typed lines */}
      {KEYS.map((k, i) => (
        <Sequence key={`k${i}`} from={k.f} durationInFrames={4}>
          <Audio src={staticFile(`audio/${k.src}`)} volume={0.3} />
        </Sequence>
      ))}

      {/* air on every camera move that actually changes distance */}
      {AIR.map((a, i) => (
        <Sequence key={`a${i}`} from={a.f} durationInFrames={26}>
          <Audio src={staticFile(`audio/${a.src}`)} volume={0.3} />
        </Sequence>
      ))}

      {/* the shock: sting on the same frame the mark lands and the desk kicks */}
      <Sequence from={SHOCK_F} durationInFrames={54}>
        <Audio src={staticFile('audio/crisis.wav')} volume={0.8} />
      </Sequence>
      <Sequence from={SHOCK_F} durationInFrames={14}>
        <Audio src={staticFile('audio/impact.wav')} volume={0.72} />
      </Sequence>

      {/* one blip per story candle — not per bar. The last 100 bars print in
       * four seconds at the end; scoring those is twenty-five hits a second. */}
      {CANDLE_HITS.map((c, i) => (
        <Sequence key={`c${i}`} from={c.f} durationInFrames={8}>
          <Audio src={staticFile(c.up ? 'audio/candle_up.wav' : 'audio/candle_down.wav')} volume={0.5} />
        </Sequence>
      ))}

      {/* the target printing */}
      <Sequence from={COIN_F} durationInFrames={40}>
        <Audio src={staticFile('audio/coin.wav')} volume={0.62} />
      </Sequence>

      {/* ...and the July confirmation reaching ITS target */}
      <Sequence from={JULY_COIN_F} durationInFrames={40}>
        <Audio src={staticFile('audio/coin.wav')} volume={0.5} />
      </Sequence>
    </AbsoluteFill>
  );
};
