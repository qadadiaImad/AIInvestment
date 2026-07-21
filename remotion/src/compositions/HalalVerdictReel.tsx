// HalalVerdictReel.tsx
import React from "react";
import { AbsoluteFill, Series } from "remotion";
import { brand } from "../brand";
import type { ReelProps } from "../props";
import { BubbleFrame } from "../components/BubbleFrame";
import { VerdictBadge } from "../components/VerdictBadge";
import { RatioBars } from "../components/RatioBars";
import { DecisiveNumber } from "../components/DecisiveNumber";
import { PurificationLine } from "../components/PurificationLine";
import { CaptionTrack } from "../components/CaptionTrack";
import { DisclaimerFooter } from "../components/DisclaimerFooter";

const SCENE_FRAMES = 240; // 8s @ 30fps, matches the bubble clip loop

const SceneShell: React.FC<{
  headline: string;
  sub?: string;
  children?: React.ReactNode;
}> = ({ headline, sub, children }) => (
  <div
    style={{
      position: "absolute",
      top: brand.safeTop + 40,
      left: 48,
      right: 48,
    }}
  >
    <h1
      style={{
        fontFamily: brand.fontBig,
        fontSize: 76,
        color: brand.text,
        margin: 0,
        lineHeight: 1.1,
      }}
    >
      {headline}
    </h1>
    {sub ? (
      <p
        style={{
          fontFamily: brand.fontBody,
          fontSize: 32,
          color: brand.muted,
          marginTop: 14,
        }}
      >
        {sub}
      </p>
    ) : null}
    <div style={{ marginTop: 48, marginRight: "4%" }}>{children}</div>
  </div>
);

export const HalalVerdictReel: React.FC<ReelProps> = (p) => (
  <AbsoluteFill style={{ background: brand.bg }}>
    <Series>
      <Series.Sequence durationInFrames={SCENE_FRAMES}>
        <SceneShell headline={p.scenes[0].headline} sub={p.scenes[0].sub}>
          <div
            style={{
              marginTop: 30,
              fontFamily: brand.fontMono,
              fontSize: 120,
              color: brand.text,
            }}
          >
            {p.ticker}
          </div>
        </SceneShell>
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENE_FRAMES}>
        <SceneShell headline={p.scenes[1].headline} sub={p.scenes[1].sub}>
          <RatioBars
            tests={p.tests}
            activityStatus={p.activityStatus}
            decisive={p.decisive}
          />
        </SceneShell>
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENE_FRAMES}>
        <SceneShell headline={p.scenes[2].headline} sub={p.scenes[2].sub}>
          <DecisiveNumber
            valuePct={p.decisive.valuePct}
            thresholdPct={p.decisive.thresholdPct}
            label={p.decisive.label}
          />
          <div style={{ marginTop: 40 }}>
            <VerdictBadge overall={p.overall} basis={p.overallBasis} />
          </div>
          <div style={{ marginTop: 28 }}>
            <PurificationLine perShare={p.purificationPerShare} />
          </div>
        </SceneShell>
      </Series.Sequence>
    </Series>
    <BubbleFrame src={p.bubbleSrc} />
    <CaptionTrack words={p.captions} />
    <DisclaimerFooter text={p.disclaimer} />
  </AbsoluteFill>
);
