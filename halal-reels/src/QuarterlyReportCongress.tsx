/**
 * QuarterlyReport — "917 Days Late" (Follow-the-Money investigation).
 * Non-valuation format from finance-reel-formats: a paper-trail episode built on our
 * own committed congress.json. HOST_ANALYST (navy) as the deadpan detective, a distinct
 * male neural voice (Christopher). Filing document cards on the LIVE screen + a
 * STOCK-Act 45-vs-917-day timeline on the back wall. Compliance: reported/filed public
 * records, NOT an accusation of wrongdoing, not financial advice.
 *
 * Verified facts (web/public/data/congress.json, 2026-08-05, perishable):
 *   McCormick (GA-06)  MSFT buy 03/15/2023 -> filed 09/17/2025 = 917-day lag
 *   McClain  (MI-09)   NVDA/AMD/TSM 03/11/2024 -> filed 08/13/2025 = 520-day lag  · STOCK Act = 45 days
 * Render: npx remotion render QuarterlyReportCongress out/quarterly_report_congress.mp4
 */
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Sequence, Audio, staticFile } from "remotion";
import { loadFont as loadLuckiest } from "@remotion/google-fonts/LuckiestGuy";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { PremiumHost, HOST_ANALYST } from "./toon/host";
import { NewsStudio } from "./toon/studio";
import caps from "../public/congress_captions.json";

const luckiest = loadLuckiest("normal", { weights: ["400"], subsets: ["latin"] });
const inter = loadInter("normal", { weights: ["700", "800", "900"], subsets: ["latin"] });
const FUN = luckiest.fontFamily;
const BODY = inter.fontFamily;

const P = { gold: "#E7B23B", mint: "#7FE9C2", red: "#E0524D", green: "#34D399", ink: "#141414", paper: "#FFF6E9" };
const ACCENT = "#E7B23B";
const F = 30;
type Cap = { words: { w: string; t0: number; t1: number }[]; dur: number };
const C = caps as Record<string, Cap>;

const A = 440, B = 275, Cn = 206, D = 200;
export const QR_CONGRESS_BEATS = { total: A + B + Cn + D }; // 1121 = ~37s
const ABS = { c1: 6, c2: 216, c3: A + 6, c4: A + B + 6, c5: A + B + Cn + 6 };

const isBlink = (f: number) => { const c = f % 78; return c < 4 || (c > 40 && c < 44); };
const flap = (f: number) => Math.floor(f / 4) % 2 === 0;

const CTICK = "STOCK ACT: 45 DAYS TO DISCLOSE A TRADE   ·   McCORMICK (GA-06) FILED MSFT 917 DAYS LATE   ·   McCLAIN (MI-09) FILED NVDA/AMD/TSM 520 DAYS LATE   ·   SELF-REPORTED · NOT AN ACCUSATION   ·   ";

const Karaoke: React.FC<{ id: keyof typeof C; cue: number; bottom?: number }> = ({ id, cue, bottom = 205 }) => {
  const f = useCurrentFrame();
  const cap = C[id];
  if (!cap) return null;
  const tt = (f - cue) / F;
  if (tt < -0.15 || tt > cap.dur + 0.4) return null;
  return (
    <div style={{ position: "absolute", left: 50, right: 50, bottom, textAlign: "center", lineHeight: 1.16, zIndex: 4 }}>
      {cap.words.map((w, i) => {
        const active = tt >= w.t0 && tt < w.t1;
        const spoken = tt >= w.t1;
        const hot = /[0-9]|days|late|rule/i.test(w.w);
        const color = active ? (hot ? P.gold : P.mint) : spoken ? P.paper : "rgba(255,246,233,0.5)";
        return <span key={i} style={{ display: "inline-block", margin: "4px 10px", fontFamily: BODY, fontWeight: 900, fontSize: 54, color, WebkitTextStroke: `3px ${P.ink}`, paintOrder: "stroke", transform: `scale(${active ? 1.1 : 1})`, textShadow: "0 6px 16px rgba(0,0,0,.5)" }}>{w.w}</span>;
      })}
    </div>
  );
};
const Bug: React.FC = () => (
  <div style={{ position: "absolute", left: 40, top: 40, fontFamily: BODY, fontWeight: 800, fontSize: 26, color: P.paper, letterSpacing: 1, textShadow: "0 2px 8px #000", zIndex: 5 }}>V<span style={{ color: P.mint }}>&amp;</span>V · QUARTERLY REPORT</div>
);
const Disclaimer: React.FC = () => (
  <div style={{ position: "absolute", left: 0, right: 0, bottom: 108, textAlign: "center", fontFamily: BODY, fontWeight: 700, fontSize: 21, color: "#DfE5Ec", textShadow: "0 1px 8px #000", zIndex: 6 }}>Public filings · reported, not an accusation of wrongdoing · not financial advice</div>
);
const Chyron: React.FC<{ f: number }> = ({ f }) => {
  const x = interpolate(f, [4, 16], [1200, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const blink = Math.floor(f / 12) % 2 === 0;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 96, transform: `translateX(${x}px)`, display: "flex", alignItems: "center", zIndex: 5 }}>
      <div style={{ background: blink ? "#D63A34" : "#8f1f1b", color: "#fff", fontFamily: BODY, fontWeight: 900, fontSize: 30, padding: "12px 20px" }}>● FOLLOW THE MONEY</div>
      <div style={{ background: "rgba(10,13,18,.92)", color: "#fff", fontFamily: BODY, fontWeight: 800, fontSize: 30, padding: "12px 22px" }}>CONGRESS · STOCK ACT FILINGS</div>
    </div>
  );
};

// LIVE-screen content: a House filing card
const FilingCard: React.FC<{ tickers: string; traded: string; filed: string; lag: string }> = ({ tickers, traded, filed, lag }) => (
  <g>
    <text x="215" y="42" textAnchor="middle" fontFamily={FUN} fontSize="40" fill={P.gold}>{tickers}</text>
    <text x="215" y="74" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="21" fill={P.mint}>PURCHASE</text>
    <line x1="34" y1="92" x2="402" y2="92" stroke="#22344c" strokeWidth="2" />
    <text x="34" y="124" fontFamily={BODY} fontWeight="700" fontSize="22" fill="#A9B3C0">TRADED</text>
    <text x="402" y="124" textAnchor="end" fontFamily={BODY} fontWeight="800" fontSize="22" fill={P.paper}>{traded}</text>
    <text x="34" y="156" fontFamily={BODY} fontWeight="700" fontSize="22" fill="#A9B3C0">FILED</text>
    <text x="402" y="156" textAnchor="end" fontFamily={BODY} fontWeight="800" fontSize="22" fill={P.paper}>{filed}</text>
    <text x="215" y="234" textAnchor="middle" fontFamily={FUN} fontSize="72" fill={P.red}>{lag}</text>
    <text x="215" y="270" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="24" fill={P.red}>DAYS LATE</text>
  </g>
);

// back wall: STOCK Act 45-day rule vs actual filing lags
const StockActWall: React.FC<{ f: number }> = ({ f }) => {
  const appear = interpolate(f, [96, 132], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const s = 780 / 917; // px per day
  const bar = (y: number, days: number, color: string, label: string) => (
    <g>
      <text x="40" y={y - 12} fontFamily={BODY} fontWeight="800" fontSize="22" fill="#cfd8e6">{label}</text>
      <rect x="40" y={y} width={Math.max(days * s, 6)} height="26" rx="4" fill={color} />
      <text x={40 + Math.max(days * s, 6) + 14} y={y + 21} fontFamily={BODY} fontWeight="900" fontSize="24" fill={color}>{days}d</text>
    </g>
  );
  return (
    <g opacity={appear}>
      <rect x="0" y="0" width="896" height="410" rx="18" fill="#0b1524" stroke="#22344c" strokeWidth="2" opacity="0.92" />
      <text x="28" y="46" fontFamily={BODY} fontWeight="900" fontSize="30" fill="#e6edf6">STOCK ACT · 45-DAY RULE vs. REALITY</text>
      {bar(96, 45, P.green, "THE LAW")}
      {bar(196, 520, P.red, "McCLAIN · NVDA/AMD/TSM")}
      {bar(300, 917, P.red, "McCORMICK · MSFT")}
      {/* deadline marker */}
      <line x1={40 + 45 * s} y1="80" x2={40 + 45 * s} y2="356" stroke={P.green} strokeWidth="2" strokeDasharray="6 6" />
    </g>
  );
};

const studioHost = (f: number) => (
  <g transform={`translate(0 ${Math.sin(f / 12) * 3})`}>
    <PremiumHost e={{ mouth: flap(f) ? "open" : "rest", blink: isBlink(f), brow: 1 }} theme={HOST_ANALYST} id="cg" />
  </g>
);

// Scene A — hook + setup (McCormick MSFT card)
const Office: React.FC = () => {
  const f = useCurrentFrame();
  const hookOverlay = interpolate(f, [0, 8, 150, 172], [0, 1, 1, 0], { extrapolateRight: "clamp" });
  const screen = <FilingCard tickers="MSFT" traded="03 / 15 / 2023" filed="09 / 17 / 2025" lag="917" />;
  return (
    <AbsoluteFill style={{ background: "#0a1017" }}>
      <AbsoluteFill><NewsStudio host={studioHost(f)} screen={screen} screenLabel="● HOUSE FILING" ticker={CTICK} accent={ACCENT} skin={HOST_ANALYST.skin} f={f} wall={<StockActWall f={f} />} /></AbsoluteFill>
      <div style={{ position: "absolute", left: 50, right: 50, top: 172, textAlign: "center", opacity: hookOverlay, zIndex: 3 }}>
        <div style={{ fontFamily: FUN, fontSize: 78, color: P.paper, WebkitTextStroke: `6px ${P.ink}`, paintOrder: "stroke", lineHeight: 1.0 }}>THE LAW: 45 DAYS.<br /><span style={{ color: P.red }}>HE TOOK 917.</span></div>
      </div>
      <Chyron f={f} />
      <Karaoke id={f < ABS.c2 ? "c1" : "c2"} cue={f < ABS.c2 ? ABS.c1 : ABS.c2} />
      <Bug /><Disclaimer />
    </AbsoluteFill>
  );
};

// Scene B — turn (McClain second case)
const Office2: React.FC = () => {
  const f = useCurrentFrame();
  const screen = <FilingCard tickers="NVDA · AMD · TSM" traded="03 / 11 / 2024" filed="08 / 13 / 2025" lag="520" />;
  return (
    <AbsoluteFill style={{ background: "#0a1017" }}>
      <AbsoluteFill><NewsStudio host={studioHost(f)} screen={screen} screenLabel="● HOUSE FILING" ticker={CTICK} accent={ACCENT} skin={HOST_ANALYST.skin} f={f} wall={<StockActWall f={f + 200} />} /></AbsoluteFill>
      <Karaoke id="c3" cue={6} />
      <Bug /><Disclaimer />
    </AbsoluteFill>
  );
};

// Scene C — button / reaction
const Reaction: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: "#20242E" }}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end" }}>
        <svg width="760" height="820" viewBox="0 0 760 820">
          <g transform="translate(-52 -90) scale(1.62)"><PremiumHost e={{ mouth: "flat", brow: -1, blink: isBlink(f) }} theme={HOST_ANALYST} id="cgr" /></g>
        </svg>
      </AbsoluteFill>
      <div style={{ position: "absolute", left: 40, right: 40, top: 250, textAlign: "center", zIndex: 4 }}>
        <div style={{ fontFamily: FUN, fontSize: 74, color: P.paper, WebkitTextStroke: "4px #000", paintOrder: "stroke", lineHeight: 1.05 }}>DISCLOSED.<br />LEGAL.</div>
        <div style={{ fontFamily: BODY, fontWeight: 900, fontSize: 40, color: P.gold, marginTop: 12 }}>Just… in no particular hurry.</div>
      </div>
      <Karaoke id="c4" cue={6} />
      <Bug /><Disclaimer />
    </AbsoluteFill>
  );
};

// Scene D — CTA / loop
const CtaEnd: React.FC = () => {
  const f = useCurrentFrame();
  const pop = interpolate(f, [0, 12], [0.85, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: P.ink, alignItems: "center", justifyContent: "flex-start" }}>
      <svg width="1080" height="500" viewBox="0 0 1080 500" style={{ marginTop: 70, transform: `scale(${pop})` }}>
        <g transform="translate(270 10) scale(0.78)"><PremiumHost e={{ blink: isBlink(f), mouth: "soft", brow: 1 }} theme={HOST_ANALYST} id="cgc" /></g>
      </svg>
      <div style={{ textAlign: "center", padding: "0 56px" }}>
        <div style={{ fontFamily: FUN, fontSize: 62, color: P.gold, WebkitTextStroke: "4px #000", paintOrder: "stroke", lineHeight: 1.05 }}>45 DAYS IS THE RULE.</div>
        <div style={{ marginTop: 22, fontFamily: BODY, fontWeight: 900, fontSize: 40, color: P.mint }}>💬 Should being late cost something?</div>
        <div style={{ marginTop: 16, fontFamily: BODY, fontWeight: 700, fontSize: 23, color: "#9AA6B2" }}>Filings: US House Clerk (public) · reported, not an accusation · not financial advice</div>
      </div>
      <Karaoke id="c5" cue={6} />
    </AbsoluteFill>
  );
};

export const QuarterlyReportCongress: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Audio src={staticFile("qr_news_bed.wav")} volume={0.14} />
    <Sequence from={ABS.c1}><Audio src={staticFile("congress_c1.mp3")} /></Sequence>
    <Sequence from={ABS.c2}><Audio src={staticFile("congress_c2.mp3")} /></Sequence>
    <Sequence from={ABS.c3}><Audio src={staticFile("congress_c3.mp3")} /></Sequence>
    <Sequence from={ABS.c4}><Audio src={staticFile("congress_c4.mp3")} /></Sequence>
    <Sequence from={ABS.c5}><Audio src={staticFile("congress_c5.mp3")} /></Sequence>
    <Sequence durationInFrames={A}><Office /></Sequence>
    <Sequence from={A} durationInFrames={B}><Office2 /></Sequence>
    <Sequence from={A + B} durationInFrames={Cn}><Reaction /></Sequence>
    <Sequence from={A + B + Cn} durationInFrames={D}><CtaEnd /></Sequence>
  </AbsoluteFill>
);
