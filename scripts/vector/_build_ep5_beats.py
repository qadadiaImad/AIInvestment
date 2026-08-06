"""One-shot: splice the authored EP5 beat array into FairMarketEp5.tsx.
File-based for the same reason as EP4: heredocs mangle quoted edits."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
P = REPO / "remotion/src/compositions/FairMarketEp5.tsx"

BEATS = r'''const BEATS: Beat[] = [
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
];'''

s = P.read_text("utf-8")
i = s.index("const BEATS: Beat[] = [")
j = s.index("\n];", i) + len("\n];")
s = s[:i] + BEATS + s[j:]
P.write_text(s, "utf-8")
print("EP5: 29 beats spliced")
