/**
 * QuarterlyReport — Episode 2: "The Intel Comeback" (Myth-Bust).
 * Built by APPLYING the content skills: viral-short-storytelling (Myth-Bust, cold
 * open, loop), short-form-scripting (beat sheet, one debate CTA, on-screen+implied
 * not-advice), viral-voiceover-audio (non-default NEURAL anchor voice via edge-tts,
 * word-by-word karaoke captions). Stars the ANCHOR cast character. Reuses the rig,
 * the newsroom bed, and the ep-1 visual language. Data: INTC ~2.9x OVER a model (2026-08-03).
 *
 * Audio: public/ep2_e1..e5.mp3 (Emma neural, deadpan) + public/ep2_captions.json (word timings).
 * Render: npx remotion render QuarterlyReportEp2 out/quarterly_report_ep2.mp4
 */
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Sequence, Audio, staticFile } from "remotion";
import { loadFont as loadLuckiest } from "@remotion/google-fonts/LuckiestGuy";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { PremiumHost, HOST_ANCHOR } from "./toon/host";
import { NewsStudio } from "./toon/studio";

const E2TICK = "INTEL: THE COMEBACK EVERYONE'S BUYING   ·   A FUNDAMENTAL MODEL: ~2.9× OVERVALUED ($90 vs $31)   ·   YOU'RE PAYING TRIPLE FOR THE STORY   ·   EDUCATIONAL — NOT FINANCIAL ADVICE   ·   ";
import caps from "../public/ep2_captions.json";

const luckiest = loadLuckiest("normal", { weights: ["400"], subsets: ["latin"] });
const inter = loadInter("normal", { weights: ["700", "800", "900"], subsets: ["latin"] });
const FUN = luckiest.fontFamily;
const BODY = inter.fontFamily;

const P = {
  skin: "#F3C9A2", skinLine: "#1A1A1A", wall: "#8A97A6", wallDk: "#6E7C8C", floor: "#B7A6AE",
  desk: "#C98BA0", deskEdge: "#A66B83", monitor: "#2B2F36", screen: "#0E1116", window: "#C7D6E4",
  orange: "#E8871E", orangeDk: "#C46A12", gold: "#E7B23B", mint: "#7FE9C2", ink: "#141414", paper: "#FFF6E9",
};

const F = 30;
type Cap = { words: { w: string; t0: number; t1: number }[]; dur: number; frames: number };
const C = caps as Record<string, Cap>;

// scene lengths
const A = 322, B = 145, Cn = 104;
export const QR_EP2_BEATS = { total: A + B + Cn }; // 571 = ~19s
// cue frames within each scene
const CUE = { e1: 4, e2: 90, e3: 187, reveal: 187 + 70, e4: 4, e5: 4 };
// absolute cues for audio
const ABS = { e1: CUE.e1, e2: CUE.e2, e3: CUE.e3, e4: A + CUE.e4, e5: A + B + CUE.e5 };

const isBlink = (f: number) => { const c = f % 78; return c < 4 || (c > 40 && c < 44); };
const flap = (f: number) => Math.floor(f / 4) % 2 === 0;

// word-by-word karaoke caption (short-form-scripting: mandatory style)
const Karaoke: React.FC<{ id: keyof typeof C; cue: number }> = ({ id, cue }) => {
  const f = useCurrentFrame();
  const cap = C[id];
  if (!cap) return null;
  const tt = (f - cue) / F;
  if (tt < -0.15 || tt > cap.dur + 0.4) return null;
  return (
    <div style={{ position: "absolute", left: 54, right: 54, bottom: 210, textAlign: "center", lineHeight: 1.15 }}>
      {cap.words.map((w, i) => {
        const active = tt >= w.t0 && tt < w.t1;
        const spoken = tt >= w.t1;
        const hot = /[0-9]|third|triple/i.test(w.w);
        const color = active ? (hot ? P.gold : P.mint) : spoken ? P.paper : "rgba(255,246,233,0.55)";
        return (
          <span key={i} style={{
            display: "inline-block", margin: "4px 11px", fontFamily: BODY, fontWeight: 900, fontSize: 60,
            color, WebkitTextStroke: `3px ${P.ink}`, paintOrder: "stroke",
            transform: `scale(${active ? 1.12 : 1})`, transition: "none",
            textShadow: "0 6px 16px rgba(0,0,0,.5)",
          }}>{w.w}</span>
        );
      })}
    </div>
  );
};

const Bug: React.FC = () => (
  <div style={{ position: "absolute", left: 40, top: 40, fontFamily: BODY, fontWeight: 800, fontSize: 26, color: P.paper, letterSpacing: 1, textShadow: "0 2px 8px #000", zIndex: 3 }}>
    V<span style={{ color: P.mint }}>&amp;</span>V · QUARTERLY REPORT
  </div>
);
const Disclaimer: React.FC = () => (
  <div style={{ position: "absolute", left: 0, right: 0, bottom: 108, textAlign: "center", fontFamily: BODY, fontWeight: 700, fontSize: 22, color: "#Dfe5ec", textShadow: "0 1px 8px #000", zIndex: 6 }}>
    Educational · a model’s read, not a call · not financial advice
  </div>
);

const Office: React.FC = () => {
  const f = useCurrentFrame();
  const bob = Math.sin(f / 9) * 4;
  const push = interpolate(f, [CUE.reveal - 12, CUE.reveal + 30], [1, 1.13], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const numAppear = interpolate(f, [CUE.reveal, CUE.reveal + 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const talking = (f < 320) && flap(f);
  const host = (
    <g transform={`translate(0 ${bob})`}>
      <PremiumHost e={{ mouth: talking ? "open" : "rest", blink: isBlink(f), brow: 2 }} theme={HOST_ANCHOR} id="ep2o" />
    </g>
  );
  // frame-1 baked "thumbnail" overlay during the hook
  const hookOverlay = interpolate(f, [0, 6, 74, 84], [0, 1, 1, 0], { extrapolateRight: "clamp" });
  const active = f < CUE.e2 ? "e1" : f < CUE.e3 ? "e2" : "e3";
  const cue = active === "e1" ? CUE.e1 : active === "e2" ? CUE.e2 : CUE.e3;
  const screen = (
    <g opacity={numAppear}>
      <text x="215" y="92" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="54" fill={P.gold}>INTC</text>
      <text x="215" y="182" textAnchor="middle" fontFamily={FUN} fontSize="94" fill={P.gold} stroke="#3D2A08" strokeWidth="2" paintOrder="stroke">2.9×</text>
      <text x="215" y="228" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="24" fill={P.paper}>OVER a model · $90 vs $31</text>
    </g>
  );
  return (
    <AbsoluteFill style={{ background: "#0a1017" }}>
      <AbsoluteFill style={{ transform: `scale(${push})`, transformOrigin: "60% 42%" }}>
        <NewsStudio host={host} screen={screen} ticker={E2TICK} accent={P.gold} skin="#F4C9A6" f={f} />
      </AbsoluteFill>
      <div style={{ position: "absolute", left: 50, right: 50, top: 150, textAlign: "center", opacity: hookOverlay, zIndex: 2 }}>
        <div style={{ fontFamily: FUN, fontSize: 92, color: P.paper, WebkitTextStroke: `7px ${P.ink}`, paintOrder: "stroke", lineHeight: 0.98 }}>
          THE INTEL<br />“COMEBACK”
        </div>
      </div>
      <Karaoke id={active as keyof typeof C} cue={cue} />
      <Bug /><Disclaimer />
    </AbsoluteFill>
  );
};

const Reaction: React.FC = () => {
  const f = useCurrentFrame();
  const shake = f > 30 ? Math.sin(f / 1.5) * 3 : 0;
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg, ${P.orange}, ${P.orangeDk})` }}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <svg width="760" height="760" viewBox="0 0 760 760" style={{ transform: `translateX(${shake}px)` }}>
          <g transform="translate(-52 -90) scale(1.62)">
            <PremiumHost e={{ mouth: "flat", blink: isBlink(f) }} theme={HOST_ANCHOR} id="ep2r" />
          </g>
        </svg>
      </AbsoluteFill>
      <Karaoke id="e4" cue={CUE.e4} />
      <Bug /><Disclaimer />
    </AbsoluteFill>
  );
};

const CtaEnd: React.FC = () => {
  const f = useCurrentFrame();
  const pop = interpolate(f, [0, 12], [0.85, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: P.ink, alignItems: "center", justifyContent: "flex-start" }}>
      <svg width="1080" height="500" viewBox="0 0 1080 500" style={{ marginTop: 90, transform: `scale(${pop})` }}>
        <g transform="translate(270 10) scale(0.78)"><PremiumHost e={{ blink: isBlink(f), mouth: "soft", brow: 1 }} theme={HOST_ANCHOR} id="ep2c" /></g>
      </svg>
      <div style={{ textAlign: "center", padding: "0 60px" }}>
        <div style={{ fontFamily: FUN, fontSize: 78, color: P.gold, WebkitTextStroke: "5px #000", paintOrder: "stroke", lineHeight: 1 }}>
          OVERPRICED HOPE?<br />OR AM I WRONG?
        </div>
        <div style={{ marginTop: 26, fontFamily: BODY, fontWeight: 900, fontSize: 40, color: P.mint }}>💬 Comment your call</div>
        <div style={{ marginTop: 18, fontFamily: BODY, fontWeight: 700, fontSize: 24, color: "#9AA6B2" }}>
          INTC figures 2026-08-03 · a model’s read · not financial advice
        </div>
      </div>
      <Karaoke id="e5" cue={CUE.e5} />
    </AbsoluteFill>
  );
};

export const QuarterlyReportEp2: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Audio src={staticFile("qr_news_bed.wav")} volume={0.15} />
    <Sequence from={ABS.e1}><Audio src={staticFile("ep2_e1.mp3")} /></Sequence>
    <Sequence from={ABS.e2}><Audio src={staticFile("ep2_e2.mp3")} /></Sequence>
    <Sequence from={ABS.e3}><Audio src={staticFile("ep2_e3.mp3")} /></Sequence>
    <Sequence from={ABS.e4}><Audio src={staticFile("ep2_e4.mp3")} /></Sequence>
    <Sequence from={ABS.e5}><Audio src={staticFile("ep2_e5.mp3")} /></Sequence>
    <Sequence durationInFrames={A}><Office /></Sequence>
    <Sequence from={A} durationInFrames={B}><Reaction /></Sequence>
    <Sequence from={A + B} durationInFrames={Cn}><CtaEnd /></Sequence>
  </AbsoluteFill>
);
