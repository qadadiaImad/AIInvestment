/**
 * "The World Owes $348 Trillion — To WHO?" — debt & bonds explainer (long form, ~91s).
 * Question → mechanism (bonds) → reveal (the creditor is mostly us). Analyst-detective host
 * + Christopher voice. Debuts the DEBT CLOCK newsroom fixture (toon/props). All figures
 * stamped 2026-08-06: IIF Global Debt Monitor (Q4'25 $348.3T), US Treasury / CRS holders,
 * CFRB/PGPF net-interest ($970B FY25 > $917B defense). Educational, not financial advice.
 */
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Sequence, Audio, staticFile } from "remotion";
import { HOST_ANALYST } from "./toon/host";
import { NewsStudio } from "./toon/studio";
import { FUN, BODY, PAL, Karaoke, Bug, Disclaimer, Chyron, BigFace, studioHost } from "./toon/reelkit";
import { DebtClock } from "./toon/props";
import caps from "../public/debt_captions.json";

const C = caps as Record<string, { words: { w: string; t0: number; t1: number }[]; dur: number }>;
const A = 1995, Cn = 420, D = 330;
export const QR_DEBT_BEATS = { total: A + Cn + D };
const ABS = { d1: 6, d2: 320, d3: 746, d4: 981, d5: 1424, d6: A + 6, d7: A + Cn + 6 };
const HOT = /[0-9]|trillion|billion|bond|who|itself|you|your|interest|military|red|black/i;
const GREEN = "#7FE9C2";
const TICK = "GLOBAL DEBT $348.3T (IIF, Q4'25)   ·   HOUSEHOLDS $64.6T · COMPANIES $100.6T · GOVERNMENTS $106.7T · BANKS $76.4T   ·   U.S. NET INTEREST $970B FY25 > DEFENSE $917B   ·   EDUCATIONAL, NOT ADVICE   ·   ";

const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

/* ---------- back-wall beats (896 × 410 region) ---------- */

const HookWall: React.FC<{ f: number }> = ({ f }) => {
  const q = 1 + Math.sin(f / 6) * 0.06;
  return (
    <g>
      <text x="448" y="70" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="30" letterSpacing="2" fill="#9fb0c6">THE WHOLE WORLD IS IN DEBT</text>
      <text x="448" y="196" textAnchor="middle" fontFamily={FUN} fontSize="118" fill={GREEN}>$348 TRILLION</text>
      <text x="300" y="330" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="52" fill="#e6edf6">…in debt to</text>
      <g transform={`translate(600 300) scale(${q})`}><text x="0" y="0" textAnchor="middle" fontFamily={FUN} fontSize="150" fill={PAL.red}>WHO?</text></g>
    </g>
  );
};

const STACK = [
  { name: "Households", v: 64.6, c: "#4ea1ff" },
  { name: "Companies", v: 100.6, c: GREEN },
  { name: "Governments", v: 106.7, c: PAL.gold },
  { name: "Banks", v: 76.4, c: "#9d8bff" },
];
const StackWall: React.FC<{ f: number; from: number }> = ({ f, from }) => {
  const L = f - from;
  const shown = STACK.reduce((a, s, i) => a + (interpolate(L, [i * 62, i * 62 + 45], [0, 1], clamp) * s.v), 0);
  return (
    <g>
      <text x="28" y="44" fontFamily={BODY} fontWeight="900" fontSize="27" fill="#e6edf6">IT'S NOT ONE LOAN — IT'S EVERYONE</text>
      {STACK.map((s, i) => {
        const g = interpolate(L, [i * 62, i * 62 + 45], [0, 1], clamp);
        const y = 78 + i * 74;
        return (
          <g key={s.name} opacity={0.35 + g * 0.65}>
            <text x="28" y={y + 34} fontFamily={BODY} fontWeight="800" fontSize="23" fill="#c9d4e2">{s.name}</text>
            <rect x="270" y={y + 8} width={g * (s.v / 120) * 470} height="42" rx="7" fill={s.c} />
            <text x={278 + g * (s.v / 120) * 470} y={y + 38} fontFamily={FUN} fontSize="30" fill={s.c}>${s.v}T</text>
          </g>
        );
      })}
      <text x="868" y="404" textAnchor="end" fontFamily={FUN} fontSize="34" fill="#fff">= ${shown.toFixed(1)}T</text>
    </g>
  );
};

const QWall: React.FC<{ f: number }> = ({ f }) => {
  const p = 1 + Math.sin(f / 7) * 0.05;
  return (
    <g>
      <text x="448" y="60" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="26" fill="#c9d4e2">EVERY DOLLAR OWED IS A DOLLAR SOMEONE IS OWED</text>
      <g transform={`translate(448 232) scale(${p})`}><text x="0" y="0" textAnchor="middle" fontFamily={FUN} fontSize="210" fill={PAL.gold}>?</text></g>
      <text x="150" y="250" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="34" fill={PAL.red}>IN THE RED</text>
      <text x="748" y="250" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="34" fill={GREEN}>IN THE BLACK</text>
      <text x="448" y="384" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="26" fill="#e6edf6">so who's on the other side?</text>
    </g>
  );
};

const BondWall: React.FC<{ f: number }> = ({ f }) => {
  const coin = interpolate((f - 981) % 90, [0, 90], [0, 1]);
  const box = (x: number, label: string, c: string) => (
    <g>
      <rect x={x - 76} y="180" width="152" height="74" rx="14" fill="#0e1a2c" stroke={c} strokeWidth="3" />
      <text x={x} y="225" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="26" fill="#fff">{label}</text>
    </g>
  );
  return (
    <g>
      <text x="448" y="40" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="27" fill="#e6edf6">THE DEBT IS A PILE OF THESE: A BOND</text>
      {box(120, "GOV'T", PAL.gold)}
      {box(776, "BUYER", GREEN)}
      {/* certificate */}
      <g transform="translate(448 217)">
        <rect x="-118" y="-70" width="236" height="140" rx="10" fill="#fdf6e3" stroke="#caa94b" strokeWidth="4" />
        <text x="0" y="-38" textAnchor="middle" fontFamily={FUN} fontSize="30" fill="#7a5c12">BOND · IOU</text>
        <text x="0" y="2" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="34" fill="#141414">$100</text>
        <text x="0" y="34" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="18" fill="#6a5a2a">pays interest · due 2035</text>
      </g>
      {/* flows */}
      <text x="284" y="150" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="19" fill={PAL.gold}>sells the IOU →</text>
      <text x="284" y="300" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="19" fill={GREEN}>← $100 cash now</text>
      <text x="612" y="150" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="19" fill={GREEN}>← lends $100</text>
      <text x="612" y="300" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="19" fill={PAL.gold}>paid back + interest →</text>
      <circle cx={196 + coin * 504} cy="330" r="9" fill={PAL.gold} />
    </g>
  );
};

const HOLD = [
  { name: "You — pensions, banks, funds", pct: 36, c: GREEN, you: true },
  { name: "Gov trust funds (Soc. Security)", pct: 20, c: PAL.mint, you: true },
  { name: "Federal Reserve", pct: 13, c: PAL.gold, you: false },
  { name: "Foreign (Japan · UK · China…)", pct: 31, c: "#5b7089", you: false },
];
const HoldersWall: React.FC<{ f: number }> = ({ f }) => {
  const rise = interpolate(f, [1424, 1470], [0, 1], clamp);
  const R = 118, T = 54, cx = 250, cy = 214, Circ = 2 * Math.PI * R;
  let off = 0;
  return (
    <g opacity={rise}>
      <text x="28" y="40" fontFamily={BODY} fontWeight="900" fontSize="26" fill="#e6edf6">WHO ACTUALLY HOLDS U.S. DEBT</text>
      <g transform={`translate(${cx} ${cy}) rotate(-90)`}>
        {HOLD.map((h) => {
          const seg = (h.pct / 100) * Circ;
          const el = <circle key={h.name} r={R} fill="none" stroke={h.c} strokeWidth={T} strokeDasharray={`${seg} ${Circ - seg}`} strokeDashoffset={-off} />;
          off += seg;
          return el;
        })}
      </g>
      <text x={cx} y={cy - 6} textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="22" fill="#fff">MOSTLY</text>
      <text x={cx} y={cy + 30} textAnchor="middle" fontFamily={FUN} fontSize="52" fill={GREEN}>YOU</text>
      {/* legend */}
      {HOLD.map((h, i) => (
        <g key={h.name} transform={`translate(452 ${96 + i * 66})`}>
          <rect x="0" y="-22" width="30" height="30" rx="6" fill={h.c} stroke={h.you ? "#fff" : "none"} strokeWidth="2" />
          <text x="44" y="-2" fontFamily={BODY} fontWeight={h.you ? 900 : 700} fontSize="21" fill={h.you ? "#fff" : "#b9c4d2"}>{h.name}</text>
          <text x="44" y="24" fontFamily={FUN} fontSize="26" fill={h.c}>{h.pct}%</text>
        </g>
      ))}
    </g>
  );
};

/* ---------- scenes ---------- */

const ClockScreen: React.FC<{ f: number }> = ({ f }) => (
  <g transform="translate(83 96)"><DebtClock f={f} digitSize={20} label="TICKING UP EVERY SECOND" /></g>
);

const Studio: React.FC = () => {
  const f = useCurrentFrame();
  const active = f < ABS.d2 ? "d1" : f < ABS.d3 ? "d2" : f < ABS.d4 ? "d3" : f < ABS.d5 ? "d4" : "d5";
  const acue = ABS[active as keyof typeof ABS];
  const wall = active === "d1" ? <HookWall f={f} /> : active === "d2" ? <StackWall f={f} from={ABS.d2} /> : active === "d3" ? <QWall f={f} /> : active === "d4" ? <BondWall f={f} /> : <HoldersWall f={f} />;
  return (
    <AbsoluteFill style={{ background: "#0a1017" }}>
      <AbsoluteFill><NewsStudio host={studioHost(f, HOST_ANALYST)} screen={<ClockScreen f={f} />} screenLabel="● WORLD DEBT" ticker={TICK} accent={GREEN} skin={HOST_ANALYST.skin} f={f} wall={wall} /></AbsoluteFill>
      <Chyron f={f} tag="FOLLOW THE MONEY" text="WHO DOES THE WORLD OWE?" red={false} />
      <Karaoke caps={C} id={active} cue={acue} hot={HOT} max={6} />
      <Bug /><Disclaimer text="Figures Aug 2026 · IIF · US Treasury · CRS · educational, not financial advice" />
    </AbsoluteFill>
  );
};

const Kicker: React.FC = () => {
  const f = useCurrentFrame();
  const g = interpolate(f, [10, 80], [0, 1], clamp);
  const bar = (x: number, v: number, cap: number, label: string, c: string, hot: boolean) => {
    const h = (v / cap) * 430 * g;
    return (
      <g>
        <rect x={x} y={640 - h} width="230" height={h} rx="10" fill={c} />
        <text x={x + 115} y={620 - h} textAnchor="middle" fontFamily={FUN} fontSize={hot ? 56 : 46} fill={c}>${v}B</text>
        <text x={x + 115} y="690" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="30" fill="#e6edf6">{label}</text>
      </g>
    );
  };
  return (
    <AbsoluteFill style={{ background: "#1a0d0d" }}>
      <div style={{ position: "absolute", top: 120, left: 0, right: 0, textAlign: "center", zIndex: 3 }}>
        <div style={{ fontFamily: FUN, fontSize: 74, color: PAL.paper, WebkitTextStroke: "4px #000", paintOrder: "stroke" }}>THE PART THAT STINGS</div>
        <div style={{ fontFamily: BODY, fontWeight: 900, fontSize: 34, color: PAL.red, marginTop: 8 }}>just the INTEREST &gt; the whole military</div>
      </div>
      <svg width="1080" height="820" viewBox="0 0 1080 820" style={{ position: "absolute", top: 300 }}>
        {bar(280, 970, 970, "INTEREST", PAL.red, true)}
        {bar(580, 917, 970, "DEFENSE", "#8593a6", false)}
      </svg>
      <div style={{ position: "absolute", bottom: 300, left: 0, right: 0, textAlign: "center", fontFamily: BODY, fontWeight: 800, fontSize: 26, color: "#c9b7b7" }}>U.S. net interest, FY2025 — paid, not paying it down</div>
      <Karaoke caps={C} id="d6" cue={6} hot={HOT} max={6} />
      <Bug /><Disclaimer text="Sources: CRFB · PGPF (FY2025) · educational, not financial advice" />
    </AbsoluteFill>
  );
};

const Cta: React.FC = () => {
  const f = useCurrentFrame();
  const pop = interpolate(f, [0, 12], [0.8, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: PAL.ink, alignItems: "center", justifyContent: "flex-start" }}>
      <svg width="1000" height="150" viewBox="0 0 1000 150" style={{ marginTop: 92, transform: `scale(${pop})` }}>
        <g transform="translate(150 6)"><DebtClock f={f + ABS.d1} digitSize={40} label="STILL TICKING…" /></g>
      </svg>
      <svg width="1080" height="440" viewBox="0 0 1080 440">
        <g transform="translate(270 8) scale(0.7)">{studioHost(f, HOST_ANALYST, false)}</g>
      </svg>
      <div style={{ textAlign: "center", padding: "0 56px", marginTop: -8 }}>
        <div style={{ fontFamily: FUN, fontSize: 60, color: GREEN, WebkitTextStroke: "4px #000", paintOrder: "stroke", lineHeight: 1.05 }}>A WORLD THAT OWES<br />ITSELF TRILLIONS</div>
        <div style={{ marginTop: 18, fontFamily: BODY, fontWeight: 900, fontSize: 38, color: PAL.mint }}>💬 Genius, or a time bomb?</div>
        <div style={{ marginTop: 14, fontFamily: BODY, fontWeight: 700, fontSize: 22, color: "#9AA6B2" }}>Figures Aug 2026 · IIF / US Treasury / CRFB · educational, not financial advice</div>
      </div>
      <Karaoke caps={C} id="d7" cue={6} hot={HOT} max={6} />
    </AbsoluteFill>
  );
};

export const QuarterlyReportDebt: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Audio src={staticFile("qr_news_bed.wav")} volume={0.12} />
    <Sequence from={ABS.d1}><Audio src={staticFile("debt_d1.mp3")} /></Sequence>
    <Sequence from={ABS.d2}><Audio src={staticFile("debt_d2.mp3")} /></Sequence>
    <Sequence from={ABS.d3}><Audio src={staticFile("debt_d3.mp3")} /></Sequence>
    <Sequence from={ABS.d4}><Audio src={staticFile("debt_d4.mp3")} /></Sequence>
    <Sequence from={ABS.d5}><Audio src={staticFile("debt_d5.mp3")} /></Sequence>
    <Sequence from={ABS.d6}><Audio src={staticFile("debt_d6.mp3")} /></Sequence>
    <Sequence from={ABS.d7}><Audio src={staticFile("debt_d7.mp3")} /></Sequence>
    <Sequence durationInFrames={A}><Studio /></Sequence>
    <Sequence from={A} durationInFrames={Cn}><Kicker /></Sequence>
    <Sequence from={A + Cn} durationInFrames={D}><Cta /></Sequence>
  </AbsoluteFill>
);
