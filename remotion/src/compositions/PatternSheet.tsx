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
import {PatternCell} from '../components/PatternCell';

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
const PICK = [
  'Double Top',
  'Double Bottom',
  'Head and Shoulders',
  'Inverse Head and Shoulders',
  'Bull Flag',
  'Bear Flag',
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
const STAGGER = 16; // frames between box starts — a ripple, not a queue

export const PatternSheet: React.FC<PatternSheetProps> = (p) => {
  const frame = useCurrentFrame();

  const byName: Record<string, PatternData> = {};
  for (const ch of p.chapters) for (const c of ch.cards as PatternData[]) byName[c.name] = c;
  const cells = PICK.map((n) => byName[n]).filter(Boolean);

  return (
    <AbsoluteFill style={{backgroundColor: PT.bg}}>
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
          10 real formations · found in SPY · real dates
        </div>
      </div>

      {/* --------------------------------------------------------- the grid */}
      {cells.map((card, i) => {
        const col = i % COLS;
        const row = Math.floor(i / COLS);
        const x = GAP + col * (CELL_W + GAP);
        const y = GRID_TOP + row * (CELL_H + GAP);
        const at = 10 + i * STAGGER;
        // the box itself lands first — a quick pop, then its chart draws
        const inP = interpolate(frame, [at - 8, at + 2], [0, 1], {
          easing: EASE.settleBack,
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        return (
          <div
            key={card.id}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: CELL_W,
              height: CELL_H,
              opacity: Math.min(1, inP * 1.4),
              transform: `scale(${0.92 + 0.08 * inP})`,
              transformOrigin: '50% 50%',
            }}
          >
            <Sequence from={at} layout="none">
              <PatternCell data={card} width={CELL_W} height={CELL_H} />
            </Sequence>
          </div>
        );
      })}

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

      {/* one blip per box as its breakout prints — sparse under any track */}
      {cells.map((card, i) => {
        const at = 10 + i * STAGGER + 178; // cell-local setupEnd+8 ≈ first reveal bar
        const up = card.bias === 'bullish';
        return (
          <Sequence key={`au${card.id}`} from={at} durationInFrames={12}>
            <Audio src={staticFile(up ? 'audio/candle_up.wav' : 'audio/candle_down.wav')} volume={0.3} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
