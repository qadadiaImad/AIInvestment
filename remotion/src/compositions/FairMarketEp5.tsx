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
import {actionCurve, holdCurve, squash} from "../motion/toon";
import {FlashCut, ShockFlicks, ShockRing, SpeedLines, kick} from "../motion/ToonFX";
import {Grain, Vignette} from "../motion/Polish";
import {Move, Turn, idle, interactXform} from "../motion/interact";
import {FLOOR_Y, Room, TVFrame, TVGlass, TV_SCREEN, H as STAGE_H} from "../motion/Set";
import {ColumnsExhibit, DecayExhibit, SplitPriceExhibit, TickerTape} from "../motion/Infographic";
import anchors from "../fixtures/cast_ep1/pose_anchors.json";
import mouthTracks from "../fixtures/cast_ep1/mouth_tracks_ep5.json";
import visemes from "../fixtures/cast_ep1/visemes.json";
import headFocus from "../fixtures/cast_ep1/head_focus.json";
import rigParts from "../fixtures/cast_ep1/rig_parts.json";
import {CharRig, type Rig, type RigPose} from "../motion/CharRig";

type A = {w: number; h: number; ink_h: number; anchor: number[]; src: string; scale: number};
const AN = anchors as unknown as Record<string, A>;
type V = Partial<Record<"closed" | "half" | "open" | "oh" | "blink", string>>;
const VI = visemes as unknown as Record<string, V>;
const TR = mouthTracks as unknown as Record<string, number[]>;
const HF = headFocus as unknown as Record<string, {fx: number; fy: number}>;
const RIG = rigParts as unknown as Record<string, Rig>;
const RIG_OFF = false;   // flipped only by the A/B motion probe

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
             // RIG CHANNELS — opt-in per shot; omitted, the derived acting
             // system drives everything (same contract as Ep1)
             walk?: number; turn?: number; point?: number; look?: number;
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
             // BROADCAST INSERT: a rectangular photo filling the screen.
             // The podium officials are FOOTAGE the show is running, not
             // cut-out figures in the room, so they need no alpha — which
             // also removes the unkeyed-white-block artefact that fighting
             // the background key kept producing.
             tvPhoto?: string};
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

export const EP5_FRAMES = 4260;   // 142s

// Hard ceiling on how far a shot may push in. A drawing scaled until the
// face fills the frame throws away the set and has nowhere left to go —
// owner rule, after a static full-zoom face-only frame. Any reframe is
// clamped so the room stays readable behind the character.
const MAX_K = 1.9;
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
  // A code-drawn exhibit for the monitor, instead of a text card. The
  // card restated the spoken line; a graphic shows the mechanism.
  graphic?: "split_price" | "decay_buyer" | "decay_seller" | "share_0dte";
  // Impact FX (speed lines + shock ring) used to be gated on `shout`
  // existing, so deleting a shout graphic silently deleted the beat's
  // punch as well. They are independent now; defaults to whether there
  // is a shout so older beats are unchanged.
  fx?: boolean;
};

// There is no longer a single height constant per character. Every beat
// carries its own staged heights, because a figure's on-screen WIDTH
// follows its height — so one global height cannot satisfy both "Rex is
// taller" and "two figures fit in a 1080px frame without touching", and
// it also cannot satisfy "nobody covers the monitor" on exhibit beats.
// The per-beat numbers are output from scripts/vector/stage_audit.py,
// which measures real ink bounds against the real BEATS array; re-run it
// after ANY staging change. What stays invariant is the relationship:
// Rex reads TALLER (he is the young one, Sol is a short round old man)
// and both plant on Set.FLOOR_Y, so the floor is always shared.

// TWO-SHOT sizes. A figure's on-screen WIDTH is driven by its height, and
// at solo size rex_eager is 1009px wide — two of those cannot fit in a
// 1080px frame, which is why every two-shot was overlapping by 150-490px
// with both characters running off the edges. Solved numerically by
// scripts/vector/overlap_audit.py: each pair sized so both fit fully
// inside the frame with a real gap between them, Rex keeping a height
// advantage. A two-shot being smaller than a solo is correct anyway — it
// is a wider shot. The per-beat heights below ARE that solver's output —
// re-run overlap_audit after any staging change to re-verify.

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
  // ═══ COLD OPEN — the cheapest trade on the board ═════════════════════
  // No filing, no vote, no timestamp this time. The episode is a
  // MECHANISM, and it never says do or don't - it says know which side
  // of the clock you are standing on.
  {at: 0, title: ["MARKET LESSONS", "WITH SOL", "ep.5 — no tomorrow"],
   actors: [{poses: ["rex_eager"], kind: "full", x: 312, y: FLOOR_Y, h: 679,
             turns: [{at: 10, tx: 840, ty: 1210}]},
            {poses: ["sol_smug_v1"], kind: "bust", x: 812, y: 1300, h: 596}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08},
           {from: 60, only: 0, k: 1.28, kEnd: 1.4, tx: 520, ty: 1020}],
   sfx: [{at: 10, name: "sfx_whip", vol: 0.45}],
   vo: "g1_rex_cheapest", speaker: "REX",
   line: "Boss! I found the cheapest trade on the board.", energy: 1.3},

  {at: 110, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1180, h: 880}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08, tx: 540, ty: 1200}],
   vo: "g2_sol_cheaphow", speaker: "SOL", line: "Cheap how."},

  {at: 190, actors: [{poses: ["rex_eager"], kind: "full", x: 500, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "g3_rex_expiring", speaker: "REX",
   line: "Options expiring today. Barely cost anything!", energy: 1.2},

  {at: 320, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1180, h: 880}],
   shots: [{from: 0, k: 1.02, kEnd: 1.1, tx: 540, ty: 1200}],
   vo: "g4_sol_notomorrow", speaker: "SOL",
   line: "Ah. The ones with no tomorrow."},

  // ═══ ACT 1 — why they're cheap ═══════════════════════════════════════
  {at: 440, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   graphic: "split_price",
   shots: [{from: 0, k: 1.0, kEnd: 1.07}],
   vo: "g5_sol_twothings", speaker: "SOL",
   line: "An option has two things in it. What it's worth now, and how much time is left."},

  {at: 640, actors: [{poses: ["sol_point_v1"], kind: "full", x: 745, y: FLOOR_Y, h: 930}],
   graphic: "split_price",
   shots: [{from: 0, k: 1.0, kEnd: 1.07},
           {from: 130, k: 1.14, kEnd: 1.24, tx: 600, ty: 1190, hideCard: true}],
   vo: "g6_sol_missingpart", speaker: "SOL",
   line: "Take the time out and it's cheap. That's not a discount, kid. That's the missing part."},

  {at: 850, actors: [{poses: ["rex_skeptic"], kind: "full", x: 470, y: FLOOR_Y, h: 960}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12, tx: 540, ty: 1120}],
   vo: "g7_rex_lessforless", speaker: "REX", line: "So I'm paying less for less."},

  {at: 970, actors: [{poses: ["sol_finger"], kind: "full", x: 800, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, k: 1.02, kEnd: 1.12, tx: 580, ty: 1190}],
   vo: "g8_sol_zerohours", speaker: "SOL",
   line: "You're paying less for a bet that has to be right in the next few hours. Or it's zero."},

  // ═══ ACT 2 — the clock. THE curve; if this graphic works the episode
  // works, so it gets three consecutive beats of screen time.
  {at: 1170, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   graphic: "decay_buyer",
   shots: [{from: 0, k: 1.0, kEnd: 1.06}],
   vo: "g9_sol_watchclock", speaker: "SOL", line: "Watch what the clock does to it."},

  {at: 1300, actors: [{poses: ["sol_point_v1"], kind: "full", x: 745, y: FLOOR_Y, h: 930}],
   graphic: "decay_buyer",
   shots: [{from: 0, k: 1.0, kEnd: 1.07}],
   vo: "g10_sol_schedule", speaker: "SOL",
   line: "That decay isn't a risk. It's the schedule. It happens whether the market moves or not."},

  {at: 1520, actors: [{poses: ["rex_eager"], kind: "full", x: 500, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, k: 1.02, kEnd: 1.1}],
   vo: "g11_rex_ifright", speaker: "REX", line: "And if I'm right?"},

  {at: 1610, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1180, h: 880}],
   shots: [{from: 0, k: 1.02, kEnd: 1.1, tx: 540, ty: 1200}],
   vo: "g12_sol_beforeclose", speaker: "SOL",
   line: "Then you're right before the close, or you were wrong."},

  {at: 1760, actors: [{poses: ["rex_listen"], kind: "full", x: 400, y: FLOOR_Y, h: 820}],
   shots: [{from: 0, k: 1.06, kEnd: 1.14, tx: 520, ty: 1250}],
   vo: "g13_rex_notomorrow", speaker: "REX", line: "...there's no tomorrow."},

  {at: 1860, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1180, h: 880}],
   shots: [{from: 0, k: 1.0, kEnd: 1.1, tx: 540, ty: 1200}],
   vo: "g14_sol_notomorrow2", speaker: "SOL", line: "There's no tomorrow."},

  // ═══ ACT 3 — who's on the other side ═════════════════════════════════
  {at: 1980, actors: [{poses: ["rex_skeptic"], kind: "full", x: 470, y: FLOOR_Y, h: 960}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12, tx: 540, ty: 1120}],
   vo: "g15_rex_whoselling", speaker: "REX", line: "So who's selling them to me?"},

  {at: 2090, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   graphic: "decay_seller",
   shots: [{from: 0, k: 1.0, kEnd: 1.07}],
   vo: "g16_sol_wantsdecay", speaker: "SOL",
   line: "Somebody who wants that decay. It's their whole position."},

  {at: 2270, actors: [{poses: ["sol_point_v1"], kind: "full", x: 745, y: FLOOR_Y, h: 930}],
   graphic: "share_0dte",
   shots: [{from: 0, k: 1.0, kEnd: 1.07}],
   vo: "g17_sol_threequarters", speaker: "SOL",
   line: "Three quarters of retail's index-options trading is now same-day."},

  {at: 2450, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1215, h: 830}],
   graphic: "share_0dte",
   shots: [{from: 0, k: 1.0, kEnd: 1.06, tx: 540, ty: 1210}],
   vo: "g18_sol_halfvolume", speaker: "SOL",
   line: "Half the volume in them, more or less, is retail."},

  {at: 2600, actors: [{poses: ["rex_listen"], kind: "full", x: 400, y: FLOOR_Y, h: 820}],
   shots: [{from: 0, k: 1.06, kEnd: 1.14, tx: 520, ty: 1250}],
   vo: "g19_rex_otherhalf", speaker: "REX", line: "And the other half?"},

  {at: 2690, actors: [{poses: ["sol_finger"], kind: "full", x: 800, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, k: 1.02, kEnd: 1.12, tx: 580, ty: 1190}],
   vo: "g20_sol_forliving", speaker: "SOL",
   line: "People who do this for a living, collecting the thing you're paying."},

  // ═══ ACT 4 — the twist: no secret at all ═════════════════════════════
  {at: 2880, actors: [{poses: ["rex_shock"], kind: "full", x: 500, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   holdMouth: true, fx: true,
   sfx: [{at: 6, name: "impact", vol: 0.45}],
   vo: "g21_rex_samescreen", speaker: "REX",
   line: "But we're both looking at the same screen!", energy: 1.3},

  {at: 3010, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "g22_sol_samescreen", speaker: "SOL",
   line: "You are. Same screen, same prices, same everything."},

  {at: 3150, actors: [{poses: ["sol_point_v1"], kind: "full", x: 745, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "g23_sol_sitwith", speaker: "SOL",
   line: "That's what I want you to sit with. There's no secret here. No filing, nobody's phone."},

  {at: 3350, actors: [{poses: ["sol_finger"], kind: "full", x: 800, y: FLOOR_Y, h: 900}],
   graphic: "decay_seller",
   shots: [{from: 0, k: 1.0, kEnd: 1.07},
           {from: 140, k: 1.14, kEnd: 1.24, tx: 600, ty: 1190, hideCard: true}],
   vo: "g24_sol_sideofclock", speaker: "SOL",
   line: "The edge isn't information this time. It's which side of the clock you're standing on."},

  // ═══ ACT 5 — the close ═══════════════════════════════════════════════
  {at: 3560, actors: [{poses: ["rex_skeptic"], kind: "full", x: 470, y: FLOOR_Y, h: 960}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12, tx: 540, ty: 1120}],
   vo: "g25_rex_whatdo", speaker: "REX", line: "So what do I do with that?"},

  {at: 3660, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1180, h: 880}],
   shots: [{from: 0, k: 1.02, kEnd: 1.1, tx: 540, ty: 1200}],
   vo: "g26_sol_stopcalling", speaker: "SOL",
   line: "You stop calling it cheap. Cheap is a price. That was never the price."},

  {at: 3840, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930},
                      {poses: ["rex_listen"], kind: "bust", x: 400, y: 1270, h: 820}],
   shots: [{from: 0, only: 0, k: 1.0, kEnd: 1.07},
           {from: 130, only: 1, k: 1.0, kEnd: 1.08}],
   vo: "g27_sol_knowpaying", speaker: "SOL",
   line: "Know what you're paying for, and know who's collecting it."},

  {at: 4020, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1180, h: 880}],
   shots: [{from: 0, k: 1.0, kEnd: 1.12, tx: 540, ty: 1200}],
   vo: "g28_sol_fair", speaker: "SOL",
   line: "Fair? No. But now you know where you're standing."},

  {at: 4160, title: ["MARKET LESSONS", "WITH SOL", ""], actors: []},
];

const beatAt = (f: number) => {
  let i = 0;
  for (let k = 0; k < BEATS.length; k++) if (f >= BEATS[k].at) i = k;
  const cur = BEATS[i];
  const next = BEATS[i + 1];
  return {cur, since: f - cur.at, hold: (next ? next.at : EP5_FRAMES) - cur.at};
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

// THE ONE CLOCK. The owner's second verdict was "non synchronised
// motions", and it was true by construction: drawing swaps ran on a
// 38-frame timer, head actions on their own envelope, visemes on the
// audio, expressions on segments - four clocks, so nothing ever landed
// together. Real acting has one clock, the speech. A "stress" is the
// track's transition into state 2 (a wide vowel): the hand steps one
// rung, the head accents, and the expression turns all ON that frame,
// and everything HOLDS between stresses instead of drifting.
const stressFor = (beat: Beat, frame: number): {n: number; since: number} => {
  const vo = beat.vo;
  const t = vo ? TR[vo] : undefined;
  if (!t) return {n: 0, since: 9999};
  const i = frame - (beat.at + VO_DELAY);
  let n = 0;
  let last = -9999;
  const lim = Math.min(Math.max(0, i), t.length - 1);
  for (let k = 1; k <= lim; k++) {
    if (t[k] === 2 && t[k - 1] !== 2 && k - last > 8) {
      n++;
      last = k;
    }
  }
  return {n, since: i - last};
};

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

// Returns the viseme KEY rather than a file path, so the same choice can
// drive a whole-drawing swap (unrigged poses) or a rig head part (rigged
// ones). Behaviour is unchanged: blink only fires when the mouth is closed
// so it never fights a talk shape, and sustained state-2 alternates
// open/oh every 7 frames so long vowels stay alive.
const visemeKey = (pose: string, state: number, speaking: boolean,
                   frame: number): string | null => {
  const v = VI[pose];
  if (!v) return null;
  const seed = (pose.charCodeAt(0) * 31 + pose.length * 7) % 97;
  const blinking = v.blink && ((frame + seed * 5) % (96 + (seed % 29))) < 3;
  if (!speaking) return blinking ? "blink" : null;
  if (state === 0) return blinking ? "blink" : (v.closed ? "closed" : null);
  if (state === 1) return v.half ? "half" : (v.closed ? "closed" : null);
  const alt = Math.floor(frame / 7) % 2 === 0;
  const first = alt ? "open" : "oh";
  const second = alt ? "oh" : "open";
  return (v as Record<string, string | undefined>)[first] ? first
    : (v as Record<string, string | undefined>)[second] ? second : null;
};

const visemeSrc = (pose: string, state: number, speaking: boolean,
                   frame: number): string => {
  const d = AN[pose];
  const k = visemeKey(pose, state, speaking, frame);
  const v = VI[pose] as unknown as Record<string, string | undefined>;
  return (k && v?.[k]) || d.src;
};

const Char: React.FC<{a: Actor; since: number; frame: number; speaking: boolean;
                      mouthState: number; shot?: Shot; shotSince: number;
                      shotLen: number; holdMouth?: boolean; otherX?: number;
                      beatLen?: number; stressN?: number;
                      stressSince?: number}> =
  ({a, since, frame, speaking, mouthState, shot, shotSince, shotLen,
    holdMouth, otherX, beatLen, stressN = 0, stressSince = 9999}) => {
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
  // temper is derived from WHO the drawing is, so no beat has to carry it
  const temper = pose.startsWith("sol") ? "calm" : "eager";
  const idl = idle(frame, pose.length, amp, temper);
  // THE HELD SHOT. toon.ts ships holdCurve() and squash() for exactly this
  // and neither was ever imported here, so a held drawing had no life
  // beyond breathing: it arrived and then simply sat. holdCurve gives the
  // three-beat shape a real hold has — arrive fast, a small secondary
  // move partway through, settle — and squash puts that on a
  // volume-preserving axis rather than a uniform resize. Amplitudes are
  // deliberately tiny; this is the difference between a drawing that is
  // held and a drawing that is parked.
  const hc = holdCurve(shotSince, Math.max(1, shotLen));
  const drift = a.kind === "closeup" ? 0 : amp * 0.010;
  const sq = squash((hc - 0.68) * 0.012);
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
  const k0 = Math.min(MAX_K, shot?.k ?? 1);
  const kE = shot?.kEnd === undefined ? undefined : Math.min(MAX_K, shot.kEnd);
  const k = kE === undefined ? k0
    : k0 + (kE - k0) * Math.min(1, shotSince / shotLen);
  const w = w0 * k, h = h0 * k;
  const hx = left0 + hf.fx * w0, hy = top0 + hf.fy * h0;
  const left = (shot?.tx ?? hx) - hf.fx * w;
  const top = (shot?.ty ?? hy) - hf.fy * h;
  const src = holdMouth ? d.src : visemeSrc(pose, mouthState, speaking, frame);
  const panel = a.kind === "panel";
  // THE RIG. It renders the same artwork, so at rest it is pixel-identical
  // to the flat <Img> — the container keeps its own idle/hold/interact
  // transforms and the rig's internal breath stays OFF, or the two would
  // stack and double the motion. Channels only open when a shot asks.
  const rig = RIG[pose];
  const vk = holdMouth ? null : visemeKey(pose, mouthState, speaking, frame);
  // ALWAYS ON. Gating the rig behind an explicit request meant 37 of 39
  // beats rendered the flat drawing exactly as before, so the episode was
  // 194 of its 196 seconds unchanged and the work was invisible. A rig that
  // only runs where someone remembered to ask is not a rig.
  const rigged = Boolean(rig) && !RIG_OFF;
  const tt = frame / 30;
  // a per-character phase offset, so two people never breathe in unison
  const ph = (pose.charCodeAt(0) % 7) * 0.9;

  // ACTING IS DERIVED, NOT AUTHORED. Everything below comes from data the
  // beat already carries — who is speaking, who else is on screen, and where
  // they stand — so every beat acts without 39 hand-written entries.

  // Face whoever you are in the room with. The sign falls out of the
  // staging: turn toward their x, away from your own.
  const faceTurn = otherX !== undefined && a.kind === "full"
    ? (otherX < a.x ? -1 : 1) * (speaking ? 0.55 : 0.40)
    : 0;
  // Speaking works the head: it drops slightly into stressed syllables
  // (mouthState 2 is a wide vowel) over a slow drift, so it never ticks
  // like a metronome. Listening is slower and mostly lateral.
  // ACTIONS, NOT OSCILLATORS. The first two passes drove the head with sine
  // waves and measured 1.02x and 1.26x the motion of the flat render. A sine
  // never ARRIVES anywhere — it is perpetual drift, which the eye reads as
  // wobble rather than intent. This repo's own house style says it plainly
  // (CLAUDE.md 10.8): anticipation, then a fast arrival, then a HOLD.
  //
  // So the character fires a discrete action roughly once a second, chosen
  // from a small vocabulary, seeded off the pose and the beat so it is
  // deterministic, repeatable and different per character.
  // Segments are now STRESSES, not a timer. While the character speaks,
  // seg advances only when the voice hits a wide vowel; between stresses
  // everything holds. The listener rides the same clock at lower gain, so
  // reaction and delivery share one rhythm. Silence falls back to a slow
  // timer so nobody freezes solid between lines.
  const onStress = speaking && stressN > 0;
  const seg = onStress ? stressN : Math.floor(shotSince / 56);
  const local = onStress ? Math.min(stressSince, 999) : shotSince - seg * 56;
  const pick = (seg * 7 + pose.length * 3 + (speaking ? 0 : 5)) % 5;
  // wind up the OPPOSITE way first, then arrive fast with a little overshoot,
  // then sit still. The wind-up is the part everyone skips and the part that
  // most reads as animation.
  const env = (t: number) => {
    if (t < 4) return -0.28 * (t / 4);
    const u = Math.min(1, (t - 4) / 9);
    return u * (1 + 0.24 * Math.sin(Math.PI * u) * (1 - u));
  };
  const e = env(local);
  const toward = otherX !== undefined ? (otherX < a.x ? -1 : 1) : -1;

  // the vocabulary. Speaking gets the big shapes; listening gets the
  // reactions, which are smaller and slower but never nothing.
  const A = speaking
    ? [
        {tilt: 11 * toward, look: 0.10, turn: 0.62 * toward, point: 0.20, lean: 0.15},
        {tilt: -6 * toward, look: -0.55, turn: 0.20 * toward, point: 0.72, lean: 0.42},
        {tilt: 8, look: 0.42, turn: 0.10 * toward, point: 0.15, lean: -0.28},
        {tilt: -12 * toward, look: -0.30, turn: 0.48 * toward, point: 0.58, lean: 0.30},
        {tilt: 5 * toward, look: 0.05, turn: 0.70 * toward, point: 0.35, lean: 0.05},
      ][pick]
    : [
        {tilt: 7 * toward, look: -0.22, turn: 0.44 * toward, point: 0, lean: 0.10},
        {tilt: -9, look: 0.30, turn: 0.30 * toward, point: 0, lean: -0.18},
        {tilt: 4 * toward, look: -0.40, turn: 0.50 * toward, point: 0.10, lean: 0.06},
        {tilt: -5 * toward, look: 0.12, turn: 0.36 * toward, point: 0, lean: -0.10},
        {tilt: 10 * toward, look: -0.15, turn: 0.52 * toward, point: 0, lean: 0.14},
      ][pick];

  // the baseline the actions ride on: he is never completely still even
  // between actions
  const idleTilt = Math.sin(tt * 1.1 + ph) * 2.2;

  // THE CUT. This is the part a rig cannot do: the drawing itself changes.
  // Each variant is a real generated drawing with a different arm position -
  // an elbow that bends, a hand that opens - which no transform of a flat
  // cut-out can produce. Segment 0 always holds the approved base drawing so
  // a beat opens on-model, and the cut lands on the same frame as the
  // action's wind-up, so it reads as a decision rather than as a glitch.
  // A SWEEP, NOT A MONTAGE. The owner's word for the previous cut was
  // "montage", and that is what it was: independent drawings hard-cut with
  // holds, each pick unrelated to the last frame shown. Drawn animation is
  // smooth because it plays CONSECUTIVE drawings — the classic on-threes
  // cadence — and the variant list is already sorted by arm height, so
  // consecutive entries ARE consecutive arm positions.
  //
  // So the arm now rides a triangle wave over that ladder: one rung every 3
  // frames for 24 frames — a genuine sweep, low to high and back — then a
  // 14-frame hold at wherever it arrived. The step count accumulates across
  // segments, so a new segment CONTINUES the ladder from where the last one
  // stopped instead of teleporting; direction reverses only at the ladder's
  // ends. Deterministic, per-character offset, no state.
  const vars = rig?.variants ?? [];
  const NL = vars.length;
  const steps = seg * 8 + Math.min(8, Math.floor(local / 3)) + pose.length * 5;
  const M = Math.max(1, 2 * (NL - 1));
  const triw = ((steps % M) + M) % M;
  const rung = triw < NL ? triw : M - triw;
  const bodyPart = NL ? "body__" + vars[rung] : "body";
  // EXPRESSION. Arm variants do nothing for a bust, and the busts are most
  // of the episode - sol_smug_v1 alone is 12 of 39 beats and shows barely
  // any body. On a bust the only thing that can act is the face, so the
  // brows change with each action while the mouth stays viseme-driven.
  // Speakers get the open, assertive shapes; listeners get the narrow,
  // judging ones, which is what a reaction actually looks like.
  const exprs = rig?.expressions ?? [];
  const exprPool = speaking
    ? exprs.filter((e) => e !== "squint" && e !== "side_eye")
    : exprs.filter((e) => e !== "wide");
  const pool = exprPool.length ? exprPool : exprs;
  const exprPart = pool.length && seg > 0
    ? "expr__" + pool[(seg * 2 + pose.length) % pool.length]
    : undefined;

  // No smear. It existed to hide teleports between unrelated drawings; a
  // one-rung ladder step needs no hiding, and a constant smear on tiny
  // steps was itself part of the "montage" smell.
  const smear = 0;
  const nod = 0;
  const tilt = A.tilt * e + idleTilt;
  const gest = Math.max(0, A.point * e);
  const push = A.lean * e;
  const faceTurnActive = a.kind === "full" ? A.turn * e : 0;

  const rigPose: RigPose = {
    breath: 1,
    breathPhase: tt * 2.0 + ph,
    sway: Math.sin(tt * 0.72 + ph) * (speaking ? 1.5 : 2.0)
      + Math.sin(tt * 0.31 + ph) * 1.1,
    stride: shot?.walk ?? 0,
    walkPhase: tt * 6.6,
    turn: shot?.turn ?? faceTurnActive,
    pointAt: shot?.point ?? gest,
    lookUp: shot?.look ?? A.look * e,
    tilt,
    lean: (shot?.walk ?? 0) * 0.25 + push,
    gestureArm: "armL",
    headPart: vk ? "head__" + vk : "head",
    bodyPart,
    exprPart,
  };
  void beatLen; void faceTurn; void nod;
  // Sol moves like a veteran, Rex like an over-eager junior — derived
  // from who the drawing is, so no beat has to carry it.
  const ix = interactXform(since, a.moves, a.turns,
                           shot?.tx ?? hx, shot?.ty ?? hy, temper);
  return (
    <div style={{position: "absolute",
      left: left + idl.dx + drift * (hc - 0.68),
      top: top + idl.dy - drift * 0.35 * (hc - 0.68),
      width: w, height: h,
      transform: `translate(${ix.dx}px, ${ix.dy}px) `
        + `scale(${pop * ix.sx * idl.sx * sq.sx * (1 + smear * 0.16)}, `
        + `${pop * ix.sy * idl.sy * sq.sy * (1 - smear * 0.05)}) `
        + `rotate(${ix.rot + idl.rot + (panel ? -1.2 : 0)}deg)`,
      transformOrigin: a.kind === "full" ? `${d.anchor[0] * 100}% ${d.anchor[1] * 100}%` : "50% 60%",
      opacity: Math.min(1, since / 3) * ix.opacity,
      ...(ix.blur + smear * 2.6 > 0.05
        ? {filter: `blur(${ix.blur + smear * 2.6}px)`} : {}),
      ...(panel ? {border: "6px solid #111", borderRadius: 8, overflow: "hidden",
        boxShadow: "10px 12px 0 rgba(0,0,0,0.35)", background: "#F7F3E8"} : {})}}>
      {rigged
        ? <CharRig rig={rig!} pose={rigPose} />
        : <Img src={staticFile(src)} style={{position: "absolute", inset: 0, width: "100%", height: "100%"}} />}
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
      {/* The body used to hard-switch on at since>14, 34, 54 — so the card
          spent its first half-second as a title over an empty cream box,
          and a binary opacity flip made that read as a failed render
          rather than a reveal. Two independent reviewers called it a
          broken graphic on the frame that carries the episode's strongest
          line. The body now starts almost with the header and FADES,
          which is the difference between a card building and a card
          missing its content. */}
      {c.lines.map((ln, i) => (
        <div key={i} style={{fontSize: 31, fontWeight: 700, lineHeight: 1.36,
          opacity: Math.max(0, Math.min(1, (since - (4 + i * 10)) / 8)),
          transform: `translateY(${(1 - Math.max(0, Math.min(1,
            (since - (4 + i * 10)) / 8))) * 6}px)`}}>{ln}</div>
      ))}
      {c.big ? (
        <div style={{fontFamily: "Impact, Arial", fontSize: 104, textAlign: "center",
          margin: "2px 0 0", color: "#7A1F2B",
          opacity: Math.max(0, Math.min(1,
            (since - (8 + c.lines.length * 10)) / 9))}}>{c.big}</div>
      ) : null}
      {c.foot ? (
        <div style={{fontSize: 20, position: "absolute", left: 34, bottom: 18,
          color: "#555"}}>{c.foot}</div>
      ) : null}
    </div>
  );
};

// The monitor's IDLE state. The studio screen used to be conditionally
// rendered — present only on beats that had an exhibit — so for the
// first 13 seconds the room had a blank wall where a monitor should be,
// and the screen popped in and out at beat boundaries instead of being
// furniture. It is now always on, and when it has nothing specific to
// show it runs the thing the episode is ABOUT.
//
// That used to be a single scrolling polyline, which read as "a chart"
// and nothing more. The subject here is a TRACKER — a portfolio
// reconstructed from disclosures — so the screen behind the hosts now
// prints that tracker as candles: each bar is a period with a range, and
// the newest one is live, wandering inside its own high/low until it
// settles. See motion/Infographic.tsx (TickerTape) for the tape rules
// and for why the series is labelled ILLUSTRATIVE on its face.
// `bare` drops the tape's own header and price readout. The episode
// title sits over the monitor on the open and the outro, and two
// unrelated blocks of text stacked on each other read as a layout bug.
// (The review panel judged this cosmetic and refuted it 2-1; it is a
// two-line change that removes a real text-on-text stack, so it is in.)
const TVIdle: React.FC<{frame: number; bare?: boolean}> = ({frame, bare}) => (
  <TickerTape frame={frame} w={TV_SCREEN.w} h={TV_SCREEN.h} bare={bare}
    label="LAWMAKER TRADE TRACKER"
    sub="disclosed positions, rebuilt from filings" />
);

// A caricature playing on the monitor. Contained by the screen, so she
// is always "footage the show is running" rather than a figure standing
// impossibly in the room next to the cast.
// TVPose (ep.1's keyed caricature insert) is unused here: episode 2
// puts footage on the monitor via Shot.tvPhoto instead.


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

export const FairMarketEp5: React.FC = () => {
  const frame = useCurrentFrame();
  const {cur, since, hold} = beatAt(frame);
  const outro = cur.at === 1685;
  const nrg = cur.energy ?? 0.7;
  const k = kick(since, 10 * nrg, 14);
  const sub2 = cur.vo2 && since >= (cur.at2 ?? 0);
  const ms = mouthStateFor(cur, frame);
  const activeSpeaker = sub2 ? cur.speaker2 : cur.speaker;
  const stress = stressFor(cur, frame);
  const {shot, shotSince, shotLen} = shotAt(cur.shots, since, hold);

  return (
    <AbsoluteFill style={{background: "#101828", overflow: "hidden"}}>
      {BEATS.map((b) => (
        <React.Fragment key={b.at}>
          {b.vo ? (
            <Sequence from={b.at + VO_DELAY} durationInFrames={320}>
              <Audio src={staticFile(`audio/fairmarket_ep5/${b.vo}.wav`)} />
            </Sequence>
          ) : null}
          {b.vo2 ? (
            <Sequence from={b.at + (b.at2 ?? 0) + VO_DELAY} durationInFrames={120}>
              <Audio src={staticFile(`audio/fairmarket_ep5/${b.vo2}.wav`)} />
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
        {/* The monitor is FURNITURE — always in the room, never popping in
            and out at beat boundaries, and it fills the upper frame that
            was otherwise dead wall above the cast. */}
        <TVFrame glow={(!!cur.card || !!cur.graphic || !!shot?.tvPhoto)
          && !shot?.hideCard} />
        <div style={{position: "absolute", left: TV_SCREEN.x, top: TV_SCREEN.y,
          width: TV_SCREEN.w, height: TV_SCREEN.h, overflow: "hidden",
          borderRadius: 4}}>
          {/* `hideCard` was a declared-but-never-read field. It is wired
              now, and it is what lets a beat push in close on a character
              WITHOUT hiding its own evidence: the exhibit is explicitly
              stood down for that shot and the monitor falls back to the
              tape, rather than a head silently covering the graphic the
              line is about. */}
          {shot?.hideCard ? <TVIdle frame={frame} bare={!!cur.title} />
            : shot?.tvPhoto ? (
              <div style={{position: "absolute", inset: 0, overflow: "hidden",
                background: "#0B1220"}}>
                <Img src={staticFile(`characters/cast_ep1/ep2/${shot.tvPhoto}.png`)}
                  style={{position: "absolute", width: "100%", height: "auto",
                    left: 0, top: `${-6 - Math.min(1, shotSince / 150) * 5}%`,
                    opacity: Math.min(1, shotSince / 10)}} />
              </div>
            ) : cur.graphic === "split_price" ? (
              <SplitPriceExhibit since={since} w={TV_SCREEN.w} h={TV_SCREEN.h}
                title="WHAT AN OPTION&#39;S PRICE IS MADE OF"
                foot="a mechanism, not a ticker · educational, not advice" />
            ) : cur.graphic === "decay_buyer" ? (
              <DecayExhibit since={since} w={TV_SCREEN.w} h={TV_SCREEN.h}
                side="buyer" title="WHAT THE CLOCK DOES TO IT"
                foot="same-day expiry · the decay is the schedule · educational, not advice" />
            ) : cur.graphic === "decay_seller" ? (
              <DecayExhibit since={since} w={TV_SCREEN.w} h={TV_SCREEN.h}
                side="seller" title="THE OTHER SIDE OF THE SAME CURVE"
                foot="a statement about market structure, not anybody’s conduct · not advice" />
            ) : cur.graphic === "share_0dte" ? (
              <ColumnsExhibit since={since} w={TV_SCREEN.w} h={TV_SCREEN.h}
                title="WHO IS IN THESE TRADES"
                cols={[{label: "of retail index-option trades: same-day",
                        sub: "~3/4", frac: 0.75},
                       {label: "of same-day volume: retail",
                        sub: "~1/2", frac: 0.5, tone: "red"}]}
                foot="shares as reported, approximate · educational, not advice" />
            ) : cur.card ? <ExhibitCard c={cur.card} since={since} />
            : <TVIdle frame={frame} bare={!!cur.title} />}
        </div>
        <TVGlass />
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
          const visible = cur.actors
            .map((o, j) => ({o, j}))
            .filter(({j}) => (shot?.show ? shot.show.includes(j)
              : shot?.only === undefined || shot.only === j));
          const other = visible.find(({j}) => j !== i)?.o;
          return <Char key={i} a={a} since={since} frame={frame} speaking={speaking}
                       mouthState={isSol ? ms.sol : ms.rex}
                       shot={shot} shotSince={shotSince} shotLen={shotLen}
                       otherX={other?.x} beatLen={hold}
                       stressN={stress.n} stressSince={stress.since}
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
      {/* The flash is punctuation, so it has to be RARE. It fired on every
          beat's frame 0 — the flash selling "WHAT?!" was identical to the
          one on a flat aside, which trains the eye to ignore it. Gated on
          the same signal the speed lines and shock ring already use. */}
      {(cur.fx ?? !!cur.shout) ? <FlashCut since={since} /> : null}
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
