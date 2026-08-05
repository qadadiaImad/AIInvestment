/**
 * "Four Buyers Hold Up the Whole Thing" — Cascade / Scenario.
 * Back-wall = 4 hyperscaler seeds (MSFT/AMZN/GOOGL/META) rippling out through the stack:
 * modeled −10% capex cut reaches 66 names ≈ 49% of the mapped AI stack (graph_analysis.json
 * cascades → hyperscaler_capex_cut). A running counter climbs as the ripple spreads.
 * HOST_ANCHOR + Emma voice. Framed as one modeled path, not a forecast.
 */
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Sequence, Audio, staticFile } from "remotion";
import { HOST_ANCHOR } from "./toon/host";
import { NewsStudio } from "./toon/studio";
import { FUN, BODY, PAL, Karaoke, Bug, Disclaimer, Chyron, BigFace, studioHost } from "./toon/reelkit";
import caps from "../public/casc_captions.json";

const C = caps as Record<string, { words: { w: string; t0: number; t1: number }[]; dur: number }>;
const A = 560, Cn = 190, D = 160;
export const QR_CASCADE_BEATS = { total: A + Cn + D };
const ABS = { x1: 6, x2: 141, x3: 320, x4: A + 6, x5: A + Cn + 6 };
const HOT = /[0-9]|cascade|downstream|half|ripples|sixty/i;
const ACCENT = "#E0524D";
const TICK = "SCENARIO · HYPERSCALER CAPEX −10%   ·   SEEDS: MSFT / AMZN / GOOGL / META   ·   CASCADE REACHES 66 NAMES (≈49% OF MAPPED STACK)   ·   ONE MODELED PATH, NOT A FORECAST   ·   ";

const SEEDS = [
  { x: 150, label: "MSFT", c: "#4ea1ff" },
  { x: 350, label: "AMZN", c: "#E7B23B" },
  { x: 548, label: "GOOGL", c: "#7FE9C2" },
  { x: 748, label: "META", c: "#9d8bff" },
];
// deterministic-ish grid of downstream dots (11 cols × 8 rows = 88 cells; 66 light up)
const COLS = 11, ROWS = 8, TOTAL = COLS * ROWS, HIT = 66;
const CascadeWall: React.FC<{ f: number }> = ({ f }) => {
  const seedGlow = interpolate(f, [10, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const spread = interpolate(f, [ABS.x3 - 40, ABS.x3 + 150], [0, HIT], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const lit = Math.floor(spread);
  const reach = Math.round((lit / 134) * 100); // 134 = mapped names in the stack
  return (
    <g>
      <rect x="0" y="0" width="896" height="410" rx="18" fill="#150c0e" stroke="#3d2224" strokeWidth="2" opacity="0.94" />
      <text x="28" y="42" fontFamily={BODY} fontWeight="900" fontSize="26" fill="#f4dede">IF THE 4 BIG BUYERS PULL BACK 10%…</text>
      {/* seed row */}
      {SEEDS.map((s) => (
        <g key={s.label} opacity={0.35 + seedGlow * 0.65}>
          <rect x={s.x - 62} y="58" width="124" height="48" rx="12" fill="#1c1012" stroke={s.c} strokeWidth="3" />
          <text x={s.x} y="89" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="24" fill="#fff">{s.label}</text>
        </g>
      ))}
      {/* downstream dot field */}
      <g transform="translate(150 140)">
        {Array.from({ length: TOTAL }).map((_, i) => {
          const col = i % COLS, row = Math.floor(i / COLS);
          // ripple order: distance from the field's top-center
          const rank = row * COLS + ((col * 7 + row * 3) % COLS);
          const on = rank < lit;
          return <circle key={i} cx={col * 60} cy={row * 30} r="9" fill={on ? PAL.red : "#3a2224"} opacity={on ? 1 : 0.5} />;
        })}
      </g>
      {/* running counter */}
      <g transform="translate(28 372)">
        <text x="0" y="0" fontFamily={FUN} fontSize="40" fill={PAL.red}>{lit}</text>
        <text x="86" y="-2" fontFamily={BODY} fontWeight="800" fontSize="22" fill="#f0c9c9">names hit</text>
        <text x="600" y="0" textAnchor="end" fontFamily={FUN} fontSize="40" fill={PAL.gold}>{reach}%</text>
        <text x="616" y="-2" fontFamily={BODY} fontWeight="800" fontSize="22" fill="#f0c9c9">of the stack</text>
      </g>
    </g>
  );
};

const Studio: React.FC = () => {
  const f = useCurrentFrame();
  const active = f < ABS.x2 ? "x1" : f < ABS.x3 ? "x2" : "x3";
  const acue = active === "x1" ? ABS.x1 : active === "x2" ? ABS.x2 : ABS.x3;
  const screen = (
    <g>
      <text x="215" y="66" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="26" fill={PAL.paper}>4 BUYERS</text>
      <text x="215" y="150" textAnchor="middle" fontFamily={FUN} fontSize="58" fill={ACCENT}>= THE</text>
      <text x="215" y="212" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="30" fill={PAL.gold}>DEMAND SIDE</text>
    </g>
  );
  return (
    <AbsoluteFill style={{ background: "#0a1017" }}>
      <AbsoluteFill><NewsStudio host={studioHost(f, HOST_ANCHOR)} screen={screen} screenLabel="● SCENARIO" ticker={TICK} accent={ACCENT} skin={HOST_ANCHOR.skin} f={f} wall={<CascadeWall f={f} />} /></AbsoluteFill>
      <Chyron f={f} tag="SCENARIO" text="THE CASCADE · IF 4 BUYERS BLINK" red={true} />
      <Karaoke caps={C} id={active} cue={acue} hot={HOT} />
      <Bug /><Disclaimer text="Modeled ripple on our dependency graph · one scenario, not a forecast · not financial advice" />
    </AbsoluteFill>
  );
};
const Turn: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: "#231416" }}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end" }}><BigFace theme={HOST_ANCHOR} f={f} mouth="flat" /></AbsoluteFill>
      <div style={{ position: "absolute", left: 40, right: 40, top: 244, textAlign: "center", zIndex: 4 }}>
        <div style={{ fontFamily: FUN, fontSize: 68, color: PAL.paper, WebkitTextStroke: "4px #000", paintOrder: "stroke", lineHeight: 1.05 }}>NOT A<br />PREDICTION.</div>
        <div style={{ fontFamily: BODY, fontWeight: 900, fontSize: 36, color: ACCENT, marginTop: 12 }}>Just what "downstream" means.</div>
      </div>
      <Karaoke caps={C} id="x4" cue={6} hot={HOT} />
      <Bug /><Disclaimer text="Modeled on our dependency graph · one scenario, not a forecast · not financial advice" />
    </AbsoluteFill>
  );
};
const Cta: React.FC = () => {
  const f = useCurrentFrame();
  const pop = interpolate(f, [0, 12], [0.85, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: PAL.ink, alignItems: "center", justifyContent: "flex-start" }}>
      <svg width="1080" height="500" viewBox="0 0 1080 500" style={{ marginTop: 70, transform: `scale(${pop})` }}>
        <g transform="translate(270 10) scale(0.78)">{studioHost(f, HOST_ANCHOR, false)}</g>
      </svg>
      <div style={{ textAlign: "center", padding: "0 56px" }}>
        <div style={{ fontFamily: FUN, fontSize: 56, color: ACCENT, WebkitTextStroke: "4px #000", paintOrder: "stroke", lineHeight: 1.05 }}>FOUR EARNINGS CALLS<br />FROM A CASCADE?</div>
        <div style={{ marginTop: 22, fontFamily: BODY, fontWeight: 900, fontSize: 40, color: PAL.mint }}>💬 Tell me below</div>
        <div style={{ marginTop: 16, fontFamily: BODY, fontWeight: 700, fontSize: 23, color: "#9AA6B2" }}>Modeled scenario on our dependency graph · not a forecast · not financial advice</div>
      </div>
      <Karaoke caps={C} id="x5" cue={6} hot={HOT} />
    </AbsoluteFill>
  );
};

export const QuarterlyReportCascade: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Audio src={staticFile("qr_news_bed.wav")} volume={0.14} />
    <Sequence from={ABS.x1}><Audio src={staticFile("casc_x1.mp3")} /></Sequence>
    <Sequence from={ABS.x2}><Audio src={staticFile("casc_x2.mp3")} /></Sequence>
    <Sequence from={ABS.x3}><Audio src={staticFile("casc_x3.mp3")} /></Sequence>
    <Sequence from={ABS.x4}><Audio src={staticFile("casc_x4.mp3")} /></Sequence>
    <Sequence from={ABS.x5}><Audio src={staticFile("casc_x5.mp3")} /></Sequence>
    <Sequence durationInFrames={A}><Studio /></Sequence>
    <Sequence from={A} durationInFrames={Cn}><Turn /></Sequence>
    <Sequence from={A + Cn} durationInFrames={D}><Cta /></Sequence>
  </AbsoluteFill>
);
