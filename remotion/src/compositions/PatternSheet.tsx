// PatternSheet.tsx — the living cheat sheet, the owner's spec verbatim: ONE
// screen, divided into ten boxes, and in each box a candlestick pattern is
// being drawn — candles printing, lines penning in — all at once, like the
// static patterns-grid posts but alive. No cycling cards, no camera: the grid
// IS the video, and the last frame IS the poster.
//
// 1080x1920, 30fps, 900 frames (30s): the boxes draw over the first ~11
// seconds with a light stagger (a sheet where everything moves in lockstep
// reads as one animation copy-pasted ten times), the breaks and verdict chips
// land through the middle, and the finished sheet HOLDS for the back half —
// that is the screenshot-and-save beat, and it makes the reel loop cleanly.
//
// Data: the real-pattern fixture. Ten of the twelve detected formations
// (cup-and-handle and megaphone sit out — their windows are the longest and
// at cell size the densest); every box carries its real SPY date range.
// Sound: one blip per box as its breakout prints. The owner scores reels with
// trending audio at post time.
import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {z} from 'zod';
import {FONT} from '../slides/theme';
import {EASE} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';
import {PT, type PatternData} from '../components/PatternCard';
import {PatternCell, cellTpFrame} from '../components/PatternCell';
import {impact} from '../motion/toon';

export const patternSheetSchema = z.object({
  chapters: z.array(
    z.object({
      title: z.string(),
      sub: z.string(),
      cards: z.array(z.any()),
    })
  ),
  footer: z.string(),
  durationInFrames: z.number(),
});
export type PatternSheetProps = z.infer<typeof patternSheetSchema>;

export const PATTERN_SHEET_FRAMES = 900;

// The ten, in reading order (left-right, top-bottom): reversals first, then
// continuation, then the wedges — the same taxonomy the classic sheets use.
// Bear Flag is honestly UNMATCHED under the winners-only rule — no SPY bear
// flag in five years whose breakdown ran to target before the stop — so Cup
// and Handle pairs with Bull Flag instead. Thresholds do not get loosened to
// fake a loser into a winner.
const PICK = [
  'Double Top',
  'Double Bottom',
  'Head and Shoulders',
  'Inverse Head and Shoulders',
  'Bull Flag',
  'Cup and Handle',
  'Ascending Triangle',
  'Symmetrical Triangle',
  'Rising Wedge',
  'Falling Wedge',
];

// ------------------------------------------------------------------ layout
const COLS = 2;
const GAP = 14;
const CELL_W = (1080 - GAP * (COLS + 1)) / COLS; // 519
const CELL_H = 300;
const GRID_TOP = 196;
const STAGGER = 18; // frames between box landings — a drum pattern, not a queue
/** Frames after a box's Sequence start at which it LANDS (the smash). */
const LAND = 7;

export const PatternSheet: React.FC<PatternSheetProps> = (p) => {
  const frame = useCurrentFrame();

  const byName: Record<string, PatternData> = {};
  for (const ch of p.chapters) for (const c of ch.cards as PatternData[]) byName[c.name] = c;
  const cells = PICK.map((n) => byName[n]).filter(Boolean);

  // The headline number, summed from the cells rather than written by hand, so
  // it cannot drift from the boxes underneath it. Each box draws a winner —
  // that is what a worked example is — and this says how rare that winner was.
  const wins = cells.reduce((s, c) => s + (c.sampleWins ?? 0), 0);
  const tries = cells.reduce((s, c) => s + (c.sampleN ?? 0), 0);

  // every landing kicks the whole sheet — the surface being smashed is the
  // frame itself, and a surface that does not move absorbed nothing
  let kx = 0;
  let ky = 0;
  for (let i = 0; i < cells.length; i++) {
    const land = 10 + i * STAGGER + LAND;
    kx += impact(frame - land, 12) * 7 * (i % 2 === 0 ? 1 : -1);
    ky += impact(frame - land - 1, 12) * 5;
  }

  return (
    <AbsoluteFill style={{backgroundColor: PT.bg}}>
      <AbsoluteFill style={{transform: `translate(${kx}px, ${ky}px)`}}>
      {/* faint ruled grid behind everything */}
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        {Array.from({length: 11}, (_, i) => (
          <line key={`v${i}`} x1={i * 108} x2={i * 108} y1={0} y2={1920} stroke="rgba(0,224,130,0.03)" strokeWidth={1} />
        ))}
        {Array.from({length: 19}, (_, i) => (
          <line key={`h${i}`} x1={0} x2={1080} y1={i * 108} y2={i * 108} stroke="rgba(0,224,130,0.03)" strokeWidth={1} />
        ))}
      </svg>

      {/* --------------------------------------------------------- masthead */}
      <div style={{position: 'absolute', top: 38, left: 0, right: 0, textAlign: 'center'}}>
        <div style={{fontFamily: FONT.mono, fontSize: 19, letterSpacing: 6, color: PT.steel, fontWeight: 700}}>
          MAYA LAB
        </div>
        <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 66, color: PT.ink, letterSpacing: -1, lineHeight: 1.02}}>
          CHART <span style={{color: '#9FC2E8'}}>PATTERNS</span>
        </div>
        <div style={{fontFamily: FONT.mono, fontSize: 19, color: PT.steel, marginTop: 8, letterSpacing: 1.6}}>
          {cells.length} real SPY formations · {tries > 0 ? `${wins} of ${tries} reached target · ` : ''}real dates
        </div>
      </div>

      {/* --------------------------------------------------------- the grid */}
      {cells.map((card, i) => {
        const col = i % COLS;
        const row = Math.floor(i / COLS);
        const x = GAP + col * (CELL_W + GAP);
        const y = GRID_TOP + row * (CELL_H + GAP);
        const at = 10 + i * STAGGER;
        const land = at + LAND;
        // THE SMASH. The box falls INTO the sheet from above the screen plane:
        // it starts big and translucent (near the lens), slams to size on the
        // landing frame, and the settle overshoots — a body hitting a surface,
        // not a fade-in. The impact ring below and the frame kick sell the
        // weight; the chart only starts drawing after the box has landed.
        const drop = interpolate(frame, [at, land], [0, 1], {
          easing: EASE.exit, // accelerating — falling
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        const settle = interpolate(frame, [land, land + 9], [1.045, 1], {
          easing: EASE.settleBack,
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        const scale = frame < land ? 1.75 - 0.75 * drop : settle;
        const opacity = frame < at ? 0 : frame < land ? 0.25 + 0.75 * drop : 1;
        return (
          <div
            key={card.id}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: CELL_W,
              height: CELL_H,
              opacity,
              transform: `scale(${scale})`,
              transformOrigin: '50% 50%',
              filter: frame >= at && frame < land ? 'blur(2px)' : undefined,
            }}
          >
            <Sequence from={land} layout="none">
              <PatternCell data={card} width={CELL_W} height={CELL_H} />
            </Sequence>
            {/* pre-landing face: the falling slab shows only its shell */}
            {frame >= at && frame < land ? (
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  borderRadius: 12,
                  border: `1.4px solid ${PT.edge}`,
                  background: 'linear-gradient(#04100C, #020806)',
                }}
              />
            ) : null}
          </div>
        );
      })}

      {/* impact rings on each landing — the sheet surface reacting */}
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, pointerEvents: 'none'}}>
        {cells.map((card, i) => {
          const col = i % COLS;
          const row = Math.floor(i / COLS);
          const cxp = GAP + col * (CELL_W + GAP) + CELL_W / 2;
          const cyp = GRID_TOP + row * (CELL_H + GAP) + CELL_H / 2;
          const land = 10 + i * STAGGER + LAND;
          const t = (frame - land) / 14;
          if (t < 0 || t > 1) return null;
          const r = interpolate(t, [0, 1], [60, 330], {easing: EASE.exit});
          const op = interpolate(t, [0, 0.15, 1], [0, 0.55, 0]);
          return (
            <g key={card.id} opacity={op}>
              <rect
                x={cxp - CELL_W / 2 - 20 * t}
                y={cyp - CELL_H / 2 - 20 * t}
                width={CELL_W + 40 * t}
                height={CELL_H + 40 * t}
                rx={14}
                fill="none"
                stroke={PT.ice}
                strokeWidth={2.5 * (1 - t)}
              />
              <circle cx={cxp} cy={cyp} r={r} fill="none" stroke="rgba(0,224,130,0.5)" strokeWidth={3 * (1 - t)} />
            </g>
          );
        })}
      </svg>

      </AbsoluteFill>

      <Vignette strength={0.24} />
      <Grain opacity={0.038} />

      {/* footer — provenance + rails, every frame */}
      <div
        style={{
          position: 'absolute',
          left: 40,
          right: 40,
          bottom: 20,
          textAlign: 'center',
          fontFamily: FONT.mono,
          fontSize: 16.5,
          color: '#7FA290',
          letterSpacing: 0.4,
          lineHeight: 1.45,
        }}
      >
        {p.footer}
      </div>

      {/* sound: an impact on every landing (ten hits eighteen frames apart —
          a drum pattern), a blip as each breakout prints, and a COIN on each
          real target fill. Winners only, so every box earns its coin. */}
      {cells.map((card, i) => {
        const start = 10 + i * STAGGER;
        const land = start + LAND;
        const breakAt = land + 178;
        const tpLocal = cellTpFrame(card);
        const up = card.bias === 'bullish';
        return (
          <React.Fragment key={`au${card.id}`}>
            <Sequence from={land} durationInFrames={14}>
              <Audio src={staticFile('audio/impact.wav')} volume={0.4} />
            </Sequence>
            <Sequence from={breakAt} durationInFrames={12}>
              <Audio src={staticFile(up ? 'audio/candle_up.wav' : 'audio/candle_down.wav')} volume={0.3} />
            </Sequence>
            {tpLocal !== null ? (
              <Sequence from={land + tpLocal} durationInFrames={26}>
                <Audio src={staticFile('audio/coin.wav')} volume={0.32} />
              </Sequence>
            ) : null}
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};
