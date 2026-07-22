// KurzSlide.tsx — Kurzgesagt-INSPIRED animated carousel slide engine.
// Renders one of three slide shapes (kurzProps.ts discriminated union) at
// 1080x1350: an intro title card over a top-half video, a per-company
// performance card, or a text/CTA card. Built entirely from our own brand
// palette (theme.ts) + the new motion primitives in slides/kurz.tsx — flat
// geometric shapes, saturated accents on our deep ground, gentle constant
// motion. No mascots, no borrowed trade dress.
import React from 'react';
import {AbsoluteFill, OffthreadVideo, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {KurzCompanyProps, KurzIntroVideoProps, KurzSlideProps, KurzTextProps} from '../slides/kurzProps';
import type {RichTextValue} from '../slides/slideProps';
import {C, FONT} from '../slides/theme';
import {Bg, Caption, Foot, Slam} from '../slides/ui';
import {BouncyCounter, FloatingBlob, IconMotif, MetricPill, OrbitDots} from '../slides/kurz';

const CANVAS_H = 1350;
const VIDEO_H = Math.round(CANVAS_H * 0.5);
const MOTIF_H = Math.round(CANVAS_H / 3);

/** Renders a body/sub field: a plain string passes through unstyled; a
 * richText segment array renders each `t` inline, bold when `b`, colored
 * when `tone` is a real color. Same shape as SlideStoryReel.tsx's RichText,
 * duplicated locally so this composition has no cross-composition import. */
const RichText: React.FC<{value: RichTextValue}> = ({value}) => {
  if (typeof value === 'string') return <>{value}</>;
  const TONE: Record<string, string> = {emerald: C.emerald, amber: C.amber, red: C.redHot, muted: C.muted};
  return (
    <>
      {value.map((seg, i) => {
        const style: React.CSSProperties = {};
        if (seg.b) style.fontWeight = 700;
        if (seg.tone && seg.tone !== 'text') style.color = TONE[seg.tone];
        return (
          <span key={i} style={style}>
            {seg.t}
          </span>
        );
      })}
    </>
  );
};

/** Small mono pill chip (kick / eyebrow label) that pops in with a spring
 * overshoot — the shared "kick" visual across introVideo and text slides. */
const KickChip: React.FC<{text: string; delay?: number; color?: string}> = ({text, delay = 0, color = C.emerald}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - delay, fps, config: {damping: 10, mass: 0.5, stiffness: 200}});
  const s = Math.min(1, p);
  return (
    <div
      style={{
        display: 'inline-flex',
        fontFamily: FONT.mono,
        fontWeight: 700,
        fontSize: 26,
        letterSpacing: 4,
        color: C.bg,
        background: color,
        padding: '12px 22px',
        borderRadius: 999,
        opacity: Math.min(1, p * 1.6),
        scale: String(s),
        translate: `0px ${(1 - s) * -16}px`,
      }}
    >
      {text}
    </div>
  );
};

/** Headline that springs in word-by-word with a slight stagger + overshoot —
 * the "breathing/springy pop" idiom applied to text instead of Slam's single
 * slam-in block, so multi-word titles read as gentle constant motion. */
const TitleWords: React.FC<{text: string; delay?: number; fontSize?: number; color?: string}> = ({
  text,
  delay = 0,
  fontSize = 64,
  color = C.ink,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = text.split(' ');
  return (
    <div
      style={{
        fontFamily: FONT.display,
        fontWeight: 700,
        fontSize,
        lineHeight: 1.1,
        color,
        display: 'flex',
        flexWrap: 'wrap',
        gap: '0 16px',
        textShadow: '0 8px 40px rgba(0,0,0,.5)',
      }}
    >
      {words.map((w, i) => {
        const p = spring({frame: frame - delay - i * 3, fps, config: {damping: 12, mass: 0.6, stiffness: 170}});
        const s = Math.min(1, p);
        return (
          <span
            key={`${w}-${i}`}
            style={{display: 'inline-block', opacity: Math.min(1, p * 1.4), translate: `0px ${(1 - s) * 30}px`, scale: String(0.85 + 0.15 * s)}}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};

/** Looping "swipe to next" nudge, bottom-right, persistent on the intro card. */
const SwipeArrow: React.FC = () => {
  const frame = useCurrentFrame();
  const nudge = Math.sin(frame / 18) * 10;
  return (
    <div style={{position: 'absolute', right: 56, bottom: 56, display: 'flex', alignItems: 'center', gap: 10, opacity: 0.85}}>
      <span style={{fontFamily: FONT.mono, fontSize: 22, letterSpacing: 2, color: C.muted}}>SWIPE</span>
      <svg width="40" height="24" viewBox="0 0 40 24" style={{translate: `${nudge}px 0px`}}>
        <line x1="2" y1="12" x2="34" y2="12" stroke={C.emerald} strokeWidth="4" strokeLinecap="round" />
        <polyline points="24,3 34,12 24,21" fill="none" stroke={C.emerald} strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
};

const IntroVideoScene: React.FC<KurzIntroVideoProps> = (p) => (
  <AbsoluteFill>
    <div style={{position: 'absolute', top: 0, left: 0, right: 0, height: VIDEO_H, overflow: 'hidden', borderRadius: '0 0 56px 56px'}}>
      {/* objectPosition biases the crop upward so the subject's head stays in frame */}
      <OffthreadVideo src={staticFile(p.videoSrc)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center 22%'}} />
    </div>
    <div style={{position: 'absolute', top: VIDEO_H, left: 0, right: 0, bottom: 0, overflow: 'hidden'}}>
      <FloatingBlob size={640} x={72} y={58} hue={C.emerald} hue2={C.mint} seed={2} opacity={0.26} />
      <div
        style={{
          position: 'relative',
          height: '100%',
          padding: '64px 76px 96px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          gap: 26,
        }}
      >
        <KickChip text={p.kick} delay={4} />
        <TitleWords text={p.title} delay={14} fontSize={70} />
        <div style={{marginTop: 6, maxWidth: 820}}>
          <Caption delay={44}>{p.sub}</Caption>
        </div>
      </div>
    </div>
    <SwipeArrow />
  </AbsoluteFill>
);

const CompanyScene: React.FC<KurzCompanyProps> = (p) => (
  <AbsoluteFill>
    <FloatingBlob size={720} x={18} y={6} hue={C.emerald} hue2={C.mint} seed={1} opacity={0.2} />
    <div style={{position: 'absolute', top: 8, left: 0, right: 0, height: MOTIF_H, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <IconMotif kind={p.motif} size={370} />
    </div>
    <div
      style={{
        position: 'absolute',
        top: MOTIF_H + 4,
        left: 0,
        right: 0,
        bottom: 0,
        padding: '0 72px 78px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 14,
      }}
    >
      <BouncyCounter value={p.perfPct} prefix="+" suffix="%" delay={6} fontSize={138} countFrames={40} />
      <div style={{fontFamily: FONT.mono, fontWeight: 600, fontSize: 24, letterSpacing: 2, color: C.muted, marginTop: -10}}>
        {p.perfLabel}
      </div>
      <div style={{textAlign: 'center', marginTop: 4}}>
        <div style={{fontFamily: FONT.mono, fontWeight: 800, fontSize: 46, color: C.ink}}>
          {p.ticker}
          <span style={{color: C.muted, fontWeight: 600, fontSize: 28}}> · {p.name}</span>
        </div>
        <div style={{fontFamily: FONT.body, fontWeight: 500, fontSize: 26, color: C.inkSoft, marginTop: 6}}>{p.tagline}</div>
      </div>
      <div style={{display: 'flex', flexDirection: 'column', gap: 12, width: '100%', marginTop: 10}}>
        {p.pills.map((pill, i) => (
          <MetricPill key={pill.label} label={pill.label} value={pill.value} delay={70 + i * 10} />
        ))}
      </div>
      <div style={{fontFamily: FONT.mono, fontSize: 19, color: C.muted, marginTop: 10, textAlign: 'center'}}>{p.footnote}</div>
    </div>
  </AbsoluteFill>
);

const TextScene: React.FC<KurzTextProps> = (p) => (
  <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', padding: '0 84px'}}>
    <FloatingBlob size={800} x={50} y={50} hue={C.emerald} hue2={C.amber} seed={3} opacity={0.2} />
    <OrbitDots n={7} radius={330} x={50} y={44} />
    <div style={{position: 'relative', display: 'flex', flexDirection: 'column', gap: 24, alignItems: 'center', textAlign: 'center', maxWidth: 880}}>
      <KickChip text={p.kick} delay={4} />
      <Slam size={76} delay={12}>
        {p.title}
      </Slam>
      <div style={{marginTop: 8}}>
        <Caption delay={40}>
          <RichText value={p.body} />
        </Caption>
      </div>
    </div>
  </AbsoluteFill>
);

export const KurzSlide: React.FC<KurzSlideProps> = (props) => {
  const tint = props.kind === 'company' ? C.emerald : props.kind === 'text' ? C.amber : C.emerald;
  return (
    <AbsoluteFill style={{fontFamily: FONT.body}}>
      <Bg tint={tint} />
      {props.kind === 'introVideo' ? (
        <IntroVideoScene {...props} />
      ) : props.kind === 'company' ? (
        <CompanyScene {...props} />
      ) : (
        <TextScene {...props} />
      )}
      <AbsoluteFill style={{padding: '0 40px 22px', alignItems: 'center', justifyContent: 'flex-end', pointerEvents: 'none'}}>
        <Foot text={props.footer} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
