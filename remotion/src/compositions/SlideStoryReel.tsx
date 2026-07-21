// SlideStoryReel.tsx — one parameterized composition reproducing the WULF visual
// language (halal-reels/src/WulfReel.tsx) from a schema-driven props object
// (../slides/slideProps.ts) instead of one hand-authored .tsx file per ticker.
//
// Beat-kind -> WulfReel-section mapping (derived by reading WulfReel.tsx,
// GevReel.tsx, EtnReel.tsx — halal-reels/ is read-only reference, not imported):
//   - persistent header chip (Head: ticker/tickerSub/badge) + persistent footer
//     (Foot: disclaimer) span the whole reel, exactly as WulfReel renders Head
//     once at the top and Foot in a single full-duration Sequence.
//   - 'hook'    -> WulfReel S1 "Hook": Slam headline (+ inline amber accentWord
//                  highlight, replacing WulfReel's hardcoded two-Slam split) + Caption sub.
//   - 'bars'    -> WulfReel S3 "Stamps" / GevReel S3 "ALL THREE RULEBOOKS": Kicker
//                  title + one <Stamp> per bar entry (ratio-vs-threshold, pass/fail) +
//                  optional Caption. ('unknown' status renders as the fail (X) glyph —
//                  Stamp only has a boolean ok/fail visual; documented simplification.)
//   - 'donut'   -> WulfReel S4 "BitcoinSlice": the ported Donut arc, parameterized
//                  (centerLabel replaces the hardcoded "BITCOIN MINING"; tone drives
//                  the ring/number color instead of a hardcoded amber).
//   - 'stamp'   -> a new single-verdict scene (no 1:1 WulfReel scene: the schema's
//                  4-state verdict enum doesn't fit ui.tsx's boolean-only <Stamp>).
//                  Built from the same visual vocabulary (rounded glyph badge +
//                  mono label + Caption) to carry the overall verdict + basis + line —
//                  in the WULF fixture this also absorbs the original debt-test /
//                  purification beats that have no dedicated kind in this schema.
//   - 'endcard' -> WulfReel S6 "EndCard": badge chip + display headline + sub line,
//                  ported inline (not importing ui.tsx's EndCard, which requires a
//                  mandatory `date` prop this schema doesn't carry).
import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Sequence,
  Series,
  interpolate,
  useCurrentFrame,
} from 'remotion';
import type {Beat, RichTextValue, SlideStoryProps} from '../slides/slideProps';
import {C, FONT} from '../slides/theme';
import {Bg, Caption, Foot, Head, Kicker, Slam, Stamp, clamp, easeOut} from '../slides/ui';
import {BubbleFrame} from '../components/BubbleFrame';

const PAD = 84;

const TONE_COLOR: Record<'pass' | 'fail' | 'warn', string> = {
  pass: C.emerald,
  fail: C.redHot,
  warn: C.amber,
};

// Rich-text segment tone -> theme color. 'text' (or an omitted tone) means
// "inherit the surrounding element's color" — matches WulfReel.tsx's plain
// <b> spans that only change weight, not color.
const RICH_TONE_COLOR: Record<'emerald' | 'amber' | 'red' | 'muted', string> = {
  emerald: C.emerald,
  amber: C.amber,
  red: C.redHot,
  muted: C.muted,
};

// Second hook line's tone (fully colors the whole line, unlike per-segment
// richText tones) — reuses the same palette.
const HEADLINE2_TONE_COLOR: Record<'amber' | 'emerald' | 'red', string> = {
  amber: C.amber,
  emerald: C.emerald,
  red: C.redHot,
};

/** Renders a sub/caption/line field: a plain string passes through unstyled;
 * a richText segment array renders each `t` inline, bold when `b`, colored
 * when `tone` is a real color (ports WulfReel.tsx's hand-authored
 * `<b style={{color: C.amber}}>38%</b>`-style emphasis spans from data). */
const RichText: React.FC<{value: RichTextValue}> = ({value}) => {
  if (typeof value === 'string') return <>{value}</>;
  return (
    <>
      {value.map((seg, i) => {
        const style: React.CSSProperties = {};
        if (seg.b) style.fontWeight = 700;
        if (seg.tone && seg.tone !== 'text') style.color = RICH_TONE_COLOR[seg.tone];
        return (
          <span key={i} style={style}>
            {seg.t}
          </span>
        );
      })}
    </>
  );
};

const VERDICT_META: Record<
  'halal' | 'not_halal' | 'questionable' | 'insufficient_data',
  {label: string; color: string; icon: string}
> = {
  halal: {label: 'HALAL', color: C.emeraldDeep, icon: '✓'},
  not_halal: {label: 'NOT HALAL', color: C.redHot, icon: '✕'},
  questionable: {label: 'REVIEW', color: C.amber, icon: '!'},
  insufficient_data: {label: 'INSUFFICIENT DATA', color: C.muted, icon: '?'},
};

/** Persistent header badge color, derived from the badge copy (schema carries a
 * plain string, not the {text,color} pair ui.tsx's <Head>/<EndCard> expect). */
const badgeColor = (badge: string): string => {
  const upper = badge.toUpperCase();
  if (upper.includes('PASS')) return C.emerald;
  if (upper.includes('FAIL') || upper.includes('NOT ')) return C.redHot;
  return C.amber; // REVIEW / QUESTIONABLE / default
};

const renderAccentedHeadline = (headline: string, accentWord?: string): React.ReactNode => {
  if (!accentWord) return headline;
  const idx = headline.toLowerCase().indexOf(accentWord.toLowerCase());
  if (idx === -1) return headline;
  const before = headline.slice(0, idx);
  const match = headline.slice(idx, idx + accentWord.length);
  const after = headline.slice(idx + accentWord.length);
  return (
    <>
      {before}
      <span style={{color: C.amber}}>{match}</span>
      {after}
    </>
  );
};

// Donut — ported from halal-reels/src/WulfReel.tsx's private Donut component,
// parameterized: centerLabel + color replace the hardcoded "BITCOIN MINING" / amber.
const Donut: React.FC<{pct: number; centerLabel: string; color: string; from: number}> = ({
  pct,
  centerLabel,
  color,
  from,
}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [from, from + 55], [0, 1], {
    ...clamp,
    easing: Easing.bezier(0.45, 0, 0.55, 1),
  });
  const R = 150;
  const CIRC = 2 * Math.PI * R;
  const shown = p * (pct / 100);
  return (
    <div style={{position: 'relative', width: 380, height: 380}}>
      <svg width="380" height="380" viewBox="0 0 380 380">
        <circle cx="190" cy="190" r={R} stroke={C.panel} strokeWidth="46" fill="none" />
        <circle
          cx="190"
          cy="190"
          r={R}
          stroke={color}
          strokeWidth="46"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={CIRC}
          strokeDashoffset={CIRC * (1 - shown)}
          style={{transformOrigin: '190px 190px', rotate: '-90deg'}}
        />
      </svg>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: FONT.mono,
        }}
      >
        <div style={{fontWeight: 800, fontSize: 84, color}}>{(shown * 100).toFixed(1)}%</div>
        <div style={{fontWeight: 600, fontSize: 24, color: C.muted, letterSpacing: 2}}>{centerLabel}</div>
      </div>
    </div>
  );
};

const HOOK_HEADLINE_SIZE = 118;
// ~1.12x the headline size — matches WulfReel.tsx's two-Slam hook ("This stock
// earns" @118 / "bitcoin money." @132; 132/118 ≈ 1.1186 ≈ 1.12x).
const HOOK_HEADLINE2_SIZE = Math.round(HOOK_HEADLINE_SIZE * 1.12);

const HookScene: React.FC<{beat: Extract<Beat, {kind: 'hook'}>}> = ({beat}) => (
  <AbsoluteFill style={{padding: PAD, justifyContent: 'center'}}>
    <Slam size={HOOK_HEADLINE_SIZE}>{renderAccentedHeadline(beat.headline, beat.accentWord)}</Slam>
    {beat.headline2 ? (
      <Slam size={HOOK_HEADLINE2_SIZE} color={HEADLINE2_TONE_COLOR[beat.headline2Tone]} delay={14}>
        {beat.headline2}
      </Slam>
    ) : null}
    <div style={{marginTop: 60, maxWidth: 900}}>
      <Caption delay={40}>
        <RichText value={beat.sub} />
      </Caption>
    </div>
  </AbsoluteFill>
);

const BarsScene: React.FC<{beat: Extract<Beat, {kind: 'bars'}>}> = ({beat}) => (
  <AbsoluteFill style={{padding: PAD, justifyContent: 'center', gap: 46}}>
    <Kicker text={beat.title} color={C.redHot} />
    {beat.bars.map((b, i) => (
      <Stamp
        key={b.label}
        ok={b.status === 'pass'}
        label={b.label}
        detail={b.ratio != null ? `${b.ratio}% vs cap ${b.threshold}%` : undefined}
        delay={8 + i * 22}
      />
    ))}
    {beat.caption ? (
      <div style={{maxWidth: 900}}>
        <Caption delay={8 + beat.bars.length * 22 + 20}>
          <RichText value={beat.caption} />
        </Caption>
      </div>
    ) : null}
  </AbsoluteFill>
);

const DonutScene: React.FC<{beat: Extract<Beat, {kind: 'donut'}>}> = ({beat}) => (
  <AbsoluteFill style={{padding: PAD, justifyContent: 'center', gap: 44, alignItems: 'center'}}>
    <Kicker text={beat.title} color={TONE_COLOR[beat.tone]} />
    <Donut pct={beat.pct} centerLabel={beat.centerLabel} color={TONE_COLOR[beat.tone]} from={10} />
    <div style={{maxWidth: 900}}>
      <Caption delay={60}>
        <RichText value={beat.caption} />
      </Caption>
    </div>
  </AbsoluteFill>
);

const StampScene: React.FC<{beat: Extract<Beat, {kind: 'stamp'}>}> = ({beat}) => {
  const meta = VERDICT_META[beat.verdict];
  return (
    <AbsoluteFill style={{padding: PAD, justifyContent: 'center', gap: 40, alignItems: 'center'}}>
      <Kicker text="THE VERDICT" color={meta.color} />
      <div style={{display: 'flex', alignItems: 'center', gap: 28}}>
        <div
          style={{
            width: 120,
            height: 120,
            borderRadius: 28,
            border: `6px solid ${meta.color}`,
            color: meta.color,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 70,
            fontWeight: 800,
            fontFamily: FONT.mono,
            background: `${meta.color}22`,
          }}
        >
          {meta.icon}
        </div>
        <div>
          <div style={{fontFamily: FONT.mono, fontWeight: 800, fontSize: 56, color: C.ink}}>{meta.label}</div>
          <div style={{fontFamily: FONT.mono, fontWeight: 600, fontSize: 26, color: C.muted, marginTop: 6, maxWidth: 640}}>
            {beat.basis}
          </div>
        </div>
      </div>
      <div style={{maxWidth: 920}}>
        <Caption delay={40}>
          <RichText value={beat.line} />
        </Caption>
      </div>
    </AbsoluteFill>
  );
};

const EndCardScene: React.FC<{beat: Extract<Beat, {kind: 'endcard'}>; badge: {text: string; color: string}}> = ({
  beat,
  badge,
}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 16], [0, 1], {...clamp, easing: easeOut});
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', gap: 44, padding: 90}}>
      <div
        style={{
          fontFamily: FONT.mono,
          fontWeight: 700,
          fontSize: 40,
          letterSpacing: 3,
          color: C.bg,
          background: badge.color,
          padding: '22px 38px',
          borderRadius: 18,
          scale: String(0.8 + 0.2 * p),
          opacity: p,
        }}
      >
        {badge.text}
      </div>
      <div
        style={{
          fontFamily: FONT.display,
          fontWeight: 600,
          fontSize: 66,
          lineHeight: 1.1,
          color: C.ink,
          textAlign: 'center',
          opacity: p,
          maxWidth: 860,
        }}
      >
        {beat.headline}
      </div>
      <div style={{fontFamily: FONT.mono, fontSize: 26, color: C.muted, opacity: p}}>
        <RichText value={beat.sub} />
      </div>
    </AbsoluteFill>
  );
};

export const SlideStoryReel: React.FC<SlideStoryProps> = (props) => {
  const totalFrames = props.beats.reduce((sum, b) => sum + b.durationInFrames, 0);
  const headerBadge = {text: props.badge, color: badgeColor(props.badge)};

  return (
    <AbsoluteFill style={{fontFamily: FONT.body}}>
      <Bg tint={headerBadge.color} />
      <AbsoluteFill style={{padding: PAD}}>
        <Head tk={props.ticker} sub={props.tickerSub} badge={headerBadge} />
      </AbsoluteFill>

      <Series>
        {props.beats.map((beat, i) => (
          <Series.Sequence key={i} durationInFrames={beat.durationInFrames} name={beat.kind}>
            {beat.kind === 'hook' ? (
              <HookScene beat={beat} />
            ) : beat.kind === 'bars' ? (
              <BarsScene beat={beat} />
            ) : beat.kind === 'donut' ? (
              <DonutScene beat={beat} />
            ) : beat.kind === 'stamp' ? (
              <StampScene beat={beat} />
            ) : (
              <EndCardScene beat={beat} badge={headerBadge} />
            )}
          </Series.Sequence>
        ))}
      </Series>

      {/* Non-looping full-span bubble (spec §0-bis): a <Series> of distinct
          talking clips, one per beat, running back-to-back for the reel's
          duration — no <Loop>. VO-less slide mode (bubbleClips: []) renders
          no bubble at all, per the schema's default. */}
      {props.bubbleClips.length > 0 ? <BubbleFrame clips={props.bubbleClips} /> : null}

      <AbsoluteFill style={{padding: PAD, justifyContent: 'flex-end', pointerEvents: 'none'}}>
        <Sequence from={0} durationInFrames={totalFrames} layout="none" name="Footer">
          <Foot text={props.disclaimer} />
        </Sequence>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
