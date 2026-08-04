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
import {actionCurve} from "../motion/toon";
import {FlashCut, ShockFlicks, ShockRing, SpeedLines, kick} from "../motion/ToonFX";
import {Grain, Vignette} from "../motion/Polish";
import {Move, Turn, idle, interactXform} from "../motion/interact";
import {FLOOR_Y, Room, TVFrame, TVGlass, TV_SCREEN, H as STAGE_H} from "../motion/Set";
import anchors from "../fixtures/cast_ep1/pose_anchors.json";
import mouthTracks from "../fixtures/cast_ep1/mouth_tracks.json";
import visemes from "../fixtures/cast_ep1/visemes.json";
import headFocus from "../fixtures/cast_ep1/head_focus.json";

type A = {w: number; h: number; ink_h: number; anchor: number[]; src: string; scale: number};
const AN = anchors as unknown as Record<string, A>;
type V = Partial<Record<"closed" | "half" | "open" | "oh" | "blink", string>>;
const VI = visemes as unknown as Record<string, V>;
const TR = mouthTracks as unknown as Record<string, number[]>;
const HF = headFocus as unknown as Record<string, {fx: number; fy: number}>;

// A SHOT is a reframing of the staged actor, held from `from` (a frame
// offset into the beat) until the next shot. Reframing is how one
// drawing yields several shots: a wide and a punch-in are two shots of
// the same pixels, so the cut gains rhythm with no second generation and
// therefore no identity drift. `k` scales about the head (head_focus.json)
// and tx/ty place that head on screen; k=1 with no tx/ty is the staged
// framing unchanged. `only` isolates one actor of a two-shot, which is
// what turns a static two-shot into shot/reverse-shot.
// `pose` swaps the DRAWING for this shot. This is not the old per-beat
// cycling that changed Sol's haircut mid-sentence: that swapped between
// near-identical framings every 14 frames. A shot-level swap happens once,
// on a phrase boundary, between two drawings the identity gate rates core
// tier for the same character AND that the shot-list review does not call
// interchangeable — i.e. a real cut to a different gesture.
type Shot = {from: number; k?: number; tx?: number; ty?: number; only?: number;
             hideCard?: boolean; pose?: string;
             // `show` is `only` for more than one actor — it lets a shot
             // hold two of three characters, which is what turns a cut-away
             // into the narrator PRESENTING someone.
             show?: number[];
             // Ramp the reframe across the shot instead of holding it —
             // a slow creep inward, which is how a held shot builds
             // pressure rather than just sitting there.
             kEnd?: number;
             // Drop the room into shadow for this shot. The lawmaker beats
             // are about money and power being moved quietly; playing them
             // in the same bright light as the rest of the episode was
             // what made her read as a caption rather than a character.
             mood?: "dark";
             // put a caricature on the studio monitor for this shot
             tvPose?: string};
const shotAt = (shots: Shot[] | undefined, since: number, hold: number) => {
  if (!shots || !shots.length) {
    return {shot: undefined, shotSince: since, shotLen: hold};
  }
  let cur = shots[0], idx = 0;
  for (let i = 0; i < shots.length; i++) {
    if (since >= shots[i].from) {
      cur = shots[i];
      idx = i;
    }
  }
  const end = idx + 1 < shots.length ? shots[idx + 1].from : hold;
  return {shot: cur, shotSince: since - cur.from,
          shotLen: Math.max(1, end - cur.from)};
};

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
// `moves` are arrivals/exits under cartoon physics and `turns` are head
// turns toward a point on stage — the two things that make a second
// character an event this one reacts to, rather than a separate picture
// that happens to share the frame. See motion/interact.ts.
type Actor = {poses: string[]; kind: "full" | "bust" | "closeup" | "panel";
              x: number; y: number; h: number;
              moves?: Move[]; turns?: Turn[]};
type Card = {title: string; lines: string[]; big?: string; foot?: string};
type Beat = {
  at: number; actors: Actor[];
  vo?: string; speaker?: "SOL" | "REX"; line?: string;
  vo2?: string; speaker2?: "SOL" | "REX"; line2?: string; at2?: number;
  shout?: string; card?: Card; title?: string[]; energy?: number;
  shots?: Shot[];
  // drawn "!!" flicks beside a head — the reaction accent on a turn
  flicks?: {at: number; x: number; y: number}[];
  // Motion hits (scripts/audio/make_toon_sfx.py). `at` is the frame the
  // sound must LAND on, which is the frame of the fast part of the move,
  // not the frame the move was scheduled — a move winds up first, and a
  // whoosh on the wind-up reads as dubbed.
  sfx?: {at: number; name: string; vol?: number}[];
  // Hold the base drawing's own mouth for the whole beat. A VO track
  // only covers the spoken word, and the mouth state falls back to
  // "closed" once it runs out — which shut Rex's mouth in the middle of
  // his own scream, because the shout lasts 26 frames and the take holds
  // for 55. On a reaction beat the drawing IS the performance.
  holdMouth?: boolean;
  // Move the shout off a character's face when the staging needs it.
  shoutAt?: {left: number; right: number; top: number};
  // Impact FX (speed lines + shock ring) used to be gated on `shout`
  // existing, so deleting a shout graphic silently deleted the beat's
  // punch as well. They are independent now; defaults to whether there
  // is a shout so older beats are unchanged.
  fx?: boolean;
};

// One height per character, used everywhere they stand. Rex is the
// TALLER of the two — he is the young one; Sol is a short round old man,
// which is also why Sol's oversized chibi head no longer makes him read
// as a giant. Both plant on Set.FLOOR_Y, so the floor is shared.
const REX_H = 1430;
const SOL_H = 1165;

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
   actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 660, y: 1170, h: 1010}],
   shots: [{from: 0}, {from: 56, k: 1.45, tx: 540, ty: 1080}],
   vo: "v1_sol_intro", speaker: "SOL",
   line: "Kid… let me tell you about the so-called “fair” market."},
  // Rex says "Boss!" — so there has to be a boss to say it TO. Sol now
  // stands in the shot wearing the smirk the shot-list review describes
  // as "dry, unimpressed skepticism", and Rex turns to him on the line.
  // NOTE: the push shot carries tx/ty, which re-centres whichever actor
  // it draws, so it must isolate one (only) or the two would stack.
  // Sol is a FULL-BODY drawing here, not the smug bust: a floating
  // head-and-shoulders standing next to a grounded full figure reads as
  // a cut-out pasted in, which is the exact complaint this pass exists
  // to fix. sol_point_v1 is core tier, clean, and otherwise unused.
  // Every standing figure is planted on FLOOR_Y now, and Rex is the
  // TALLER of the two — he is the young one and Sol is a short round old
  // man, which is also why Sol's head can stay large without him reading
  // as a giant.
  {at: 110, actors: [{poses: ["rex_eager"], kind: "full", x: 320, y: FLOOR_Y, h: REX_H,
                      turns: [{at: 10, tx: 860, ty: 1120}]},
                     {poses: ["sol_point_v1"], kind: "full", x: 830, y: FLOOR_Y, h: SOL_H}],
   shots: [{from: 0}, {from: 60, only: 0, k: 1.3, tx: 540, ty: 760}],
   sfx: [{at: 14, name: "sfx_whip", vol: 0.42}],
   vo: "v2_rex_fundamentals", speaker: "REX", line: "Boss! It's all fundamentals, right?!", energy: 1},
  // Sol is laughing AT someone, so keep that someone in frame: Rex
  // crouched screen-left in profile, facing right at him.
  // Scale: Sol was 63% of frame height beside a 34% crouching Rex who
  // was also clipped by the left edge — it read as a giant beside a
  // child, and clipped Sol frame-right too.
  // HEAD SIZE, not body height, is what makes two characters read as the
  // same scale — these drawings have very different head-to-body ratios
  // (scripts/vector/head_scale.py). Matched by ink height, Sol's head
  // rendered 432px wide against rex_listen's 128px: a giant beside a
  // child. rex_skeptic's proportions match Sol's, and "arms crossed, not
  // convinced" is the right read for being laughed at anyway.
  {at: 195, actors: [{poses: ["sol_laugh"], kind: "full", x: 760, y: FLOOR_Y, h: SOL_H},
                     {poses: ["rex_skeptic"], kind: "full", x: 300, y: FLOOR_Y, h: REX_H,
                      turns: [{at: 14, tx: -260, ty: 1820}]}],
   sfx: [{at: 18, name: "sfx_whip", vol: 0.38}],
   vo: "v3_sol_ha", speaker: "SOL", line: "HA! …Fundamentals.", energy: 1.1},
  // EYELINE. rex_listen is drawn in profile facing RIGHT, so Rex has to
  // stand screen-LEFT for his gaze to land on Sol; he was on the right,
  // staring away from the man talking to him. Sol now slides in from the
  // right to join him instead of simply being there on the cut.
  // rex_listen is a realistically-proportioned crouch among chibi
  // drawings — its head measures a quarter of Sol's at equal ink height,
  // so it is staged much larger and read as foreground rather than
  // matched by body height.
  {at: 255, actors: [{poses: ["rex_listen"], kind: "full", x: 268, y: FLOOR_Y, h: 1090},
                     {poses: ["sol_finger"], kind: "full", x: 790, y: FLOOR_Y, h: SOL_H,
                      moves: [{at: 0, kind: "inR"}]}],
   shots: [{from: 0}, {from: 30, only: 1, k: 1.5, tx: 560, ty: 900}, {from: 74}],
   sfx: [{at: 4, name: "sfx_whoosh", vol: 0.45}],
   vo: "v4_sol_politics", speaker: "SOL", line: "Sometimes… it trades on POLITICS."},
  {at: 345, actors: [{poses: ["rex_shock"], kind: "closeup", x: 540, y: 900, h: 1920}],
   // No shout graphic here: it sat over his collar at low contrast and
   // duplicated the subtitle directly beneath it. The held scream and
   // the speed lines carry the beat.
   holdMouth: true, fx: true,
   vo: "v5_rex_what", speaker: "REX", line: "WHAT?!", energy: 1.5},
  // Sol stands screen-RIGHT here like he does in every other beat. He was
  // on the left, which crossed the line the rest of the episode
  // establishes — and it also stacked him under the exhibit card instead
  // of balancing it.
  {at: 400, actors: [{poses: ["sol_point"], kind: "full", x: 800, y: FLOOR_Y, h: SOL_H},
                     // Rex is present for this whole 8s but only cut to
                     // once, silently, to react to the reveal — the shot
                     // that makes Sol's line land on somebody.
                     // The lawmaker the filing is about. A generic senior
                     // -stateswoman ARCHETYPE drawn as flat caricature —
                     // never a likeness of a named individual, and no
                     // on-screen text names anyone. The card states only
                     // what the public filing states, and the footer
                     // carries the parody / not-an-accusation rail.
                     // Steepled fingers, narrowed eyes: she is thinking
                     // about the trade, not presenting it. She now plays
                     // ON THE STUDIO MONITOR (Shot.tvPose) rather than
                     // standing in the room — she is archive footage the
                     // show is running, which is both truer to what she
                     // is and removes the scale problem of a
                     // differently-drawn figure sharing the floor.
                     {poses: ["rex_skeptic"], kind: "bust", x: 540, y: 1010, h: 1060}],
   card: {title: "JULY 2022 · PUBLIC FILING",
          lines: ["The then-Speaker's household sold",
                  "25,000 NVIDIA shares — days before",
                  "Congress passed billions in chip subsidies.",
                  "Sold at a loss (≈ $341K), amid the scrutiny."],
          foot: "STOCK Act disclosure · widely reported"},
   // 8s was one static shot — 22% of the episode. Cut on the VO's own
   // pauses (scripts/vector/phrase_cuts.py) between the speaker and the
   // evidence: wide+card, punch to Sol, back to the card, kicker CU.
   // shot 3 cuts to sol_finger: it breaks up 8s of a single drawing, it
   // is the "here's the key insight" gesture the line wants, and unlike
   // sol_point it carries a gated blink, so Sol blinks during the
   // longest sequence in the episode.
   // cut points are the VO's own pauses (scripts/vector/phrase_cuts.py).
   // The lawmaker held for 22 frames before — under a second, so she
   // registered as a flash. She now gets 50 frames of her own in the
   // dark, then 33 more with Sol in frame presenting her, which is what
   // ties her into the telling instead of interrupting it.
   shots: [{from: 0, only: 0},
           {from: 58, only: 0, k: 3.0, tx: 520, ty: 860},
           {from: 88, only: 0, mood: "dark", tvPose: "congress_scheme"},
           {from: 138, only: 0, mood: "dark", tvPose: "congress_scheme",
            k: 1.0, kEnd: 1.12},
           {from: 171, only: 1},
           {from: 190, only: 0, k: 2.2, tx: 560, ty: 960}],
   vo: "v6_sol_exhibit", speaker: "SOL",
   line: "July 2022. The Speaker's household sold NVIDIA — days before the chip subsidies passed. At a loss, kid."},
  // rex_eager instead of rex_shock_v1, and NO panel. The panel existed to
  // present a full-bleed drawing honestly, but its cream backing plate
  // read as "character pasted on a little white card" — the owner's
  // objection. A clean-silhouette drawing needs no plate: it just floats.
  // She RETURNS here — arms crossed, cold, while the card explains that
  // the trades became a product. One appearance reads as a cutaway; a
  // recurring figure reads as a character in the story.
  {at: 640, actors: [{poses: ["rex_eager"], kind: "full", x: 620, y: FLOOR_Y, h: REX_H}],
   card: {title: "FEB 2023 · IT BECAME A PRODUCT",
          lines: ["An ETF now copies Democratic lawmakers'",
                  "disclosed trades. Actively managed."],
          big: "NANC", foot: "public filings in · portfolio out"},
   // Both in frame: Rex is the one SPEAKING this line, so cutting him out
   // of it repeats the mistake that shut his mouth mid-scream at 345.
   // She looms behind him instead.
   shots: [{from: 0, mood: "dark", tvPose: "congress_smug"},
           {from: 47, k: 1.35, tx: 600, ty: 1180}],
   // No shout graphic: with both characters staged there is nowhere for
   // 150pt type to land except across a face, and the subtitle already
   // carries the line. The impact FX stay.
   fx: true,
   vo: "v7_rex_index", speaker: "REX", line: "They made it an INDEX?!",
   energy: 1.3},
  // was sol_point_v1 — which the shot-list review groups as
  // interchangeable with beat 400's sol_point (same stance, same size,
  // both WS to camera), so the two longest Sol beats read as one shot.
  // sol_smug_v1 is core tier, carries visemes + a blink, and is the only
  // Sol CU with a CLEAN silhouette — sol_smug reads the same but is
  // full-bleed, so covering the frame forced an extreme crop that lost
  // the eyes. Reused from beat 0, but at 4x the size and 25s later; the
  // shot-list review only warns against cutting the smug set together
  // back to back.
  // ...and then he's gone. The vanish is what MOTIVATES the pop-in at
  // 895: Rex asks an empty room, and Sol answers from somewhere he
  // wasn't. Without the exit, the pop is just an arrival.
  {at: 740, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 540, y: 1040, h: 1330,
                      moves: [{at: 138, kind: "vanish"}]}],
   shots: [{from: 0}, {from: 64, k: 1.3, tx: 520, ty: 880}, {from: 119}],
   sfx: [{at: 138, name: "sfx_poof", vol: 0.5}],
   vo: "v8_sol_legal", speaker: "SOL",
   line: "All disclosed. In ranges. Up to 45 days late. All legal."},
  // was a static 4s two-shot with both characters on screen while they
  // took turns speaking. Now shot/reverse-shot, cutting on the handover.
  // THE EXCHANGE. Rex asks the room; Sol is not there, then POPS IN top
  // right and Rex's head whips round to find him. Both stay on screen for
  // the answer, so the last beat is two characters in one space rather
  // than two solo portraits cut together.
  {at: 895, actors: [{poses: ["rex_eager"], kind: "full", x: 360, y: FLOOR_Y, h: REX_H,
                      turns: [{at: 56, tx: 830, ty: 1060}]},
                     // sol_smug_v1: clean silhouette, so he pops in as a
                     // floating figure with no backing plate.
                     // he pops up BEHIND THE DESK beside Rex now, not in
                     // mid-air — the set gives him somewhere to be
                     {poses: ["sol_smug_v1"], kind: "bust", x: 862, y: 1268, h: 640,
                      moves: [{at: 52, kind: "pop"}]}],
   shots: [{from: 0, only: 0, k: 1.25, tx: 520, ty: 1000},
           {from: 50}],
   // beside REX's measured head (~356,1076), fanning up toward Sol
   flicks: [{at: 57, x: 560, y: 1130}],
   sfx: [{at: 52, name: "sfx_pop", vol: 0.6},
         {at: 60, name: "sfx_whip", vol: 0.42}],
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

const Char: React.FC<{a: Actor; since: number; frame: number; speaking: boolean;
                      mouthState: number; shot?: Shot; shotSince: number;
                      shotLen: number; holdMouth?: boolean}> =
  ({a, since, frame, speaking, mouthState, shot, shotSince, shotLen,
    holdMouth}) => {
  const cycling = speaking && cycleAllowed(a.poses);
  const idx = cycling
    ? CYCLE[Math.floor(since / SWAP) % CYCLE.length] % a.poses.length
    : 0;
  const pose = shot?.pose ?? a.poses[idx];
  const d = AN[pose];
  if (!d) return null;
  const swapSince = since % SWAP;
  // the snap belongs to the SHOT, not the beat: a reframe is a cut and
  // has to arrive with its own anticipation/settle, or the punch-in
  // reads as a zoom.
  const act = actionCurve(cycling ? swapSince : shotSince, 2, 5, 8);
  const pop = 0.955 + 0.045 * Math.min(1, Math.max(0, act));
  const amp = a.kind === "closeup" ? STAGE_H * 0.5 : a.h;
  // No boil. Its 2-frame random offset read as the picture vibrating on
  // these large clean vectors; idle() breathes and shifts weight instead.
  const idl = idle(frame, pose.length, amp);
  const scale = a.kind === "full" ? a.h / d.ink_h
    : a.kind === "closeup"
    // cover the frame: no canvas edge can fall inside it. 1.04 pads the
    // boil/bob/pop jitter so a wobble can't reveal a corner.
    ? 1.04 * Math.max(W / d.w, H / d.h)
    : a.h / d.h;
  const w0 = d.w * scale, h0 = d.h * scale;
  const left0 = a.kind === "full" ? a.x - d.anchor[0] * w0 : a.x - w0 / 2;
  const top0 = a.kind === "full" ? a.y - d.anchor[1] * h0 : a.y - h0 / 2;
  // Reframe about the HEAD, so a punch-in keeps the face on screen
  // instead of drifting toward the canvas centre.
  const hf = HF[pose] ?? {fx: 0.5, fy: 0.32};
  const k0 = shot?.k ?? 1;
  const k = shot?.kEnd === undefined ? k0
    : k0 + (shot.kEnd - k0) * Math.min(1, shotSince / shotLen);
  const w = w0 * k, h = h0 * k;
  const hx = left0 + hf.fx * w0, hy = top0 + hf.fy * h0;
  const left = (shot?.tx ?? hx) - hf.fx * w;
  const top = (shot?.ty ?? hy) - hf.fy * h;
  const src = holdMouth ? d.src : visemeSrc(pose, mouthState, speaking, frame);
  const panel = a.kind === "panel";
  const ix = interactXform(since, a.moves, a.turns,
                           shot?.tx ?? hx, shot?.ty ?? hy);
  return (
    <div style={{position: "absolute", left: left + idl.dx, top: top + idl.dy,
      width: w, height: h,
      transform: `translate(${ix.dx}px, ${ix.dy}px) `
        + `scale(${pop * ix.sx * idl.sx}, ${pop * ix.sy * idl.sy}) `
        + `rotate(${ix.rot + idl.rot + (panel ? -1.2 : 0)}deg)`,
      transformOrigin: a.kind === "full" ? `${d.anchor[0] * 100}% ${d.anchor[1] * 100}%` : "50% 60%",
      opacity: Math.min(1, since / 3) * ix.opacity,
      ...(ix.blur > 0.05 ? {filter: `blur(${ix.blur}px)`} : {}),
      ...(panel ? {border: "6px solid #111", borderRadius: 8, overflow: "hidden",
        boxShadow: "10px 12px 0 rgba(0,0,0,0.35)", background: "#F7F3E8"} : {})}}>
      <Img src={staticFile(src)} style={{position: "absolute", inset: 0, width: "100%", height: "100%"}} />
    </div>
  );
};

// The exhibit is now BROADCAST — it fills the studio monitor rather than
// floating in the air, so the characters are looking at something in the
// room with them. Type is sized to the screen, not the frame.
const ExhibitCard: React.FC<{c: Card; since: number}> = ({c, since}) => {
  const slide = Math.min(1, since / 9);
  return (
    <div style={{position: "absolute", inset: 0, background: "#F7F4E9",
      fontFamily: "Arial", color: "#111", padding: "26px 34px",
      transform: `translateY(${(1 - slide) * 14}px)`, opacity: slide}}>
      <div style={{fontFamily: "Impact, Arial", fontSize: 38, letterSpacing: 1,
        borderBottom: "4px solid #111", paddingBottom: 8, marginBottom: 14}}>{c.title}</div>
      {c.lines.map((ln, i) => (
        <div key={i} style={{fontSize: 31, fontWeight: 700, lineHeight: 1.36,
          opacity: since > 14 + i * 20 ? 1 : 0}}>{ln}</div>
      ))}
      {c.big ? (
        <div style={{fontFamily: "Impact, Arial", fontSize: 104, textAlign: "center",
          margin: "2px 0 0", color: "#7A1F2B", opacity: since > 30 ? 1 : 0}}>{c.big}</div>
      ) : null}
      {c.foot ? (
        <div style={{fontSize: 20, position: "absolute", left: 34, bottom: 18,
          color: "#555"}}>{c.foot}</div>
      ) : null}
    </div>
  );
};

// A caricature playing on the monitor. Contained by the screen, so she
// is always "footage the show is running" rather than a figure standing
// impossibly in the room next to the cast.
const TVPose: React.FC<{pose: string; since: number}> = ({pose, since}) => {
  const d = AN[pose];
  if (!d) return null;
  // Framed like an interview insert, not a full-length portrait: a
  // standing figure letterboxed into a 16:9 screen is a sliver, so she
  // is pushed in until her head and hands fill the picture.
  const s = (TV_SCREEN.h * 1.85) / d.h;
  const w = d.w * s, h = d.h * s;
  const rise = Math.min(1, since / 12);
  return (
    <div style={{position: "absolute", inset: 0, overflow: "hidden",
      background: "linear-gradient(180deg,#1B2438 0%,#0E1422 100%)"}}>
      <Img src={staticFile(d.src)}
        style={{position: "absolute", width: w, height: h,
          left: TV_SCREEN.w / 2 - w / 2,
          top: TV_SCREEN.h * 0.06 - h * 0.06 + (1 - rise) * 30,
          opacity: rise}} />
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
  const {cur, since, hold} = beatAt(frame);
  const outro = cur.at === 1015;
  const nrg = cur.energy ?? 0.7;
  const k = kick(since, 10 * nrg, 14);
  const sub2 = cur.vo2 && since >= (cur.at2 ?? 0);
  const ms = mouthStateFor(cur, frame);
  const activeSpeaker = sub2 ? cur.speaker2 : cur.speaker;
  const {shot, shotSince, shotLen} = shotAt(cur.shots, since, hold);

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
          {(b.sfx ?? []).map((s, i) => (
            <Sequence key={`s${i}`} from={b.at + s.at} durationInFrames={22}>
              <Audio src={staticFile(`audio/${s.name}.wav`)} volume={s.vol ?? 0.5} />
            </Sequence>
          ))}
        </React.Fragment>
      ))}
      <div style={{position: "absolute", inset: 0,
        transform: `translate(${k.x}px, ${k.y * 0.4}px) scale(${1 + 0.03 * Math.max(0, 1 - since / 10) * nrg})`,
        transformOrigin: "50% 45%"}}>
        <Room dark={shot?.mood === "dark"} />
        {cur.card || shot?.tvPose ? (
          <>
            <TVFrame glow />
            <div style={{position: "absolute", left: TV_SCREEN.x, top: TV_SCREEN.y,
              width: TV_SCREEN.w, height: TV_SCREEN.h, overflow: "hidden",
              borderRadius: 4}}>
              {shot?.tvPose ? <TVPose pose={shot.tvPose} since={shotSince} />
                : cur.card ? <ExhibitCard c={cur.card} since={since} /> : null}
            </div>
            <TVGlass />
          </>
        ) : null}
        {/* DARK MOOD. Sits above the room and below the characters, so the
            figures stay readable while the space around them goes cold and
            closes in — a slow squeeze rather than a cut to black. */}
        {shot?.mood === "dark" ? (
          <div style={{position: "absolute", inset: 0, pointerEvents: "none",
            background: "radial-gradient(ellipse 62% 46% at 50% 52%,"
              + " rgba(8,10,18,0) 0%, rgba(8,10,18,0.55) 62%,"
              + " rgba(5,6,12,0.9) 100%)",
            opacity: Math.min(1, shotSince / 10)}} />
        ) : null}
        {(cur.fx ?? !!cur.shout) && since < 26
          ? <SpeedLines k={Math.max(0, 1 - since / 26)} seed={cur.at} /> : null}
        {cur.title && !outro ? (
          <div style={{position: "absolute", left: 60, top: 150, fontFamily: "Impact, Arial",
            color: "#F2F6FF", lineHeight: 1.02}}>
            <div style={{fontSize: 110}}>{cur.title[0]}</div>
            <div style={{fontSize: 110, color: "#FFD860"}}>{cur.title[1]}</div>
            <div style={{fontSize: 42, fontFamily: "Arial", fontWeight: 700, marginTop: 16,
              color: "#9FB2D8"}}>{cur.title[2]}</div>
          </div>
        ) : null}
        {cur.actors.map((a, i) => {
          if (shot?.show && !shot.show.includes(i)) return null;
          if (!shot?.show && shot?.only !== undefined && shot.only !== i) return null;
          const isSol = a.poses[0].startsWith("sol");
          const speaking = activeSpeaker === (isSol ? "SOL" : "REX");
          return <Char key={i} a={a} since={since} frame={frame} speaking={speaking}
                       mouthState={isSol ? ms.sol : ms.rex}
                       shot={shot} shotSince={shotSince} shotLen={shotLen}
                       holdMouth={cur.holdMouth} />;
        })}
        {(cur.flicks ?? []).map((f, i) => (
          <ShockFlicks key={i} x={f.x} y={f.y} since={since - f.at} size={72} />
        ))}
        {cur.fx ?? !!cur.shout ? <ShockRing x={540} y={860} since={since} /> : null}
        {cur.shout ? (
          <>
            <div style={{position: "absolute",
              left: cur.shoutAt?.left ?? 0, right: cur.shoutAt?.right ?? 0,
              top: cur.shoutAt?.top ?? 1380, textAlign: "center",
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
