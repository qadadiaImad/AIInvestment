// FairMarketEp1 v4 — voiced anime short with LIMITED-ANIMATION density:
// each beat cycles 2-3 adjacent LoRA drawings while its line is spoken
// (pose fills), and the speaking character's mouth is articulated by
// swapping WHOLE VISEME DRAWINGS (visemes.json: per-pose closed/half/
// open/oh/blink SVGs, inpaint-generated with the cast LoRA so every
// mouth is native art at the native position — supersedes the v3 code
// overlay the owner rejected). States come per-frame from the VO
// amplitude (mouth_tracks.json, 30fps 0/1/2); sustained open holds
// alternate open/oh, and a pose-seeded blink fires on closed-mouth
// frames. Every viseme SVG shares its base drawing's exact canvas, so
// all layout math is untouched. Facts/rails unchanged from v2.
import React from "react";
import {AbsoluteFill, Audio, Img, Sequence, staticFile, useCurrentFrame} from "remotion";
import {actionCurve, bob, boil} from "../motion/toon";
import {FlashCut, ShockRing, SpeedLines, kick} from "../motion/ToonFX";
import {Grain, Vignette} from "../motion/Polish";
import anchors from "../fixtures/cast_ep1/pose_anchors.json";
import mouthTracks from "../fixtures/cast_ep1/mouth_tracks.json";
import visemes from "../fixtures/cast_ep1/visemes.json";

type A = {w: number; h: number; ink_h: number; anchor: number[]; src: string; scale: number};
const AN = anchors as unknown as Record<string, A>;
type V = Partial<Record<"closed" | "half" | "open" | "oh" | "blink", string>>;
const VI = visemes as unknown as Record<string, V>;
const TR = mouthTracks as unknown as Record<string, number[]>;

export const FAIRMARKET_FRAMES = 1085;
const VO_DELAY = 6;

// kind: "full"  — figure standing in frame, scaled by ink height, placed
//                 by its ground-contact anchor
//       "bust"  — clean-silhouette upper body floating at a point
//       "closeup" — a FULL-BLEED drawing (its head is clipped by its own
//                 canvas edge, see scripts/vector/shot_class.py). Scaled
//                 to COVER the frame so the canvas boundary is never
//                 visible; `h` is ignored, `y` biases the vertical crop.
//       "panel" — a full-bleed drawing used SMALL, where covering the
//                 frame would bury the exhibit card. Its canvas edge is
//                 owned instead of hidden: ruled border + drop shadow +
//                 slight tilt, the same manga-panel language as the card.
type Actor = {poses: string[]; kind: "full" | "bust" | "closeup" | "panel"; x: number; y: number; h: number};
type Card = {title: string; lines: string[]; big?: string; foot?: string};
type Beat = {
  at: number; actors: Actor[];
  vo?: string; speaker?: "SOL" | "REX"; line?: string;
  vo2?: string; speaker2?: "SOL" | "REX"; line2?: string; at2?: number;
  shout?: string; card?: Card; title?: string[]; energy?: number;
};

// ONE drawing per beat. Every pose here is "core" tier in the identity
// gate (scripts/vector/pose_contact.py -> same haircut, same 3/4 head
// direction, same wardrobe as the canonical sol_smug / rex_eager) AND a
// clean silhouette, except where the kind is "closeup"/"panel" which
// exist to present the full-bleed drawings honestly. Deliberately NOT
// used: sol_armswide (single-tuft hair + side profile), sol_whisper_v1
// (no cardigan, no bow tie), rex_determined (adds a necktie no other
// Rex drawing has), rex_eager_v1/rex_skeptic/sol_shrug_v1 (a leaner,
// thinner-lined rendering cluster).
const BEATS: Beat[] = [
  {at: 0, title: ["MARKET LESSONS", "WITH SOL", "ep.1 — the 'fair' market"],
   actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 740, y: 1330, h: 760}],
   vo: "v1_sol_intro", speaker: "SOL",
   line: "Kid… let me tell you about the so-called “fair” market."},
  {at: 110, actors: [{poses: ["rex_eager"], kind: "full", x: 540, y: 1700, h: 1090}],
   vo: "v2_rex_fundamentals", speaker: "REX", line: "Boss! It's all fundamentals, right?!", energy: 1},
  {at: 195, actors: [{poses: ["sol_laugh"], kind: "full", x: 540, y: 1770, h: 1270}],
   vo: "v3_sol_ha", speaker: "SOL", line: "HA! …Fundamentals.", energy: 1.1},
  {at: 255, actors: [{poses: ["sol_finger"], kind: "full", x: 430, y: 1640, h: 1000},
                     {poses: ["rex_listen"], kind: "full", x: 850, y: 1750, h: 700}],
   vo: "v4_sol_politics", speaker: "SOL", line: "Sometimes… it trades on POLITICS."},
  {at: 345, actors: [{poses: ["rex_shock"], kind: "closeup", x: 540, y: 900, h: 1920}],
   vo: "v5_rex_what", speaker: "REX", line: "WHAT?!", shout: "WHAT?!", energy: 1.5},
  {at: 400, actors: [{poses: ["sol_point"], kind: "full", x: 230, y: 1830, h: 800}],
   card: {title: "JULY 2022 · PUBLIC FILING",
          lines: ["The then-Speaker's household sold",
                  "25,000 NVIDIA shares — days before",
                  "Congress passed billions in chip subsidies.",
                  "Sold at a loss (≈ $341K), amid the scrutiny."],
          foot: "STOCK Act disclosure · widely reported"},
   vo: "v6_sol_exhibit", speaker: "SOL",
   line: "July 2022. The Speaker's household sold NVIDIA — days before the chip subsidies passed. At a loss, kid."},
  {at: 640, actors: [{poses: ["rex_shock_v1"], kind: "panel", x: 760, y: 1370, h: 620}],
   card: {title: "FEB 2023 · IT BECAME A PRODUCT",
          lines: ["An ETF now copies Democratic lawmakers'",
                  "disclosed trades. Actively managed."],
          big: "NANC", foot: "public filings in · portfolio out"},
   vo: "v7_rex_index", speaker: "REX", line: "They made it an INDEX?!",
   shout: "AN INDEX?!", energy: 1.3},
  {at: 740, actors: [{poses: ["sol_point_v1"], kind: "full", x: 540, y: 1790, h: 1180}],
   vo: "v8_sol_legal", speaker: "SOL",
   line: "All disclosed. In ranges. Up to 45 days late. All legal."},
  {at: 895, actors: [{poses: ["rex_eager"], kind: "full", x: 350, y: 1740, h: 1000},
                     {poses: ["sol_wink"], kind: "panel", x: 770, y: 1370, h: 560}],
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
const W = 1080, H = 1920;

// Intra-beat pose cycling is OFF by default. Each pose variant is an
// independent LoRA generation, so swapping drawings mid-sentence changed
// Sol's haircut and head direction every 14 frames — it read as a glitch,
// not as animation. Density now comes from the viseme swaps, blinks and
// the toon motion instead. A pair may only re-enter this set if the
// identity gate certifies both drawings as the same haircut, head
// direction and framing (scripts/vector/pose_contact.py).
const SAFE_CYCLES: string[][] = [];
const cycleAllowed = (poses: string[]) =>
  poses.length > 1 &&
  SAFE_CYCLES.some((g) => poses.every((p) => g.includes(p)));

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

// Pick the drawing for this frame: the base pose art, or one of its
// inpainted viseme variants. Blink only fires when the mouth is closed
// (never fights a talk shape); sustained state-2 holds alternate
// open/oh every 7 frames so long vowels stay alive.
const visemeSrc = (pose: string, state: number, speaking: boolean,
                   frame: number): string => {
  const d = AN[pose];
  const v = VI[pose];
  if (!v) return d.src;
  const seed = (pose.charCodeAt(0) * 31 + pose.length * 7) % 97;
  const blinking = v.blink && ((frame + seed * 5) % (96 + (seed % 29))) < 3;
  if (!speaking) return blinking ? v.blink! : d.src;
  if (state === 0) return blinking ? v.blink! : (v.closed ?? d.src);
  if (state === 1) return v.half ?? v.closed ?? d.src;
  const alt = Math.floor(frame / 7) % 2 === 0;
  return (alt ? v.open : v.oh) ?? v.open ?? v.oh ?? d.src;
};

const Char: React.FC<{a: Actor; since: number; frame: number; speaking: boolean; mouthState: number}> =
  ({a, since, frame, speaking, mouthState}) => {
  const cycling = speaking && cycleAllowed(a.poses);
  const idx = cycling
    ? CYCLE[Math.floor(since / SWAP) % CYCLE.length] % a.poses.length
    : 0;
  const pose = a.poses[idx];
  const d = AN[pose];
  if (!d) return null;
  const swapSince = since % SWAP;
  const act = actionCurve(cycling ? swapSince : since, 2, 5, 8);
  const pop = 0.955 + 0.045 * Math.min(1, Math.max(0, act));
  const amp = a.kind === "closeup" ? H * 0.5 : a.h;
  const bl = boil(frame, pose.length, amp * 0.0015);
  const by = bob(frame, pose.length + 2, amp * 0.004, 36);
  const scale = a.kind === "full" ? a.h / d.ink_h
    : a.kind === "closeup"
    // cover the frame: no canvas edge can fall inside it. 1.04 pads the
    // boil/bob/pop jitter so a wobble can't reveal a corner.
    ? 1.04 * Math.max(W / d.w, H / d.h)
    : a.h / d.h;
  const w = d.w * scale, h = d.h * scale;
  const left = a.kind === "full" ? a.x - d.anchor[0] * w : a.x - w / 2;
  const top = a.kind === "full" ? a.y - d.anchor[1] * h : a.y - h / 2;
  const src = visemeSrc(pose, mouthState, speaking, frame);
  const panel = a.kind === "panel";
  return (
    <div style={{position: "absolute", left: left + bl.x, top: top + by + bl.y,
      width: w, height: h, transform: `scale(${pop})${panel ? " rotate(-1.2deg)" : ""}`,
      transformOrigin: a.kind === "full" ? `${d.anchor[0] * 100}% ${d.anchor[1] * 100}%` : "50% 60%",
      opacity: Math.min(1, since / 3),
      ...(panel ? {border: "6px solid #111", borderRadius: 8, overflow: "hidden",
        boxShadow: "10px 12px 0 rgba(0,0,0,0.35)", background: "#F7F3E8"} : {})}}>
      <Img src={staticFile(src)} style={{position: "absolute", inset: 0, width: "100%", height: "100%"}} />
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
