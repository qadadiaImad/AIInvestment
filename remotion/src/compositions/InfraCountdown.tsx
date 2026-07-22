// InfraCountdown.tsx — "same sector, four completely different prices vs
// fundamentals" countdown reel. Tickers reveal worst -> best (by discount to
// modeled fair value); each one expands into a 5-stat table, Chip points at
// it, then it collapses into a compact chip that slots into the FRONT of a
// horizontal ranking rail (every new reveal is the new best-so-far, so it
// always takes slot 0 and pushes earlier chips one slot right — see
// rampedSlot in motion/craft.ts). Finale: full rail, Chip celebrates.
//
// 9:16, built entirely on the motion-craft library (EASE/SPRINGS/FRAMES/
// stagger/rampedSlot) + the Polish finish layers, per
// references/animation-craft-playbook.md.
import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {z} from 'zod';
import {C, FONT} from '../slides/theme';
import {RIGS} from './FamilyRigShowcase';
import {EASE, SPRINGS, stagger, fadeOf, cameraPushIn, rampedSlot} from '../motion/craft';
import {Grain, Vignette} from '../motion/Polish';

const tickerSchema = z.object({
  sym: z.string(),
  name: z.string(),
  price: z.number(),
  fair: z.number(),
  discountPct: z.number(), // + = undervalued, - = overvalued
  verdict: z.string(),
  netMargin: z.number(),
  debtEquity: z.number(),
});

export const infraCountdownSchema = z.object({
  bgSrc: z.string(),
  kick: z.string(),
  title: z.string(),
  tagline: z.string(),
  footer: z.string(),
  // reveal order = worst -> best (last-ranked revealed first, finale = #1)
  tickers: z.array(tickerSchema).min(2).max(6),
  durationInFrames: z.number(),
});
export type InfraCountdownProps = z.infer<typeof infraCountdownSchema>;

// ---------------------------------------------------------------- timing
const INTRO_END = 70;
const SEGMENT_LEN = 200;
const COLLAPSE_START = 155;
const COLLAPSE_LEN = 40; // -> lands at local 195, 5f before next segment

const segmentStart = (i: number) => INTRO_END + i * SEGMENT_LEN;
const insertFrameOf = (i: number) => segmentStart(i) + COLLAPSE_START + COLLAPSE_LEN;

// ------------------------------------------------------------ stat card
const Stat: React.FC<{label: string; value: string; tone?: 'good' | 'bad' | 'neutral'; delay: number; frame: number; fps: number}> = ({
  label,
  value,
  tone = 'neutral',
  delay,
  frame,
  fps,
}) => {
  const p = spring({frame: frame - delay, fps, config: SPRINGS.pop});
  const color = tone === 'good' ? C.emerald : tone === 'bad' ? C.redHot : C.ink;
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'baseline',
        width: '100%',
        opacity: fadeOf(p),
        translate: `${(1 - Math.min(1, p)) * 22}px 0px`,
      }}
    >
      <span style={{fontFamily: FONT.body, fontWeight: 500, fontSize: 30, color: C.muted}}>{label}</span>
      <span style={{fontFamily: FONT.mono, fontWeight: 800, fontSize: 34, color}}>{value}</span>
    </div>
  );
};

const TickerCard: React.FC<{t: z.infer<typeof tickerSchema>; localFrame: number; fps: number}> = ({t, localFrame, fps}) => {
  // entrance 0->EXPAND_SETTLE, hold, collapse COLLAPSE_START->+COLLAPSE_LEN
  const enter = spring({frame: localFrame, fps, config: SPRINGS.heavy});
  const collapseP =
    localFrame >= COLLAPSE_START
      ? interpolate(localFrame, [COLLAPSE_START, COLLAPSE_START + COLLAPSE_LEN], [0, 1], {
          easing: EASE.exit,
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : 0;
  const good = t.discountPct >= 0;
  const scale = (0.85 + 0.15 * Math.min(1, enter)) * (1 - collapseP * 0.62);
  const opacity = fadeOf(enter) * (1 - collapseP);
  // collapsing card drifts down+right toward the rail's front slot
  const driftY = collapseP * 640;
  const driftX = collapseP * -300;
  return (
    <div
      style={{
        position: 'absolute',
        left: '50%',
        top: 590,
        translate: `calc(-50% + ${driftX}px) ${(1 - Math.min(1, enter)) * 40 + driftY}px`,
        scale: String(scale),
        opacity,
        width: 760,
        borderRadius: 40,
        background: 'rgba(10,13,18,0.74)',
        border: `1.5px solid ${good ? 'rgba(52,211,153,.5)' : 'rgba(224,82,77,.5)'}`,
        boxShadow: `0 30px 90px rgba(0,0,0,.55), 0 0 60px ${good ? 'rgba(52,211,153,.16)' : 'rgba(224,82,77,.16)'}`,
        padding: '42px 54px 30px',
        backdropFilter: 'blur(3px)',
      }}
    >
      <div style={{display: 'flex', alignItems: 'baseline', gap: 18, marginBottom: 8}}>
        <span style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 84, color: C.ink}}>{t.sym}</span>
        <span style={{fontFamily: FONT.body, fontWeight: 500, fontSize: 32, color: C.muted}}>{t.name}</span>
      </div>
      <div
        style={{
          display: 'inline-flex',
          fontFamily: FONT.mono,
          fontWeight: 800,
          fontSize: 26,
          letterSpacing: 2,
          color: C.bg,
          background: good ? C.emerald : C.redHot,
          padding: '10px 22px',
          borderRadius: 999,
          marginBottom: 20,
        }}
      >
        {t.verdict.toUpperCase()}
      </div>
      <div style={{width: '100%', height: 2, background: C.line, marginBottom: 16}} />
      <div style={{display: 'flex', flexDirection: 'column', gap: 13}}>
        <Stat label="Price" value={`$${t.price.toFixed(2)}`} delay={stagger(0, 5, 'dramatic')} frame={localFrame} fps={fps} />
        <Stat label="Fair value" value={`$${t.fair.toFixed(2)}`} delay={stagger(1, 5, 'dramatic')} frame={localFrame} fps={fps} />
        <Stat
          label={good ? 'Undervalued by' : 'Overvalued by'}
          value={`${Math.abs(t.discountPct).toFixed(1)}%`}
          tone={good ? 'good' : 'bad'}
          delay={stagger(2, 5, 'dramatic')}
          frame={localFrame}
          fps={fps}
        />
        <Stat
          label="Net margin"
          value={`${t.netMargin >= 0 ? '+' : ''}${t.netMargin.toFixed(1)}%`}
          tone={t.netMargin >= 15 ? 'good' : t.netMargin < 0 ? 'bad' : 'neutral'}
          delay={stagger(3, 5, 'dramatic')}
          frame={localFrame}
          fps={fps}
        />
        <Stat
          label="Debt / equity"
          value={t.debtEquity.toFixed(2)}
          tone={t.debtEquity <= 0.5 ? 'good' : t.debtEquity > 1.2 ? 'bad' : 'neutral'}
          delay={stagger(4, 5, 'dramatic')}
          frame={localFrame}
          fps={fps}
        />
      </div>
    </div>
  );
};

// ------------------------------------------------------------- rail chip
// Rail sits in its own vertical band, clear of both the expand-card above
// (which bottoms out ~1156) and Chip below (which starts ~1480) — no
// cross-band collision at any point in the timeline.
const CHIP_W = 224;
const CHIP_GAP = 18;
const RAIL_Y = 1310;
const RAIL_LEFT = 60;

const RailChip: React.FC<{t: z.infer<typeof tickerSchema>; slot: number; frame: number; insertFrame: number; fps: number}> = ({
  t,
  slot,
  frame,
  insertFrame,
  fps,
}) => {
  const good = t.discountPct >= 0;
  const rank = Math.round(slot);
  const x = RAIL_LEFT + slot * (CHIP_W + CHIP_GAP);
  // arrival pop, independent of the ongoing slot-slide spring
  const arrive = spring({frame: frame - insertFrame, fps, config: SPRINGS.snappy});
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: RAIL_Y,
        width: CHIP_W,
        borderRadius: 20,
        background: 'rgba(10,13,18,0.82)',
        border: `1.5px solid ${good ? 'rgba(52,211,153,.55)' : 'rgba(224,82,77,.5)'}`,
        padding: '14px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
        opacity: fadeOf(arrive),
        scale: String(0.7 + 0.3 * Math.min(1, arrive)),
        boxShadow: rank === 0 ? `0 0 30px ${good ? 'rgba(52,211,153,.35)' : 'rgba(224,82,77,.3)'}` : 'none',
      }}
    >
      <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
        <span style={{fontFamily: FONT.mono, fontWeight: 800, fontSize: 15, color: C.muted}}>#{rank + 1}</span>
        <span style={{fontFamily: FONT.mono, fontWeight: 800, fontSize: 15, color: good ? C.emerald : C.redHot}}>
          {t.discountPct >= 0 ? '+' : ''}
          {t.discountPct.toFixed(0)}%
        </span>
      </div>
      <span style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 32, color: C.ink}}>{t.sym}</span>
    </div>
  );
};

// -------------------------------------------------------------- scene
export const InfraCountdown: React.FC<InfraCountdownProps> = (props) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const n = props.tickers.length;
  const insertFrames = props.tickers.map((_, i) => insertFrameOf(i));
  const outroStart = insertFrames[n - 1] + 40;

  // which segment (if any) is currently on stage
  let activeIdx = -1;
  for (let i = 0; i < n; i++) {
    const s = segmentStart(i);
    if (frame >= s && frame < s + SEGMENT_LEN) activeIdx = i;
  }

  // camera: one push-in intention, emphasis hit on the finale insert
  const cam = cameraPushIn(frame, props.durationInFrames, {hitFrame: insertFrames[n - 1], hitAmount: 0.1});

  // Chip: walks in during intro, points during segments, jumps at the outro
  const chipMode = frame < INTRO_END ? 'walk' : frame >= outroStart ? 'jump' : 'point';
  const chipX = interpolate(frame, [0, INTRO_END], [-320, 128], {
    easing: EASE.cruise,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const Rig = RIGS.chip;

  const introP = spring({frame, fps, config: SPRINGS.hero});
  const outroP = spring({frame: frame - outroStart, fps, config: SPRINGS.hero});

  return (
    <AbsoluteFill style={{fontFamily: FONT.body, background: C.bg, overflow: 'hidden'}}>
      <AbsoluteFill style={{scale: String(cam), transformOrigin: '50% 42%'}}>
        <Img src={staticFile(props.bgSrc)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </AbsoluteFill>
      {/* legibility scrim: strongest at the bottom rail, gentle at the top */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(10,13,18,.55) 0%, rgba(10,13,18,.15) 20%, rgba(10,13,18,.1) 55%, rgba(10,13,18,.7) 82%, rgba(10,13,18,.92) 100%)',
        }}
      />

      {/* intro title */}
      {frame < INTRO_END + 20 ? (
        <div
          style={{
            position: 'absolute',
            top: 96,
            left: 0,
            right: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 14,
            opacity: fadeOf(introP),
            translate: `0px ${(1 - Math.min(1, introP)) * -20}px`,
          }}
        >
          <div
            style={{
              fontFamily: FONT.mono,
              fontWeight: 700,
              fontSize: 24,
              letterSpacing: 5,
              color: C.bg,
              background: C.emerald,
              padding: '11px 24px',
              borderRadius: 999,
            }}
          >
            {props.kick}
          </div>
          <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 56, color: C.ink, textAlign: 'center', maxWidth: 920}}>
            {props.title}
          </div>
        </div>
      ) : null}

      {/* the active ticker's expanding/collapsing table */}
      {activeIdx >= 0 ? <TickerCard t={props.tickers[activeIdx]} localFrame={frame - segmentStart(activeIdx)} fps={fps} /> : null}

      {/* the ranking rail: every revealed ticker, sliding toward its slot */}
      {props.tickers.map((t, j) => {
        const slot = rampedSlot(frame, j, insertFrames);
        if (slot === null) return null;
        return <RailChip key={t.sym} t={t} slot={slot} frame={frame} insertFrame={insertFrames[j]} fps={fps} />;
      })}

      {/* Chip, hosting — own vertical band below the rail, clear of it */}
      <div style={{position: 'absolute', left: chipX, bottom: 60}}>
        <Rig size={380} mode={chipMode} />
      </div>

      {/* outro tagline */}
      {frame >= outroStart ? (
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 300,
            display: 'flex',
            justifyContent: 'center',
            padding: '0 90px',
            opacity: fadeOf(outroP),
            translate: `0px ${(1 - Math.min(1, outroP)) * 24}px`,
          }}
        >
          <div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 46, color: C.ink, textAlign: 'center', textShadow: '0 6px 30px rgba(0,0,0,.6)'}}>
            {props.tagline}
          </div>
        </div>
      ) : null}

      <div
        style={{
          position: 'absolute',
          bottom: 34,
          left: 0,
          right: 0,
          textAlign: 'center',
          fontFamily: FONT.mono,
          fontSize: 18,
          color: 'rgba(232,237,242,.6)',
        }}
      >
        {props.footer}
      </div>

      <Vignette strength={0.5} />
      <Grain />
    </AbsoluteFill>
  );
};
