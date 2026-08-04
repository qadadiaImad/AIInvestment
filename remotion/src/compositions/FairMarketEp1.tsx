// FairMarketEp1 v3 — voiced anime short with LIMITED-ANIMATION density:
// each beat cycles 2-3 adjacent LoRA drawings while its line is spoken
// (pose fills), and the speaking character's mouth is articulated by a
// code overlay driven per-frame by the VO amplitude (mouth_tracks.json,
// 30fps states 0/1/2) at the auto-detected mouth anchor of the active
// drawing (mouth_anchors.json). Facts/rails unchanged from v2.
import React from "react";
import {AbsoluteFill, Audio, Img, Sequence, staticFile, useCurrentFrame} from "remotion";
import {actionCurve, bob, boil} from "../motion/toon";
import {FlashCut, ShockRing, SpeedLines, kick} from "../motion/ToonFX";
import {Grain, Vignette} from "../motion/Polish";
import anchors from "../fixtures/cast_ep1/pose_anchors.json";
import mouthAnchors from "../fixtures/cast_ep1/mouth_anchors.json";
import mouthTracks from "../fixtures/cast_ep1/mouth_tracks.json";

type A = {w: number; h: number; ink_h: number; anchor: number[]; src: string; scale: number};
const AN = anchors as unknown as Record<string, A>;
type M = {x: number; y: number; w: number; skin: string};
const MO = mouthAnchors as unknown as Record<string, M>;
const TR = mouthTracks as unknown as Record<string, number[]>;

export const FAIRMARKET_FRAMES = 1085;
const VO_DELAY = 6;

type Actor = {poses: string[]; kind: "full" | "bust"; x: number; y: number; h: number};
type Card = {title: string; lines: string[]; big?: string; foot?: string};
type Beat = {
  at: number; actors: Actor[];
  vo?: string; speaker?: "SOL" | "REX"; line?: string;
  vo2?: string; speaker2?: "SOL" | "REX"; line2?: string; at2?: number;
  shout?: string; card?: Card; title?: string[]; energy?: number;
};

const BEATS: Beat[] = [
  {at: 0, title: ["MARKET LESSONS", "WITH SOL", "ep.1 — the 'fair' market"],
   actors: [{poses: ["sol_smug_v1", "sol_smug_v2"], kind: "bust", x: 740, y: 1330, h: 760}],
   vo: "v1_sol_intro", speaker: "SOL",
   line: "Kid… let me tell you about the so-called “fair” market."},
  {at: 110, actors: [{poses: ["rex_eager", "rex_eager_v1"], kind: "full", x: 540, y: 1700, h: 1090}],
   vo: "v2_rex_fundamentals", speaker: "REX", line: "Boss! It's all fundamentals, right?!", energy: 1},
  {at: 195, actors: [{poses: ["sol_laugh", "sol_laugh_v1"], kind: "full", x: 540, y: 1770, h: 1270}],
   vo: "v3_sol_ha", speaker: "SOL", line: "HA! …Fundamentals.", energy: 1.1},
  {at: 255, actors: [{poses: ["sol_whisper"], kind: "bust", x: 370, y: 920, h: 860},
                     {poses: ["rex_listen"], kind: "full", x: 850, y: 1750, h: 700}],
   vo: "v4_sol_politics", speaker: "SOL", line: "Sometimes… it trades on POLITICS."},
  {at: 345, actors: [{poses: ["rex_shock", "rex_shock_v1"], kind: "bust", x: 540, y: 880, h: 1260}],
   vo: "v5_rex_what", speaker: "REX", line: "WHAT?!", shout: "WHAT?!", energy: 1.5},
  {at: 400, actors: [{poses: ["sol_point", "sol_point_v1", "sol_finger"], kind: "full", x: 230, y: 1830, h: 800}],
   card: {title: "JULY 2022 · PUBLIC FILING",
          lines: ["The then-Speaker's household sold",
                  "25,000 NVIDIA shares — days before",
                  "Congress passed billions in chip subsidies.",
                  "Sold at a loss (≈ $341K), amid the scrutiny."],
          foot: "STOCK Act disclosure · widely reported"},
   vo: "v6_sol_exhibit", speaker: "SOL",
   line: "July 2022. The Speaker's household sold NVIDIA — days before the chip subsidies passed. At a loss, kid."},
  {at: 640, actors: [{poses: ["rex_shock_v1", "rex_shock"], kind: "bust", x: 860, y: 1560, h: 600}],
   card: {title: "FEB 2023 · IT BECAME A PRODUCT",
          lines: ["An ETF now copies Democratic lawmakers'",
                  "disclosed trades. Actively managed."],
          big: "NANC", foot: "public filings in · portfolio out"},
   vo: "v7_rex_index", speaker: "REX", line: "They made it an INDEX?!",
   shout: "AN INDEX?!", energy: 1.3},
  {at: 740, actors: [{poses: ["sol_shrug"], kind: "full", x: 540, y: 1770, h: 1230}],
   vo: "v8_sol_legal", speaker: "SOL",
   line: "All disclosed. In ranges. Up to 45 days late. All legal."},
  {at: 895, actors: [{poses: ["rex_determined"], kind: "full", x: 350, y: 1720, h: 1050},
                     {poses: ["sol_wink", "sol_wink_v1"], kind: "bust", x: 830, y: 1500, h: 550}],
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

const CYCLE = [0, 1, 0, 2];
const SWAP = 14;

const mouthStateFor = (beat: Beat, frame: number): {sol: number; rex: number} => {
  const out = {sol: 0, rex: 0};
  const apply = (vo?: string, speaker?: string, offset = 0) => {
    if (!vo || !speaker) return;
    const t = TR[vo];
    const i = frame - (beat.at + offset + VO_DELAY);
    if (t && i >= 0 && i < t.length) {
      if (speaker === "SOL") out.sol = Math.max(out.sol, t[i]);
      else out.rex = Math.max(out.rex, t[i]);
    }
  };
  apply(beat.vo, beat.speaker, 0);
  apply(beat.vo2, beat.speaker2, beat.at2 ?? 0);
  return out;
};

const Mouth: React.FC<{m: M; state: number; w: number; h: number}> = ({m, state, w, h}) => {
  const mw = m.w * w;
  const cx = m.x * w, cy = m.y * h;
  return (
    <>
      <div style={{position: "absolute", left: cx - mw * 0.85, top: cy - mw * 0.7,
        width: mw * 1.7, height: mw * 1.4, borderRadius: "50%", background: m.skin}} />
      {state === 0 ? (
        <div style={{position: "absolute", left: cx - mw * 0.45, top: cy - mw * 0.06,
          width: mw * 0.9, height: Math.max(5, mw * 0.13), borderRadius: 8, background: "#5A2028"}} />
      ) : state === 1 ? (
        <div style={{position: "absolute", left: cx - mw * 0.38, top: cy - mw * 0.24,
          width: mw * 0.76, height: mw * 0.5, borderRadius: "50%", background: "#6E2530",
          border: "3px solid #3A1015"}} />
      ) : (
        <div style={{position: "absolute", left: cx - mw * 0.5, top: cy - mw * 0.44,
          width: mw, height: mw * 0.92, borderRadius: "46%", background: "#6E2530",
          border: "3px solid #3A1015", overflow: "hidden"}}>
          <div style={{position: "absolute", left: "14%", bottom: -mw * 0.12, width: "72%",
            height: mw * 0.4, borderRadius: "50%", background: "#B84A56"}} />
        </div>
      )}
    </>
  );
};

const Char: React.FC<{a: Actor; since: number; frame: number; speaking: boolean; mouthState: number}> =
  ({a, since, frame, speaking, mouthState}) => {
  const idx = a.poses.length > 1 && speaking
    ? CYCLE[Math.floor(since / SWAP) % CYCLE.length] % a.poses.length
    : 0;
  const pose = a.poses[idx];
  const d = AN[pose];
  if (!d) return null;
  const swapSince = since % SWAP;
  const act = actionCurve(speaking ? swapSince : since, 2, 5, 8);
  const pop = 0.955 + 0.045 * Math.min(1, Math.max(0, act));
  const bl = boil(frame, pose.length, a.h * 0.0015);
  const by = bob(frame, pose.length + 2, a.h * 0.004, 36);
  const scale = a.h / (a.kind === "full" ? d.ink_h : d.h);
  const w = d.w * scale, h = d.h * scale;
  const left = a.kind === "full" ? a.x - d.anchor[0] * w : a.x - w / 2;
  const top = a.kind === "full" ? a.y - d.anchor[1] * h : a.y - h / 2;
  const m = MO[pose];
  return (
    <div style={{position: "absolute", left: left + bl.x, top: top + by + bl.y,
      width: w, height: h, transform: `scale(${pop})`,
      transformOrigin: a.kind === "full" ? `${d.anchor[0] * 100}% ${d.anchor[1] * 100}%` : "50% 60%",
      opacity: Math.min(1, since / 3)}}>
      <Img src={staticFile(d.src)} style={{position: "absolute", inset: 0, width: w, height: h}} />
      {m && speaking ? <Mouth m={m} state={mouthState} w={w} h={h} /> : null}
    </div>
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
  const ms = mouthStateFor(cur, frame);
  const activeSpeaker = sub2 ? cur.speaker2 : cur.speaker;

  return (
    <AbsoluteFill style={{background: "#101828", overflow: "hidden"}}>
      {BEATS.map((b) => (
        <React.Fragment key={b.at}>
          {b.vo ? (
            <Sequence from={b.at + VO_DELAY} durationInFrames={320}>
              <Audio src={staticFile(`audio/fairmarket/${b.vo}.wav`)} />
            </Sequence>
          ) : null}
          {b.vo2 ? (
            <Sequence from={b.at + (b.at2 ?? 0) + VO_DELAY} durationInFrames={120}>
              <Audio src={staticFile(`audio/fairmarket/${b.vo2}.wav`)} />
            </Sequence>
          ) : null}
        </React.Fragment>
      ))}
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
        {cur.actors.map((a, i) => {
          const isSol = a.poses[0].startsWith("sol");
          const speaking = activeSpeaker === (isSol ? "SOL" : "REX");
          return <Char key={i} a={a} since={since} frame={frame} speaking={speaking}
                       mouthState={isSol ? ms.sol : ms.rex} />;
        })}
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
