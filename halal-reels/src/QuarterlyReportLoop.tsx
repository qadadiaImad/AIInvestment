/**
 * "The Loop That Pays For Itself" — Mechanism Explainer (circular AI deals).
 * Back-wall draws the money loop: MSFT ⇄ OpenAI (invests / buys cloud), NVDA ⇄ OpenAI
 * (invests / buys chips) — all four directed edges are in our graph_analysis.json.
 * HOST_QUANT + Brian voice. No valuation verdict; the payoff is the loop closing.
 */
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Sequence, Audio, staticFile } from "remotion";
import { HOST_QUANT } from "./toon/host";
import { NewsStudio } from "./toon/studio";
import { FUN, BODY, PAL, isBlink, Karaoke, Bug, Disclaimer, Chyron, BigFace, studioHost } from "./toon/reelkit";
import caps from "../public/loop_captions.json";

const C = caps as Record<string, { words: { w: string; t0: number; t1: number }[]; dur: number }>;
const A = 535, Cn = 150, D = 155;
export const QR_LOOP_BEATS = { total: A + Cn + D };
const ABS = { l1: 6, l2: 190, l3: 360, l4: A + 6, l5: A + Cn + 6 };
const HOT = /[0-9]|circle|back|money|bubble/i;
const ACCENT = "#7FE9C2";
const TICK = "AI CIRCULAR DEALS   ·   MSFT ⇄ OpenAI (equity / cloud)   ·   NVDA ⇄ OpenAI (equity / chips)   ·   SOURCE: V&V DEPENDENCY GRAPH   ·   EDUCATIONAL, NOT ADVICE   ·   ";

const Node: React.FC<{ x: number; y: number; label: string; c: string }> = ({ x, y, label, c }) => (
  <g>
    <rect x={x - 78} y={y - 34} width="156" height="68" rx="14" fill="#0e1a2c" stroke={c} strokeWidth="3" />
    <text x={x} y={y + 10} textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="34" fill="#fff">{label}</text>
  </g>
);
const LoopWall: React.FC<{ f: number }> = ({ f }) => {
  const a1 = interpolate(f, [24, 84], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const a2 = interpolate(f, [190, 250], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const flow = -(f * 1.5) % 32;
  const arrow = (d: string, c: string, label: string, lx: number, ly: number, live: boolean) => (
    <g>
      <path d={d} fill="none" stroke={c} strokeWidth="6" markerEnd="url(#lp-arrow)" strokeDasharray={live ? "14 8" : "none"} strokeDashoffset={live ? flow : 0} strokeLinecap="round" />
      <text x={lx} y={ly} textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="21" fill={c}>{label}</text>
    </g>
  );
  const live = f > 355;
  return (
    <g>
      <defs><marker id="lp-arrow" markerWidth="9" markerHeight="9" refX="6" refY="4.5" orient="auto"><path d="M0 0 L9 4.5 L0 9 z" fill="#fff" /></marker></defs>
      <rect x="0" y="0" width="896" height="410" rx="18" fill="#0b1524" stroke="#22344c" strokeWidth="2" opacity="0.92" />
      <text x="28" y="46" fontFamily={BODY} fontWeight="900" fontSize="28" fill="#e6edf6">FOLLOW THE MONEY — AI, IN A CIRCLE</text>
      <g transform="translate(0 30)"><Node x={448} y={210} label="OpenAI" c={PAL.gold} /></g>
      {/* MSFT loop */}
      <g opacity={a1} transform="translate(0 30)">
        <Node x={150} y={150} label="MSFT" c="#4ea1ff" />
        {arrow("M228 150 C300 140 340 170 378 200", "#4ea1ff", "invests $", 300, 150, live)}
        {arrow("M378 250 C330 288 250 288 210 200", PAL.mint, "buys its cloud", 262, 300, live)}
      </g>
      {/* NVDA loop */}
      <g opacity={a2} transform="translate(0 30)">
        <Node x={746} y={150} label="NVDA" c={PAL.green} />
        {arrow("M668 150 C600 140 556 170 518 200", PAL.green, "invests $", 600, 150, live)}
        {arrow("M518 250 C566 288 646 288 686 200", "#ffd27a", "buys its chips", 636, 300, live)}
      </g>
    </g>
  );
};

const Studio: React.FC = () => {
  const f = useCurrentFrame();
  const active = f < ABS.l2 ? "l1" : f < ABS.l3 ? "l2" : "l3";
  const acue = active === "l1" ? ABS.l1 : active === "l2" ? ABS.l2 : ABS.l3;
  const screen = (
    <g>
      <text x="215" y="70" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="30" fill={PAL.paper}>THE CIRCLE</text>
      <text x="215" y="150" textAnchor="middle" fontFamily={FUN} fontSize="66" fill={ACCENT}>$ → $</text>
      <text x="215" y="212" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="24" fill="#A9B3C0">out… and back</text>
    </g>
  );
  return (
    <AbsoluteFill style={{ background: "#0a1017" }}>
      <AbsoluteFill><NewsStudio host={studioHost(f, HOST_QUANT)} screen={screen} screenLabel="● THE DEAL" ticker={TICK} accent={ACCENT} skin={HOST_QUANT.skin} f={f} wall={<LoopWall f={f} />} /></AbsoluteFill>
      <Chyron f={f} tag="THE AI TRADE" text="CIRCULAR FINANCING · EXPLAINED" red={false} />
      <Karaoke caps={C} id={active} cue={acue} hot={HOT} />
      <Bug /><Disclaimer text="From our AI-stack dependency graph · relationships as mapped · not financial advice" />
    </AbsoluteFill>
  );
};

const Turn: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: "#20242E" }}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end" }}><BigFace theme={HOST_QUANT} f={f} mouth="flat" /></AbsoluteFill>
      <div style={{ position: "absolute", left: 40, right: 40, top: 250, textAlign: "center", zIndex: 4 }}>
        <div style={{ fontFamily: FUN, fontSize: 70, color: PAL.paper, WebkitTextStroke: "4px #000", paintOrder: "stroke", lineHeight: 1.05 }}>NOBODY'S<br />LYING.</div>
        <div style={{ fontFamily: BODY, fontWeight: 900, fontSize: 40, color: ACCENT, marginTop: 12 }}>It's just… a circle.</div>
      </div>
      <Karaoke caps={C} id="l4" cue={6} hot={HOT} />
      <Bug /><Disclaimer text="From our AI-stack dependency graph · not financial advice" />
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
        <div style={{ fontFamily: FUN, fontSize: 60, color: ACCENT, WebkitTextStroke: "4px #000", paintOrder: "stroke", lineHeight: 1.05 }}>GENIUS — OR A<br />BUBBLE ON A LOOP?</div>
        <div style={{ marginTop: 22, fontFamily: BODY, fontWeight: 900, fontSize: 40, color: PAL.mint }}>💬 What do you call this?</div>
        <div style={{ marginTop: 16, fontFamily: BODY, fontWeight: 700, fontSize: 23, color: "#9AA6B2" }}>Deals as mapped in our dependency graph · educational · not financial advice</div>
      </div>
      <Karaoke caps={C} id="l5" cue={6} hot={HOT} />
    </AbsoluteFill>
  );
};

export const QuarterlyReportLoop: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Audio src={staticFile("qr_news_bed.wav")} volume={0.14} />
    <Sequence from={ABS.l1}><Audio src={staticFile("loop_l1.mp3")} /></Sequence>
    <Sequence from={ABS.l2}><Audio src={staticFile("loop_l2.mp3")} /></Sequence>
    <Sequence from={ABS.l3}><Audio src={staticFile("loop_l3.mp3")} /></Sequence>
    <Sequence from={ABS.l4}><Audio src={staticFile("loop_l4.mp3")} /></Sequence>
    <Sequence from={ABS.l5}><Audio src={staticFile("loop_l5.mp3")} /></Sequence>
    <Sequence durationInFrames={A}><Studio /></Sequence>
    <Sequence from={A} durationInFrames={Cn}><Turn /></Sequence>
    <Sequence from={A + Cn} durationInFrames={D}><Cta /></Sequence>
  </AbsoluteFill>
);
