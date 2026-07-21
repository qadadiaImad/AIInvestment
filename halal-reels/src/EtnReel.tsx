import React from "react";
import { AbsoluteFill, Sequence, interpolate, useCurrentFrame, Audio, staticFile } from "remotion";
import { DATE, ETN } from "./data";
import { C, FONT } from "./theme";
import { Bg, Caption, EndCard, Foot, Head, Kicker, Slam, Stamp, clamp, easeOut, inOut, pop } from "./ui";

const Book: React.FC<{ label: string; color: string; delay: number }> = ({ label, color, delay }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [delay, delay + 14], [0, 1], { ...clamp, easing: pop });
  return (
    <div
      style={{
        width: 176,
        height: 250,
        borderRadius: 14,
        border: `4px solid ${color}`,
        background: `linear-gradient(160deg, ${color}30, ${color}10)`,
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "center",
        paddingBottom: 20,
        fontFamily: FONT.mono,
        fontWeight: 800,
        fontSize: 30,
        color,
        opacity: p,
        translate: `0px ${(1 - p) * 120}px`,
        rotate: `${(1 - p) * 6}deg`,
        boxShadow: "0 20px 50px rgba(0,0,0,.45)",
      }}
    >
      {label}
    </div>
  );
};

const PanelMeter: React.FC<{
  title: string;
  question: string;
  value: number;
  cap: number;
  ok: boolean;
  from: number;
  countEnd: number;
  stampDelay: number;
}> = ({ title, question, value, cap, ok, from, countEnd, stampDelay }) => {
  const frame = useCurrentFrame();
  const appear = interpolate(frame, [from, from + 14], [0, 1], { ...clamp, easing: easeOut });
  const p = interpolate(frame, [from + 14, countEnd], [0, 1], { ...clamp, easing: inOut });
  const v = p * value;
  const over = v > cap;
  const color = ok ? C.emeraldDeep : C.redHot;
  const scaleMax = 55;
  return (
    <div
      style={{
        flex: 1,
        border: `2px solid ${over || (ok && p > 0.9) ? color : C.line}`,
        borderRadius: 26,
        background: C.panel,
        padding: 40,
        opacity: appear,
        translate: `0px ${(1 - appear) * 60}px`,
      }}
    >
      <div style={{ fontFamily: FONT.mono, fontWeight: 800, fontSize: 34, color, letterSpacing: 1 }}>{title}</div>
      <div style={{ fontFamily: FONT.body, fontSize: 30, lineHeight: 1.35, color: C.inkSoft, marginTop: 14, minHeight: 120 }}>
        {question}
      </div>
      <div style={{ fontFamily: FONT.mono, fontWeight: 800, fontSize: 96, color: over ? C.redHot : C.ink, marginTop: 10 }}>
        {v.toFixed(0)}¢
        <span style={{ fontSize: 36, color: C.muted, fontWeight: 700 }}> / $1</span>
      </div>
      <div style={{ position: "relative", height: 30, marginTop: 26, background: "rgba(255,255,255,.07)", borderRadius: 9 }}>
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            bottom: 0,
            width: `${Math.min(100, (v / scaleMax) * 100)}%`,
            background: over ? C.redHot : C.emeraldDeep,
            borderRadius: 9,
          }}
        />
        <div
          style={{
            position: "absolute",
            left: `${(cap / scaleMax) * 100}%`,
            top: -12,
            bottom: -12,
            borderLeft: `4px dashed ${C.ink}`,
            opacity: 0.85,
          }}
        />
      </div>
      <div style={{ fontFamily: FONT.mono, fontSize: 24, color: C.muted, marginTop: 18 }}>limit {cap}¢</div>
      <div style={{ marginTop: 26 }}>
        <Stamp ok={ok} label={ok ? "PASS" : "FAIL"} delay={stampDelay} />
      </div>
    </div>
  );
};

const PAD = 84;
// Beat-synced (voice_etn.wav): "Depends which rulebook" 6.2-7.5 ; "One compares" 8.64 ;
// "14c/dollar" 12.3-13.0 ; "Pass" 16.4 ; "Two others" 17.3 ; "40c/dollar" 21.3-22.5 ;
// "over their limit" 22.9-23.7 ; "Same company" 26.0 ; "Different math" 28.6-29.0 ;
// "always on the card" 30.4-32.4

export const EtnReel: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ fontFamily: FONT.body }}>
      <Bg />
      <Audio src={staticFile("voice_etn.wav")} />
      <AbsoluteFill style={{ padding: PAD }}>
        <Head tk="ETN" sub="POWER MANAGEMENT · NYSE" badge={ETN.badge} />
      </AbsoluteFill>

      {/* S1 — hook + books */}
      <Sequence from={8} durationInFrames={251} name="Hook">
        <AbsoluteFill style={{ padding: PAD, justifyContent: "center" }}>
          <Slam size={104}>One stock.</Slam>
          <Slam size={104} delay={14}>
            Three rulebooks.
          </Slam>
          <Slam size={104} color={C.emerald} delay={30}>
            Two different answers.
          </Slam>
          <div style={{ display: "flex", gap: 34, marginTop: 70 }}>
            <Book label="AAOIFI" color={C.emerald} delay={182} />
            <Book label="FTSE" color={C.amber} delay={192} />
            <Book label="MSCI" color={C.amber} delay={202} />
          </div>
          <div style={{ marginTop: 56, maxWidth: 920 }}>
            <Caption delay={100}>
              A <b style={{ color: C.emerald }}>halal screen</b> checks how much debt a company carries.
              But the rulebooks <b style={{ color: C.amber }}>measure it differently</b>…
            </Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S2 — split meters */}
      <Sequence from={259} durationInFrames={522} name="SplitTest">
        <AbsoluteFill style={{ padding: PAD, paddingTop: 250, gap: 30 }}>
          <Kicker text="SAME DEBT — TWO MEASURES" />
          <div style={{ display: "flex", gap: 30, flex: 1, maxHeight: 900 }}>
            <PanelMeter
              title="AAOIFI"
              question="Debt vs what the market says the company is worth"
              value={ETN.aaoifiPct}
              cap={ETN.aaoifiCap}
              ok
              from={6}
              countEnd={130}
              stampDelay={230}
            />
            <PanelMeter
              title="FTSE & MSCI"
              question="Debt vs everything the company owns"
              value={ETN.assetsPct}
              cap={ETN.assetsCap}
              ok={false}
              from={255}
              countEnd={410}
              stampDelay={460}
            />
          </div>
          <div style={{ maxWidth: 950 }}>
            <Caption delay={420}>
              <b style={{ color: C.emerald }}>14¢ per $1 — pass.</b>{" "}
              <b style={{ color: C.redHot }}>40¢ per $1 — fail.</b> Same company. Same numbers.
            </Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S3 — the lesson */}
      <Sequence from={781} durationInFrames={200} name="Lesson">
        <AbsoluteFill style={{ padding: PAD, justifyContent: "center", gap: 44 }}>
          <Slam size={116} delay={25}>Same numbers.</Slam>
          <Slam size={116} color={C.amber} delay={72}>
            Different math.
          </Slam>
          <div
            style={{
              fontFamily: FONT.mono,
              fontWeight: 800,
              fontSize: 74,
              color: C.ink,
              marginTop: 30,
              opacity: interpolate(frame, [781 + 104, 781 + 118], [0, 1], clamp),
            }}
          >
            <span style={{ color: C.redHot }}>2/3 say no</span>
            <span style={{ color: C.muted }}> · </span>
            <span style={{ color: C.emerald }}>1/3 says yes</span>
          </div>
          <div style={{ maxWidth: 950 }}>
            <Caption delay={130}>
              Neither is &quot;the truth&quot; — so anyone saying a stock is simply{" "}
              <b style={{ color: C.amber }}>&quot;fine&quot;</b> without naming their rulebook is skipping
              the part that decides the answer.
            </Caption>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* S4 — end card */}
      <Sequence from={981} name="EndCard">
        <Bg />
        <EndCard badge={ETN.badge} line="Passes AAOIFI. Fails FTSE & MSCI. Always check the rulebook." date={DATE} />
      </Sequence>

      <AbsoluteFill style={{ padding: PAD, justifyContent: "flex-end", pointerEvents: "none" }}>
        <Sequence from={0} durationInFrames={981} layout="none" name="Footer">
          <Foot />
        </Sequence>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
