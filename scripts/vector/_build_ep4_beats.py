"""One-shot: splice the authored EP4 beat array into FairMarketEp4.tsx.

Written as a file rather than a heredoc on purpose: this session has now
twice had a shell heredoc silently mangle a quoted edit (the v8 no-op, and
the first attempt at this splice). A file written by the editor tool has no
quoting layer to fight.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
P = REPO / "remotion/src/compositions/FairMarketEp4.tsx"

BEATS = r'''const BEATS: Beat[] = [
  // ═══ COLD OPEN — Rex owns this one ═══════════════════════════════════
  // He does not observe this story; he BOUGHT it. The episode is him
  // learning that a licence is not a sale, which is the only reason a
  // policy explainer holds two minutes.
  {at: 0, title: ["MARKET LESSONS", "WITH SOL", "ep.4 — ninety-five to nothing"],
   actors: [{poses: ["rex_eager"], kind: "full", x: 312, y: FLOOR_Y, h: 679,
             turns: [{at: 10, tx: 840, ty: 1210}]},
            {poses: ["sol_smug_v1"], kind: "bust", x: 812, y: 1300, h: 596}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08},
           {from: 60, only: 0, k: 1.28, kEnd: 1.4, tx: 520, ty: 1020}],
   sfx: [{at: 10, name: "sfx_whip", vol: 0.45}],
   vo: "f1_rex_bought", speaker: "REX",
   line: "Boss! I bought the chip story.", energy: 1.3},

  {at: 110, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1180, h: 880}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08, tx: 540, ty: 1200}],
   vo: "f2_sol_which", speaker: "SOL", line: "Which chip story."},

  {at: 190, actors: [{poses: ["rex_eager"], kind: "full", x: 500, y: FLOOR_Y, h: 900}],
   graphic: "lic_10b",
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "f3_rex_approved", speaker: "REX",
   line: "Export licences came through. Ten billion dollars' worth. Approved!",
   energy: 1.2},

  {at: 360, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.02, kEnd: 1.12, tx: 580, ty: 1190}],
   vo: "f4_sol_shipped", speaker: "SOL", line: "Approved. And how much shipped?"},

  // ═══ ACT 1 — the gap ═════════════════════════════════════════════════
  {at: 500, actors: [{poses: ["rex_skeptic"], kind: "full", x: 470, y: FLOOR_Y, h: 960}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12, tx: 540, ty: 1120}],
   vo: "f5_rex_saysapproved", speaker: "REX", line: "...it says approved."},

  {at: 610, actors: [{poses: ["sol_finger"], kind: "full", x: 800, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, k: 1.02, kEnd: 1.12, tx: 580, ty: 1190}],
   vo: "f6_sol_asked", speaker: "SOL",
   line: "I know what it says. I asked what shipped."},

  {at: 760, actors: [{poses: ["rex_listen"], kind: "full", x: 400, y: FLOOR_Y, h: 820}],
   shots: [{from: 0, k: 1.06, kEnd: 1.14, tx: 520, ty: 1250}],
   vo: "f7_rex_veryfew", speaker: "REX", line: "\"Very few.\""},

  // The category words are the accuracy rail: approved, shipped, booked.
  {at: 860, actors: [{poses: ["sol_point_v1"], kind: "full", x: 745, y: FLOOR_Y, h: 930}],
   graphic: "gap_bars",
   shots: [{from: 0, k: 1.0, kEnd: 1.07},
           {from: 130, k: 1.14, kEnd: 1.24, tx: 600, ty: 1190, hideCard: true}],
   vo: "f8_sol_commerce", speaker: "SOL",
   line: "Those are the Commerce Department's words to Congress, kid. Very few."},

  {at: 1060, actors: [{poses: ["rex_skeptic"], kind: "full", x: 470, y: FLOOR_Y, h: 960}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12, tx: 540, ty: 1120}],
   vo: "f9_rex_notsale", speaker: "REX", line: "So the licence isn't the sale."},

  {at: 1180, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "f10_sol_permission", speaker: "SOL",
   line: "The licence is permission. Permission is not a customer."},

  // ═══ ACT 2 — what it used to be ══════════════════════════════════════
  {at: 1350, actors: [{poses: ["sol_point_v1"], kind: "full", x: 745, y: FLOOR_Y, h: 930}],
   graphic: "collapse_95",
   shots: [{from: 0, k: 1.0, kEnd: 1.07}],
   sfx: [{at: 20, name: "impact", vol: 0.4}],
   vo: "f11_sol_95", speaker: "SOL",
   line: "Two years ago they had about ninety-five percent of that market."},

  {at: 1550, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1215, h: 830}],
   graphic: "collapse_95",
   shots: [{from: 0, k: 1.0, kEnd: 1.06, tx: 540, ty: 1210}],
   vo: "f12_sol_17b", speaker: "SOL", line: "Seventeen billion in revenue from it."},

  {at: 1680, actors: [{poses: ["rex_listen"], kind: "full", x: 400, y: FLOOR_Y, h: 820}],
   shots: [{from: 0, k: 1.06, kEnd: 1.14, tx: 520, ty: 1250}],
   vo: "f13_rex_andnow", speaker: "REX", line: "And now?"},

  {at: 1760, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   graphic: "collapse_95",
   shots: [{from: 0, k: 1.0, kEnd: 1.07},
           {from: 120, k: 1.14, kEnd: 1.24, tx: 600, ty: 1190, hideCard: true}],
   vo: "f14_sol_foreclosed", speaker: "SOL",
   line: "Their own filing says they're effectively foreclosed from it."},

  {at: 1950, actors: [{poses: ["rex_skeptic"], kind: "full", x: 470, y: FLOOR_Y, h: 960}],
   shots: [{from: 0, k: 1.04, kEnd: 1.12, tx: 540, ty: 1120}],
   vo: "f15_rex_ownfiling", speaker: "REX", line: "Their own filing?"},

  {at: 2060, actors: [{poses: ["sol_finger"], kind: "full", x: 800, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, k: 1.02, kEnd: 1.12, tx: 580, ty: 1190}],
   vo: "f16_sol_inwriting", speaker: "SOL",
   line: "That's the part people skip. The company told you. In writing."},

  // ═══ ACT 3 — where it went ═══════════════════════════════════════════
  {at: 2240, actors: [{poses: ["rex_eager"], kind: "full", x: 500, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, k: 1.02, kEnd: 1.1}],
   vo: "f17_rex_waiting", speaker: "REX",
   line: "So the customers are waiting for the licences."},

  {at: 2380, actors: [{poses: ["sol_point_v1"], kind: "full", x: 745, y: FLOOR_Y, h: 930}],
   graphic: "collapse_95",
   shots: [{from: 0, k: 1.0, kEnd: 1.07},
           {from: 130, k: 1.14, kEnd: 1.24, tx: 600, ty: 1190, hideCard: true}],
   vo: "f18_sol_elsewhere", speaker: "SOL",
   line: "The customers went and bought somewhere else while everyone waited."},

  {at: 2580, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   shots: [{from: 0, k: 1.0, kEnd: 1.08}],
   vo: "f19_sol_yearofmaybe", speaker: "SOL",
   line: "A year of \"maybe\" is long enough to build a supply chain that doesn't need you."},

  {at: 2780, actors: [{poses: ["rex_listen"], kind: "full", x: 400, y: FLOOR_Y, h: 820}],
   shots: [{from: 0, k: 1.06, kEnd: 1.14, tx: 520, ty: 1250}],
   vo: "f20_rex_whenlicences", speaker: "REX", line: "And when the licences come?"},

  {at: 2890, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1180, h: 880}],
   shots: [{from: 0, k: 1.02, kEnd: 1.1, tx: 540, ty: 1200}],
   vo: "f21_sol_comesback", speaker: "SOL",
   line: "The permission comes back. The customer doesn't. Not automatically."},

  // ═══ ACT 4 — the lesson ══════════════════════════════════════════════
  {at: 3080, actors: [{poses: ["rex_eager"], kind: "full", x: 500, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, k: 1.02, kEnd: 1.1}],
   vo: "f22_rex_readright", speaker: "REX",
   line: "I read the headline right, though. It did say approved.", energy: 1.1},

  {at: 3240, actors: [{poses: ["sol_finger"], kind: "full", x: 800, y: FLOOR_Y, h: 900}],
   shots: [{from: 0, k: 1.02, kEnd: 1.12, tx: 580, ty: 1190}],
   vo: "f23_sol_wrongnoun", speaker: "SOL",
   line: "You read it right. You just read the wrong noun."},

  // THE EPISODE IN ONE GRAPHIC. Three words, three columns, three numbers.
  {at: 3400, actors: [{poses: ["sol_point"], kind: "full", x: 790, y: FLOOR_Y, h: 930}],
   graphic: "three_nouns",
   shots: [{from: 0, k: 1.0, kEnd: 1.06}],
   vo: "f24_sol_threewords", speaker: "SOL",
   line: "Approved is a government word. Shipped is a business word. Booked is an accountant's word."},

  {at: 3640, actors: [{poses: ["rex_listen"], kind: "full", x: 400, y: FLOOR_Y, h: 820}],
   graphic: "three_nouns",
   shots: [{from: 0, k: 1.06, kEnd: 1.14, tx: 520, ty: 1250}],
   vo: "f25_rex_notsame", speaker: "REX", line: "They're not the same number."},

  {at: 3760, actors: [{poses: ["sol_point_v1"], kind: "full", x: 745, y: FLOOR_Y, h: 930},
                      {poses: ["rex_skeptic"], kind: "bust", x: 420, y: 1250, h: 850}],
   graphic: "three_nouns",
   shots: [{from: 0, only: 0, k: 1.0, kEnd: 1.06},
           {from: 140, only: 1, k: 1.0, kEnd: 1.08, hideCard: true}],
   vo: "f26_sol_nevergap", speaker: "SOL",
   line: "They're never the same number. That gap is where the money is made and lost."},

  {at: 3980, actors: [{poses: ["sol_smug_v1"], kind: "bust", x: 560, y: 1180, h: 880}],
   shots: [{from: 0, k: 1.0, kEnd: 1.12, tx: 540, ty: 1200}],
   vo: "f27_sol_fair", speaker: "SOL",
   line: "Fair? No. But now you know which noun to look for."},

  {at: 4110, title: ["MARKET LESSONS", "WITH SOL", ""], actors: []},
];'''

s = P.read_text("utf-8")
i = s.index("const BEATS: Beat[] = [")
j = s.index("\n];", i) + len("\n];")
s = s[:i] + BEATS + s[j:]
P.write_text(s, "utf-8")
print("EP4: 28 beats spliced")
