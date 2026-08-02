// StrategyLesson.tsx — the explainer sequel to a TradingQuiz reel (9:16).
//
// The quiz asks "buy or sell?"; this reel walks the same tape slowly and
// teaches WHY. Beats, timed off the detector's indices (never re-derived):
//
//   1. the two reference lines, with the actors on them — sellers defend
//      yesterday's high, buyers defend yesterday's low
//   2. a follow-cam rides the rally toward the top line, guide arrow tracing
//   3. the break: a highlight box around the bars that closed above the line,
//      and the acceptance rule stated while they print
//   4. the failure: the closes slip back inside, red arrow, impact
//   5. the rule card: LINE -> BREAK -> ACCEPTANCE
//
// Shares the TradingQuiz terminal house style (bg, palette, glass, boot,
// candle tick-printing) but carries its own copies, like every sibling
// composition in this repo. Camera is a follow-cam: keyframed focus +
// scale via translate((1-s)(f-center)) scale(s), which keeps the frame
// edges covered for any s >= 1. Level labels anchor RIGHT in this comp —
// the follow-cam spends the tight phase far right of the quiz camera's
// focus, and left-anchored labels would slide off frame.
import React from 'react';
import {AbsoluteFill, Audio, interpolate, random, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {z} from 'zod';
import {C, FONT} from '../slides/theme';
import {EASE, SPRINGS, fadeOf} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';

const candleSchema = z.object({
  o: z.number(),
  h: z.number(),
  l: z.number(),
  c: z.number(),
});

export const strategyLessonSchema = z.object({
  kick: z.string(),
  indexLabel: z.string().optional(),
  subject: z.string(),
  levelPrice: z.number(),
  levelLabel: z.string(),
  level2Price: z.number(),
  level2Label: z.string(),
  /** First bar that CLOSED above the top line (detector index). */
  breakAt: z.number(),
  /** Last bar that closed above the line — where acceptance ended. */
  decisionAt: z.number(),
  /** Four beat captions: actors, the ride, the break, the failure. */
  captions: z.array(z.string()).length(4),
  ruleTitle: z.string(),
  ruleText: z.string(),
  footer: z.string(),
  durationInFrames: z.number(),
  candles: z.array(candleSchema).min(10),
});
export type StrategyLessonProps = z.infer<typeof strategyLessonSchema>;

// ------------------------------------------------------------------ palette
const T = {
  bg: '#02070A',
  grid: 'rgba(0,224,130,0.055)',
  gridBold: 'rgba(0,224,130,0.115)',
  ice: '#22E07E',
  steel: '#4E7A64',
  panelTop: '#04100C',
  panelBot: '#020806',
  edge: 'rgba(0,224,130,0.20)',
  up: '#00E676',
  down: '#FF3B30',
};

// ---------------------------------------------------------------- timing
// Beat boundaries. Candle appear-times are derived from these plus the
// fixture's break/decision indices, so the tape always prints in story time.
const SCREEN_IN = 8;
const LINES_IN = 26;
const CHIPS_IN = 56;
const RALLY_IN = 90;      // bars 0..breakAt-1 print across this window
const RALLY_END = 300;
const BATTLE_END = 460;   // bars breakAt..decisionAt print RALLY_END..here
const FADE_END = 560;     // bars decisionAt+1.. print BATTLE_END..here
const RULE_IN = 590;
export const STRATEGY_LESSON_FRAMES = 690;
const BEATS: Array<[number, number]> = [
  [20, RALLY_IN + 55],
  [RALLY_IN + 65, RALLY_END],
  [RALLY_END + 6, BATTLE_END - 6],
  [BATTLE_END + 6, RULE_IN - 12],
];

const CANDLE_TICKS = 3;

// ---------------------------------------------------------------- geometry
const SCREEN = {x: 34, y: 384, w: 1012, h: 958};
const CHROME_H = 56;
const CHART = {x0: 78, x1: 754, y0: 492, y1: 1198};

export const StrategyLesson: React.FC<StrategyLessonProps> = (p) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const n = p.candles.length;

  // Static symmetric frame containing every bar and both lines — no reveal
  // rescale in a lesson; the whole story is on screen from the start.
  const rawLo = Math.min(...p.candles.map((k) => k.l), p.level2Price);
  const rawHi = Math.max(...p.candles.map((k) => k.h), p.levelPrice);
  const pad = (rawHi - rawLo) * 0.07;
  const lo = rawLo - pad;
  const hi = rawHi + pad;
  const priceToY = (v: number) => CHART.y1 - ((v - lo) / (hi - lo)) * (CHART.y1 - CHART.y0);

  const slot = (CHART.x1 - CHART.x0) / n;
  const bodyW = Math.min(24, Math.max(2.5, slot * 0.62));
  const wickW = Math.min(2.5, Math.max(1.1, bodyW * 0.3));
  const cx = (i: number) => CHART.x0 + slot * i + slot / 2;

  // Story-time appear frame per bar: rally, battle, fade — each beat prints
  // its own bars across its own window.
  const appearAt = (i: number): number => {
    if (i < p.breakAt) return RALLY_IN + (i / Math.max(1, p.breakAt)) * (RALLY_END - RALLY_IN - 14);
    if (i <= p.decisionAt)
      return RALLY_END + ((i - p.breakAt) / Math.max(1, p.decisionAt - p.breakAt + 1)) * (BATTLE_END - RALLY_END - 16);
    return BATTLE_END + ((i - p.decisionAt - 1) / Math.max(1, n - p.decisionAt - 1)) * (FADE_END - BATTLE_END - 10);
  };
  const CANDLE_FORM = 7;

  // ------------------------------------------------------------ follow-cam
  // Keyframed ride: settle in, follow the rally up to the line, hold tight
  // through the battle, release wide as the failure prints.
  const camS = interpolate(
    frame,
    [0, RALLY_IN, RALLY_END, BATTLE_END - 30, BATTLE_END, FADE_END, p.durationInFrames],
    [1.0, 1.05, 1.21, 1.22, 1.2, 1.0, 1.03],
    {easing: EASE.cruise, extrapolateRight: 'clamp'}
  );
  const camFx = interpolate(frame, [0, RALLY_IN, RALLY_END, BATTLE_END, FADE_END], [540, 260, 500, 600, 540], {
    easing: EASE.cruise,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const camFy = interpolate(frame, [0, RALLY_IN, RALLY_END, BATTLE_END, FADE_END], [960, 950, 680, 700, 960], {
    easing: EASE.cruise,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const camTx = (1 - camS) * (camFx - 540);
  const chartT = `translate(${camTx}px, ${(1 - camS) * (camFy - 960)}px) scale(${camS})`;
  // Chart-space x of the frame's left/right edges under the camera — the
  // level labels and actor chips clamp to this so the follow-cam can never
  // push them off screen (x' = 540 + s(q-540) + tx  =>  q at x'=edge).
  const visL = (0 - 540 - camTx) / camS + 540;
  const visR = (1080 - 540 - camTx) / camS + 540;
  const labelAnchorX = Math.min(SCREEN.x + SCREEN.w - 34, visR - 22);
  const chipAnchorX = Math.max(CHART.x0 + 6, visL + 22);

  // ------------------------------------------------------------ elements
  const screenP = spring({frame: frame - SCREEN_IN, fps, config: SPRINGS.heavy});
  const boot = frame < SCREEN_IN + 16 ? (frame % 3 === 0 ? 0.72 : 1) : 1;
  const gridP = interpolate(frame, [LINES_IN - 6, LINES_IN + 20], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const step = (hi - lo) / 5;
  const gridLines = Array.from({length: 6}, (_, i) => lo + step * i);

  const levels = [
    {price: p.levelPrice, label: p.levelLabel, at: LINES_IN, actor: 'SELLERS', col: T.down, below: false},
    {price: p.level2Price, label: p.level2Label, at: LINES_IN + 8, actor: 'BUYERS', col: T.up, below: true},
  ];

  const hookP = spring({frame, fps, config: SPRINGS.hero});
  const ruleP = spring({frame: frame - RULE_IN, fps, config: SPRINGS.heavy});

  // Guide arrow along the rally (beat 2), drawn on then gone by the battle.
  const arrowP = interpolate(frame, [RALLY_IN + 70, RALLY_END - 40], [0, 1], {
    easing: EASE.cruise,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const arrowOut = interpolate(frame, [RALLY_END - 10, RALLY_END + 14], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const aFrom = {x: cx(2), y: priceToY(Math.min(...p.candles.slice(0, 8).map((k) => k.l))) + 26};
  const aTo = {x: cx(p.breakAt - 2), y: priceToY(p.levelPrice) + 46};
  const aTip = {
    x: aFrom.x + (aTo.x - aFrom.x) * arrowP,
    y: aFrom.y + (aTo.y - aFrom.y) * arrowP,
  };
  const aAng = (Math.atan2(aTo.y - aFrom.y, aTo.x - aFrom.x) * 180) / Math.PI;

  // Highlight box around the acceptance run (beat 3).
  const boxP = spring({frame: frame - (RALLY_END + 26), fps, config: SPRINGS.pop});
  const boxed = p.candles.slice(p.breakAt, p.decisionAt + 1);
  const boxX = cx(p.breakAt) - slot * 0.58;
  const boxW = slot * (p.decisionAt - p.breakAt + 1.16);
  const boxTop = priceToY(Math.max(...boxed.map((k) => k.h))) - 16;
  const boxBot = priceToY(Math.min(...boxed.map((k) => k.l))) + 16;

  // Failure arrow (beat 4): from the last acceptance bar down into the range.
  // Fires only once the fade has mostly PRINTED — an arrow ahead of the tape
  // would assert downside the chart hasn't shown yet.
  const FAIL_IN = FADE_END - 26;
  const failP = spring({frame: frame - FAIL_IN, fps, config: SPRINGS.pop});
  const fFrom = {x: cx(p.decisionAt) + slot * 0.7, y: priceToY(p.candles[p.decisionAt].c)};
  const lastBars = p.candles.slice(p.decisionAt + 1);
  const fTo = {
    x: cx(n - 3),
    y: priceToY(Math.min(...lastBars.map((k) => k.c))) + 10,
  };
  const fAng = (Math.atan2(fTo.y - fFrom.y, fTo.x - fFrom.x) * 180) / Math.PI;

  const renderCandle = (k: z.infer<typeof candleSchema>, i: number) => {
    const raw = (frame - appearAt(i)) / CANDLE_FORM;
    if (raw <= 0) return null;
    const stepN = Math.min(CANDLE_TICKS, Math.ceil(Math.min(1, raw) * CANDLE_TICKS));
    const settled = stepN >= CANDLE_TICKS;
    const f = stepN / CANDLE_TICKS;
    const hNow = k.o + (k.h - k.o) * Math.min(1, f * 1.22);
    const lNow = k.o + (k.l - k.o) * Math.min(1, f * 1.22);
    const drift = (random(`k${i}t${stepN}`) - 0.5) * (k.h - k.l) * 0.7;
    const cNow = settled ? k.c : Math.max(lNow, Math.min(hNow, k.o + (k.c - k.o) * f + drift));
    const col = cNow >= k.o ? C.emerald : C.redHot;
    const x = cx(i);
    const yTop = priceToY(Math.max(k.o, cNow));
    const yBot = priceToY(Math.min(k.o, cNow));
    return (
      <g key={i} style={{filter: `drop-shadow(0 0 ${settled ? 6 : 11}px ${col}${settled ? '77' : 'cc'})`}}>
        <line x1={x} x2={x} y1={priceToY(hNow)} y2={priceToY(lNow)} stroke={col} strokeWidth={wickW} />
        <rect x={x - bodyW / 2} y={yTop} width={bodyW} height={Math.max(2, yBot - yTop)} rx={2} fill={col} />
      </g>
    );
  };

  // Caption for the active beat, if any.
  const beatIdx = BEATS.findIndex(([a, b]) => frame >= a && frame <= b);

  return (
    <AbsoluteFill style={{background: T.bg, fontFamily: FONT.body}}>
      {/* background — same drafting plate as the quiz */}
      <AbsoluteFill>
        <svg
          width={1080}
          height={1920}
          style={{
            position: 'absolute',
            inset: 0,
            transform: `translate(${Math.sin(frame / 220) * 5}px, ${Math.cos(frame / 260) * 6}px)`,
          }}
        >
          {Array.from({length: 14}, (_, i) => i * 90).map((x, i) => (
            <line key={`v${x}`} x1={x} x2={x} y1={-40} y2={1960} stroke={i % 3 === 0 ? T.gridBold : T.grid} strokeWidth={1} />
          ))}
          {Array.from({length: 23}, (_, i) => i * 90).map((y, i) => (
            <line key={`h${y}`} x1={-40} x2={1120} y1={y} y2={y} stroke={i % 3 === 0 ? T.gridBold : T.grid} strokeWidth={1} />
          ))}
        </svg>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(120% 55% at 50% 6%, rgba(0,224,130,0.11), transparent 60%),' +
              'radial-gradient(110% 50% at 20% 104%, rgba(0,224,130,0.09), transparent 62%),' +
              'radial-gradient(110% 50% at 85% 104%, rgba(255,59,48,0.06), transparent 62%)',
          }}
        />
      </AbsoluteFill>

      {/* ------------------------------------------------ chart layer (cam) */}
      <AbsoluteFill style={{transform: chartT}}>
        <div
          style={{
            position: 'absolute',
            left: SCREEN.x,
            top: SCREEN.y,
            width: SCREEN.w,
            height: SCREEN.h,
            borderRadius: 30,
            opacity: fadeOf(screenP) * boot,
            transform: `translateY(${interpolate(screenP, [0, 1], [26, 0])}px)`,
            background: `linear-gradient(180deg, ${T.panelTop} 0%, ${T.panelBot} 100%)`,
            border: `1px solid ${T.edge}`,
            boxShadow: `0 40px 100px -30px #000, inset 0 1px 0 rgba(255,255,255,.05), 0 0 70px ${T.up}18`,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              height: CHROME_H,
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '0 22px',
              borderBottom: `1px solid ${T.edge}`,
              background: 'rgba(0,224,130,.045)',
            }}
          >
            {[T.down, '#E0A23B', T.up].map((col) => (
              <div key={col} style={{width: 11, height: 11, borderRadius: 999, background: col, opacity: 0.62}} />
            ))}
            <div style={{marginLeft: 12, fontFamily: FONT.mono, fontSize: 19, letterSpacing: 2, color: T.steel}}>
              MAYA LAB — {p.subject}
            </div>
            <div style={{marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8}}>
              <div style={{width: 8, height: 8, borderRadius: 999, background: T.up, opacity: 0.4 + Math.sin(frame / 8) * 0.35}} />
              <div style={{fontFamily: FONT.mono, fontSize: 17, letterSpacing: 2, color: T.steel}}>REPLAY</div>
            </div>
          </div>
          <AbsoluteFill
            style={{
              pointerEvents: 'none',
              background: 'repeating-linear-gradient(0deg, rgba(255,255,255,.020) 0px, rgba(255,255,255,.020) 1px, transparent 1px, transparent 4px)',
            }}
          />
          <AbsoluteFill
            style={{
              pointerEvents: 'none',
              background: `linear-gradient(115deg, transparent ${20 + Math.sin(frame / 150) * 12}%, rgba(255,255,255,.045) ${38 + Math.sin(frame / 150) * 12}%, transparent ${56 + Math.sin(frame / 150) * 12}%)`,
            }}
          />
        </div>

        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
          {gridP > 0
            ? gridLines.map((v, i) => (
                <g key={`g${i}`} opacity={gridP * 0.5}>
                  <line x1={CHART.x0 - 6} x2={SCREEN.x + SCREEN.w - 26} y1={priceToY(v)} y2={priceToY(v)} stroke={T.edge} strokeWidth={1} />
                </g>
              ))
            : null}

          {/* the two lines + right-anchored labels + actor chips ON the lines */}
          {levels.map((lv) => {
            const lp = interpolate(frame, [lv.at, lv.at + 22], [0, 1], {
              easing: EASE.enter,
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            if (lp <= 0) return null;
            const ly = priceToY(lv.price);
            const pulse = 0.55 + Math.sin(Math.max(0, frame - lv.at) / 11) * 0.45;
            const chipP = spring({frame: frame - CHIPS_IN, fps, config: SPRINGS.pop});
            const labelW = lv.label.length * 15.5 + 16;
            const chipY = lv.below ? ly + 12 : ly - 46;
            const triY = lv.below ? chipY + 11 : chipY + 23;
            return (
              <g key={`lv-${lv.label}`}>
                <line
                  x1={CHART.x0 - 6}
                  x2={CHART.x0 - 6 + (SCREEN.x + SCREEN.w - 26 - (CHART.x0 - 6)) * lp}
                  y1={ly}
                  y2={ly}
                  stroke={T.ice}
                  strokeWidth={3}
                  strokeDasharray="14 10"
                  style={{filter: `drop-shadow(0 0 ${6 + pulse * 8}px ${T.ice}dd)`}}
                />
                <g opacity={fadeOf(lp)}>
                  <rect x={labelAnchorX - labelW} y={lv.below ? ly + 10 : ly - 44} width={labelW} height={34} rx={8} fill={T.panelTop} opacity={0.92} />
                  <text
                    x={labelAnchorX - 8}
                    y={lv.below ? ly + 36 : ly - 18}
                    fill={T.ice}
                    fontFamily={FONT.mono}
                    fontWeight={700}
                    fontSize={25}
                    letterSpacing={2}
                    textAnchor="end"
                  >
                    {lv.label}
                  </text>
                </g>
                {chipP > 0.01 ? (
                  <g opacity={fadeOf(chipP)} style={{filter: `drop-shadow(0 0 10px ${lv.col}66)`}}>
                    <rect x={chipAnchorX} y={chipY} width={lv.actor.length * 14 + 42} height={34} rx={8} fill="rgba(2,10,7,.9)" stroke={lv.col} strokeWidth={1.4} />
                    <polygon
                      points={
                        lv.below
                          ? `${chipAnchorX + 16},${triY} ${chipAnchorX + 28},${triY} ${chipAnchorX + 22},${triY - 11}`
                          : `${chipAnchorX + 16},${triY - 11} ${chipAnchorX + 28},${triY - 11} ${chipAnchorX + 22},${triY}`
                      }
                      fill={lv.col}
                    />
                    <text x={chipAnchorX + 38} y={chipY + 24} fill={lv.col} fontFamily={FONT.mono} fontWeight={800} fontSize={22} letterSpacing={2}>
                      {lv.actor}
                    </text>
                  </g>
                ) : null}
              </g>
            );
          })}

          {p.candles.map((k, i) => renderCandle(k, i))}

          {/* the rally guide arrow */}
          {arrowP > 0 && arrowOut > 0 ? (
            <g opacity={0.75 * arrowOut}>
              <line x1={aFrom.x} y1={aFrom.y} x2={aTip.x} y2={aTip.y} stroke="#D8E6DE" strokeWidth={4} strokeLinecap="round" strokeDasharray="2 10" />
              {arrowP > 0.12 ? (
                <polygon
                  points={`${aTip.x + 20},${aTip.y} ${aTip.x - 8},${aTip.y - 12} ${aTip.x - 8},${aTip.y + 12}`}
                  fill="#D8E6DE"
                  transform={`rotate(${aAng} ${aTip.x} ${aTip.y})`}
                />
              ) : null}
            </g>
          ) : null}

          {/* acceptance-run highlight */}
          {boxP > 0.01 ? (
            <g opacity={fadeOf(boxP) * 0.95}>
              <rect
                x={boxX}
                y={boxTop}
                width={Math.max(34, boxW)}
                height={boxBot - boxTop}
                rx={12}
                fill={`${T.ice}12`}
                stroke={T.ice}
                strokeWidth={3.5}
                style={{filter: `drop-shadow(0 0 14px ${T.ice}aa)`}}
              />
            </g>
          ) : null}

          {/* the failure arrow */}
          {failP > 0.01 ? (
            <g opacity={fadeOf(failP)} style={{filter: `drop-shadow(0 0 12px ${T.down}aa)`}}>
              <line x1={fFrom.x} y1={fFrom.y} x2={fTo.x} y2={fTo.y} stroke={T.down} strokeWidth={8} strokeLinecap="round" />
              <polygon
                points={`${fTo.x + 24},${fTo.y} ${fTo.x - 8},${fTo.y - 16} ${fTo.x - 8},${fTo.y + 16}`}
                fill={T.down}
                transform={`rotate(${fAng} ${fTo.x} ${fTo.y})`}
              />
            </g>
          ) : null}
        </svg>
      </AbsoluteFill>

      {/* ------------------------------------------------------- HUD layer */}
      <div
        style={{
          position: 'absolute',
          top: 112,
          left: 0,
          right: 0,
          textAlign: 'center',
          opacity: fadeOf(hookP),
          transform: `scale(${interpolate(hookP, [0, 1], [0.86, 1])})`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            fontFamily: FONT.mono,
            fontWeight: 700,
            fontSize: 21,
            letterSpacing: 4,
            color: T.ice,
            border: `1px solid ${T.edge}`,
            borderRadius: 999,
            padding: '6px 18px',
            marginBottom: 14,
          }}
        >
          {p.indexLabel ? <span style={{color: T.steel}}>{p.indexLabel}</span> : null}
          MAYA LAB
        </div>
        <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 76, color: C.ink, letterSpacing: -1}}>
          {p.kick.split(' ')[0]} <span style={{color: T.ice}}>{p.kick.split(' ').slice(1).join(' ')}</span>
        </div>
      </div>

      {/* beat captions, bottom band */}
      {beatIdx >= 0 ? (
        <div
          key={beatIdx}
          style={{
            position: 'absolute',
            top: 1408,
            left: 70,
            right: 70,
            textAlign: 'center',
            opacity:
              fadeOf(spring({frame: frame - BEATS[beatIdx][0], fps, config: SPRINGS.pop})) *
              interpolate(frame, [BEATS[beatIdx][1] - 12, BEATS[beatIdx][1]], [1, 0], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              }),
          }}
        >
          <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 48, lineHeight: 1.22, color: C.ink}}>
            {p.captions[beatIdx]}
          </div>
        </div>
      ) : null}

      {/* rule card */}
      {ruleP > 0 ? (
        <div
          style={{
            position: 'absolute',
            top: 1392,
            left: 46,
            right: 46,
            opacity: fadeOf(ruleP),
            transform: `translateY(${interpolate(ruleP, [0, 1], [30, 0])}px)`,
            background: 'rgba(0,224,130,.07)',
            border: `1px solid ${T.edge}`,
            borderRadius: 26,
            padding: '24px 30px',
            backdropFilter: 'blur(6px)',
          }}
        >
          <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 24, letterSpacing: 3, color: T.ice, marginBottom: 12}}>
            {p.ruleTitle.toUpperCase()}
          </div>
          <div style={{fontFamily: FONT.body, fontWeight: 500, fontSize: 33, lineHeight: 1.3, color: C.ink}}>{p.ruleText}</div>
        </div>
      ) : null}

      {/* footer */}
      <div
        style={{
          position: 'absolute',
          bottom: 68,
          left: 46,
          right: 46,
          display: 'flex',
          alignItems: 'stretch',
          justifyContent: 'center',
          borderTop: `1px solid ${T.edge}`,
          paddingTop: 18,
        }}
      >
        {p.footer.split('·').map((cell, i, all) => (
          <div
            key={cell}
            style={{
              flex: 1,
              textAlign: 'center',
              padding: '0 14px',
              borderRight: i < all.length - 1 ? `1px solid ${T.edge}` : undefined,
              fontFamily: FONT.mono,
              fontSize: 19,
              lineHeight: 1.35,
              color: T.steel,
            }}
          >
            {cell.trim()}
          </div>
        ))}
      </div>

      {/* ------------------------------------------------------- sound
       * whoosh on the lines, tones only for the battle + fade bars (a tone
       * per rally bar would be noise), impact when the failure arrow lands. */}
      <Sequence from={LINES_IN} durationInFrames={40}>
        <Audio src={staticFile('audio/whoosh_in.wav')} volume={0.5} />
      </Sequence>
      {p.candles.map((k, i) =>
        i >= p.breakAt ? (
          <Sequence key={`s${i}`} from={Math.round(appearAt(i))} durationInFrames={6}>
            <Audio src={staticFile(k.c >= k.o ? 'audio/candle_up.wav' : 'audio/candle_down.wav')} volume={0.4} />
          </Sequence>
        ) : null
      )}
      <Sequence from={FADE_END - 26} durationInFrames={30}>
        <Audio src={staticFile('audio/impact.wav')} volume={0.65} />
      </Sequence>

      <Grain />
      <Vignette />
    </AbsoluteFill>
  );
};
