/**
 * QuarterlyReport — a Cyanide & Happiness-style flat-2D animated finance sketch.
 *
 * Proof-of-concept for the "make things like that C&H reel" ask. The whole point:
 * the characters are VECTOR (SVG drawn in code), so they are 100% identical every
 * frame — no AI-art, no LoRA, no consistency drift. Cutout animation (mouth-flap,
 * blink, idle bob, hard cuts) is done with Remotion interpolate(). Deadpan satire
 * driven by our real value-screen data (NVDA ~1.8x UNDER a model, 2026-08-03).
 *
 * Register in Root.tsx: <Composition id="QuarterlyReport" ... durationInFrames={QR_BEATS.total} />
 * Render: npx remotion render QuarterlyReport out/quarterly_report.mp4
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  Sequence,
  spring,
  useVideoConfig,
} from "remotion";
import { loadFont as loadLuckiest } from "@remotion/google-fonts/LuckiestGuy";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";

const luckiest = loadLuckiest("normal", { weights: ["400"], subsets: ["latin"] });
const inter = loadInter("normal", { weights: ["700", "800", "900"], subsets: ["latin"] });
const FUN = luckiest.fontFamily;
const BODY = inter.fontFamily;

// C&H-ish flat palette
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

const FPS_TITLE = 48;
const FPS_SCENE = 216;
const FPS_REACT = 78;
const FPS_END = 48;
export const QR_BEATS = {
  title: FPS_TITLE,
  scene: FPS_SCENE,
  react: FPS_REACT,
  end: FPS_END,
  total: FPS_TITLE + FPS_SCENE + FPS_REACT + FPS_END, // 390 = 13s
};

// ---- helpers ----
const isBlinking = (f: number) => {
  const c = f % 78; // blink roughly every 2.6s
  return c < 4 || (c > 40 && c < 44);
};
// mouth-flap: only "talk" inside given windows (frames relative to scene)
const talkWindows: [number, number][] = [
  [6, 66],
  [78, 150],
  [156, 212],
];
const isTalking = (f: number) => talkWindows.some(([a, b]) => f >= a && f <= b);
const mouthOpen = (f: number) => isTalking(f) && Math.floor(f / 4) % 2 === 0;

// ================= CHARACTER =================
const Guy: React.FC<{ talk: boolean; blink: boolean; bob: number }> = ({ talk, blink, bob }) => {
  const open = talk;
  return (
    <g transform={`translate(0 ${bob})`}>
      {/* neck */}
      <line x1="270" y1="300" x2="270" y2="360" stroke={P.skinLine} strokeWidth="9" />
      {/* shirt / body */}
      <path
        d="M150 520 C150 400 205 350 270 350 C335 350 390 400 390 520 Z"
        fill={P.shirt}
        stroke={P.skinLine}
        strokeWidth="9"
      />
      {/* arms (noodle) */}
      <path d="M175 400 C120 430 110 500 150 540" fill="none" stroke={P.skinLine} strokeWidth="9" strokeLinecap="round" />
      <path d="M365 400 C430 430 445 500 405 545" fill="none" stroke={P.skinLine} strokeWidth="9" strokeLinecap="round" />
      {/* hands */}
      <circle cx="150" cy="542" r="13" fill={P.skin} stroke={P.skinLine} strokeWidth="8" />
      <circle cx="405" cy="547" r="13" fill={P.skin} stroke={P.skinLine} strokeWidth="8" />
      {/* head */}
      <circle cx="270" cy="200" r="115" fill={P.skin} stroke={P.skinLine} strokeWidth="10" />
      {/* eyebrows (deadpan, slightly flat) */}
      <line x1="212" y1="150" x2="252" y2="152" stroke={P.skinLine} strokeWidth="8" strokeLinecap="round" />
      <line x1="288" y1="152" x2="328" y2="150" stroke={P.skinLine} strokeWidth="8" strokeLinecap="round" />
      {/* eyes */}
      {blink ? (
        <>
          <line x1="222" y1="196" x2="252" y2="196" stroke={P.skinLine} strokeWidth="8" strokeLinecap="round" />
          <line x1="288" y1="196" x2="318" y2="196" stroke={P.skinLine} strokeWidth="8" strokeLinecap="round" />
        </>
      ) : (
        <>
          <circle cx="237" cy="196" r="14" fill={P.skinLine} />
          <circle cx="303" cy="196" r="14" fill={P.skinLine} />
        </>
      )}
      {/* mouth */}
      {open ? (
        <ellipse cx="270" cy="252" rx="20" ry="15" fill={P.skinLine} />
      ) : (
        <line x1="242" y1="252" x2="298" y2="252" stroke={P.skinLine} strokeWidth="7" strokeLinecap="round" />
      )}
    </g>
  );
};

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
            {/* two laughing faces flanking */}
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
          <div
            style={{
              marginTop: -6,
              fontFamily: FUN,
              fontSize: 96,
              color: P.paper,
              WebkitTextStroke: `7px ${P.ink}`,
              paintOrder: "stroke",
              letterSpacing: 3,
              lineHeight: 1,
            }}
          >
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

// ================= OFFICE SCENE =================
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
        textShadow: `0 4px 0 rgba(0,0,0,.65), 4px 0 0 ${P.ink}, -4px 0 0 ${P.ink}, 0 -4px 0 ${P.ink}, 0 6px 18px rgba(0,0,0,.55)`,
        WebkitTextStroke: `3px ${P.ink}`,
        paintOrder: "stroke",
      }}
    >
      {parts[0]}
      {hot && <span style={{ color: P.green }}>{hot}</span>}
      {parts[1]}
    </div>
  );
};

const OfficeScene: React.FC = () => {
  const f = useCurrentFrame();
  const bob = Math.sin(f / 9) * 4;
  const push = interpolate(f, [138, 190], [1, 1.14], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  // number reveal on the monitor
  const numAppear = interpolate(f, [132, 150], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  let cap: React.ReactNode = null;
  if (f >= 6 && f < 72) cap = <Caption text="Welcome to the Quarterly Report." />;
  else if (f >= 78 && f < 150) cap = <Caption text="This quarter, the market called Nvidia a “bubble.”" />;
  else if (f >= 150) cap = <Caption text="A model says it’s worth 1.8× the price. So… half off." hot="1.8× the price" />;

  return (
    <AbsoluteFill style={{ background: P.wall }}>
      <AbsoluteFill style={{ transform: `scale(${push})`, transformOrigin: "60% 42%" }}>
        <svg width="1080" height="1920" viewBox="0 0 1080 1920">
          {/* wall + floor */}
          <rect x="0" y="0" width="1080" height="1180" fill={P.wall} />
          <rect x="0" y="1180" width="1080" height="740" fill={P.floor} />
          <line x1="0" y1="1180" x2="1080" y2="1180" stroke={P.wallDk} strokeWidth="6" />
          {/* window */}
          <rect x="700" y="230" width="300" height="360" fill={P.window} stroke={P.skinLine} strokeWidth="10" />
          <line x1="850" y1="230" x2="850" y2="590" stroke={P.skinLine} strokeWidth="8" />
          <line x1="700" y1="410" x2="1000" y2="410" stroke={P.skinLine} strokeWidth="8" />
          {/* desk */}
          <rect x="0" y="1180" width="1080" height="80" fill={P.desk} stroke={P.deskEdge} strokeWidth="6" />
          {/* pen cup */}
          <rect x="120" y="1120" width="70" height="70" rx="8" fill={P.green} stroke={P.skinLine} strokeWidth="7" />
          <line x1="140" y1="1120" x2="132" y2="1060" stroke={P.skinLine} strokeWidth="7" strokeLinecap="round" />
          <line x1="165" y1="1120" x2="172" y2="1055" stroke={P.orange} strokeWidth="9" strokeLinecap="round" />
          {/* monitor */}
          <g transform="translate(600 760)">
            <rect x="0" y="0" width="430" height="300" rx="14" fill={P.monitor} stroke={P.skinLine} strokeWidth="10" />
            <rect x="24" y="24" width="382" height="252" rx="6" fill={P.screen} />
            <rect x="195" y="300" width="40" height="70" fill={P.monitor} stroke={P.skinLine} strokeWidth="8" />
            <rect x="150" y="368" width="130" height="16" rx="6" fill={P.monitor} stroke={P.skinLine} strokeWidth="8" />
            {/* number reveal on screen */}
            <g opacity={numAppear}>
              <text x="215" y="108" textAnchor="middle" fontFamily={BODY} fontWeight="900" fontSize="56" fill="#7FE9C2">NVDA</text>
              <text x="215" y="204" textAnchor="middle" fontFamily={FUN} fontSize="104" fill="#5AF0A8" stroke="#0A3D2A" strokeWidth="2" paintOrder="stroke">1.8×</text>
              <text x="215" y="250" textAnchor="middle" fontFamily={BODY} fontWeight="800" fontSize="28" fill={P.paper}>UNDER a model</text>
            </g>
          </g>
          {/* the analyst behind the desk (head/torso rising above desk edge) */}
          <g transform="translate(120 640)">
            <Guy talk={mouthOpen(f)} blink={isBlinking(f)} bob={bob} />
          </g>
        </svg>
      </AbsoluteFill>
      {cap}
    </AbsoluteFill>
  );
};

// ================= REACTION (hard cut, C&H signature) =================
const ReactionFace: React.FC = () => {
  const f = useCurrentFrame();
  const shake = f > 40 ? Math.sin(f / 1.5) * 3 : 0;
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg, ${P.orange}, ${P.orangeDk})` }}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <svg width="760" height="760" viewBox="0 0 760 760" style={{ transform: `translateX(${shake}px)` }}>
          <circle cx="380" cy="360" r="300" fill={P.skin} stroke={P.skinLine} strokeWidth="14" />
          {/* deadpan dot eyes */}
          <circle cx="290" cy="330" r="30" fill={P.skinLine} />
          <circle cx="470" cy="330" r="30" fill={P.skinLine} />
          {/* dead-straight mouth */}
          <line x1="250" y1="470" x2="510" y2="470" stroke={P.skinLine} strokeWidth="14" strokeLinecap="round" />
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
      <Sequence durationInFrames={QR_BEATS.title}>
        <TitleCard />
      </Sequence>
      <Sequence from={QR_BEATS.title} durationInFrames={QR_BEATS.scene}>
        <OfficeScene />
      </Sequence>
      <Sequence from={QR_BEATS.title + QR_BEATS.scene} durationInFrames={QR_BEATS.react}>
        <ReactionFace />
      </Sequence>
      <Sequence from={QR_BEATS.title + QR_BEATS.scene + QR_BEATS.react} durationInFrames={QR_BEATS.end}>
        <EndCard />
      </Sequence>
    </AbsoluteFill>
  );
};
