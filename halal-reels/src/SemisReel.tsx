import React from "react";
import { AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import { C, FONT } from "./theme";
import { Foot, GrokClip, LimitMeter, RollingCaption, StickerHook, clamp, easeOut, pop } from "./ui";
import { CrashChart, RotationFlow } from "./charts";
import {
  CRASH_LEN,
  CTA_LEN,
  FORCED_LEN,
  KOREA_LEN,
  LEVERAGE_B,
  LEVERAGE_PREV_B,
  LEV_LEN,
  ROT_LEN,
  SEMIS_DATE,
  SEMIS_MINI_STARTS,
  SEMIS_MINI_TOTAL,
  SEMIS_STARTS,
  SEMIS_TOTAL,
  SNDK_DROP_PCT,
  US_LEN,
  WHOOSH_OFFSETS,
  crashCandles,
  gapCloses,
} from "./semisData";

// ---------------------------------------------------------------------------
// SemisReel -- "semis are running out of buyers" (2026-08-02 source reel),
// faithfully retold as a hybrid Grok-video + Remotion chart/typography
// remake. Seven beats: CRASH -> LEVERAGE -> KOREA -> FORCED -> US -> ROTATION
// -> CTA. Each beat is a self-contained scene component whose animation runs
// entirely off its own Sequence-local `useCurrentFrame()` (0-based once
// inside a <Sequence>), so the exact same scene components are reused for
// both the full reel (SEMIS_STARTS) and the mini cut (SEMIS_MINI_STARTS:
// crash -> rotation -> cta) -- only the <Sequence from=/durationInFrames=>
// wiring differs, mirroring CorrelationReel's mini-offset technique.
// ---------------------------------------------------------------------------

export const SEMIS_BEATS = { total: SEMIS_TOTAL };
export { SEMIS_MINI_TOTAL };

const SEMIS_RAIL =
  "Relaying reported market data · educational only — not financial advice · not a trade signal.";

const PAD = 84;

/** Small persistent disclaimer rail, shown on every beat (mirrors
 * CorrelationReel's RailFoot). */
const RailFoot: React.FC = () => (
  <div style={{ position: "absolute", bottom: 40, left: PAD, right: PAD, textAlign: "center", zIndex: 10 }}>
    <Foot text={SEMIS_RAIL} />
  </div>
);

/** Centers chart/graphic content in the clear band between the pinned
 * StickerHook (top) and the RollingCaption (bottom). */
const ChartSlot: React.FC<{ children: React.ReactNode; top?: number }> = ({ children, top = 620 }) => (
  <div style={{ position: "absolute", top, left: 0, right: 0, display: "flex", justifyContent: "center", zIndex: 4 }}>
    {children}
  </div>
);

/** Simple falling line for the Korea "gap down" beat -- amber (data-toned,
 * not decorative red; red is reserved for CrashChart's down-candles). */
const GapLine: React.FC<{ data: number[]; reveal: number; width: number; height: number }> = ({
  data,
  reveal,
  width,
  height,
}) => {
  const n = data.length;
  const shown = Math.max(2, Math.floor(reveal * n));
  const pts = data
    .slice(0, shown)
    .map((v, i) => `${(i / (n - 1)) * width},${height - v * height}`)
    .join(" ");
  const lastIdx = shown - 1;
  const lx = (lastIdx / (n - 1)) * width;
  const ly = height - data[lastIdx] * height;
  return (
    <svg width={width} height={height} style={{ overflow: "visible" }}>
      <polyline points={pts} fill="none" stroke={C.amber} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={lx} cy={ly} r={10} fill={C.mint} />
    </svg>
  );
};

// ---------------------------------------------------------------------------
// Music bed: low-volume across the whole reel, ducked briefly under each
// whoosh cue so the sfx reads clearly (mirrors CorrelationReel).
// ---------------------------------------------------------------------------
const MUSIC_VOL = 0.28;
const MUSIC_DUCK_VOL = 0.1;
const MUSIC_DUCK_LEN = 26;

const duckAt = (frame: number, center: number): number | null => {
  const rel = frame - center;
  if (rel >= 0 && rel < MUSIC_DUCK_LEN) {
    return interpolate(
      rel,
      [0, 5, MUSIC_DUCK_LEN - 5, MUSIC_DUCK_LEN],
      [MUSIC_VOL, MUSIC_DUCK_VOL, MUSIC_DUCK_VOL, MUSIC_VOL],
      clamp,
    );
  }
  return null;
};

const musicVolumeFor = (whooshFrames: number[]) => (frame: number) => {
  for (const center of whooshFrames) {
    const v = duckAt(frame, center);
    if (v !== null) return v;
  }
  return MUSIC_VOL;
};

const MINI_WHOOSH = [SEMIS_MINI_STARTS.crash, SEMIS_MINI_STARTS.rot, SEMIS_MINI_STARTS.cta];

// ---------------------------------------------------------------------------
// Beat scenes -- each drives entirely off its own Sequence-local frame.
// ---------------------------------------------------------------------------

const CrashScene: React.FC = () => {
  const frame = useCurrentFrame();
  const reveal = interpolate(frame, [0, CRASH_LEN], [0, 1], { ...clamp, easing: easeOut });
  return (
    <>
      <GrokClip src="semis/panic_floor.mp4" kind="video" />
      <ChartSlot>
        <CrashChart candles={crashCandles(60)} reveal={reveal} dropPct={SNDK_DROP_PCT} width={900} height={520} />
      </ChartSlot>
      <StickerHook pre="Semis are running out of" keyword="buyers" from={0} />
      <RollingCaption text="SanDisk crashed 14.1% today — semis are running out of buyers." from={20} asReported />
    </>
  );
};

const LeverageScene: React.FC = () => (
  <>
    <GrokClip src="semis/leverage_bg.jpg" kind="image" />
    <div style={{ position: "absolute", top: 640, left: PAD, right: PAD, zIndex: 4 }}>
      <LimitMeter
        value={LEVERAGE_B}
        cap={LEVERAGE_PREV_B}
        scaleMax={45}
        from={30}
        fmt={(v) => `$${v.toFixed(0)}B`}
        capLabel="PRIOR RECORD"
        overLabel="RECORD"
      />
    </div>
    <RollingCaption text="Retail leverage just hit a record $39B." from={10} asReported />
  </>
);

const KoreaScene: React.FC = () => {
  const frame = useCurrentFrame();
  const reveal = interpolate(frame, [0, KOREA_LEN], [0, 1], { ...clamp, easing: easeOut });
  return (
    <>
      <GrokClip src="semis/seoul.mp4" kind="video" />
      <ChartSlot>
        <GapLine data={gapCloses(60)} reveal={reveal} width={900} height={420} />
      </ChartSlot>
      <RollingCaption text="It worked in Korea — until the market kept gapping lower." from={10} asReported />
    </>
  );
};

const ForcedScene: React.FC = () => (
  <>
    <GrokClip src="semis/forced_bg.jpg" kind="image" />
    <RollingCaption text="Now margin buyers are becoming forced sellers." from={10} />
  </>
);

const UsScene: React.FC = () => {
  const frame = useCurrentFrame();
  const reveal = interpolate(frame, [0, US_LEN], [0, 1], { ...clamp, easing: easeOut });
  return (
    <>
      <GrokClip src="semis/us_exchange.mp4" kind="video" />
      <ChartSlot top={700}>
        <CrashChart candles={crashCandles(40)} reveal={reveal} dropPct={SNDK_DROP_PCT} width={640} height={340} />
      </ChartSlot>
      <RollingCaption text="Today showed it's a U.S. problem too." from={10} />
    </>
  );
};

const RotationScene: React.FC = () => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [0, ROT_LEN], [0, 1], { ...clamp, easing: easeOut });
  return (
    <>
      <GrokClip src="semis/rotation_bg.jpg" kind="image" />
      <ChartSlot>
        <RotationFlow t={t} width={900} height={520} />
      </ChartSlot>
      <RollingCaption
        text="Bizarrely, healthcare just had its best week since 2022 — defensive rotation."
        from={10}
        asReported
      />
    </>
  );
};

const CtaScene: React.FC = () => {
  const frame = useCurrentFrame();
  const pillP = interpolate(frame, [40, 60], [0, 1], { ...clamp, easing: pop });
  const subP = interpolate(frame, [60, 80], [0, 1], clamp);
  return (
    <>
      <GrokClip src="semis/terminal_bg.jpg" kind="image" />
      <StickerHook pre="One corner cracked. Watch the" keyword="rotation" from={0} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 26, padding: 90, zIndex: 5 }}>
        <div
          style={{
            fontFamily: FONT.mono,
            fontWeight: 700,
            fontSize: 34,
            letterSpacing: 3,
            color: C.bg,
            background: C.mint,
            padding: "18px 32px",
            borderRadius: 16,
            opacity: pillP,
            scale: String(0.8 + 0.2 * pillP),
          }}
        >
          COMMENT &quot;SEMIS&quot;
        </div>
        <div
          style={{
            fontFamily: FONT.body,
            fontWeight: 600,
            fontSize: 32,
            color: C.mint,
            opacity: subP,
            textAlign: "center",
            maxWidth: 820,
          }}
        >
          → and I&apos;ll DM you the breakdown
        </div>
      </AbsoluteFill>
      <div
        style={{
          position: "absolute",
          bottom: 96,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: FONT.mono,
          fontSize: 22,
          color: C.muted,
          opacity: subP,
          zIndex: 4,
        }}
      >
        data as of {SEMIS_DATE}
      </div>
      <RailFoot />
    </>
  );
};

// ---------------------------------------------------------------------------
// Root composition. `mini` swaps the 7-beat full timeline (SEMIS_STARTS) for
// the 3-beat crash -> rotation -> cta cut (SEMIS_MINI_STARTS), reusing the
// exact same scene components -- no scene re-authors its timing off an
// absolute reel offset, so only the <Sequence> wiring below changes.
// ---------------------------------------------------------------------------
export const SemisReel: React.FC<{ mini?: boolean }> = ({ mini = false }) => {
  const whooshFrames = mini ? MINI_WHOOSH : WHOOSH_OFFSETS;
  const musicVolume = musicVolumeFor(whooshFrames);

  return (
    <AbsoluteFill style={{ fontFamily: FONT.body, background: C.bg }}>
      <Audio src={staticFile("quiz/music.mp3")} volume={musicVolume} />
      {whooshFrames.map((f, idx) => (
        <Sequence key={f} from={f} durationInFrames={40} name={`Whoosh${idx}`}>
          <Audio src={staticFile("quiz/reveal.mp3")} volume={0.5} />
        </Sequence>
      ))}

      {mini ? (
        <>
          <Sequence from={SEMIS_MINI_STARTS.crash} durationInFrames={CRASH_LEN} name="Crash">
            <CrashScene />
            <RailFoot />
          </Sequence>
          <Sequence from={SEMIS_MINI_STARTS.rot} durationInFrames={ROT_LEN} name="Rotation">
            <RotationScene />
            <RailFoot />
          </Sequence>
          <Sequence from={SEMIS_MINI_STARTS.cta} durationInFrames={CTA_LEN} name="CTA">
            <CtaScene />
          </Sequence>
        </>
      ) : (
        <>
          <Sequence from={SEMIS_STARTS.crash} durationInFrames={CRASH_LEN} name="Crash">
            <CrashScene />
            <RailFoot />
          </Sequence>
          <Sequence from={SEMIS_STARTS.lev} durationInFrames={LEV_LEN} name="Leverage">
            <LeverageScene />
            <RailFoot />
          </Sequence>
          <Sequence from={SEMIS_STARTS.korea} durationInFrames={KOREA_LEN} name="Korea">
            <KoreaScene />
            <RailFoot />
          </Sequence>
          <Sequence from={SEMIS_STARTS.forced} durationInFrames={FORCED_LEN} name="Forced">
            <ForcedScene />
            <RailFoot />
          </Sequence>
          <Sequence from={SEMIS_STARTS.us} durationInFrames={US_LEN} name="US">
            <UsScene />
            <RailFoot />
          </Sequence>
          <Sequence from={SEMIS_STARTS.rot} durationInFrames={ROT_LEN} name="Rotation">
            <RotationScene />
            <RailFoot />
          </Sequence>
          <Sequence from={SEMIS_STARTS.cta} durationInFrames={CTA_LEN} name="CTA">
            <CtaScene />
          </Sequence>
        </>
      )}
    </AbsoluteFill>
  );
};
