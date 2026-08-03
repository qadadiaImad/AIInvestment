// FairMarketEp1 v2 — "Market Lessons with Sol", ~36s ANIME-style dialogue
// short (owner: anime, not reader-manga). grok-TTS voices (sal/rex) +
// anime subtitles carry the dialogue; shouts are screen text with
// ToonFX; multi-character staging is composed solo LoRA renders.
// Facts on the exhibit cards are verified public record (July-2022 NVDA
// filing, Forbes 2022-07-27; NANC ETF launched Feb 2023). All text and
// numbers are code-set. Parody/educational rails on every frame.
import React from "react";
import {AbsoluteFill, Audio, Img, Sequence, staticFile, useCurrentFrame} from "remotion";
import {actionCurve, bob, boil} from "../motion/toon";
import {FlashCut, ShockRing, SpeedLines, kick} from "../motion/ToonFX";
import {Grain, Vignette} from "../motion/Polish";
import anchors from "../fixtures/cast_ep1/pose_anchors.json";

type A = {w: number; h: number; ink_h: number; anchor: number[]; src: string; scale: number};
const AN = anchors as unknown as Record<string, A>;

export const FAIRMARKET_FRAMES = 1085;

type Actor = {pose: string; kind: "full" | "bust"; x: number; y: number; h: number; flip?: boolean};
type Card = {title: string; lines: string[]; big?: string; foot?: string};
type Beat = {
  at: number; actors: Actor[];
  vo?: string; speaker?: "SOL" | "REX"; line?: string;
  vo2?: string; speaker2?: "SOL" | "REX"; line2?: string; at2?: number;
  shout?: string; card?: Card; title?: string[]; energy?: number;
};

const BEATS: Beat[] = [
  {at: 0, title: ["MARKET LESSONS", "WITH SOL", "ep.1 — the 'fair' market"],
   actors: [{pose: "sol_smug", kind: "bust", x: 740, y: 1330, h: 760}],
   vo: "v1_sol_intro", speaker: "SOL",
   line: "Kid… let me tell you about the so-called “fair” market."},
  {at: 110, actors: [{pose: "rex_eager", kind: "full", x: 540, y: 1700, h: 1090}],
   vo: "v2_rex_fundamentals", speaker: "REX", line: "Boss! It's all fundamentals, right?!", energy: 1},
  {at: 195, actors: [{pose: "sol_laugh", kind: "full", x: 540, y: 1770, h: 1270}],
   vo: "v3_sol_ha", speaker: "SOL", line: "HA! …Fundamentals.", energy: 1.1},
  {at: 255, actors: [{pose: "sol_whisper", kind: "bust", x: 370, y: 920, h: 860},
                     {pose: "rex_listen", kind: "full", x: 850, y: 1750, h: 700}],
   vo: "v4_sol_politics", speaker: "SOL", line: "Sometimes… it trades on POLITICS."},
  {at: 345, actors: [{pose: "rex_shock", kind: "bust", x: 540, y: 880, h: 1260}],
   vo: "v5_rex_what", speaker: "REX", line: "WHAT?!", shout: "WHAT?!", energy: 1.5},
  {at: 400, actors: [{pose: "sol_point", kind: "full", x: 230, y: 1830, h: 800}],
   card: {title: "JULY 2022 · PUBLIC FILING",
          lines: ["The then-Speaker's household sold",
                  "25,000 NVIDIA shares — days before",
                  "Congress passed billions in chip subsidies.",
                  "Sold at a loss (≈ $341K), amid the scrutiny."],
          foot: "STOCK Act disclosure · widely reported"},
   vo: "v6_sol_exhibit", speaker: "SOL",
   line: "July 2022. The Speaker's household sold NVIDIA — days before the chip subsidies passed. At a loss, kid."},
  {at: 640, actors: [{pose: "rex_shock", kind: "bust", x: 860, y: 1560, h: 600}],
   card: {title: "FEB 2023 · IT BECAME A PRODUCT",
          lines: ["An ETF now copies Democratic lawmakers'",
                  "disclosed trades. Actively managed."],
          big: "NANC", foot: "public filings in · portfolio out"},
   vo: "v7_rex_index", speaker: "REX", line: "They made it an INDEX?!",
   shout: "AN INDEX?!", energy: 1.3},
  {at: 740, actors: [{pose: "sol_shrug", kind: "full", x: 540, y: 1770, h: 1230}],
   vo: "v8_sol_legal", speaker: "SOL",
   line: "All disclosed. In ranges. Up to 45 days late. All legal."},
  {at: 895, actors: [{pose: "rex_determined", kind: "full", x: 350, y: 1720, h: 1050},
                     {pose: "sol_wink", kind: "bust", x: 830, y: 1500, h: 550}],
   vo: "v9_rex_filings", speaker: "REX", line: "So — read the filings!",
   vo2: "v10_sol_learning", speaker2: "SOL", line2: "Now you're learning, kid.", at2: 60},
  {at: 1015, title: ["MARKET LESSONS", "WITH SOL", ""], actors: []},
];

const beatAt = (f: number) => {
  let i = 0;
  for (let k = 0; k < BEATS.length; k++) if (f >= BEATS[k].at) i = k;
  const cur = BEATS[i];
  const next = BEATS[i + 1];
  return {cur, since: f - cur.at, hold: (next ? next.at : FAIRMARKET_FRAMES) - cur.at};
};

const Char: React.FC<{a: Actor; since: number; frame: number}> = ({a, since, frame}) => {
  const d = AN[a.pose];
  if (!d) return null;
  const act = actionCurve(since, 3, 6, 9);
  const pop = 0.94 + 0.06 * Math.min(1, Math.max(0, act));
  const bl = boil(frame, a.pose.length, a.h * 0.0015);
  const by = bob(frame, a.pose.length + 2, a.h * 0.004, 36);
  const scale = a.h / (a.kind === "full" ? d.ink_h : d.h);
  const w = d.w * scale, h = d.h * scale;
  const left = a.kind === "full" ? a.x - d.anchor[0] * w : a.x - w / 2;
  const top = a.kind === "full" ? a.y - d.anchor[1] * h : a.y - h / 2;
  return (
    <Img src={staticFile(d.src)}
      style={{position: "absolute", left: left + bl.x, top: top + by + bl.y,
        width: w, height: h,
        transform: `${a.flip ? "scaleX(-1) " : ""}scale(${pop})`,
        transformOrigin: a.kind === "full" ? `${d.anchor[0] * 100}% ${d.anchor[1] * 100}%` : "50% 60%",
        opacity: Math.min(1, since / 3)}} />
  );
};

const ExhibitCard: React.FC<{c: Card; since: number}> = ({c, since}) => {
  const pop = 0.9 + 0.1 * Math.min(1, since / 8);
  return (
    <div style={{position: "absolute", left: 90, top: 300, width: 900,
      background: "#FFFDF4", border: "6px solid #111", borderRadius: 10,
      transform: `scale(${pop}) rotate(-1.2deg)`, padding: "34px 40px",
      boxShadow: "10px 12px 0 rgba(0,0,0,0.3)", fontFamily: "Arial", color: "#111"}}>
      <div style={{fontFamily: "Impact, Arial", fontSize: 44, letterSpacing: 1,
        borderBottom: "4px solid #111", paddingBottom: 10, marginBottom: 18}}>{c.title}</div>
      {c.lines.map((ln, i) => (
        <div key={i} style={{fontSize: 38, fontWeight: 700, lineHeight: 1.5,
          opacity: since > 14 + i * 22 ? 1 : 0}}>{ln}</div>
      ))}
      {c.big ? (
        <div style={{fontFamily: "Impact, Arial", fontSize: 150, textAlign: "center",
          margin: "16px 0 4px", color: "#7A1F2B", opacity: since > 30 ? 1 : 0}}>{c.big}</div>
      ) : null}
      {c.foot ? <div style={{fontSize: 24, marginTop: 14, color: "#555"}}>{c.foot}</div> : null}
    </div>
  );
};

const Subtitle: React.FC<{speaker: string; line: string}> = ({speaker, line}) => (
  <div style={{position: "absolute", left: 60, right: 60, bottom: 90, textAlign: "center"}}>
    <div style={{fontFamily: "Impact, Arial", fontSize: 30, letterSpacing: 2,
      color: speaker === "SOL" ? "#E8A54B" : "#FF8A50", marginBottom: 6,
      textShadow: "2px 2px 0 #000"}}>{speaker}</div>
    <div style={{fontFamily: "Arial", fontWeight: 800, fontSize: 44, lineHeight: 1.3,
      color: "white",
      textShadow: "3px 3px 0 #000, -3px 3px 0 #000, 3px -3px 0 #000, -3px -3px 0 #000, 0 4px 8px rgba(0,0,0,0.8)"}}>
      {line}
    </div>
  </div>
);

export const FairMarketEp1: React.FC = () => {
  const frame = useCurrentFrame();
  const {cur, since} = beatAt(frame);
  const outro = cur.at === 1015;
  const nrg = cur.energy ?? 0.7;
  const k = kick(since, 10 * nrg, 14);
  const sub2 = cur.vo2 && since >= (cur.at2 ?? 0);

  return (
    <AbsoluteFill style={{background: "#101828", overflow: "hidden"}}>
      {/* VO tracks */}
      {BEATS.map((b) => (
        <React.Fragment key={b.at}>
          {b.vo ? (
            <Sequence from={b.at + 6} durationInFrames={320}>
              <Audio src={staticFile(`audio/fairmarket/${b.vo}.wav`)} />
            </Sequence>
          ) : null}
          {b.vo2 ? (
            <Sequence from={b.at + (b.at2 ?? 0) + 6} durationInFrames={120}>
              <Audio src={staticFile(`audio/fairmarket/${b.vo2}.wav`)} />
            </Sequence>
          ) : null}
        </React.Fragment>
      ))}
      {/* camera-kicked stage */}
      <div style={{position: "absolute", inset: 0,
        transform: `translate(${k.x}px, ${k.y * 0.4}px) scale(${1 + 0.03 * Math.max(0, 1 - since / 10) * nrg})`,
        transformOrigin: "50% 45%"}}>
        <div style={{position: "absolute", left: 540 - 640, top: 980 - 640, width: 1280,
          height: 1280, borderRadius: "50%", background: "#1A2740"}} />
        {cur.shout && since < 26 ? <SpeedLines k={Math.max(0, 1 - since / 26)} seed={cur.at} /> : null}
        {cur.title && !outro ? (
          <div style={{position: "absolute", left: 60, top: 150, fontFamily: "Impact, Arial",
            color: "#F2F6FF", lineHeight: 1.02}}>
            <div style={{fontSize: 110}}>{cur.title[0]}</div>
            <div style={{fontSize: 110, color: "#FFD860"}}>{cur.title[1]}</div>
            <div style={{fontSize: 42, fontFamily: "Arial", fontWeight: 700, marginTop: 16,
              color: "#9FB2D8"}}>{cur.title[2]}</div>
          </div>
        ) : null}
        {cur.card ? <ExhibitCard c={cur.card} since={since} /> : null}
        {cur.actors.map((a) => <Char key={a.pose} a={a} since={since} frame={frame} />)}
        {cur.shout ? (
          <>
            <ShockRing x={540} y={860} since={since} />
            <div style={{position: "absolute", left: 0, right: 0, top: 1380, textAlign: "center",
              fontFamily: "Impact, Arial", fontSize: 150, color: "#FFD860",
              transform: `rotate(-3deg) scale(${0.7 + 0.3 * Math.min(1, since / 4)})`,
              textShadow: "6px 6px 0 #000", opacity: since < 40 ? 1 : Math.max(0, 1 - (since - 40) / 10)}}>
              {cur.shout}
            </div>
          </>
        ) : null}
      </div>
      <FlashCut since={since} />
      {!outro && cur.line && !sub2 ? <Subtitle speaker={cur.speaker ?? ""} line={cur.line} /> : null}
      {!outro && sub2 ? <Subtitle speaker={cur.speaker2 ?? ""} line={cur.line2 ?? ""} /> : null}
      {outro ? (
        <div style={{position: "absolute", inset: 0, background: "#0B111E",
          display: "flex", flexDirection: "column", justifyContent: "center",
          alignItems: "center", textAlign: "center", fontFamily: "Arial", color: "#E8F0FF"}}>
          <div style={{fontFamily: "Impact, Arial", fontSize: 96}}>MARKET LESSONS</div>
          <div style={{fontFamily: "Impact, Arial", fontSize: 96, color: "#FFD860"}}>WITH SOL</div>
          <div style={{fontSize: 30, marginTop: 40, color: "#8FA3C8", maxWidth: 760, lineHeight: 1.6}}>
            PARODY · STYLIZED CHARACTERS · BASED ON PUBLIC FILINGS & REPORTS
            <br />EDUCATIONAL, NOT ADVICE · NOT AN ACCUSATION
            <br />made with a local model + code · $0
          </div>
        </div>
      ) : (
        <div style={{position: "absolute", left: 0, right: 0, bottom: 20, textAlign: "center",
          fontFamily: "Arial", fontSize: 22, color: "#6C7FA6"}}>
          parody · public record · educational, not advice
        </div>
      )}
      <Vignette strength={0.28} />
      <Grain opacity={0.03} />
    </AbsoluteFill>
  );
};
