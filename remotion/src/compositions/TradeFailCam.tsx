// TradeFailCam.tsx — the 40s fail reel, third format: SINGLE SCREEN.
//
// No room, no monitor, no camera moves. The frame IS the trading terminal —
// the same green-on-near-black window the channel's quiz reels already ship —
// and the character is an upper-body corner cam at the bottom right, the way a
// streamer sits over their own chart. The owner's spec, verbatim: one screen
// with the trading window open, timer like the reels in prod, character upper
// body down-right, smaller but still big.
//
// What replaces the camera as the source of motion, since there is nothing to
// cut between:
//   * the chart itself — structure draws with a live pen head, the y-axis
//     moves through its three honest views, the stop firing is a terminal
//     alarm (red wash + pulsing stop line, inside the panel);
//   * the character — pose cuts with the full toon grammar (anticipation,
//     squash, smear, boil), PLUS a vertical channel the room version never
//     had: he rises into frame, sinks with dread through the wait, shoots up
//     on the break, slumps through the facepalm. The bottom edge crops him,
//     so height IS emotion.
//   * the frame — one 2-frame punch + impact kick on the break, and that is
//     the only time the frame itself moves. A single screen that shakes twice
//     is a screen with a fault.
//
// Sweat is ONE drop, gliding slowly down his temple on a loop (ToonFX
// SweatSlide). The three-bead version read as a gag; one slow drop reads as
// dread, which is the emotion the wait actually carries.
//
// Data discipline unchanged from TradeFailReel: every price, level, pivot,
// trendline and outcome comes from the scanner's fixture; this file owns
// timing, staging and prose only. IBIT is named as an ETF on every frame.
// No P&L, no returns; the loss is stated in R.
import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {FONT} from '../slides/theme';
import {EASE, fadeOf} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';
import {StructureChart} from '../components/StructureChart';
import {PoseCut, poseHead, type Cut} from '../characters/poseCut';
import {FlashCut, ShockFlicks, SweatSlide, kick} from '../motion/ToonFX';
import {tradeFailReelSchema} from './TradeFailReel';
import staging from '../fixtures/btc_reel/cam_staging.json';

/** Same data contract as TradeFailReel minus the room staging — the cam
 * format stages the character itself. Zod strips the extra fields, so the
 * same fixture feeds both compositions. */
export const tradeFailCamSchema = tradeFailReelSchema.omit({
  charCenterX: true,
  charFeetY: true,
  charHeight: true,
});
export type TradeFailCamProps = z.infer<typeof tradeFailCamSchema>;

export const TRADE_FAIL_CAM_FRAMES = 1200;

// ------------------------------------------------------------ the beat sheet
// Same eight beats as the room version — the story did not change, the staging
// did. Quiz stays 4.0s per the owner's override.
const B = {quiz: 660, wait: 780, end: 1200};
const COUNT_PER = 30;
const COUNT_N = 4;

// Chart layer draw-ins (chart time == frame time; the panel is never remapped).
const SUPPORT_IN = 150;
const RES_IN = 198;
const TREND_IN = 246;
const PATTERN_IN = 424;
const TRADE_IN = 516;
const DECISION_IN = 466;
const OUTCOME_IN = 966;

const HAMMER_IN = 366;
const HAMMER_FORM = 54;
const ENTRYBAR_IN = 432;
const BREAK_IN = 968;
const BREAK_FORM = 46;

/** The break, visually: by ~32 frames into the breaking bar's print its low is
 * through the stop. Alarm, flash, punch, shock pose, flicks and the impact
 * sound ALL key off this one number so nothing can drift apart. */
const SHOCK_AT = 1000;

// ------------------------------------------------------------------ staging
// EVERYTHING spatial comes from cam_staging.json — the same file
// scripts/btc_reel/check_overlaps.py verifies against the pose drawings' real
// ink profiles. That is what makes "the character never overlaps any text or
// display object" a checked property instead of a hope: staging changes land
// in the JSON, the checker runs, THEN the render happens. Do not hand-edit
// coordinates here.
const PANEL = staging.panel;
const PANEL_UI = staging.ui;
const CAM = staging.cam;
const LANES = staging.lanes;

const EASE_BY_NAME: Record<string, (t: number) => number> = {
  settleBack: EASE.settleBack,
  exit: EASE.exit,
  cruise: EASE.cruise,
  enter: EASE.enter,
};

// The cut sheet, from staging. Deliberately CALMER than the last iteration —
// 25 cuts, not 36. The owner's note: too many actions reads as hyperactivity.
// The long holds are where the sweat drop, the sink and the small gaze tilts
// do the emotional work; the tight cutting is reserved for the one place a
// take earns it (four drawings across the reaction). The negative tilts on
// the watching poses lean him back so his face rises toward the panel — he is
// LOOKING AT THE SCREEN, which is the whole premise of a corner cam.
const CUTS: Cut[] = staging.cuts as Cut[];

const CAM_DY_KEYS = staging.camDy as [number, number, string | null][];
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

// The vertical channel — the format's own expressive axis. Because the bottom
// edge crops him, moving his anchor down IS the emotion: he pops up to open,
// sinks through the wait, SHOOTS up on the break, slumps into the facepalm.
// Values live in staging so the overlap checker sees the same envelope.
const CAM_DY: Key[] = CAM_DY_KEYS.map(([f, v, e]) => ({
  f,
  v,
  ease: e ? EASE_BY_NAME[e] : undefined,
}));

type Caption = {from: number; to: number; text: string};

export const TradeFailCam: React.FC<TradeFailCamProps> = (p) => {
  const frame = useCurrentFrame();
  const ns = p.setupBars;
  const revealCount = p.bars.length - ns;

  // ------------------------------------------------------------ bar schedule
  // Identical rhythm to the room version: history fast, the hammer and the
  // break long, the ambiguous bars stretched, the collapse quick.
  const {appearFrames, formFrames} = React.useMemo(() => {
    const a: number[] = [];
    const f: number[] = [];
    const histN = p.trigger.bar;
    for (let i = 0; i < p.bars.length; i++) {
      if (i < histN) {
        a.push(40 + Math.round((i * (344 - 40)) / Math.max(1, histN - 1)));
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

  // --------------------------------------------------------------- the punch
  // The ONLY frame motion in the piece: a 2-frame scale punch + a decaying
  // impact kick when the stop fires. On a single fixed screen, one hit lands;
  // a second would read as a rendering fault.
  const kk = kick(frame - SHOCK_AT, 15, 18);
  const punch =
    frame >= SHOCK_AT && frame < SHOCK_AT + 6 ? 1 + 0.022 * (1 - (frame - SHOCK_AT) / 6) : 1;

  // ------------------------------------------------------------ the character
  const camDy = track(frame, CAM_DY);
  const footY = CAM.footY + camDy;
  const head = poseHead({
    frame,
    height: CAM.ink,
    footX: CAM.footX,
    footY,
    cuts: CUTS,
    end: B.end,
    motion: 'toon',
    facing: 'left',
  }) ?? {x: CAM.footX, y: footY - CAM.ink * 0.85, w: CAM.ink * 0.3};
  // The measured head band catches the shoulder line on the hunched poses and
  // inflates the width (crouch reports 0.675 of the box). Clamp it for the
  // FX, or the drop drifts off the skull and the flicks off the frame.
  const hw = Math.min(head.w, 240);

  // ------------------------------------------------------------- the quiz
  const inQuiz = frame >= B.quiz && frame < B.wait;
  const secsLeft = Math.max(0, COUNT_N - Math.floor((frame - B.quiz) / COUNT_PER));
  const quizP =
    interpolate(frame, [B.quiz, B.quiz + 14], [0, 1], {
      easing: EASE.enter,
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }) *
    interpolate(frame, [B.wait - 10, B.wait], [1, 0], {
      easing: EASE.exit,
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  const ringP = inQuiz
    ? interpolate(frame, [B.quiz, B.wait], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})
    : 0;
  // Each second lands with a pop on the digit — the timer TICKS instead of
  // draining. Same neutral ring; the answer colour still appears nowhere here.
  const tickFrame = B.quiz + Math.floor(Math.max(0, frame - B.quiz) / COUNT_PER) * COUNT_PER;
  const digitPop = inQuiz ? 1 + 0.16 * Math.exp(-(frame - tickFrame) / 4.5) : 1;

  const answerP =
    interpolate(frame, [SHOCK_AT + 6, SHOCK_AT + 20], [0, 1], {
      easing: EASE.enter,
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }) *
    interpolate(frame, [1092, 1108], [1, 0], {
      easing: EASE.exit,
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  const rzP = interpolate(frame, [1112, 1132], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const barsIn = Math.min(p.slAt, Math.max(0, Math.floor((frame - 800) / 40) + 1));

  // Caption WINDOWS live in staging (the overlap checker guards the caption
  // lane during exactly these frames); the texts live here. The counter
  // reaches 4 BARS at frame 920 — the caption must never say "four bars"
  // while the HUD above it says one.
  const captionTexts = [
    `${p.symbol}, daily. Everything here is real.`,
    `Support ${p.support.price.toFixed(2)}, held ${p.support.touches}×. Trendline rising into it.`,
    `Then this: ${p.trigger.name.toLowerCase()}.`,
    `Long ${p.entry.toFixed(2)}. Stop under the wick. Target 2R.`,
    'It stalls at the entry.',
    'Four bars. It goes nowhere.',
    `Stopped. It kept going — ${Math.abs(p.drop).toFixed(0)}% lower.`,
  ];
  const captions: Caption[] = (staging.captionWindows as [number, number][]).map(([from, to], i) => ({
    from,
    to,
    text: captionTexts[i] ?? '',
  }));
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

  const R = 92;
  const CIRC = 2 * Math.PI * R;

  return (
    <AbsoluteFill style={{backgroundColor: '#02070A'}}>
      {/* faint ruled grid on the frame itself, so the terminal extends past
          the panel instead of the panel floating on a void */}
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        {Array.from({length: 11}, (_, i) => (
          <line key={`v${i}`} x1={i * 108} x2={i * 108} y1={0} y2={1920} stroke="rgba(0,224,130,0.03)" strokeWidth={1} />
        ))}
        {Array.from({length: 19}, (_, i) => (
          <line key={`h${i}`} x1={0} x2={1080} y1={i * 108} y2={i * 108} stroke="rgba(0,224,130,0.03)" strokeWidth={1} />
        ))}
      </svg>

      {/* ------------------------------------------------------- the world:
          panel + character, punched and kicked together on the break so the
          hit is one event happening to one screen. */}
      <AbsoluteFill
        style={{
          transform: `translate(${kk.x}px, ${kk.y}px) scale(${punch})`,
          transformOrigin: '540px 960px',
        }}
      >
        {/* -------------------------------------------------- the terminal */}
        <div
          style={{
            position: 'absolute',
            left: PANEL.x,
            top: PANEL.y,
            width: PANEL.w,
            height: PANEL.h,
            borderRadius: 18,
            overflow: 'hidden',
            border: '1px solid rgba(0,224,130,0.20)',
            boxShadow: '0 0 70px rgba(0,230,118,0.07), 0 18px 60px rgba(0,0,0,0.55)',
          }}
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
            alarmAt={SHOCK_AT}
            neutralTagDuring={[B.quiz, B.wait]}
            subject={`MAYA LAB · ${p.subject}`}
            stamp={p.stamp}
            width={PANEL.w}
            height={PANEL.h}
            ui={PANEL_UI}
          />
        </div>

        {/* ------------------------------------------------ the corner cam.
            Upper body, cropped by the frame's own bottom edge. The drop
            shadow is what seats him ON the terminal instead of floating in
            front of it. */}
        <AbsoluteFill style={{filter: 'drop-shadow(0 0 30px rgba(0,0,0,0.7))', pointerEvents: 'none'}}>
          <PoseCut
            height={CAM.ink}
            footX={CAM.footX}
            footY={footY}
            facing="left"
            cuts={CUTS}
            end={B.end}
            motion="toon"
            shadow={false}
          />
        </AbsoluteFill>

        {/* ONE sweat drop, gliding slowly, looping — quiz through the wait,
            gone the moment the break resolves the tension into shock. */}
        {frame >= B.quiz + 8 && frame < 996 ? (
          <SweatSlide x={head.x} y={head.y} w={hw} since={frame - (B.quiz + 8)} />
        ) : null}

        {/* The take: three small flicks beside his head, in the free corner
            above him — the full radial burst has no chart-free room here. */}
        {/* +2: the first two shock frames are the smear, and the squash moves
            the head under the FX anchor while it fires. The flicks land as the
            drawing settles, which is also when a hand-drawn take flicks. */}
        <ShockFlicks
          x={Math.min(head.x + hw * 0.4, 1080 - hw * 0.75)}
          y={head.y - hw * 0.7}
          since={frame - (SHOCK_AT + 2)}
          size={hw * 0.36}
        />
      </AbsoluteFill>

      {/* THE HIT's flash — outside the punch so it cannot scale. */}
      <FlashCut since={frame - SHOCK_AT} frames={2} color="#FFEFE8" max={0.5} />

      {/* --------------------------------------------------------- top band */}
      <div
        style={{
          position: 'absolute',
          top: 34,
          left: 30,
          fontFamily: FONT.mono,
          fontSize: 22,
          letterSpacing: 5,
          color: '#4E7A64',
          fontWeight: 700,
        }}
      >
        MAYA LAB
      </div>

      {inQuiz || (frame >= B.quiz - 2 && frame < B.wait + 2) ? (
        <div
          style={{
            position: 'absolute',
            top: 84,
            left: 0,
            right: 0,
            textAlign: 'center',
            fontFamily: FONT.mono,
            fontSize: 46,
            fontWeight: 700,
            color: '#E8EDF2',
            letterSpacing: 1.5,
            opacity: quizP,
            transform: `translateY(${(1 - quizP) * -12}px)`,
          }}
        >
          BOUNCE OR BREAKDOWN?
        </div>
      ) : null}

      {frame >= B.wait && frame < SHOCK_AT - 4 ? (
        <div
          style={{
            position: 'absolute',
            top: 88,
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
              background: 'rgba(4,16,12,.85)',
              border: '2px solid rgba(232,237,242,.22)',
              fontFamily: FONT.mono,
              fontSize: 32,
              fontWeight: 700,
              color: '#E8EDF2',
              letterSpacing: 2,
            }}
          >
            POSITION OPEN · {barsIn} {barsIn === 1 ? 'BAR' : 'BARS'} · UNRESOLVED
          </span>
        </div>
      ) : null}

      {answerP > 0 ? (
        <div
          style={{
            position: 'absolute',
            top: 76,
            left: 0,
            right: 0,
            textAlign: 'center',
            opacity: answerP,
            transform: `scale(${interpolate(answerP, [0, 1], [1.16, 1])})`,
          }}
        >
          <span
            style={{
              display: 'inline-block',
              padding: '14px 38px',
              borderRadius: 14,
              background: '#FF3B30',
              fontFamily: FONT.mono,
              fontSize: 52,
              fontWeight: 700,
              color: '#0B0304',
              letterSpacing: 2,
            }}
          >
            BREAKDOWN
          </span>
        </div>
      ) : null}

      {rzP > 0 ? (
        <div style={{position: 'absolute', top: 88, left: 0, right: 0, textAlign: 'center', opacity: rzP}}>
          <span
            style={{
              display: 'inline-block',
              padding: '11px 24px',
              borderRadius: 11,
              background: 'rgba(4,16,12,.88)',
              border: '2px solid rgba(255,59,48,.5)',
              fontFamily: FONT.mono,
              fontSize: 27,
              fontWeight: 700,
              color: '#E8EDF2',
              letterSpacing: 1.5,
            }}
          >
            PLANNED −1R · BEST IT EVER GOT +{p.mfe.toFixed(2)}R
          </span>
        </div>
      ) : null}

      {/* ------------------------------------------------------------ hook */}
      {frame < 96 ? (
        <div
          style={{
            position: 'absolute',
            top: 470,
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
              fontSize: 96,
              fontWeight: 700,
              color: '#E8EDF2',
              lineHeight: 1.0,
              letterSpacing: -2,
              textShadow: '0 4px 30px rgba(0,0,0,.8)',
            }}
          >
            EVERY RULE
            <br />
            <span style={{color: '#22E07E'}}>SAID BUY</span>
          </div>
        </div>
      ) : null}

      {/* -------------------------------------------- timer + chips, lower
          band LEFT — beside the cam, not over the chart. */}
      {quizP > 0 ? (
        <div style={{position: 'absolute', inset: 0, opacity: quizP}}>
          <svg width={520} height={300} style={{position: 'absolute', top: LANES.ring.y0, left: 0}}>
            <circle cx={250} cy={130} r={R} fill="rgba(4,16,12,.8)" stroke="rgba(255,255,255,.16)" strokeWidth={3} />
            <circle
              cx={250}
              cy={130}
              r={R}
              fill="none"
              stroke="#E8EDF2"
              strokeWidth={9}
              strokeLinecap="round"
              strokeDasharray={CIRC}
              strokeDashoffset={CIRC * ringP}
              transform="rotate(-90 250 130)"
            />
            <text
              x={250}
              y={156}
              fontFamily={FONT.mono}
              fontSize={78}
              fontWeight={700}
              fill="#E8EDF2"
              textAnchor="middle"
              transform={`translate(${250 * (1 - digitPop)} ${130 * (1 - digitPop)}) scale(${digitPop})`}
            >
              {secsLeft}
            </text>
          </svg>
          <div style={{position: 'absolute', top: LANES.chips.y0 + 6, left: LANES.chips.x0, display: 'flex', gap: 18}}>
            {['BOUNCE', 'BREAKDOWN'].map((t, i) => (
              <div
                key={t}
                style={{
                  padding: '14px 26px',
                  borderRadius: 12,
                  background: 'rgba(4,16,12,.82)',
                  border: '2px solid rgba(232,237,242,.28)',
                  fontFamily: FONT.mono,
                  fontSize: 30,
                  fontWeight: 700,
                  color: '#E8EDF2',
                  letterSpacing: 1.2,
                  opacity: interpolate(frame, [B.quiz + 6 + i * 5, B.quiz + 16 + i * 5], [0, 1], {
                    extrapolateLeft: 'clamp',
                    extrapolateRight: 'clamp',
                  }),
                  transform: `translateY(${interpolate(frame, [B.quiz + 6 + i * 5, B.quiz + 18 + i * 5], [16, 0], {
                    easing: EASE.settleBack,
                    extrapolateLeft: 'clamp',
                    extrapolateRight: 'clamp',
                  })}px)`,
                }}
              >
                {t}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* --------------------------------------------------- the lesson.
          Lower band, left of the cam, held to the last frame. */}
      {frame >= 1104 ? (
        <div
          style={{
            position: 'absolute',
            top: LANES.lesson.y0,
            left: LANES.lesson.x0,
            width: LANES.lesson.x1 - LANES.lesson.x0,
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
              padding: '24px 26px',
              borderRadius: 16,
              background: 'rgba(4,16,12,.92)',
              border: '2px solid rgba(34,224,126,.55)',
              fontFamily: FONT.body,
              fontWeight: 800,
              fontSize: 35,
              lineHeight: 1.18,
              color: '#E8EDF2',
              letterSpacing: -0.5,
            }}
          >
            A GOOD SETUP IS NOT A PREDICTION.
            <div style={{fontSize: 24, fontWeight: 600, color: '#9FD9BC', marginTop: 10, letterSpacing: 0}}>
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
            left: LANES.caption.x0,
            width: LANES.caption.x1 - LANES.caption.x0,
            bottom: 1920 - LANES.caption.y1,
            opacity: fadeOf(capP),
            transform: `translateY(${(1 - capP) * 14}px)`,
          }}
        >
          <span
            style={{
              display: 'inline-block',
              padding: '13px 22px',
              borderRadius: 13,
              background: 'rgba(4,14,10,.9)',
              border: '1px solid rgba(255,255,255,.12)',
              fontFamily: FONT.body,
              fontWeight: 700,
              fontSize: 32,
              lineHeight: 1.24,
              color: '#E8EDF2',
              letterSpacing: -0.4,
            }}
          >
            {caption.text}
          </span>
        </div>
      ) : null}

      <Vignette strength={0.28} />
      <Grain opacity={0.04} />

      {/* Footer on every frame — provenance + not-advice, left of the cam so
          he can never stand on the disclaimer. */}
      <div
        style={{
          position: 'absolute',
          left: LANES.footer.x0,
          bottom: 1920 - LANES.footer.y1 + 8,
          width: LANES.footer.x1 - LANES.footer.x0,
          fontFamily: FONT.mono,
          fontSize: 15.5,
          color: '#7FA290',
          letterSpacing: 0.4,
          lineHeight: 1.42,
          textAlign: 'left',
        }}
      >
        {p.footer}
      </div>

      {/* ------------------------------------------------------------ sound */}
      {Array.from({length: COUNT_N}, (_, i) => (
        <Sequence key={`tick${i}`} from={B.quiz + i * COUNT_PER} durationInFrames={COUNT_PER}>
          <Audio src={staticFile(i % 2 === 0 ? 'audio/tick.wav' : 'audio/tock.wav')} volume={0.6} />
        </Sequence>
      ))}
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
