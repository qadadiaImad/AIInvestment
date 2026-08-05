/**
 * "Rank the AI Stack: Who Breaks First" — Ranking / Tier-List.
 * Back-wall = the 5 AI-stack layers ranked worst→best health (from graph_analysis.json
 * layers): Application 53.6 (weakest) → Energy 58 → Chips 65.2 → Labs 66.4 → Infra 66.7
 * (healthiest, the twist). NVDA flagged as the #1 single-point-of-failure. HOST_QUANT.
 */
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Sequence, Audio, staticFile } from "remotion";
import { HOST_QUANT } from "./toon/host";
import { NewsStudio } from "./toon/studio";
import { FUN, BODY, PAL, Karaoke, Bug, Disclaimer, Chyron, BigFace, studioHost } from "./toon/reelkit";
import caps from "../public/tier_captions.json";

const C = caps as Record<string, { words: { w: string; t0: number; t1: number }[]; dur: number }>;
const A = 615, Cn = 160, D = 150;
export const QR_TIER_BEATS = { total: A + Cn + D };
const ABS = { t1: 6, t2: 200, t3: 400, t4: A + 6, t5: A + Cn + 6 };
const HOT = /[0-9]|first|healthiest|weakest|twist|failure/i;
const ACCENT = "#E7B23B";
const TICK = "AI STACK HEALTH · APPLICATION 53.6 (WEAKEST) · ENERGY 58.0 · CHIPS 65.2 · LABS 66.4 · INFRA 66.7 (HEALTHIEST) · NVDA = #1 SINGLE POINT OF FAILURE · V&V DEPENDENCY GRAPH · ";

const ROWS = [
  { name: "APPLICATION", score: 53.6, note: "the apps", c: PAL.red },
  { name: "ENERGY", score: 58.0, note: "the power grid", c: "#E88B2A" },
  { name: "CHIPS", score: 65.2, note: "NVDA · #1 point of failure", c: PAL.green },
  { name: "AI LABS", score: 66.4, note: "OpenAI · Anthropic", c: PAL.green },
  { name: "INFRASTRUCTURE", score: 66.7, note: "MSFT · AMZN · healthiest", c: PAL.mint },
];
const TierWall: React.FC<{ f: number }> = ({ f }) => (
  <g>
    <rect x="0" y="0" width="896" height="410" rx="18" fill="#0b1524" stroke="#22344c" strokeWidth="2" opacity="0.92" />
    <text x="28" y="46" fontFamily={BODY} fontWeight="900" fontSize="28" fill="#e6edf6">AI STACK · RANKED BY WHO BREAKS FIRST</text>
    {ROWS.map((r, i) => {
      const ap = interpolate(f, [50 + i * 58, 100 + i * 58], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
      const y = 78 + i * 62;
      const twist = i === 4;
      return (
        <g key={r.name} opacity={ap} transform={`translate(${(1 - ap) * 40} 0)`}>
          <circle cx="52" cy={y + 22} r="24" fill={r.c} /><text x="52" y={y + 31} textAnchor="middle" fontFamily={FUN} fontSize="30" fill="#0a1220">{i + 1}</text>
          <text x="92" y={y + 20} fontFamily={BODY} fontWeight="900" fontSize="27" fill="#fff">{r.name}</text>
          <text x="92" y={y + 46} fontFamily={BODY} fontWeight="700" fontSize="19" fill="#8fa0b5">{r.note}</text>
          <rect x="560" y={y + 4} width={(r.score - 45) / 25 * 260} height="36" rx="6" fill={r.c} opacity="0.85" />
          <text x="866" y={y + 32} textAnchor="end" fontFamily={FUN} fontSize="34" fill={r.c}>{r.score}</text>
          {twist && <text x="360" y={y + 20} fontFamily={BODY} fontWeight="900" fontSize="18" fill={PAL.mint}>◀ HEALTHIEST?!</text>}
        </g>
      );
    })}
  </g>
);

const Studio: React.FC = () => {
  const f = useCurrentFrame();
  const active = f < ABS.t2 ? "t1" : f < ABS.t3 ? "t2" : "t3";
  const acue = active === "t1" ? ABS.t1 : active === "t2" ? ABS.t2 : ABS.t3;
  const screen = (
    <g>
      <text x="215" y="66" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="26" fill={PAL.paper}>5 LAYERS</text>
      <text x="215" y="150" textAnchor="middle" fontFamily={FUN} fontSize="60" fill={ACCENT}>RANKED</text>
      <text x="215" y="210" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="22" fill="#A9B3C0">by who breaks first</text>
    </g>
  );
  return (
    <AbsoluteFill style={{ background: "#0a1017" }}>
      <AbsoluteFill><NewsStudio host={studioHost(f, HOST_QUANT)} screen={screen} screenLabel="● HEALTH SCORES" ticker={TICK} accent={ACCENT} skin={HOST_QUANT.skin} f={f} wall={<TierWall f={f} />} /></AbsoluteFill>
      <Chyron f={f} tag="AI STACK" text="TIER LIST · WHO BREAKS FIRST" red={false} />
      <Karaoke caps={C} id={active} cue={acue} hot={HOT} />
      <Bug /><Disclaimer text="Layer-health from our dependency graph · relative scores · not financial advice" />
    </AbsoluteFill>
  );
};
const Turn: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: "#20242E" }}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end" }}><BigFace theme={HOST_QUANT} f={f} mouth="flat" /></AbsoluteFill>
      <div style={{ position: "absolute", left: 40, right: 40, top: 240, textAlign: "center", zIndex: 4 }}>
        <div style={{ fontFamily: FUN, fontSize: 92, color: PAL.green, WebkitTextStroke: "5px #000", paintOrder: "stroke" }}>NVDA</div>
        <div style={{ fontFamily: BODY, fontWeight: 900, fontSize: 38, color: PAL.paper }}>ranks mid-health…</div>
        <div style={{ fontFamily: BODY, fontWeight: 900, fontSize: 32, color: PAL.red, marginTop: 8 }}>…but it's the #1 point of failure</div>
      </div>
      <Karaoke caps={C} id="t4" cue={6} hot={HOT} />
      <Bug /><Disclaimer text="Betweenness centrality from our dependency graph · not financial advice" />
    </AbsoluteFill>
  );
};
const Cta: React.FC = () => {
  const f = useCurrentFrame();
  const pop = interpolate(f, [0, 12], [0.85, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: PAL.ink, alignItems: "center", justifyContent: "flex-start" }}>
      <svg width="1080" height="500" viewBox="0 0 1080 500" style={{ marginTop: 70, transform: `scale(${pop})` }}>
        <g transform="translate(270 10) scale(0.78)">{studioHost(f, HOST_QUANT, false)}</g>
      </svg>
      <div style={{ textAlign: "center", padding: "0 56px" }}>
        <div style={{ fontFamily: FUN, fontSize: 62, color: ACCENT, WebkitTextStroke: "4px #000", paintOrder: "stroke", lineHeight: 1.05 }}>WHICH LAYER<br />CRACKS FIRST?</div>
        <div style={{ marginTop: 22, fontFamily: BODY, fontWeight: 900, fontSize: 40, color: PAL.mint }}>💬 Fight me in the comments</div>
        <div style={{ marginTop: 16, fontFamily: BODY, fontWeight: 700, fontSize: 23, color: "#9AA6B2" }}>Health scores from our AI-stack graph · relative · not financial advice</div>
      </div>
      <Karaoke caps={C} id="t5" cue={6} hot={HOT} />
    </AbsoluteFill>
  );
};

export const QuarterlyReportTier: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Audio src={staticFile("qr_news_bed.wav")} volume={0.14} />
    <Sequence from={ABS.t1}><Audio src={staticFile("tier_t1.mp3")} /></Sequence>
    <Sequence from={ABS.t2}><Audio src={staticFile("tier_t2.mp3")} /></Sequence>
    <Sequence from={ABS.t3}><Audio src={staticFile("tier_t3.mp3")} /></Sequence>
    <Sequence from={ABS.t4}><Audio src={staticFile("tier_t4.mp3")} /></Sequence>
    <Sequence from={ABS.t5}><Audio src={staticFile("tier_t5.mp3")} /></Sequence>
    <Sequence durationInFrames={A}><Studio /></Sequence>
    <Sequence from={A} durationInFrames={Cn}><Turn /></Sequence>
    <Sequence from={A + Cn} durationInFrames={D}><Cta /></Sequence>
  </AbsoluteFill>
);
