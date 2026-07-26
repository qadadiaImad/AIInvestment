// TradingStyles.tsx — long-form "Find Your Trading Style" explainer (9:16, 2:20).
//
// Ten trading styles, each given a full 12-second scene with its own animated
// chart simulation. The premise the whole piece rests on: no style is better
// than another, the right one depends on the viewer's available time,
// temperament and goals. Nothing here ranks them.
//
// Every chart is REAL. scripts/trading_styles/find_real_windows.py scans actual
// IBKR bars and keeps only windows that already pass the structural test for
// their regime — a range that genuinely tests both boundaries, a breakout that
// genuinely closes beyond its box, an event bar that genuinely gaps. A regime
// with no qualifying real window is reported UNMATCHED rather than fabricated.
// Each scene names its instrument, timeframe and date range on screen.
//
// One renderer, ten data payloads. The scene component below draws any regime
// from its bars plus optional overlays (levels, moving average, an event flag,
// signal ticks, an allocation ring), so adding a style is a data change.
//
// Visual language: green trading-terminal on near-black — ruled grid, a dotted
// world map behind everything, glowing candles, boxed SUPPORT/RESISTANCE tags,
// a moving average, and an activity histogram under the plot.
//
// The histogram is TRUE RANGE, not volume, and is labelled as such. Volume was
// not transcribed with these bars, and drawing an invented volume series under
// a chart of real prices would be the one dishonest pixel in the whole piece.
// True range is derived from the same real OHLC.
import React from 'react';
import {AbsoluteFill, interpolate, random, Sequence, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {z} from 'zod';
import {C, FONT} from '../slides/theme';
import {EASE, SPRINGS, fadeOf} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';

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
  hist: 'rgba(0,224,130,0.30)',
};

// Per-style accent. Carries identity, not sentiment — these are chapter
// colours, never a judgement about the style.
// One green family, not ten hues. The reference board is monochrome green and
// a rainbow would also read as ranking the styles.
const ACCENTS = [
  '#00E676', '#2BE59A', '#00D9A3', '#4CE68A', '#00E676',
  '#7BEF7B', '#00E0B0', '#3DDC84', '#5CE68F', '#00E676',
];

const barSchema = z.object({o: z.number(), h: z.number(), l: z.number(), c: z.number()});

const markerSchema = z.object({
  kind: z.enum(['entry', 'exit', 'event', 'level']),
  bar: z.number(),
  label: z.string(),
});

const styleSchema = z.object({
  n: z.number(),
  name: z.string(),
  timeframe: z.string(),
  hold: z.string(),
  oneLiner: z.string(),
  bullets: z.array(z.string()),
  demands: z.string(),
  regime: z.string(),
  markers: z.array(markerSchema),
});

const regimeSchema = z.object({
  bars: z.array(barSchema),
  levels: z.array(z.number()).optional(),
  ma: z.array(z.number()).optional(),
  signals: z.array(z.number()).optional(),
  eventAt: z.number().optional(),
  breakAt: z.number().optional(),
  sessionSplit: z.array(z.number()).optional(),
  allocation: z.array(z.object({label: z.string(), pct: z.number()})).optional(),
  note: z.string().optional(),
  symbol: z.string().optional(),
  interval: z.string().optional(),
  from: z.string().optional(),
  to: z.string().optional(),
  retrieved_at: z.string().optional(),
  source: z.string().optional(),
});

export const tradingStylesSchema = z.object({
  title: z.string(),
  subtitle: z.string(),
  outroTitle: z.string(),
  outroLine: z.string(),
  footer: z.string(),
  styles: z.array(styleSchema),
  regimes: z.record(z.string(), regimeSchema),
  durationInFrames: z.number(),
});
export type TradingStylesProps = z.infer<typeof tradingStylesSchema>;

// ---------------------------------------------------------------- timing
export const INTRO = 300;      // 10s
export const SCENE = 360;      // 12s per style
export const OUTRO = 300;      // 10s
export const TRADING_STYLES_FRAMES = INTRO + SCENE * 10 + OUTRO; // 4200 = 2:20

// Beats inside one 12s scene.
const S = {
  cardIn: 0,
  chartIn: 26,
  drawStart: 40,
  // 2.2 frames/bar: even the 60-bar regime finishes by frame ~172, which leaves
  // the back half of the scene for the copy to breathe rather than arriving in
  // the last two seconds.
  drawPer: 2.2,
  levelIn: 120,
  markersIn: 158,
  bulletsIn: 196,
  demandsIn: 244,
  out: 344,
};

// ---------------------------------------------------------------- geometry
const PLOT = {x0: 92, x1: 988, y0: 560, y1: 1090};
const HIST = {y: 1118, h: 86};
const PANEL = {x: 46, y: 462, w: 988, h: 762};

// ------------------------------------------------------------ shared chrome
// Coarse equirectangular landmass mask, 64 columns x 26 rows, drawn as a dot
// matrix behind the whole piece. It is deliberately crude — at ~6% opacity it
// is texture that reads as "global markets", not a map anyone should navigate by.
const WORLD = [
  '................................................................',
  '.......########....................#####........................',
  '....###############..........################################...',
  '...###############.........###############################......',
  '....#############........###############################.......',
  '.....###########........##############################.........',
  '......########..........############################...........',
  '.......######............#########.####..#########.............',
  '........####..............#######...##....######...............',
  '.........###...............#####...........####................',
  '.........####...............####............###................',
  '..........####...............###.............##................',
  '..........####................##..............#................',
  '...........###.................#..............................',
  '...........###.................##.............................',
  '...........###.................###...........#####.............',
  '...........##..................####.........########...........',
  '...........##..................####........##########..........',
  '............#..................###.........#########...........',
  '............#..................###..........#######............',
  '............#..................##............#####.............',
  '...............................##.............###.............',
  '................................#..............#..............',
  '................................................................',
  '....................######################......................',
  '................................................................',
];

const BoardGrid: React.FC<{frame: number}> = ({frame}) => {
  const dots: {x: number; y: number}[] = [];
  const cw = 1080 / WORLD[0].length;
  const ch = 1120 / WORLD.length;
  WORLD.forEach((row, r) =>
    row.split('').forEach((ch2, c) => {
      if (ch2 === '#') dots.push({x: c * cw + cw / 2, y: 300 + r * ch + ch / 2});
    })
  );
  return (
    <AbsoluteFill>
      {/* dotted world behind everything */}
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, opacity: 0.9}}>
        {dots.map((d, i) => (
          <circle
            key={i}
            cx={d.x}
            cy={d.y}
            r={2.1}
            fill={T.up}
            opacity={0.055 + Math.sin(frame / 40 + i * 0.35) * 0.02}
          />
        ))}
      </svg>
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
            'radial-gradient(120% 55% at 50% 6%, rgba(0,224,130,0.10), transparent 60%),' +
            'radial-gradient(110% 50% at 20% 100%, rgba(0,224,130,0.09), transparent 62%),' +
            'radial-gradient(110% 50% at 85% 100%, rgba(255,59,48,0.06), transparent 62%)',
        }}
      />
    </AbsoluteFill>
  );
};

const Footer: React.FC<{text: string}> = ({text}) => (
  <div
    style={{
      position: 'absolute',
      bottom: 62,
      left: 46,
      right: 46,
      display: 'flex',
      borderTop: `1px solid ${T.edge}`,
      paddingTop: 16,
    }}
  >
    {text.split('·').map((cell, i, all) => (
      <div
        key={cell}
        style={{
          flex: 1,
          textAlign: 'center',
          padding: '0 14px',
          borderRight: i < all.length - 1 ? `1px solid ${T.edge}` : undefined,
          fontFamily: FONT.mono,
          fontSize: 18,
          lineHeight: 1.35,
          color: T.steel,
        }}
      >
        {cell.trim()}
      </div>
    ))}
  </div>
);

// ------------------------------------------------------------------ scene
const StyleScene: React.FC<{
  s: z.infer<typeof styleSchema>;
  r: z.infer<typeof regimeSchema>;
  accent: string;
}> = ({s, r, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const bars = r.bars;

  const lo = Math.min(...bars.map((b) => b.l));
  const hi = Math.max(...bars.map((b) => b.h));
  const pad = (hi - lo) * 0.08;
  const toY = (v: number) =>
    PLOT.y1 - ((v - (lo - pad)) / (hi + pad - (lo - pad))) * (PLOT.y1 - PLOT.y0);
  const slot = (PLOT.x1 - PLOT.x0) / bars.length;
  const cx = (i: number) => PLOT.x0 + slot * i + slot / 2;
  const bodyW = Math.max(3, Math.min(18, slot * 0.62));

  const cardP = spring({frame: frame - S.cardIn, fps, config: SPRINGS.hero});
  const chartP = spring({frame: frame - S.chartIn, fps, config: SPRINGS.heavy});
  const outP = interpolate(frame, [S.out, S.out + 16], [1, 0], {
    easing: EASE.exit,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const drawn = Math.max(0, Math.floor((frame - S.drawStart) / S.drawPer) + 1);

  // Same hard-tick print as TradingQuiz: bars jump, they don't ease.
  const TICKS = 3;
  const FORM = Math.max(2, Math.round(S.drawPer));
  const renderBar = (b: z.infer<typeof barSchema>, i: number) => {
    const appearAt = S.drawStart + i * S.drawPer;
    const raw = (frame - appearAt) / FORM;
    if (raw <= 0) return null;
    const step = Math.min(TICKS, Math.ceil(Math.min(1, raw) * TICKS));
    const settled = step >= TICKS;
    const f = step / TICKS;
    const hN = b.o + (b.h - b.o) * Math.min(1, f * 1.22);
    const lN = b.o + (b.l - b.o) * Math.min(1, f * 1.22);
    const drift = (random(`${s.n}b${i}t${step}`) - 0.5) * (b.h - b.l) * 0.7;
    const cN = settled ? b.c : Math.max(lN, Math.min(hN, b.o + (b.c - b.o) * f + drift));
    const col = cN >= b.o ? T.up : T.down;
    const x = cx(i);
    const yT = toY(Math.max(b.o, cN));
    const yB = toY(Math.min(b.o, cN));
    return (
      <g key={i} style={{filter: `drop-shadow(0 0 ${settled ? 6 : 12}px ${col}${settled ? 'aa' : 'ee'})`}}>
        <line x1={x} x2={x} y1={toY(hN)} y2={toY(lN)} stroke={col} strokeWidth={1.8} />
        <rect x={x - bodyW / 2} y={yT} width={bodyW} height={Math.max(2, yB - yT)} rx={1.5} fill={col} />
      </g>
    );
  };

  const levelP = interpolate(frame, [S.levelIn, S.levelIn + 20], [0, 1], {
    easing: EASE.enter,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const markP = spring({frame: frame - S.markersIn, fps, config: SPRINGS.pop});
  const bulletsP = spring({frame: frame - S.bulletsIn, fps, config: SPRINGS.heavy});
  const demandsP = spring({frame: frame - S.demandsIn, fps, config: SPRINGS.heavy});

  // Moving average, drawn only as far as the bars have printed.
  const maPath = r.ma
    ? r.ma
        .slice(0, Math.min(drawn, r.ma.length))
        .map((v, i) => `${i === 0 ? 'M' : 'L'}${cx(i).toFixed(1)},${toY(v).toFixed(1)}`)
        .join(' ')
    : '';

  return (
    <AbsoluteFill style={{opacity: outP}}>
      {/* ---- number + name ---- */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 62,
          right: 62,
          opacity: fadeOf(cardP),
          transform: `translateY(${interpolate(cardP, [0, 1], [26, 0])}px)`,
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', gap: 22}}>
          <div
            style={{
              width: 92,
              height: 92,
              borderRadius: 22,
              background: accent,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: FONT.display,
              fontWeight: 700,
              fontSize: 52,
              color: T.bg,
              boxShadow: `0 0 46px ${accent}55`,
              flexShrink: 0,
            }}
          >
            {s.n}
          </div>
          <div style={{minWidth: 0}}>
            <div
              style={{
                fontFamily: FONT.display,
                fontWeight: 700,
                fontSize: s.name.length > 16 ? 62 : 76,
                lineHeight: 1.02,
                color: C.ink,
                letterSpacing: -1.5,
              }}
            >
              {s.name}
            </div>
            <div style={{fontFamily: FONT.body, fontWeight: 500, fontSize: 31, color: T.ice, marginTop: 8}}>
              {s.oneLiner}
            </div>
          </div>
        </div>

        {/* timeframe / hold, the two facts from the reference card */}
        <div style={{display: 'flex', gap: 14, marginTop: 26}}>
          {[
            {k: 'TIMEFRAME', v: s.timeframe},
            {k: 'HOLD', v: s.hold},
          ].map((f) => (
            <div
              key={f.k}
              style={{
                flex: 1,
                border: `1px solid ${T.edge}`,
                borderRadius: 16,
                padding: '13px 18px',
                background: 'rgba(126,158,201,.05)',
              }}
            >
              <div style={{fontFamily: FONT.mono, fontSize: 17, letterSpacing: 2.5, color: T.steel}}>{f.k}</div>
              <div style={{fontFamily: FONT.mono, fontWeight: 700, fontSize: 25, color: C.ink, marginTop: 5}}>
                {f.v}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ---- the terminal ---- */}
      <div
        style={{
          position: 'absolute',
          left: PANEL.x,
          top: PANEL.y,
          width: PANEL.w,
          height: PANEL.h,
          borderRadius: 26,
          opacity: fadeOf(chartP),
          transform: `translateY(${interpolate(chartP, [0, 1], [22, 0])}px)`,
          background: `linear-gradient(180deg, ${T.panelTop} 0%, ${T.panelBot} 100%)`,
          border: `1px solid ${T.edge}`,
          boxShadow: `0 36px 90px -30px #000, inset 0 1px 0 rgba(255,255,255,.05), 0 0 60px ${accent}12`,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: 48,
            display: 'flex',
            alignItems: 'center',
            gap: 9,
            padding: '0 20px',
            borderBottom: `1px solid ${T.edge}`,
            background: 'rgba(126,158,201,.045)',
          }}
        >
          {[T.down, '#E0A23B', T.up].map((c) => (
            <div key={c} style={{width: 10, height: 10, borderRadius: 999, background: c, opacity: 0.55}} />
          ))}
          <div style={{marginLeft: 10, fontFamily: FONT.mono, fontSize: 17, letterSpacing: 2, color: T.steel}}>
            {r.symbol ?? 'SPY'} · {(r.interval ?? '1d').toUpperCase()} · {r.from} → {r.to}
          </div>
          {/* Every regime is normalised to fill the plot, or a scalping chart
           * would be a flat line and unreadable for twelve seconds. That makes
           * a 1.9-point microrange LOOK as violent as a 35-point trend, so the
           * actual span is stated numerically — the shape is comparable, the
           * scale is not, and the viewer is told which is which. */}
          <div
            style={{
              marginLeft: 16,
              fontFamily: FONT.mono,
              fontSize: 16,
              letterSpacing: 1,
              color: T.ice,
              opacity: 0.85,
            }}
          >
            {bars.length} bars · span ${(hi - lo).toFixed(2)}
          </div>
          <div style={{marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 7}}>
            <div
              style={{
                width: 7,
                height: 7,
                borderRadius: 999,
                background: accent,
                opacity: 0.4 + Math.sin(frame / 8) * 0.35,
              }}
            />
            <div style={{fontFamily: FONT.mono, fontSize: 15, letterSpacing: 2, color: T.steel}}>LIVE</div>
          </div>
        </div>
        <AbsoluteFill
          style={{
            pointerEvents: 'none',
            background:
              'repeating-linear-gradient(0deg, rgba(255,255,255,.018) 0px, rgba(255,255,255,.018) 1px, transparent 1px, transparent 4px)',
          }}
        />
      </div>

      {/* ---- plot ---- */}
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        {/* session split guides (day trading) */}
        {r.sessionSplit && chartP > 0
          ? r.sessionSplit.map((f, i) => (
              <line
                key={`ss${i}`}
                x1={PLOT.x0 + (PLOT.x1 - PLOT.x0) * f}
                x2={PLOT.x0 + (PLOT.x1 - PLOT.x0) * f}
                y1={PLOT.y0 - 14}
                y2={PLOT.y1 + 10}
                stroke={T.edge}
                strokeWidth={1}
                strokeDasharray="5 7"
                opacity={levelP * 0.9}
              />
            ))
          : null}

        {/* activity histogram — TRUE RANGE of each real bar, not volume */}
        {chartP > 0
          ? bars.slice(0, drawn).map((b, i) => {
              const maxTr = Math.max(...bars.map((x) => x.h - x.l)) || 1;
              const hgt = ((b.h - b.l) / maxTr) * (HIST.h - 4);
              return (
                <rect
                  key={`tr${i}`}
                  x={cx(i) - bodyW / 2}
                  y={HIST.y + HIST.h - hgt}
                  width={bodyW}
                  height={Math.max(1, hgt)}
                  fill={T.hist}
                />
              );
            })
          : null}
        {chartP > 0 ? (
          <text x={PLOT.x0 - 6} y={HIST.y - 6} fill={T.steel} fontFamily={FONT.mono} fontSize={15} letterSpacing={2}>
            TRUE RANGE
          </text>
        ) : null}

        {/* structural levels, tagged the way the reference board does it */}
        {r.levels && levelP > 0
          ? r.levels.map((v, i) => {
              const top = i === 0;
              const tag = r.levels && r.levels.length > 1 ? (top ? 'RESISTANCE' : 'SUPPORT') : 'LEVEL';
              const w = tag.length * 12 + 26;
              return (
                <g key={`lv${i}`} opacity={levelP}>
                  <line
                    x1={PLOT.x0 - 8}
                    x2={PLOT.x0 - 8 + (PLOT.x1 + 8 - (PLOT.x0 - 8)) * levelP}
                    y1={toY(v)}
                    y2={toY(v)}
                    stroke={T.up}
                    strokeWidth={2}
                    strokeDasharray="12 9"
                    style={{filter: `drop-shadow(0 0 8px ${T.up}cc)`}}
                  />
                  <rect
                    x={PLOT.x1 - w}
                    y={toY(v) + (top ? -40 : 10)}
                    width={w}
                    height={30}
                    rx={7}
                    fill="rgba(2,10,7,.85)"
                    stroke={T.up}
                    strokeWidth={1.4}
                  />
                  <text
                    x={PLOT.x1 - w / 2}
                    y={toY(v) + (top ? -19 : 31)}
                    fill={T.up}
                    fontFamily={FONT.mono}
                    fontWeight={700}
                    fontSize={17}
                    letterSpacing={1.5}
                    textAnchor="middle"
                  >
                    {tag}
                  </text>
                  <text
                    x={PLOT.x0 - 10}
                    y={toY(v) - 8}
                    fill={T.up}
                    fontFamily={FONT.mono}
                    fontWeight={700}
                    fontSize={17}
                    textAnchor="start"
                    opacity={0.8}
                  >
                    {v.toFixed(1)}
                  </text>
                </g>
              );
            })
          : null}

        {/* moving average */}
        {maPath ? (
          <path d={maPath} fill="none" stroke={T.ice} strokeWidth={2.5} opacity={0.9} strokeLinecap="round" style={{filter: `drop-shadow(0 0 8px ${T.ice}aa)`}} />
        ) : null}

        {bars.map(renderBar)}

        {/* systematic signal ticks — one rule, fired mechanically */}
        {r.signals && markP > 0
          ? r.signals
              .filter((i) => i < drawn)
              .map((i) => (
                <g key={`sg${i}`} opacity={fadeOf(markP)}>
                  <circle cx={cx(i)} cy={toY(bars[i].c)} r={7} fill="none" stroke={T.ice} strokeWidth={2.5} style={{filter: `drop-shadow(0 0 7px ${T.ice}cc)`}} />
                  <circle cx={cx(i)} cy={toY(bars[i].c)} r={2.5} fill={T.ice} />
                </g>
              ))
          : null}

        {/* event flag — news */}
        {r.eventAt !== undefined && markP > 0 && drawn > r.eventAt ? (
          <g opacity={fadeOf(markP)}>
            <line
              x1={cx(r.eventAt)}
              x2={cx(r.eventAt)}
              y1={PLOT.y0 - 12}
              y2={PLOT.y1 + 8}
              stroke={T.ice}
              strokeWidth={2}
              strokeDasharray="6 6"
              opacity={0.8}
            />
            <rect x={cx(r.eventAt) - 52} y={PLOT.y0 - 44} width={104} height={30} rx={7} fill={T.ice} />
            <text
              x={cx(r.eventAt)}
              y={PLOT.y0 - 23}
              fill={T.bg}
              fontFamily={FONT.mono}
              fontWeight={800}
              fontSize={17}
              textAnchor="middle"
            >
              THE PRINT
            </text>
          </g>
        ) : null}

        {/* trade markers */}
        {markP > 0
          ? s.markers
              .filter((m) => m.kind === 'entry' || m.kind === 'exit')
              .map((m, i) => {
                // Absolute bar index, computed against the real series by the
                // generator — not a fraction guessed by a model.
                const bi = Math.max(0, Math.min(bars.length - 1, Math.round(m.bar)));
                if (bi >= drawn) return null;
                const isEntry = m.kind === 'entry';
                const col = isEntry ? T.up : T.down;
                const y = toY(isEntry ? bars[bi].l : bars[bi].h);
                const dy = isEntry ? 30 : -30;
                const p = spring({frame: frame - S.markersIn - i * 4, fps, config: SPRINGS.pop});
                return (
                  <g key={`mk${i}`} opacity={fadeOf(p)}>
                    <polygon
                      points={
                        isEntry
                          ? `${cx(bi)},${y + 12} ${cx(bi) - 9},${y + 26} ${cx(bi) + 9},${y + 26}`
                          : `${cx(bi)},${y - 12} ${cx(bi) - 9},${y - 26} ${cx(bi) + 9},${y - 26}`
                      }
                      fill={col}
                      style={{filter: `drop-shadow(0 0 8px ${col}aa)`}}
                    />
                    <text
                      x={cx(bi)}
                      y={y + dy + (isEntry ? 24 : -18)}
                      fill={col}
                      fontFamily={FONT.mono}
                      fontWeight={800}
                      fontSize={18}
                      textAnchor="middle"
                    >
                      {m.label}
                    </text>
                  </g>
                );
              })
          : null}
      </svg>

      {/* ---- allocation ring (portfolio scene only) ---- */}
      {r.allocation && markP > 0 ? (
        <div
          style={{
            position: 'absolute',
            right: 74,
            top: 590,
            display: 'flex',
            flexDirection: 'column',
            gap: 9,
            opacity: fadeOf(markP),
          }}
        >
          {r.allocation.map((a, i) => (
            <div key={a.label} style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <div
                style={{
                  width: interpolate(markP, [0, 1], [0, a.pct * 2.6]),
                  height: 15,
                  borderRadius: 4,
                  background: ACCENTS[i * 2],
                }}
              />
              <div style={{fontFamily: FONT.mono, fontSize: 17, color: T.steel, whiteSpace: 'nowrap'}}>
                {a.label} {a.pct}%
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {/* ---- bullets ---- */}
      <div
        style={{
          position: 'absolute',
          top: 1268,
          left: 56,
          right: 56,
          opacity: fadeOf(bulletsP),
          transform: `translateY(${interpolate(bulletsP, [0, 1], [22, 0])}px)`,
          display: 'flex',
          gap: 14,
        }}
      >
        {s.bullets.map((b, i) => (
          <div
            key={b}
            style={{
              flex: 1,
              border: `1px solid ${T.edge}`,
              borderRadius: 18,
              padding: '17px 20px',
              background: 'rgba(126,158,201,.06)',
              fontFamily: FONT.body,
              fontWeight: 500,
              fontSize: 27,
              lineHeight: 1.26,
              color: C.ink,
              borderLeft: `3px solid ${accent}`,
            }}
          >
            {b}
          </div>
        ))}
      </div>

      {/* ---- what it demands ---- */}
      <div
        style={{
          position: 'absolute',
          top: 1440,
          left: 56,
          right: 56,
          opacity: fadeOf(demandsP),
          transform: `translateY(${interpolate(demandsP, [0, 1], [18, 0])}px)`,
        }}
      >
        <div style={{fontFamily: FONT.mono, fontSize: 19, letterSpacing: 3, color: accent, marginBottom: 9}}>
          WHAT IT ASKS OF YOU
        </div>
        <div style={{fontFamily: FONT.display, fontWeight: 600, fontSize: 38, lineHeight: 1.2, color: C.ink}}>
          {s.demands}
        </div>
      </div>

      {/* progress rail — ten chapters, this is where you are */}
      <div style={{position: 'absolute', top: 108, left: 62, right: 62, display: 'flex', gap: 6}}>
        {Array.from({length: 10}, (_, i) => (
          <div
            key={i}
            style={{
              flex: 1,
              height: 4,
              borderRadius: 999,
              background: i < s.n - 1 ? T.edge : i === s.n - 1 ? accent : 'rgba(126,158,201,.10)',
              opacity: i === s.n - 1 ? 1 : 0.8,
            }}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------- intro
const Intro: React.FC<{title: string; subtitle: string; names: string[]}> = ({title, subtitle, names}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = spring({frame, fps, config: SPRINGS.hero});
  const b = spring({frame: frame - 22, fps, config: SPRINGS.heavy});
  const out = interpolate(frame, [INTRO - 26, INTRO - 4], [1, 0], {
    easing: EASE.exit,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill style={{opacity: out, alignItems: 'center', justifyContent: 'center', padding: '0 70px'}}>
      <div
        style={{
          fontFamily: FONT.mono,
          fontSize: 22,
          letterSpacing: 5,
          color: T.ice,
          border: `1px solid ${T.edge}`,
          borderRadius: 999,
          padding: '8px 22px',
          opacity: fadeOf(a),
        }}
      >
        MAYA LAB
      </div>
      <div
        style={{
          fontFamily: FONT.display,
          fontWeight: 700,
          fontSize: 108,
          lineHeight: 0.98,
          letterSpacing: -3,
          color: C.ink,
          textAlign: 'center',
          marginTop: 26,
          opacity: fadeOf(a),
          transform: `scale(${interpolate(a, [0, 1], [0.9, 1])})`,
        }}
      >
        {title.split(' ').slice(0, -1).join(' ')}{' '}
        <span style={{color: T.ice}}>{title.split(' ').slice(-1)}</span>
      </div>
      <div
        style={{
          fontFamily: FONT.body,
          fontWeight: 500,
          fontSize: 34,
          lineHeight: 1.3,
          color: T.steel,
          textAlign: 'center',
          marginTop: 26,
          opacity: fadeOf(b),
        }}
      >
        {subtitle}
      </div>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 10,
          justifyContent: 'center',
          marginTop: 46,
          maxWidth: 900,
        }}
      >
        {names.map((n, i) => {
          const p = spring({frame: frame - 46 - i * 5, fps, config: SPRINGS.snappy});
          return (
            <div
              key={n}
              style={{
                fontFamily: FONT.mono,
                fontSize: 21,
                letterSpacing: 1.5,
                color: C.ink,
                border: `1px solid ${T.edge}`,
                borderRadius: 999,
                padding: '9px 18px',
                background: 'rgba(126,158,201,.05)',
                opacity: fadeOf(p),
                transform: `translateY(${interpolate(p, [0, 1], [16, 0])}px)`,
              }}
            >
              {n}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------- outro
const Outro: React.FC<{title: string; line: string}> = ({title, line}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = spring({frame, fps, config: SPRINGS.hero});
  const b = spring({frame: frame - 26, fps, config: SPRINGS.heavy});
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', padding: '0 76px'}}>
      <div
        style={{
          fontFamily: FONT.display,
          fontWeight: 700,
          fontSize: 82,
          lineHeight: 1.04,
          letterSpacing: -2,
          color: C.ink,
          textAlign: 'center',
          opacity: fadeOf(a),
          transform: `scale(${interpolate(a, [0, 1], [0.9, 1])})`,
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontFamily: FONT.body,
          fontWeight: 500,
          fontSize: 36,
          lineHeight: 1.34,
          color: T.ice,
          textAlign: 'center',
          marginTop: 30,
          opacity: fadeOf(b),
        }}
      >
        {line}
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------- root
export const TradingStyles: React.FC<TradingStylesProps> = (p) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: T.bg, fontFamily: FONT.body}}>
      <BoardGrid frame={frame} />

      <Sequence durationInFrames={INTRO}>
        <Intro title={p.title} subtitle={p.subtitle} names={p.styles.map((s) => s.name)} />
      </Sequence>

      {p.styles.map((s, i) => (
        <Sequence key={s.n} from={INTRO + i * SCENE} durationInFrames={SCENE}>
          <StyleScene s={s} r={p.regimes[s.regime]} accent={ACCENTS[i % ACCENTS.length]} />
        </Sequence>
      ))}

      <Sequence from={INTRO + SCENE * p.styles.length} durationInFrames={OUTRO}>
        <Outro title={p.outroTitle} line={p.outroLine} />
      </Sequence>

      <Footer text={p.footer} />
      <Grain />
      <Vignette />
    </AbsoluteFill>
  );
};
