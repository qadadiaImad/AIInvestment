/**
 * QuarterlyReport — Korea "1 in 30" (retail-leverage / human-stakes).
 * Applies the content skills + the human-stakes viral-framing research:
 * cold-open on the human number -> leverage mechanic as the twist (an everyman's
 * account balance ticks RED past zero) -> cost stated plainly (empathetic, no
 * mockery) -> scale-out to the viewer, no advice. Neural anchor VO (Emma) +
 * word-by-word karaoke + newsroom bed. Reuses the rig + cast (anchor + analyst
 * everyman). Attributed, perishable figures; framed past-tense (KOSPI rebounded after).
 *
 * Audio: public/korea_k1..k5.mp3 + public/korea_captions.json.
 * Render: npx remotion render QuarterlyReportKorea out/quarterly_report_korea.mp4
 */
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Sequence, Audio, staticFile } from "remotion";
import { loadFont as loadLuckiest } from "@remotion/google-fonts/LuckiestGuy";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { PremiumHost, HOST_ANCHOR, HOST_ANALYST } from "./toon/host";
import caps from "../public/korea_captions.json";

const luckiest = loadLuckiest("normal", { weights: ["400"], subsets: ["latin"] });
const inter = loadInter("normal", { weights: ["700", "800", "900"], subsets: ["latin"] });
const FUN = luckiest.fontFamily;
const BODY = inter.fontFamily;

const P = {
  skinLine: "#1A1A1A", wall: "#8A97A6", wallDk: "#6E7C8C", floor: "#B7A6AE", desk: "#C98BA0", deskEdge: "#A66B83",
  monitor: "#2B2F36", screen: "#0E1116", window: "#C7D6E4", orange: "#E8871E", orangeDk: "#C46A12",
  gold: "#E7B23B", mint: "#7FE9C2", red: "#E0524D", green: "#34D399", ink: "#141414", paper: "#FFF6E9",
};

const F = 30;
type Cap = { words: { w: string; t0: number; t1: number }[]; dur: number };
const C = caps as Record<string, Cap>;

// scene lengths (frames)
const A = 365, B = 250, Cn = 140, D = 150;
export const QR_KOREA_BEATS = { total: A + B + Cn + D }; // 905 = ~30s
const CUE = { k1: 6, k2: 146, k3: 6, k4: 6, k5: 6 };
const ABS = { k1: 6, k2: 146, k3: A + 6, k4: A + B + 6, k5: A + B + Cn + 6 };

const isBlink = (f: number) => { const c = f % 78; return c < 4 || (c > 40 && c < 44); };
const flap = (f: number) => Math.floor(f / 4) % 2 === 0;
const won = (n: number) => "₩" + (n < 0 ? "-" : "+") + Math.abs(Math.round(n)).toLocaleString("en-US");

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
        const hot = /[0-9]|borrowed|leverage|homes/i.test(w.w);
        const color = active ? (hot ? P.gold : P.mint) : spoken ? P.paper : "rgba(255,246,233,0.5)";
        return (
          <span key={i} style={{ display: "inline-block", margin: "4px 10px", fontFamily: BODY, fontWeight: 900, fontSize: 54, color,
            WebkitTextStroke: `3px ${P.ink}`, paintOrder: "stroke", transform: `scale(${active ? 1.1 : 1})`, textShadow: "0 6px 16px rgba(0,0,0,.5)" }}>{w.w}</span>
        );
      })}
    </div>
  );
};

const Bug: React.FC = () => (
  <div style={{ position: "absolute", left: 40, top: 40, fontFamily: BODY, fontWeight: 800, fontSize: 26, color: P.paper, letterSpacing: 1, textShadow: "0 2px 8px #000", zIndex: 5 }}>
    V<span style={{ color: P.mint }}>&amp;</span>V · QUARTERLY REPORT
  </div>
);
const Disclaimer: React.FC = () => (
  <div style={{ position: "absolute", left: 0, right: 0, bottom: 66, textAlign: "center", fontFamily: BODY, fontWeight: 700, fontSize: 21, color: "#DfE5Ec", textShadow: "0 1px 8px #000", zIndex: 5 }}>
    Educational · reported figures, perishable · not financial advice
  </div>
);
const Source: React.FC<{ t: string }> = ({ t }) => (
  <div style={{ position: "absolute", left: 0, right: 0, bottom: 96, textAlign: "center", fontFamily: BODY, fontWeight: 700, fontSize: 19, color: "#A9B3C0", textShadow: "0 1px 8px #000", zIndex: 5 }}>{t}</div>
);

const Chyron: React.FC<{ f: number }> = ({ f }) => {
  const x = interpolate(f, [4, 16], [1200, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const blink = Math.floor(f / 12) % 2 === 0;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 96, transform: `translateX(${x}px)`, display: "flex", alignItems: "center", zIndex: 5 }}>
      <div style={{ background: blink ? "#D63A34" : "#8f1f1b", color: "#fff", fontFamily: BODY, fontWeight: 900, fontSize: 30, padding: "12px 20px", letterSpacing: 1 }}>● BREAKING</div>
      <div style={{ background: "rgba(10,13,18,.92)", color: "#fff", fontFamily: BODY, fontWeight: 800, fontSize: 30, padding: "12px 22px", letterSpacing: 1 }}>SOUTH KOREA — RETAIL LEVERAGE UNWIND</div>
    </div>
  );
};

const Newsroom: React.FC<{ host: React.ReactNode; monitor: React.ReactNode }> = ({ host, monitor }) => (
  <svg width="1080" height="1920" viewBox="0 0 1080 1920">
    <rect x="0" y="0" width="1080" height="1180" fill={P.wall} />
    <rect x="0" y="1180" width="1080" height="740" fill={P.floor} />
    <line x1="0" y1="1180" x2="1080" y2="1180" stroke={P.wallDk} strokeWidth="6" />
    <rect x="700" y="230" width="300" height="360" fill={P.window} stroke={P.skinLine} strokeWidth="10" />
    <line x1="850" y1="230" x2="850" y2="590" stroke={P.skinLine} strokeWidth="8" />
    <line x1="700" y1="410" x2="1000" y2="410" stroke={P.skinLine} strokeWidth="8" />
    {/* host sits BEHIND the desk */}
    <g transform="translate(70 566) scale(1.18)">{host}</g>
    <rect x="0" y="1180" width="1080" height="80" fill={P.desk} stroke={P.deskEdge} strokeWidth="6" />
    <rect x="0" y="1260" width="1080" height="660" fill={P.floor} />
    <g transform="translate(600 770)">
      <rect x="0" y="0" width="430" height="300" rx="14" fill={P.monitor} stroke={P.skinLine} strokeWidth="10" />
      <rect x="24" y="24" width="382" height="252" rx="6" fill={P.screen} />
      <rect x="195" y="300" width="40" height="70" fill={P.monitor} stroke={P.skinLine} strokeWidth="8" />
      <rect x="150" y="368" width="130" height="16" rx="6" fill={P.monitor} stroke={P.skinLine} strokeWidth="8" />
      {monitor}
    </g>
  </svg>
);

// ---------- Scene A: office (hook + setup) ----------
const Office: React.FC = () => {
  const f = useCurrentFrame();
  const bob = Math.sin(f / 12) * 3;
  const talking = f < 353 && flap(f);
  const host = (
    <g transform={`translate(0 ${bob})`}>
      <PremiumHost e={{ mouth: talking ? "open" : "rest", blink: isBlink(f), brow: 2 }} theme={HOST_ANCHOR} id="office" />
    </g>
  );
  const s1 = interpolate(f, [30, 48], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }); // 1.2M
  const s2 = interpolate(f, [CUE.k2 + 6, CUE.k2 + 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }); // 38.6T
  const hookOverlay = interpolate(f, [0, 8, 120, 138], [0, 1, 1, 0], { extrapolateRight: "clamp" });
  const monitor = f < CUE.k2 ? (
    <g opacity={s1}>
      <text x="215" y="118" textAnchor="middle" fontFamily={FUN} fontSize="86" fill={P.red}>1.2M</text>
      <text x="215" y="182" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="34" fill={P.paper}>MARGIN CALLS</text>
      <text x="215" y="224" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="26" fill="#A9B3C0">IN ONE WEEK</text>
    </g>
  ) : (
    <g opacity={s2}>
      <text x="215" y="108" textAnchor="middle" fontFamily={FUN} fontSize="78" fill={P.gold}>₩38.6T</text>
      <text x="215" y="164" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="30" fill={P.paper}>MARGIN DEBT — RECORD</text>
      <text x="215" y="214" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="27" fill={P.mint}>Samsung + SK Hynix</text>
    </g>
  );
  return (
    <AbsoluteFill style={{ background: P.wall }}>
      <AbsoluteFill><Newsroom host={host} monitor={monitor} /></AbsoluteFill>
      <div style={{ position: "absolute", left: 50, right: 50, top: 168, textAlign: "center", opacity: hookOverlay, zIndex: 3 }}>
        <div style={{ fontFamily: FUN, fontSize: 76, color: P.paper, WebkitTextStroke: `6px ${P.ink}`, paintOrder: "stroke", lineHeight: 1.0 }}>1,200,000<br />MARGIN CALLS.</div>
      </div>
      <Chyron f={f} />
      <Karaoke id={f < CUE.k2 ? "k1" : "k2"} cue={f < CUE.k2 ? CUE.k1 : CUE.k2} />
      {f >= CUE.k2 && <Source t="Seoul Economic Daily · Jun 2026" />}
      <Bug /><Disclaimer />
    </AbsoluteFill>
  );
};

// ---------- Scene B: everyman cutaway — balance ticks red past zero ----------
const Cutaway: React.FC = () => {
  const f = useCurrentFrame();
  const bal = interpolate(f, [30, 210], [12000000, -8400000], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const neg = bal < 0;
  const shake = neg ? Math.sin(f / 2) * 3 : 0;
  const kospi = interpolate(f, [24, 60], [9385, 6820], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#141821" }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 150, textAlign: "center", zIndex: 2 }}>
        <div style={{ fontFamily: BODY, fontWeight: 800, fontSize: 30, color: "#8893A4", letterSpacing: 3 }}>ACCOUNT BALANCE</div>
        <div style={{ fontFamily: FUN, fontSize: 120, color: neg ? P.red : P.green, transform: `translateX(${shake}px)`, WebkitTextStroke: "4px #000", paintOrder: "stroke", lineHeight: 1.1 }}>{won(bal)}</div>
        <div style={{ fontFamily: BODY, fontWeight: 800, fontSize: 30, color: P.gold, marginTop: 8 }}>KOSPI {Math.round(kospi).toLocaleString()} · <span style={{ color: P.red }}>−27%</span></div>
      </div>
      <svg width="1080" height="760" viewBox="0 0 1080 760" style={{ position: "absolute", bottom: 130 }}>
        <g transform={`translate(270 30) scale(1.0) translate(0 ${Math.sin(f / 12) * 3})`}>
          <PremiumHost e={{ blink: isBlink(f), mouth: neg ? "flat" : "rest", brow: neg ? -3 : 0 }} theme={HOST_ANALYST} id="cut" />
        </g>
      </svg>
      <Karaoke id="k3" cue={CUE.k3} bottom={110} />
      <Bug />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 60, textAlign: "center", fontFamily: BODY, fontWeight: 700, fontSize: 20, color: "#8893A4", zIndex: 5 }}>illustrative · not a real account · not financial advice</div>
    </AbsoluteFill>
  );
};

// ---------- Scene C: empathetic reaction (no comedic shake) ----------
const Reaction: React.FC = () => {
  const f = useCurrentFrame();
  return (
  <AbsoluteFill style={{ background: "#20242E" }}>
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end" }}>
      <svg width="760" height="820" viewBox="0 0 760 820">
        <g transform="translate(-52 -90) scale(1.62)">
          <PremiumHost e={{ mouth: "flat", brow: -2, blink: isBlink(f) }} theme={HOST_ANCHOR} id="react" />
        </g>
      </svg>
    </AbsoluteFill>
    <div style={{ position: "absolute", left: 40, right: 40, top: 250, textAlign: "center", zIndex: 4 }}>
      <div style={{ fontFamily: FUN, fontSize: 96, color: P.red, WebkitTextStroke: "5px #000", paintOrder: "stroke" }}>62%</div>
      <div style={{ fontFamily: BODY, fontWeight: 900, fontSize: 40, color: P.paper }}>were in their 20s–30s</div>
      <div style={{ fontFamily: BODY, fontWeight: 800, fontSize: 28, color: "#A9B3C0", marginTop: 6 }}>~360,000 forcibly liquidated</div>
    </div>
    <Karaoke id="k4" cue={CUE.k4} />
    <Source t="BigGo Finance · Jul 2026" /><Bug />
  </AbsoluteFill>
  );
};

// ---------- Scene D: CTA / loop ----------
const CtaEnd: React.FC = () => {
  const f = useCurrentFrame();
  const pop = interpolate(f, [0, 12], [0.85, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: P.ink, alignItems: "center", justifyContent: "flex-start" }}>
      <svg width="1080" height="500" viewBox="0 0 1080 500" style={{ marginTop: 70, transform: `scale(${pop})` }}>
        <g transform="translate(270 10) scale(0.78)"><PremiumHost e={{ blink: isBlink(f), mouth: "soft", brow: 1 }} theme={HOST_ANCHOR} id="cta" /></g>
      </svg>
      <div style={{ textAlign: "center", padding: "0 56px" }}>
        <div style={{ fontFamily: FUN, fontSize: 60, color: P.gold, WebkitTextStroke: "4px #000", paintOrder: "stroke", lineHeight: 1.05 }}>
          LEVERAGE DOESN’T CREATE<br />THE RISK. IT REVEALS IT.
        </div>
        <div style={{ marginTop: 22, fontFamily: BODY, fontWeight: 900, fontSize: 40, color: P.mint }}>💬 Would you have sold?</div>
        <div style={{ marginTop: 16, fontFamily: BODY, fontWeight: 700, fontSize: 23, color: "#9AA6B2" }}>
          Korea figures Jun–Jul 2026 · reported, perishable · not financial advice
        </div>
      </div>
      <Karaoke id="k5" cue={CUE.k5} />
    </AbsoluteFill>
  );
};

export const QuarterlyReportKorea: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Audio src={staticFile("qr_news_bed.wav")} volume={0.14} />
    <Sequence from={ABS.k1}><Audio src={staticFile("korea_k1.mp3")} /></Sequence>
    <Sequence from={ABS.k2}><Audio src={staticFile("korea_k2.mp3")} /></Sequence>
    <Sequence from={ABS.k3}><Audio src={staticFile("korea_k3.mp3")} /></Sequence>
    <Sequence from={ABS.k4}><Audio src={staticFile("korea_k4.mp3")} /></Sequence>
    <Sequence from={ABS.k5}><Audio src={staticFile("korea_k5.mp3")} /></Sequence>
    <Sequence durationInFrames={A}><Office /></Sequence>
    <Sequence from={A} durationInFrames={B}><Cutaway /></Sequence>
    <Sequence from={A + B} durationInFrames={Cn}><Reaction /></Sequence>
    <Sequence from={A + B + Cn} durationInFrames={D}><CtaEnd /></Sequence>
  </AbsoluteFill>
);
