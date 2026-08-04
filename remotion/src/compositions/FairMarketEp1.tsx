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
import {CounterExhibit, PerformanceExhibit, TickerTape,
        TimelineExhibit} from "../motion/Infographic";
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

export const FAIRMARKET_FRAMES = 4290;

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
  graphic?: "timeline_nvidia" | "counter_45days" | "perf_2024" | "lag_cost";
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
  // ═══ ACT 1 — THE CLAIM ═══════════════════════════════════════════════
  {at: 0, title: ["MARKET LESSONS", "WITH SOL", "ep.1 — the 'fair' market"],
   actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 660, y: 1170, h: 1010}],
   shots: [{from: 0, k: 1.0, kEnd: 1.05},
           {from: 62, k: 1.34, kEnd: 1.48, tx: 540, ty: 1080}],
   vo: "v1_sol_intro", speaker: "SOL",
   line: "Kid… let me tell you about the so-called “fair” market."},

  // Rex says "Boss!" — so there has to be a boss to say it TO. Every
  // standing figure plants on FLOOR_Y, and Rex is the TALLER of the two:
  // he is the young one, Sol is a short round old man. These pair heights
  // are scripts/vector/overlap_audit.py output, not eyeballed.
  {at: 120, actors: [{poses: ["rex_eager"], kind: "full", x: 327, y: FLOOR_Y, h: 717,
                      turns: [{at: 10, tx: 860, ty: 1180}]},
                     {poses: ["sol_point_v1"], kind: "full", x: 831, y: FLOOR_Y, h: 629}],
   shots: [{from: 0, k: 1.0, kEnd: 1.14}],
   sfx: [{at: 14, name: "sfx_whip", vol: 0.42}],
   vo: "v2_rex_fundamentals", speaker: "REX",
   line: "Boss! It's all fundamentals, right?!", energy: 1},

  // Sol is laughing AT someone, so keep that someone in frame. Matched by
  // HEAD size rather than body height (scripts/vector/head_scale.py) —
  // rex_skeptic's proportions match Sol's, and "arms crossed, not
  // convinced" is the right read for being laughed at anyway.
  {at: 211, actors: [{poses: ["sol_laugh"], kind: "full", x: 814, y: FLOOR_Y, h: 622},
                     {poses: ["rex_skeptic"], kind: "full", x: 309, y: FLOOR_Y, h: 710,
                      turns: [{at: 14, tx: -260, ty: 1650}]}],
   shots: [{from: 0, k: 1.0, kEnd: 1.12}],
   sfx: [{at: 18, name: "sfx_whip", vol: 0.38}],
   vo: "v3_sol_ha", speaker: "SOL", line: "HA! …Fundamentals.", energy: 1.1},

  // EYELINE. rex_listen is drawn in profile facing RIGHT, so Rex stands
  // screen-LEFT for his gaze to land on Sol, who slides in from the right
  // to join him rather than simply being there on the cut.
  {at: 276, actors: [{poses: ["rex_listen"], kind: "full", x: 236, y: FLOOR_Y, h: 659},
                     {poses: ["sol_finger"], kind: "full", x: 840, y: FLOOR_Y, h: 578,
                      moves: [{at: 0, kind: "inR"}]}],
   shots: [{from: 0, k: 1.0, kEnd: 1.06},
           {from: 32, only: 1, k: 1.42, kEnd: 1.56, tx: 560, ty: 900}],
   sfx: [{at: 4, name: "sfx_whoosh", vol: 0.45}],
   vo: "v4_sol_politics", speaker: "SOL", line: "Sometimes… it trades on POLITICS."},

  // THE TAKE — and it stays IN THE ROOM, at a size where the room is
  // actually visible. First pass at this fix only went from "covers
  // 1080x1920" to "900px of head" — still a face filling the frame, just
  // a slightly smaller one. At 900px staged, Rex's whole figure sits
  // BELOW the monitor's lower edge, so the set, the tracker and the
  // parody footer are all readable behind the scream.
  // The original defect: this was a cover-framed closeup —
  // the drawing scaled until it covered 1080x1920, which threw the set
  // away and left a face filling the screen with nowhere to go. Owner
  // ruling, twice: never a full-zoomed face-only frame. Rex is now a
  // grounded full figure at 1080px — a medium shot. Even at the top of
  // the push the room and the top two thirds of the monitor stay visible
  // behind him, so the take reads as a boy reacting IN a place.
  {at: 369, actors: [{poses: ["rex_shock"], kind: "full", x: 520, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, k: 1.0, kEnd: 1.10}],
   // The scream lasts 27 frames and the take holds 55, so the mouth would
   // fall back to "closed" mid-shout without this.
   holdMouth: true, fx: true,
   sfx: [{at: 6, name: "impact", vol: 0.55}],
   vo: "v5_rex_what", speaker: "REX", line: "WHAT?!", energy: 1.5},

  // ═══ ACT 2 — THE EVIDENCE ════════════════════════════════════════════
  // The exhibit is a DRAWN timeline, not a paragraph: the rail draws, both
  // events land, a bracket measures the gap between them and the share
  // count runs up. The gap IS the point, and no paragraph makes you feel
  // a gap. It needs ~70 frames to build, so the exhibit shot holds 80.
  //
  // Everyone on an exhibit beat is staged SHORT (<=930) so no head reaches
  // above the monitor's lower edge at y=736. Nothing may hide the
  // evidence — same rule as nothing may hide the other character.
  // Verified by scripts/vector/exhibit_clearance.py.
  {at: 416, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930},
                     {poses: ["rex_skeptic"], kind: "bust", x: 470, y: 1250, h: 880}],
   graphic: "timeline_nvidia",
   shots: [{from: 0, only: 0, k: 1.0, kEnd: 1.07},
           {from: 86, only: 0, k: 1.34, kEnd: 1.44, tx: 560, ty: 1180, hideCard: true},
           {from: 150, only: 0, mood: "dark", tvPose: "congress_scheme",
            k: 1.0, kEnd: 1.1},
           {from: 232, only: 1, k: 1.0, kEnd: 1.1, hideCard: true}],
   vo: "v6_sol_exhibit", speaker: "SOL",
   line: "July 2022. The Speaker's household sold NVIDIA — days before the chip subsidies passed. At a loss, kid."},

  // ═══ ACT 3 — THE LEADERBOARD (new) ═══════════════════════════════════
  // Rex used to blurt "They made it an INDEX?!" out of nowhere — he
  // announced a fact he had no way of knowing, which is narration
  // captioning itself. This act is the ramp that EARNS that reaction:
  // one filing -> people track these portfolios like a leaderboard ->
  // here are the ones they watch -> somebody wrapped it in a fund.
  {at: 666, actors: [{poses: ["rex_skeptic"], kind: "full", x: 298, y: FLOOR_Y, h: 681,
                      turns: [{at: 12, tx: 860, ty: 1200}]},
                     {poses: ["sol_finger"], kind: "full", x: 834, y: FLOOR_Y, h: 597}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08},
           {from: 52, only: 0, k: 1.36, kEnd: 1.48, tx: 520, ty: 1010}],
   vo: "a3_rex_onetrade", speaker: "REX",
   line: "One trade. One person. That's a coincidence, boss, not a strategy."},

  {at: 822, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1120, h: 1040}],
   shots: [{from: 0, k: 1.0, kEnd: 1.09},
           {from: 60, k: 1.2, kEnd: 1.34, tx: 540, ty: 1010}],
   vo: "a3_sol_leaderboard", speaker: "SOL",
   line: "One? People track these disclosures like a leaderboard."},

  // THE TAPE IS THE POINT of this beat, so Sol is staged clear of it and
  // the monitor runs its default state: candles printing, the newest one
  // live and wandering inside its own range. See motion/Infographic.tsx.
  {at: 940, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.06},
           {from: 92, k: 1.16, kEnd: 1.26, tx: 620, ty: 1180}],
   vo: "a3_sol_portfolios", speaker: "SOL",
   line: "Whole portfolios. Filing by filing. Year by year."},

  // The lawmaker archetype returns — the same figure from the July 2022
  // exhibit, so she reads as a character in the story rather than a
  // one-off cutaway. She plays ON THE MONITOR: archive footage the show
  // is running, never a figure standing impossibly in the room.
  {at: 1084, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, mood: "dark", tvPose: "congress_scheme", k: 1.0, kEnd: 1.08},
           // kEnd was 1.34, which pushed Sol 28px over the monitor at the
           // top of the creep — measured by scripts/vector/stage_audit.py,
           // not eyeballed. Nothing may hide the evidence.
           {from: 96, mood: "dark", tvPose: "congress_scheme",
            k: 1.22, kEnd: 1.26, tx: 600, ty: 1200}],
   vo: "a3_sol_speaker", speaker: "SOL",
   line: "The Speaker's household. Technology, mostly. Big positions, disclosed late."},

  // THE SECOND ARCHETYPE, and the reason the line is worded the way it is.
  // Periodic-transaction reporting under the STOCK Act is a CONGRESSIONAL
  // mechanism, and a president is not a member of Congress — so with both
  // caricatures in play the script says "politicians whose trades people
  // track", never "congress investors". Caricature, no on-screen name, no
  // accusation; the footer carries the parody / public-record rail.
  {at: 1258, actors: [{poses: ["sol_finger"], kind: "full", x: 760, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, mood: "dark", tvPose: "congress2_scheme", k: 1.0, kEnd: 1.07},
           {from: 104, mood: "dark", tvPose: "congress2_scheme",
            k: 1.2, kEnd: 1.32, tx: 600, ty: 1210}],
   vo: "a3_sol_others", speaker: "SOL",
   line: "And it's not one person, or one party. Other politicians get tracked exactly the same way."},

  {at: 1444, actors: [{poses: ["rex_shock"], kind: "full", x: 500, y: FLOOR_Y, h: 880}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   holdMouth: true, fx: true,
   sfx: [{at: 6, name: "impact", vol: 0.5}],
   vo: "a3_rex_score", speaker: "REX", line: "Somebody's keeping score? Like a fantasy league?", energy: 1.4},

  // THE NUMBER, on the beat that claims it. Sol says the trackers
  // reported those portfolios beating the market — so the monitor shows
  // exactly that, sourced and dated, instead of leaving the viewer to
  // take his word for it. Staged short (930) so nothing covers it, and
  // the push holds off until the bars have finished racing.
  {at: 1552, actors: [{poses: ["sol_point_v1"], kind: "full", x: 745, y: FLOOR_Y, h: 930}],
   graphic: "perf_2024",
   shots: [{from: 0, k: 1.0, kEnd: 1.06},
           {from: 108, k: 1.18, kEnd: 1.3, tx: 600, ty: 1190, hideCard: true}],
   vo: "a3_sol_beating", speaker: "SOL",
   line: "Some years, the trackers reported those portfolios beating the market. That's why people watch."},

  {at: 1731, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1120, h: 1040}],
   shots: [{from: 0, k: 1.12, kEnd: 1.28, tx: 540, ty: 1030}],
   vo: "a3_sol_obvious", speaker: "SOL", line: "And then somebody did the obvious thing."},

  // ...which is what Rex is now reacting TO, instead of announcing.
  {at: 1812, actors: [{poses: ["rex_eager"], kind: "full", x: 560, y: FLOOR_Y, h: 930}],
   card: {title: "FEB 2023 · IT BECAME A PRODUCT",
          lines: ["An ETF now copies Democratic lawmakers'",
                  "disclosed trades. Actively managed."],
          big: "NANC", foot: "public filings in · portfolio out"},
   shots: [{from: 0, k: 1.0, kEnd: 1.1}],
   fx: true,
   sfx: [{at: 6, name: "impact", vol: 0.5}],
   vo: "v7_rex_index", speaker: "REX", line: "They made it an INDEX?!",
   energy: 1.3},

  {at: 1879, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, mood: "dark", tvPose: "congress2_smug", k: 1.0, kEnd: 1.08},
           {from: 88, k: 1.18, kEnd: 1.3, tx: 600, ty: 1200}],
   vo: "v11_sol_bothsides", speaker: "SOL",
   line: "And it's not one party, kid. There's a fund that copies the other side too."},

  {at: 2030, actors: [{poses: ["rex_skeptic"], kind: "full", x: 500, y: FLOOR_Y, h: 1120}],
   shots: [{from: 0, k: 1.08, kEnd: 1.2, tx: 540, ty: 1060}],
   vo: "v12_rex_both", speaker: "REX", line: "Both sides have one? Okay — who's winning?",
   energy: 1.2},

  // What a filing actually contains — the mechanics, not a restatement of
  // the line. A range, not an amount; a date, not a price; filed weeks
  // later. This is the fact that makes act four's failure inevitable.
  {at: 2130, actors: [{poses: ["sol_point_v1"], kind: "full", x: 745, y: FLOOR_Y, h: 930},
                      {poses: ["rex_skeptic"], kind: "bust", x: 400, y: 1250, h: 860}],
   card: {title: "WHAT THE FILING ACTUALLY SAYS",
          lines: ["A range, not an amount.",
                  "A date, not a price.",
                  "Filed up to 45 days later."],
          foot: "STOCK Act periodic transaction report"},
   shots: [{from: 0, only: 0, k: 1.0, kEnd: 1.07},
           {from: 104, only: 0, k: 1.24, kEnd: 1.36, tx: 600, ty: 1190, hideCard: true},
           {from: 158, only: 1, k: 1.0, kEnd: 1.1, hideCard: true}],
   vo: "v8_sol_legal", speaker: "SOL",
   line: "All disclosed. In ranges. Up to 45 days late. All legal."},

  // ═══ ACT 4 — REX ACTS ON IT, AND IS WRONG ════════════════════════════
  // This is where the glint-eyed rex_eager drawing gets an honest job:
  // Rex is genuinely excited exactly once, right here, and wears the
  // ordinary-eyed rex_skeptic / rex_listen through the rest of the act.
  // The owner's note about the eyes, answered by the writing.
  {at: 2296, actors: [{poses: ["rex_eager"], kind: "full", x: 312, y: FLOOR_Y, h: 679},
                      {poses: ["sol_smug_v1"], kind: "bust", x: 812, y: 1290, h: 596}],
   shots: [{from: 0, k: 1.0, kEnd: 1.07},
           {from: 54, only: 0, k: 1.42, kEnd: 1.56, tx: 520, ty: 1040}],
   vo: "a2_rex_copy", speaker: "REX",
   line: "Then I'll just copy them! Buy what they buy!", energy: 1.3},

  {at: 2403, actors: [{poses: ["sol_finger"], kind: "full", x: 834, y: FLOOR_Y, h: 597},
                      {poses: ["rex_skeptic"], kind: "full", x: 298, y: FLOOR_Y, h: 681}],
   shots: [{from: 0, k: 1.0, kEnd: 1.06},
           {from: 46, only: 0, k: 1.38, kEnd: 1.52, tx: 560, ty: 990}],
   vo: "a2_sol_sixweeks", speaker: "SOL",
   line: "Copy them. With a filing from six weeks ago?"},

  // Staged at 1180 with a 1.26 push this was the biggest Rex in the
  // episode by a wide margin, and rex_skeptic is the most realistically
  // -proportioned drawing in the set — at that size the proportion gap
  // stops reading as "closer" and starts reading as a different
  // character. Sized to match his other solos instead.
  {at: 2508, actors: [{poses: ["rex_skeptic"], kind: "full", x: 470, y: FLOOR_Y, h: 960}],
   shots: [{from: 0, k: 1.06, kEnd: 1.16, tx: 540, ty: 1120}],
   vo: "a2_rex_six", speaker: "REX", line: "Six weeks?"},

  {at: 2558, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930},
                      {poses: ["rex_skeptic"], kind: "bust", x: 430, y: 1250, h: 880}],
   graphic: "counter_45days",
   shots: [{from: 0, only: 0, k: 1.0, kEnd: 1.07},
           {from: 92, only: 0, k: 1.3, kEnd: 1.42, tx: 560, ty: 1190, hideCard: true},
           {from: 162, only: 1, k: 1.0, kEnd: 1.12, hideCard: true}],
   vo: "a2_sol_edge", speaker: "SOL",
   line: "The trade is public. The edge is not. By the time you read it, the move already happened."},

  // ═══ THE HOLE IN THE ARGUMENT, CLOSED ════════════════════════════════
  // Sol shows Rex a fund that copies disclosed trades, then demolishes
  // Rex for proposing to copy disclosed trades. A viewer catches that
  // instantly and until now nothing answered it — the episode's one real
  // logical gap, sitting on its own hinge.
  //
  // Rex gets to catch him, which is also the only time in the episode the
  // junior wins a point. Sol concedes rather than squashing him, and the
  // concession happens to be the most interesting fact in the piece.
  {at: 2745, actors: [{poses: ["rex_skeptic"], kind: "full", x: 298, y: FLOOR_Y, h: 681,
                       turns: [{at: 10, tx: 860, ty: 1200}]},
                      {poses: ["sol_finger"], kind: "full", x: 834, y: FLOOR_Y, h: 597}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08},
           {from: 60, only: 0, k: 1.34, kEnd: 1.46, tx: 520, ty: 1010}],
   sfx: [{at: 12, name: "sfx_whip", vol: 0.4}],
   vo: "a4_rex_butthefund", speaker: "REX",
   line: "Hold on. Then how does the fund work? It's reading the same late filings I am."},

  {at: 2904, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1180, h: 880}],
   // pulled back: a 1040px bust at k=1.16 is a face filling the frame,
   // which is the one framing the owner has ruled out twice
   shots: [{from: 0, k: 1.0, kEnd: 1.08, tx: 540, ty: 1200}],
   vo: "a4_sol_lagcost", speaker: "SOL",
   line: "It is. Same forty-five days, same paperwork. And look what the delay costs."},

  // THE NUMBER THAT MAKES THE POINT. Three bars: the disclosed portfolio,
  // the fund copying it 45 days late, and the index. The lag eats about
  // two thirds of the edge — which is the honest answer, and a better one
  // than either "copying works" or "copying is useless".
  {at: 3075, actors: [{poses: ["sol_point_v1"], kind: "full", x: 745, y: FLOOR_Y, h: 930}],
   graphic: "lag_cost",
   shots: [{from: 0, k: 1.0, kEnd: 1.06},
           {from: 130, k: 1.16, kEnd: 1.28, tx: 600, ty: 1190, hideCard: true}],
   vo: "a4_sol_survives", speaker: "SOL",
   line: "Seventy-one percent on the disclosed portfolio. Twenty-seven for the fund copying it late. The market did twenty-five."},

  {at: 3306, actors: [{poses: ["sol_finger"], kind: "full", x: 800, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, k: 1.08, kEnd: 1.2, tx: 580, ty: 1180}],
   vo: "a4_sol_thin", speaker: "SOL",
   line: "So the edge does survive the wait, kid. Most of it doesn't."},

  {at: 3430, actors: [{poses: ["rex_listen"], kind: "full", x: 400, y: FLOOR_Y, h: 820}],
   shots: [{from: 0, k: 1.06, kEnd: 1.16, tx: 520, ty: 1250}],
   vo: "a2_rex_useless", speaker: "REX", line: "So the filings are useless."},

  // Sol's reframe — and then he's gone, which is what makes his answer on
  // the next-but-one beat an answer from somewhere he wasn't.
  {at: 3504, actors: [{poses: ["sol_finger"], kind: "full", x: 840, y: FLOOR_Y, h: 578,
                       moves: [{at: 140, kind: "vanish"}]},
                      {poses: ["rex_listen"], kind: "full", x: 236, y: FLOOR_Y, h: 659}],
   shots: [{from: 0, k: 1.0, kEnd: 1.06},
           {from: 58, only: 0, k: 1.44, kEnd: 1.58, tx: 560, ty: 980}],
   sfx: [{at: 140, name: "sfx_poof", vol: 0.5}],
   vo: "a2_sol_map", speaker: "SOL",
   line: "No. They're a map of attention. Who is watching what, and when."},

  // ═══ ACT 5 — THE PAYOFF ══════════════════════════════════════════════
  // Rex asks the empty room. Nobody is there to answer, which is the
  // setup for the pop-in.
  {at: 3651, actors: [{poses: ["rex_listen"], kind: "full", x: 400, y: FLOOR_Y, h: 800,
                       turns: [{at: 16, tx: 900, ty: 1250}]}],
   shots: [{from: 0, k: 1.04, kEnd: 1.14, tx: 520, ty: 1260}],
   vo: "a5_rex_dowhat", speaker: "REX", line: "So what do I actually do with it? Asking for me."},

  // ...and Sol answers from behind the desk, where he was not a moment
  // ago. The one piece of ACTIONABLE method in the episode, and the only
  // place it belongs: after Rex has been wrong once and asked for it.
  {at: 3762, actors: [{poses: ["rex_skeptic"], kind: "full", x: 312, y: FLOOR_Y, h: 679,
                       turns: [{at: 20, tx: 830, ty: 1230}]},
                      {poses: ["sol_smug_v1"], kind: "bust", x: 812, y: 1300, h: 596,
                       moves: [{at: 14, kind: "pop"}]}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08},
           {from: 74, only: 1, k: 1.3, kEnd: 1.42, tx: 560, ty: 1080}],
   flicks: [{at: 21, x: 560, y: 1130}],
   sfx: [{at: 14, name: "sfx_pop", vol: 0.6},
         {at: 24, name: "sfx_whip", vol: 0.42}],
   vo: "a5_sol_homework", speaker: "SOL",
   line: "Watch what they sit near. Committees. Hearings. Then do your own homework."},

  {at: 3921, actors: [{poses: ["rex_eager"], kind: "full", x: 312, y: FLOOR_Y, h: 679},
                      {poses: ["sol_smug_v1"], kind: "bust", x: 812, y: 1300, h: 596}],
   shots: [{from: 0, only: 0, k: 1.2, kEnd: 1.32, tx: 520, ty: 1000},
           {from: 62, k: 1.0, kEnd: 1.08}],
   vo: "v9_rex_filings", speaker: "REX", line: "So — read the filings!",
   vo2: "v10_sol_learning", speaker2: "SOL", line2: "Now you're learning, kid.", at2: 62},

  // THE THESIS, CLOSED. The cold open promised to explain the "fair"
  // market and the 60-second cut never came back to the word. Sol answers
  // it to camera, and the answer is the honest one: not fair — legible.
  {at: 4042, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1120, h: 1040}],
   shots: [{from: 0, k: 1.06, kEnd: 1.2, tx: 540, ty: 1040}],
   vo: "a5_sol_fair", speaker: "SOL", line: "Fair? No. But now you can read it."},

  {at: 4134, title: ["MARKET LESSONS", "WITH SOL", ""], actors: []},
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
        + `scale(${pop * ix.sx * idl.sx * sq.sx}, ${pop * ix.sy * idl.sy * sq.sy}) `
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
const TVPose: React.FC<{pose: string; since: number}> = ({pose, since}) => {
  const d = AN[pose];
  if (!d) return null;
  // Framed like an interview insert, not a full-length portrait.
  //
  // Scaling by HEIGHT (the old `TV_SCREEN.h * 1.85 / d.h`) sizes a
  // portrait-shaped drawing by its long axis, so on an 864x486 screen it
  // came out 611px wide and sat in 250px of black bars — a small dark
  // picture inside a large dark rectangle, which is exactly the "she
  // appears and disappears too quickly to register" complaint in visual
  // form. Scale by WIDTH so she fills the screen edge to edge, and take
  // the crop off the BOTTOM: the head and hands are the performance, the
  // legs were never in the shot anyway.
  const s = (TV_SCREEN.w * 0.92) / d.w;
  const w = d.w * s, h = d.h * s;
  const rise = Math.min(1, since / 12);
  // slow drift down over the hold, so a 5-second insert is never a still
  const drift = Math.min(1, since / 150) * 24;
  // Anchor the crop on the FACE (about 29% down these busts) rather than
  // on the top edge. Pinning the top cut the chin off the taller of the
  // two drawings, which reads as a framing mistake rather than a choice.
  return (
    <div style={{position: "absolute", inset: 0, overflow: "hidden",
      background: "linear-gradient(180deg,#1B2438 0%,#0E1422 100%)"}}>
      <Img src={staticFile(d.src)}
        style={{position: "absolute", width: w, height: h,
          left: TV_SCREEN.w / 2 - w / 2,
          top: TV_SCREEN.h / 2 - h * 0.29 - drift + (1 - rise) * 30,
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
  const outro = cur.at === 1685;
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
        {/* The monitor is FURNITURE — always in the room, never popping in
            and out at beat boundaries, and it fills the upper frame that
            was otherwise dead wall above the cast. */}
        <TVFrame glow={(!!cur.card || !!shot?.tvPose) && !shot?.hideCard} />
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
            : shot?.tvPose ? <TVPose pose={shot.tvPose} since={shotSince} />
            : cur.graphic === "timeline_nvidia" ? (
              <TimelineExhibit since={since} w={TV_SCREEN.w} h={TV_SCREEN.h}
                title="JULY 2022 · PUBLIC FILING"
                left={{date: "JUL 2022", label: "household sells\n25,000 NVIDIA shares"}}
                right={{date: "AUG 2022", label: "Congress passes\nchip subsidies"}}
                gapLabel="DAYS APART"
                counter={{to: 25000, label: "shares disclosed"}}
                foot="STOCK Act disclosure · widely reported" />
            ) : cur.graphic === "perf_2024" ? (
              <PerformanceExhibit since={since} w={TV_SCREEN.w} h={TV_SCREEN.h}
                title="REPORTED RETURN" year="2024"
                rows={[{label: "A TRACKED LAWMAKER HOUSEHOLD", pct: 70.9, tone: "red"},
                       {label: "S&P 500", pct: 24.9, tone: "blue"}]}
                foot="as reported by Unusual Whales' 2024 congressional trading report - disclosed trades, public record" />
            ) : cur.graphic === "lag_cost" ? (
              <PerformanceExhibit since={since} w={TV_SCREEN.w} h={TV_SCREEN.h}
                title="WHAT THE 45-DAY LAG COSTS" year="2024"
                rows={[{label: "THE DISCLOSED PORTFOLIO", pct: 70.9, tone: "red"},
                       {label: "A FUND COPYING IT, 45 DAYS LATE", pct: 26.8, tone: "grey"},
                       {label: "S&P 500", pct: 24.9, tone: "blue"}]}
                foot="portfolio: Unusual Whales 2024 report - fund: NANC 2024 total return - the edge survives the delay, most of it does not" />
            ) : cur.graphic === "counter_45days" ? (
              <CounterExhibit since={since} w={TV_SCREEN.w} h={TV_SCREEN.h}
                title="WHY COPYING FAILS" to={45} unit="days"
                caption="The reporting window can run this long. By the time a trade is public, the move already happened."
                foot="STOCK Act reporting window" />
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
