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
import {ExhibitPlate} from "../motion/ExhibitPlate";
import {FLOOR_Y, NewsBand, PANEL_FLOOR, Room, RoundDesk, SEATS, WALL, WallFrame, H as STAGE_H} from "../motion/Set";
import {BigNumberExhibit, TickerTape} from "../motion/Infographic";
import {SeriesExhibit} from "../motion/Series";
import {MachineParts, MachineLoop} from "../motion/Machine";
import anchors from "../fixtures/cast_ep1/pose_anchors.json";
import mouthTracks from "../fixtures/cast_ep1/mouth_tracks_bubbles.json";
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
const RIG_OFF = true;    // OWNER CALL 2026-08-06: the rig acting (drawing
// swaps, arm sweeps, turns, head accents) read as ugly extra body movement.
// Reverted to the approved flat viseme rendering - breathing, holds, mouth
// and blinks stay; the acting system stays in the code, dormant, should it
// ever be wanted again.

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

export const BUBBLES_FRAMES = 5083;   // 169s

// Hard ceiling on how far a shot may push in. A drawing scaled until the
// face fills the frame throws away the set and has nowhere left to go —
// owner rule, after a static full-zoom face-only frame. Any reframe is
// clamped so the room stays readable behind the character.
const MAX_K = 1.9;

// ---------------------------------------------------------------- FRAMING
// The staging was authored phone-first, where sitting close to the desk
// reads as intimate. On a YouTube page the same framing reads as crowded:
// the cast fills the frame and the studio around them disappears.
//
// Two independent dials, deliberately separate because they fix different
// halves of that complaint:
//
//   CAM_PULL  scales how far each authored push-in travels. The camera
//             still moves exactly where the beat says, it just moves less
//             far. 1.0 is the original; 0.45 turns a 1.30x push into 1.135.
//             It cannot usefully go below 1.0 at rest - the room is drawn
//             to fill the frame exactly, so zooming past that reveals the
//             canvas edge.
//   CAST      scales every actor's staged height. Feet stay planted on
//             FLOOR_Y, so the figures shrink downward into the set instead
//             of floating, and the wall above them gains room.
const CAM_PULL = 0.45;
const CAST = 0.88;
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
  graphic?: "fedfunds" | "caseshiller" | "drawdown2008" | "unrate"
    | "dotcom" | "wealth" | "machine_parts" | "machine_loop";
  // A generated caricature plate on the wall (motion/ExhibitPlate), same
  // contract as ep.1.
  exhibit?: string;
  // Force the live candlestick tape back onto the wall. A beat with no
  // wall content of its own HOLDS the exhibit it is reacting to instead
  // of cutting back to the tape — 19 of ep.2's 32 beats used to fall
  // through to it. Exactly one beat carries `wall: "chart"`: the one
  // where the market moving before the news IS the line.
  wall?: "chart";
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
  {at: 0,
   exhibit: "b_machine",
   actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b01_sol_bubble", speaker: "SOL",
   line: "Kid... let me show you how a bubble gets built."},

  {at: 131,
   actors: [{poses: ["rex_skeptic"], kind: "full", x: 298, y: FLOOR_Y, h: 1000},
            {poses: ["sol_finger"], kind: "full", x: 834, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b02_rex_bath", speaker: "REX",
   line: "Boss! Bubbles - like bath bubbles? Should I bring the duck?"},

  {at: 286,
   sfx: [{at: 81, name: "faah", vol: 0.28}],
   actors: [{poses: ["sol_smug_v1"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b03_sol_rent", speaker: "SOL",
   line: "Not that kind. This kind takes your RENT."},

  {at: 399,
   actors: [{poses: ["sol_finger"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b04_sol_lehman", speaker: "SOL",
   line: "September 2008. Lehman Brothers files for bankruptcy."},

  {at: 530,
   sfx: [{at: 0, name: "vine_boom_hit", vol: 0.26}],
   actors: [{poses: ["rex_shock"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b05_rex_what", speaker: "REX",
   line: "The whole BANK?!"},

  {at: 607,
   graphic: "machine_parts",
   actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b06_sol_notcause", speaker: "SOL",
   line: "The whole bank. And it wasn't even the cause."},

  {at: 730,
   exhibit: "b_empty_chair",
   actors: [{poses: ["rex_eager"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b07_rex_name", speaker: "REX",
   line: "Then who's the villain? Give me a name, boss."},

  {at: 858,
   actors: [{poses: ["sol_smug_v1"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b08_sol_aname", speaker: "SOL",
   line: "A name?"},

  {at: 907,
   sfx: [{at: 105, name: "core", vol: 0.3}],
   actors: [{poses: ["sol_finger"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b09_sol_nomame", speaker: "SOL",
   line: "There isn't one. Just a machine. Four moving parts."},

  {at: 1036,
   graphic: "fedfunds",
   actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b11_sol_cheap", speaker: "SOL",
   line: "It starts when money gets cheap. ...Stupid cheap."},

  {at: 1151,
   actors: [{poses: ["rex_listen"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b10_rex_discount", speaker: "REX",
   line: "Cheap like a discount?"},

  {at: 1215,
   actors: [{poses: ["sol_finger"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b12_sol_onepercent", speaker: "SOL",
   line: "Fed funds fell under ONE percent."},

  {at: 1302,
   actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b13_sol_months", speaker: "SOL",
   line: "Under one and a half... for TWENTY-TWO months."},

  {at: 1417,
   actors: [{poses: ["rex_eager"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b14_rex_free", speaker: "REX",
   line: "Twenty-two months of free money?!"},

  {at: 1494,
   exhibit: "b_corkboard",
   actors: [{poses: ["sol_finger"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b15_sol_parttwo", speaker: "SOL",
   line: "Cheap money needs a STORY. Something to excuse the price."},

  {at: 1632,
   actors: [{poses: ["rex_skeptic"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b16_rex_true", speaker: "REX",
   line: "In '08 the story was - houses always go up. That's just TRUE."},

  {at: 1812,
   graphic: "caseshiller",
   actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b17_sol_only", speaker: "SOL",
   line: "True. Until it's the only reason anyone gives for the price."},

  {at: 1959,
   actors: [{poses: ["rex_eager"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b18_rex_excuse", speaker: "REX",
   line: "So it's not a reason. It's an EXCUSE."},

  {at: 2072,
   actors: [{poses: ["sol_smug_v1"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b19_sol_learning", speaker: "SOL",
   line: "Excuse? ...Now you're learning, kid."},

  {at: 2152,
   exhibit: "b_block_tower",
   actors: [{poses: ["sol_finger"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b20_sol_partthree", speaker: "SOL",
   line: "Then somebody borrows against the story."},

  {at: 2245,
   actors: [{poses: ["rex_eager"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b21_rex_crowbar", speaker: "REX",
   line: "Leverage - like a crowbar? More leverage means more power, right?"},

  {at: 2401,
   actors: [{poses: ["sol_finger"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b22_sol_youcontrol", speaker: "SOL",
   line: "Crowbar? ...With one, YOU control the wobble."},

  {at: 2511,
   sfx: [{at: 73, name: "whoosh_fire", vol: 0.3}],
   actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b23_sol_controlsyou", speaker: "SOL",
   line: "Borrowed money... the wobble controls YOU."},

  {at: 2602,
   exhibit: "b_falling_card",
   actors: [{poses: ["sol_finger"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b24_sol_partfour", speaker: "SOL",
   line: "And sooner or later... somebody HAS to sell."},

  {at: 2714,
   actors: [{poses: ["rex_skeptic"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b25_rex_margin", speaker: "REX",
   line: "Forced? Like a margin call?"},

  {at: 2792,
   graphic: "machine_loop",
   actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b26_sol_forced", speaker: "SOL",
   line: "Forced. The lender wants cash you don't have."},

  {at: 2908,
   exhibit: "b_cracked_facade",
   actors: [{poses: ["rex_eager"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b27_rex_banks", speaker: "REX",
   line: "Okay - so the BANKS. They're the villain. They went first."},

  {at: 3057,
   actors: [{poses: ["sol_smug_v1"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b28_sol_no", speaker: "SOL",
   line: "No."},

  {at: 3105,
   actors: [{poses: ["sol_finger"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b29_sol_bottomblock", speaker: "SOL",
   line: "That's the tower losing its bottom block."},

  {at: 3204,
   exhibit: "b_conveyor",
   actors: [{poses: ["rex_listen"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b30_rex_whostacked", speaker: "REX",
   line: "Then who stacked it?"},

  {at: 3276,
   actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b31_sol_broker", speaker: "SOL",
   line: "The broker. The bank. The buyer who believed the story."},

  {at: 3415,
   actors: [{poses: ["rex_skeptic"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b32_rex_nobody", speaker: "REX",
   line: "So nobody's responsible?"},

  {at: 3484,
   graphic: "machine_parts",
   sfx: [{at: 86, name: "core", vol: 0.33}],
   actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b33_sol_everyone", speaker: "SOL",
   line: "Everyone's responsible. Nobody's the villain."},

  {at: 3586,
   graphic: "caseshiller",
   actors: [{poses: ["sol_finger"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b34_sol_houses", speaker: "SOL",
   line: "House prices fell TWENTY-SEVEN percent."},

  {at: 3695,
   actors: [{poses: ["rex_eager"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b35_rex_quarter", speaker: "REX",
   line: "Just over a quarter of a house."},

  {at: 3792,
   graphic: "drawdown2008",
   actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b36_sol_market", speaker: "SOL",
   line: "The market fell FIFTY-FIVE percent."},

  {at: 3872,
   actors: [{poses: ["rex_skeptic"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b37_rex_half", speaker: "REX",
   line: "...Half."},

  {at: 3921,
   graphic: "unrate",
   actors: [{poses: ["sol_finger"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b38_sol_jobs", speaker: "SOL",
   line: "Unemployment. Four point four... to TEN."},

  {at: 4018,
   graphic: "wealth",
   sfx: [{at: 71, name: "core_tiktok", vol: 0.3}],
   actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b39_sol_trillion", speaker: "SOL",
   line: "Eleven and a half TRILLION. Gone."},

  {at: 4108,
   exhibit: "b_two_machines",
   actors: [{poses: ["rex_eager"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b42_rex_once", speaker: "REX",
   line: "Okay but - that's the big one. That's ONCE."},

  {at: 4236,
   actors: [{poses: ["sol_smug_v1"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b43_sol_once", speaker: "SOL",
   line: "Once?"},

  {at: 4285,
   actors: [{poses: ["sol_finger"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b44_sol_runback", speaker: "SOL",
   line: "Run it back eight years."},

  {at: 4371,
   actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b45_sol_internet", speaker: "SOL",
   line: "Same four parts. Different story. This time... the internet."},

  {at: 4511,
   graphic: "dotcom",
   actors: [{poses: ["sol_finger"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b46_sol_seventyseven", speaker: "SOL",
   line: "Dot-com fell SEVENTY-SEVEN percent."},

  {at: 4599,
   sfx: [{at: 0, name: "vine_boom_hit", vol: 0.26}],
   actors: [{poses: ["rex_shock"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b47_rex_what2", speaker: "REX",
   line: "WHAT?!"},

  {at: 4647,
   actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b48_sol_backtoeven", speaker: "SOL",
   line: "Took until twenty-fifteen to get back to even."},

  {at: 4764,
   actors: [{poses: ["rex_eager"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b49_rex_fifteen", speaker: "REX",
   line: "Fifteen years?!"},

  {at: 4817,
   actors: [{poses: ["sol_finger"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b50_sol_fifteen", speaker: "SOL",
   line: "Fifteen years, kid."},

  {at: 4889,
   exhibit: "b_machine_lit",
   actors: [{poses: ["rex_skeptic"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "b51_rex_notmoney", speaker: "REX",
   line: "So the bubble didn't cost you money?"},

  {at: 4983,
   sfx: [{at: 84, name: "whoosh", vol: 0.27}],
   actors: [{poses: ["sol_smug_v1"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12}],
   vo: "b52_sol_time", speaker: "SOL",
   line: "No. It cost you TIME."},
];

// Frame, relative to a beat's start, at which its exhibit becomes visible.
// A beat may open on an archive photo (`tvPhoto`) and cut to its exhibit.
const exhibitFromOf = (b: Beat) =>
  (b.shots ?? []).find((s) => !s.tvPhoto && !s.hideCard)?.from ?? 0;

// What the wall shows on a beat that sets no wall content of its own: the
// exhibit it is REACTING to, still up, rather than a cut back to the tape.
// Hold only an image plate — the code-drawn graphics and the text cards
// animate off their own beat clock and cannot be held past it.
type Held =
  | {kind: "exhibit"; name: string; start: number}
  | {kind: "graphic"; name: string; start: number};

// Holds GRAPHICS as well as exhibits - see scripts/bubbles/patch_hold.py
// for why the exhibit-only version was a bug.
const heldAt = (i: number): Held | null => {
  for (let k = i; k >= 0; k--) {
    const b = BEATS[k];
    if (b.exhibit)
      return {kind: "exhibit", name: b.exhibit, start: b.at + exhibitFromOf(b)};
    if (b.graphic)
      return {kind: "graphic", name: b.graphic, start: b.at};
    if (b.wall === "chart" || b.card || b.title) return null;
  }
  return null;
};

const beatAt = (f: number) => {
  let i = 0;
  for (let k = 0; k < BEATS.length; k++) if (f >= BEATS[k].at) i = k;
  const cur = BEATS[i];
  const next = BEATS[i + 1];
  return {cur, idx: i, since: f - cur.at,
    hold: (next ? next.at : BUBBLES_FRAMES) - cur.at};
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
  const amp = a.kind === "closeup" ? STAGE_H * 0.5 : a.h * CAST;
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
  // CAST pulls every staged height at one point, so the beats keep their
  // authored relative sizes (Rex taller than Sol, busts bigger than fulls)
  // and only the overall occupancy of the frame changes.
  const ah = a.h * CAST;
  const scale = a.kind === "full" ? ah / d.ink_h
    : a.kind === "closeup"
    // cover the frame: no canvas edge can fall inside it. 1.04 pads the
    // boil/bob/pop jitter so a wobble can't reveal a corner.
    ? 1.04 * Math.max(W / d.w, H / d.h)
    : ah / d.h;
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
  <TickerTape frame={frame} w={WALL.w} h={WALL.h} bare={bare}
    label="LAWMAKER TRADE TRACKER"
    sub="disclosed positions, rebuilt from filings" />
);

// A caricature playing on the monitor. Contained by the screen, so she
// is always "footage the show is running" rather than a figure standing
// impossibly in the room next to the cast.
// TVPose (ep.1's keyed caricature insert) is unused here: episode 2
// puts footage on the monitor via Shot.tvPhoto instead.


const Subtitle: React.FC<{speaker: string; line: string}> = ({speaker, line}) => (
  <>
    {/* SCRIM. The desk's rim is a curve, so it crosses the caption
        zone at the wings no matter where the text sits. */}
    <div style={{position: "absolute", left: 0, right: 0, bottom: 150,
      height: 300, pointerEvents: "none",
      background: "linear-gradient(180deg, rgba(6,10,18,0) 0%,"
        + " rgba(6,10,18,0.55) 34%, rgba(6,10,18,0.72) 70%,"
        + " rgba(6,10,18,0.55) 100%)"}} />
  <div style={{position: "absolute", left: 60, right: 60, bottom: 196, textAlign: "center"}}>
    <div style={{fontFamily: "Impact, Arial", fontSize: 30, letterSpacing: 2,
      color: speaker === "SOL" ? "#E8A54B" : "#FF8A50", marginBottom: 6,
      textShadow: "2px 2px 0 #000"}}>{speaker}</div>
    <div style={{fontFamily: "Arial", fontWeight: 800, fontSize: 44, lineHeight: 1.3,
      color: "white",
      textShadow: "3px 3px 0 #000, -3px 3px 0 #000, 3px -3px 0 #000, -3px -3px 0 #000, 0 4px 8px rgba(0,0,0,0.8)"}}>
      {line}
    </div>
  </div>
  </>
);

export const Bubbles: React.FC = () => {
  const frame = useCurrentFrame();
  const {cur, idx, since, hold} = beatAt(frame);
  // What the wall is showing: the beat's own exhibit, or the one it is
  // reacting to, held. `wall: "chart"` opts back into the tape.
  const held = cur.wall === "chart" ? null : heldAt(idx);
  const wallEx = cur.exhibit
    ? {name: cur.exhibit, start: cur.at + exhibitFromOf(cur)}
    : held && held.kind === "exhibit" ? held : null;
  // the graphic actually on the wall, and the clock it runs on
  const gName = cur.graphic
    ?? (held && held.kind === "graphic" ? held.name : undefined);
  const gSince = cur.graphic ? since
    : held && held.kind === "graphic" ? frame - held.start : 0;
  const outro = cur.at === 1685;
  const nrg = cur.energy ?? 0.7;
  const k = kick(since, 10 * nrg, 14);
  const sub2 = cur.vo2 && since >= (cur.at2 ?? 0);
  const ms = mouthStateFor(cur, frame);
  const activeSpeaker = sub2 ? cur.speaker2 : cur.speaker;
  const stress = stressFor(cur, frame);
  const {shot, shotSince, shotLen} = shotAt(cur.shots, since, hold);
  // scene-camera values: the authored punch-ins become lens moves
  // centred on the active speaker's seat
  const pull = (k: number) => 1 + (Math.min(1.3, k) - 1) * CAM_PULL;
  const camK0 = pull(shot?.k ?? 1);
  const camK1 = shot?.kEnd === undefined ? camK0 : pull(shot.kEnd);
  const camK = camK0 + (camK1 - camK0)
    * Math.min(1, shotSince / Math.max(1, shotLen));
  const camSeat = SEATS[(sub2 ? cur.speaker2 : cur.speaker) === "SOL"
    ? "sol" : "rex"];
  const camX = shot?.tx ?? camSeat.x;
  const camY = Math.min(1420, shot?.ty ?? 1240);

  return (
    <AbsoluteFill style={{background: "#101828", overflow: "hidden"}}>
      {BEATS.map((b) => (
        <React.Fragment key={b.at}>
          {b.vo ? (
            <Sequence from={b.at + VO_DELAY} durationInFrames={320}>
              <Audio src={staticFile(`audio/fairmarket_bubbles/${b.vo}.wav`)} />
            </Sequence>
          ) : null}
          {b.vo2 ? (
            <Sequence from={b.at + (b.at2 ?? 0) + VO_DELAY} durationInFrames={120}>
              <Audio src={staticFile(`audio/fairmarket_bubbles/${b.vo2}.wav`)} />
            </Sequence>
          ) : null}
          {/* 320, not 22. A <Sequence> TRUNCATES its audio, and 22 frames is
              0.73s — which silently chopped every sting longer than that.
              riser_suspense is 10.08s and the stingmap asks for it as "a low
              bed across the line"; it was being cut to a seventh of a second.
              riser_metallic (2.76s) and whoosh (0.98s) were cut too. A
              generous window costs nothing: <Audio> stops when the file ends,
              so the sound plays its natural length and no further. */}
          {(b.sfx ?? []).map((s, i) => (
            <Sequence key={`s${i}`} from={b.at + s.at} durationInFrames={320}>
              <Audio src={staticFile(`audio/${s.name}.wav`)} volume={s.vol ?? 0.5} />
            </Sequence>
          ))}
        </React.Fragment>
      ))}
      {/* THE SCENE CAMERA. The panel holds still and the LENS does the
          work, like a match-analysis broadcast: the per-beat k/kEnd
          that used to punch into one drawing now zooms the whole
          studio about the speaker's seat, desk and wall included. */}
      <div style={{position: "absolute", inset: 0,
        transform: `translate(${k.x}px, ${k.y * 0.4}px) `
          + `scale(${(1 + 0.03 * Math.max(0, 1 - since / 10) * nrg) * camK})`,
        transformOrigin: `${camX}px ${camY}px`}}>
        <Room dark={shot?.mood === "dark"} />
        {/* the painted studio plate over the flat room: generated anime
            background (provenance beside the file), cover-fit and dimmed so
            the drawn wall, cast and table sit ON it */}
        <Img src={staticFile("characters/cast_ep1/studio_bg.png")}
          style={{position: "absolute", inset: 0, width: "100%",
            height: "100%", objectFit: "cover",
            opacity: shot?.mood === "dark" ? 0.35 : 0.55,
            filter: "saturate(0.9) brightness(0.75)"}} />
        {/* The monitor is FURNITURE — always in the room, never popping in
            and out at beat boundaries, and it fills the upper frame that
            was otherwise dead wall above the cast. */}
        {/* Beat-scoped, so the halo cannot blink off at a mid-beat cut. */}
        <WallFrame glow={(!!cur.card || !!cur.graphic
          || (cur.shots ?? []).some((s) => !!s.tvPhoto)) && !shot?.hideCard} />
        <div style={{position: "absolute", left: WALL.x, top: WALL.y,
          width: WALL.w, height: WALL.h, overflow: "hidden",
          borderRadius: 6,
          // `hideCard` STANDS THE WALL DOWN; it does not swap it for the
          // tape. Cutting to the candlestick idle on a tight push-in was
          // the largest remaining source of chart repetition in ep.1 and
          // ep.2 has eight of these shots. Dimming yields the frame to the
          // close-up while keeping the beat's own content up.
          opacity: shot?.hideCard ? 0.34 : 1}}>
          {shot?.tvPhoto ? (
              <div style={{position: "absolute", inset: 0, overflow: "hidden",
                background: "#0B1220"}}>
                <Img src={staticFile(`characters/cast_ep1/ep2/${shot.tvPhoto}.png`)}
                  style={{position: "absolute", width: "100%", height: "auto",
                    left: 0, top: `${-6 - Math.min(1, shotSince / 150) * 5}%`,
                    opacity: Math.min(1, shotSince / 10)}} />
              </div>
            ) : wallEx ? (
              /* `callout` only on the beat that authored the exhibit — a
                 held plate must not re-fire the previous beat's ring. */
              <ExhibitPlate name={wallEx.name} since={frame - wallEx.start}
                w={WALL.w} h={WALL.h}
                dir={(wallEx.start / 90) % 2 < 1 ? 1 : -1} />
            ) : gName === "machine_parts" ? (
              <MachineParts since={gSince} w={WALL.w} h={WALL.h} />
            ) : gName === "machine_loop" ? (
              <MachineLoop since={gSince} w={WALL.w} h={WALL.h} />
            ) : gName === "wealth" ? (
              <BigNumberExhibit since={gSince} w={WALL.w} h={WALL.h}
                kicker="HOUSEHOLD NET WORTH LOST" value="$11.5 TRILLION"
                caption="peak 2007 Q3 to trough 2009 Q1, a fall of 16.3%"
                foot="Federal Reserve Z.1, households and nonprofits - FRED TNWBSHNO" />
            ) : gName ? (
              <SeriesExhibit name={gName as never}
                since={gSince} w={WALL.w} h={WALL.h} />
            ) : cur.card ? <ExhibitCard c={cur.card} since={since} />
            : <TVIdle frame={frame} bare={!!cur.title} />}
        </div>
        <div style={{position: "absolute", left: WALL.x, top: WALL.y,
          width: WALL.w, height: WALL.h, pointerEvents: "none",
          background: "linear-gradient(118deg, rgba(255,255,255,0.08) 0%,"
            + " rgba(255,255,255,0.02) 26%, rgba(255,255,255,0) 46%)",
          boxShadow: "inset 0 0 90px rgba(0,0,0,0.5)"}} />
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
          // THE PANEL. Seats are fixed per character - a desk show's
          // talent does not wander - and the beat's authored staging is
          // overridden wholesale. The table, drawn over the actors,
          // hides everything below the chest, which is what makes a
          // standing drawing read as seated.
          const seat = SEATS[isSol ? "sol" : "rex"];
          const aSeat = {...a, kind: "full" as const, x: seat.x,
                         y: PANEL_FLOOR, h: seat.h, moves: undefined,
                         turns: undefined};
          // the CAMERA zooms, the characters do not
          const shotSeat = shot ? {...shot, k: 1, kEnd: undefined,
                                   tx: undefined, ty: undefined} : shot;
          return <Char key={i} a={aSeat} since={since} frame={frame} speaking={speaking}
                       mouthState={isSol ? ms.sol : ms.rex}
                       shot={shotSeat} shotSince={shotSince} shotLen={shotLen}
                       otherX={other?.x} beatLen={hold}
                       stressN={stress.n} stressSince={stress.since}
                       holdMouth={cur.holdMouth} />;
        })}
        <RoundDesk dark={shot?.mood === "dark"} />
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
        <div style={{position: "absolute", left: 0, right: 0, bottom: 6, textAlign: "center",
          fontFamily: "Arial", fontSize: 20, color: "#6C7FA6"}}>
          parody · public record · educational, not advice
        </div>
      )}
      <NewsBand frame={frame} dark={shot?.mood === "dark"} />
      <Vignette strength={0.28} />
      <Grain opacity={0.03} />
    </AbsoluteFill>
  );
};
