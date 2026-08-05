/**
 * QuarterlyReport — a Cyanide & Happiness-style flat-2D animated finance sketch,
 * now with a South-Park-style voice (Windows SAPI pitched up ~1.16x) and a
 * synthesized newsroom music bed. All audio is offline/free (see scripts below):
 *   public/qr_l1..l5.wav   — the pitched VO lines
 *   public/qr_news_bed.wav — the numpy-synth broadcast bed
 *
 * The characters are VECTOR (SVG in code) = 100% frame-consistent, no AI-art drift.
 * Cutout animation (mouth-flap synced to the VO, blink, idle bob, hard cuts) via
 * interpolate(). Deadpan satire on real data (NVDA 1.8x UNDER a model, 2026-08-03).
 *
 * Render: npx remotion render QuarterlyReport out/quarterly_report.mp4
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  Sequence,
  spring,
  Audio,
  staticFile,
  useVideoConfig,
} from "remotion";
import { loadFont as loadLuckiest } from "@remotion/google-fonts/LuckiestGuy";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { PremiumHost, HOST_QUANT } from "./toon/host";

const luckiest = loadLuckiest("normal", { weights: ["400"], subsets: ["latin"] });
const inter = loadInter("normal", { weights: ["700", "800", "900"], subsets: ["latin"] });
const FUN = luckiest.fontFamily;
const BODY = inter.fontFamily;

const P = {
  skin: "#F3C9A2",
  skinLine: "#1A1A1A",
  shirt: "#37B6A6",
  wall: "#8A97A6",
  wallDk: "#6E7C8C",
  floor: "#B7A6AE",
  desk: "#C98BA0",
  deskEdge: "#A66B83",
  monitor: "#2B2F36",
  screen: "#0E1116",
  window: "#C7D6E4",
  orange: "#E8871E",
  orangeDk: "#C46A12",
  green: "#37D399",
  ink: "#141414",
  paper: "#FFF6E9",
};

// Beat lengths chosen to hold each pitched VO line (frames @30fps):
// l1 49f · l2 83f · l3 146f · l4 65f · l5 48f
const FPS_TITLE = 54;
const FPS_SCENE = 264;
const FPS_REACT = 90;
const FPS_END = 96;
export const QR_BEATS = {
  title: FPS_TITLE,
  scene: FPS_SCENE,
  react: FPS_REACT,
  end: FPS_END,
  total: FPS_TITLE + FPS_SCENE + FPS_REACT + FPS_END, // 504 = 16.8s
};
// absolute VO cue frames
const CUE = {
  l1: 4,
  l2: FPS_TITLE + 8,
  l3: FPS_TITLE + 100,
  l4: FPS_TITLE + FPS_SCENE + 6,
  l5: FPS_TITLE + FPS_SCENE + FPS_REACT + 8,
  reveal: FPS_TITLE + 130,
};

// ---- animation helpers ----
const isBlinking = (f: number) => {
  const c = f % 78;
  return c < 4 || (c > 40 && c < 44);
};
const inWindows = (f: number, wins: [number, number][]) => wins.some(([a, b]) => f >= a && f <= b);
const flap = (f: number) => Math.floor(f / 4) % 2 === 0;

// ================= TITLE CARD =================
const TitleCard: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: f, fps, config: { damping: 12, mass: 0.6 } });
  const s = interpolate(pop, [0, 1], [0.7, 1]);
  const laughEye = (cx: number) => (
    <g>
      <path d={`M${cx - 26} -14 Q${cx - 13} -30 ${cx} -14`} fill="none" stroke={P.ink} strokeWidth="9" strokeLinecap="round" />
      <path d={`M${cx} -14 Q${cx + 13} -30 ${cx + 26} -14`} fill="none" stroke={P.ink} strokeWidth="9" strokeLinecap="round" />
    </g>
  );
  return (
    <AbsoluteFill style={{ background: `linear-gradient(160deg, ${P.orange}, ${P.orangeDk})` }}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ transform: `scale(${s})`, textAlign: "center" }}>
          <svg width="900" height="360" viewBox="-450 -180 900 360">
            {[-330, 330].map((cx) => (
              <g key={cx} transform={`translate(${cx} -20)`}>
                <circle cx="0" cy="0" r="86" fill={P.paper} stroke={P.ink} strokeWidth="10" />
                {laughEye(-1)}
                <path d="M-40 30 Q0 70 40 30" fill="none" stroke={P.ink} strokeWidth="10" strokeLinecap="round" />
              </g>
            ))}
            <text x="0" y="-8" textAnchor="middle" fontFamily={FUN} fontSize="150" fill={P.paper} stroke={P.ink} strokeWidth="7" paintOrder="stroke" style={{ letterSpacing: 2 }}>
              V &amp; V
            </text>
          </svg>
          <div style={{ marginTop: -6, fontFamily: FUN, fontSize: 96, color: P.paper, WebkitTextStroke: `7px ${P.ink}`, paintOrder: "stroke", letterSpacing: 3, lineHeight: 1 }}>
            QUARTERLY REPORT
          </div>
          <div style={{ marginTop: 22, fontFamily: BODY, fontWeight: 800, fontSize: 34, color: P.ink, opacity: 0.85 }}>
            an AI-stack market segment · ep. 1
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ================= CAPTION =================
const Caption: React.FC<{ text: string; hot?: string }> = ({ text, hot }) => {
  const parts = hot ? text.split(hot) : [text];
  return (
    <div
      style={{
        position: "absolute",
        left: 60,
        right: 60,
        bottom: 150,
        textAlign: "center",
        fontFamily: BODY,
        fontWeight: 900,
        fontSize: 58,
        lineHeight: 1.12,
        color: P.paper,
        WebkitTextStroke: `3px ${P.ink}`,
        paintOrder: "stroke",
        textShadow: `0 6px 18px rgba(0,0,0,.55)`,
      }}
    >
      {parts[0]}
      {hot && <span style={{ color: P.green }}>{hot}</span>}
      {parts[1]}
    </div>
  );
};

// ================= OFFICE SCENE =================
const OfficeScene: React.FC = () => {
  const f = useCurrentFrame();
  const bob = Math.sin(f / 9) * 4;
  const push = interpolate(f, [126, 180], [1, 1.14], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const numAppear = interpolate(f, [126, 146], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const talking = inWindows(f, [[8, 91], [100, 246]]) && flap(f);
  const host = (
    <g transform={`translate(0 ${bob})`}>
      <PremiumHost e={{ mouth: talking ? "open" : "rest", blink: isBlinking(f), brow: 2 }} theme={HOST_QUANT} id="ep1o" />
    </g>
  );

  let cap: React.ReactNode = null;
  if (f >= 8 && f < 96) cap = <Caption text="This quarter, the market called Nvidia a “bubble.”" />;
  else if (f >= 100) cap = <Caption text="A model says it’s worth 1.8× the price. So… half off." hot="1.8× the price" />;

  return (
    <AbsoluteFill style={{ background: P.wall }}>
      <AbsoluteFill style={{ transform: `scale(${push})`, transformOrigin: "60% 42%" }}>
        <svg width="1080" height="1920" viewBox="0 0 1080 1920">
          <rect x="0" y="0" width="1080" height="1180" fill={P.wall} />
          <rect x="0" y="1180" width="1080" height="740" fill={P.floor} />
          <line x1="0" y1="1180" x2="1080" y2="1180" stroke={P.wallDk} strokeWidth="6" />
          <rect x="700" y="230" width="300" height="360" fill={P.window} stroke={P.skinLine} strokeWidth="10" />
          <line x1="850" y1="230" x2="850" y2="590" stroke={P.skinLine} strokeWidth="8" />
          <line x1="700" y1="410" x2="1000" y2="410" stroke={P.skinLine} strokeWidth="8" />
          <g transform="translate(70 566) scale(1.18)">{host}</g>
          <rect x="0" y="1180" width="1080" height="80" fill={P.desk} stroke={P.deskEdge} strokeWidth="6" />
          <rect x="0" y="1260" width="1080" height="660" fill={P.floor} />
          <rect x="120" y="1120" width="70" height="70" rx="8" fill={P.green} stroke={P.skinLine} strokeWidth="7" />
          <line x1="140" y1="1120" x2="132" y2="1060" stroke={P.skinLine} strokeWidth="7" strokeLinecap="round" />
          <line x1="165" y1="1120" x2="172" y2="1055" stroke={P.orange} strokeWidth="9" strokeLinecap="round" />
          <g transform="translate(600 760)">
            <rect x="0" y="0" width="430" height="300" rx="14" fill={P.monitor} stroke={P.skinLine} strokeWidth="10" />
            <rect x="24" y="24" width="382" height="252" rx="6" fill={P.screen} />
            <rect x="195" y="300" width="40" height="70" fill={P.monitor} stroke={P.skinLine} strokeWidth="8" />
            <rect x="150" y="368" width="130" height="16" rx="6" fill={P.monitor} stroke={P.skinLine} strokeWidth="8" />
            <g opacity={numAppear}>
              <text x="215" y="108" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="56" fill="#7FE9C2">NVDA</text>
              <text x="215" y="204" textAnchor="middle" fontFamily={FUN} fontSize="104" fill="#5AF0A8" stroke="#0A3D2A" strokeWidth="2" paintOrder="stroke">1.8×</text>
              <text x="215" y="250" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="28" fill={P.paper}>UNDER a model</text>
            </g>
          </g>
        </svg>
      </AbsoluteFill>
      {cap}
    </AbsoluteFill>
  );
};

// ================= REACTION =================
const ReactionFace: React.FC = () => {
  const f = useCurrentFrame();
  const shake = f > 30 ? Math.sin(f / 1.5) * 3 : 0;
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg, ${P.orange}, ${P.orangeDk})` }}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <svg width="760" height="760" viewBox="0 0 760 760" style={{ transform: `translateX(${shake}px)` }}>
          <g transform="translate(-52 -90) scale(1.62)">
            <PremiumHost e={{ mouth: "flat", blink: isBlinking(f) }} theme={HOST_QUANT} id="ep1r" />
          </g>
        </svg>
      </AbsoluteFill>
      <Caption text="So naturally, everyone sold it." />
    </AbsoluteFill>
  );
};

// ================= END CARD =================
const EndCard: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: f, fps, config: { damping: 13 } });
  return (
    <AbsoluteFill style={{ background: P.ink, alignItems: "center", justifyContent: "center" }}>
      <div style={{ transform: `scale(${interpolate(pop, [0, 1], [0.8, 1])})`, textAlign: "center", padding: 60 }}>
        <div style={{ fontFamily: FUN, fontSize: 96, color: P.green, WebkitTextStroke: `5px #000`, paintOrder: "stroke" }}>
          GREAT JOB,<br />EVERYONE.
        </div>
        <div style={{ marginTop: 40, fontFamily: BODY, fontWeight: 900, fontSize: 44, color: P.paper }}>
          VALUE &amp; VALUES
        </div>
        <div style={{ marginTop: 14, fontFamily: BODY, fontWeight: 700, fontSize: 26, color: "#9AA6B2" }}>
          Figures as of 2026-08-03 · educational, not financial advice.
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ================= COMPOSITION =================
export const QuarterlyReport: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {/* newsroom music bed under everything */}
      <Audio src={staticFile("qr_news_bed.wav")} volume={0.16} />
      {/* South-Park-style VO cues */}
      <Sequence from={CUE.l1}><Audio src={staticFile("qr_l1.wav")} /></Sequence>
      <Sequence from={CUE.l2}><Audio src={staticFile("qr_l2.wav")} /></Sequence>
      <Sequence from={CUE.l3}><Audio src={staticFile("qr_l3.wav")} /></Sequence>
      <Sequence from={CUE.l4}><Audio src={staticFile("qr_l4.wav")} /></Sequence>
      <Sequence from={CUE.l5}><Audio src={staticFile("qr_l5.wav")} /></Sequence>
      {/* number-reveal sting (reuse the quiz reveal sfx) */}
      <Sequence from={CUE.reveal}><Audio src={staticFile("quiz/reveal.mp3")} volume={0.5} /></Sequence>

      <Sequence durationInFrames={QR_BEATS.title}><TitleCard /></Sequence>
      <Sequence from={QR_BEATS.title} durationInFrames={QR_BEATS.scene}><OfficeScene /></Sequence>
      <Sequence from={QR_BEATS.title + QR_BEATS.scene} durationInFrames={QR_BEATS.react}><ReactionFace /></Sequence>
      <Sequence from={QR_BEATS.title + QR_BEATS.scene + QR_BEATS.react} durationInFrames={QR_BEATS.end}><EndCard /></Sequence>
    </AbsoluteFill>
  );
};
