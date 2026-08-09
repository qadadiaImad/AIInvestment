"""Generate the Bubbles composition by adapting the shipped ep.2 one.

WHY ADAPT RATHER THAN AUTHOR. FairMarketEp2.tsx is ~1000 lines and almost
all of it is machinery that took this repo weeks to get right: the viseme
mouth tracks, the interact/idle acting, the hold-the-previous-exhibit wall
chain, the beat-scoped wall glow, the CAM_PULL/CAST framing, the panel
staging audit's assumptions. Retyping that for a third episode would be
re-earning bugs already paid for. Only the BEATS array and the graphics
menu are genuinely new, so only those are replaced.

The episode is NOT written over FairMarketEp3.tsx. That slot holds the
congressional-ban-vote episode - a different subject with its own recorded
VO on disk - and its script being rejected is not a reason to destroy it.
This ships as its own composition, titled "ep.3" on screen.

Beat timings here are ESTIMATES from word count. That is fine and expected:
retime_beats.py derives every start from the measured audio afterwards and
lands on exact total frames. Never hand-tune these.

  python scripts/bubbles/build_composition.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "remotion/src/compositions/FairMarketEp2.tsx"
DST = REPO / "remotion/src/compositions/Bubbles.tsx"

FPS = 30
WPS = 2.75          # measured delivery pace of the shipped episodes
GAP = 14            # frames of air between beats
LEAD = 6            # VO_DELAY already accounts for the rest

# speaker -> staging. Single-speaker beats dominate; the two-shots are
# placed by hand below where the beat is a genuine exchange.
SOLO = {
    "SOL": '[{poses: ["%s"], kind: "full", x: 790, y: FLOOR_Y, h: 930}]',
    "REX": '[{poses: ["%s"], kind: "full", x: 330, y: FLOOR_Y, h: 1000}]',
}
TWO = ('[{poses: ["rex_skeptic"], kind: "full", x: 298, y: FLOOR_Y, h: 1000},\n'
       '            {poses: ["sol_finger"], kind: "full", x: 834, y: FLOOR_Y, h: 900}]')

SOL_POSE = ["sol_point", "sol_finger", "sol_point_v1", "sol_smug_v1"]
REX_POSE = ["rex_eager", "rex_skeptic", "rex_listen", "rex_shock"]

# (speaker, vo, line, wall_kind, wall_value, pose_hint, two_shot)
#   wall_kind: E=exhibit  G=graphic  H=hold (no key emitted)
B = [
 ("SOL","b01_sol_machine","Kid... before we do 2008, I want to show you the machine.","E","b_machine",0,0),
 ("REX","b02_rex_what","The machine?! I thought we were doing the housing crash - the banks, ALL of it!","H","",0,1),
 ("SOL","b03_sol_running","We are. The housing crash is just this thing running one more time.","H","",1,0),
 ("REX","b04_rex_name","So who breaks it? Give me a name - I'll write it down.","E","b_empty_chair",1,0),
 ("SOL","b05_sol_four","HA! ...Nobody breaks it alone. Four parts run it. Every time.","G","machine_parts",3,0),
 ("SOL","b06_sol_cheap","Part one. Money gets cheap.","G","fedfunds",0,0),
 ("REX","b07_rex_onsale","Cheap like... on sale?","H","",2,0),
 ("SOL","b08_sol_loan","Cheap like the loan that cost you a lot now costs you a little.","H","",1,0),
 ("SOL","b09_sol_months","It sat under one and a half percent for twenty-two months.","H","",0,0),
 ("SOL","b10_sol_story","Part two. A story shows up that explains why the price makes sense.","E","b_corkboard",1,0),
 ("REX","b11_rex_true","In '08 the story was - houses always go up. That's just true, isn't it?","H","",1,0),
 ("SOL","b12_sol_only","It was true. Right up until it was the only reason anyone gave for the price.","G","caseshiller",0,0),
 ("SOL","b13_sol_leverage","Part three. Leverage. Borrowed money, stacked on borrowed money.","E","b_block_tower",1,0),
 ("REX","b14_rex_crowbar","Leverage, like a crowbar? More leverage means more power - that's GOOD, right?","H","",0,0),
 ("SOL","b15_sol_wobble","More leverage means a small wobble at the bottom becomes a collapse at the top.","H","",1,0),
 ("SOL","b16_sol_sell","Part four. Someone has to sell.","E","b_falling_card",0,0),
 ("REX","b17_rex_margin","Forced? Like margin calls?","H","",1,0),
 ("SOL","b18_sol_borrow","Borrow to buy. The price drops.","H","",1,0),
 ("SOL","b19_sol_cash","The lender wants cash you haven't got - so you sell into a falling market.","G","machine_loop",0,0),
 ("SOL","b20_sol_loop","That closes the loop. Now watch it run.","H","",1,0),
 ("REX","b21_rex_banks","Finally. So - the investment banks. That's the villain. They went first.","E","b_cracked_facade",0,0),
 ("SOL","b22_sol_no","No.","H","",3,0),
 ("SOL","b23_sol_tower","That's the tower losing its bottom block. Not the hand that built it.","H","",1,0),
 ("REX","b24_rex_brokers","Then it's the brokers who wrote the bad loans! Or the agencies that graded them safe!","E","b_conveyor",0,1),
 ("SOL","b25_sol_broker","Every hand on this belt touched the loan. The broker who wrote it.","H","",1,0),
 ("SOL","b26_sol_bundled","The bank that bundled it. The agency that graded it.","H","",0,0),
 ("SOL","b27_sol_grade","The fund that bought the grade - not the house.","H","",1,0),
 ("SOL","b28_sol_owner","And the homeowner who refinanced, because the story said the price only goes up.","H","",0,0),
 ("SOL","b29_sol_sitwith","That's the part I need you to sit with. Not one desk. Not one signature.","H","",1,0),
 ("REX","b30_rex_dodge","So nobody's responsible? That feels like a dodge.","H","",2,0),
 ("SOL","b31_sol_choices","Different question. People made choices, and some were bad ones.","H","",0,0),
 ("SOL","b32_sol_fourparts","But it didn't need one villain pulling one lever. It needed four ordinary parts pointed the same way at once.","G","machine_parts",1,0),
 ("SOL","b33_sol_notstay","And when the fourth part hit, it didn't stay inside mortgages.","H","",0,0),
 ("SOL","b34_sol_market","The market fell fifty-five percent.","G","drawdown2008",1,0),
 ("SOL","b35_sol_jobs","Unemployment went from four point four, to ten percent.","G","unrate",0,0),
 ("SOL","b36_sol_wealth","And eleven and a half trillion dollars of household wealth stopped existing.","G","wealth",1,0),
 ("REX","b37_rex_once","Okay but that's the big one. That's once.","E","b_two_machines",1,0),
 ("SOL","b38_sol_backeight","Run it back eight years. Same four parts, different story - this time the story was the internet.","G","dotcom",0,0),
 ("SOL","b39_sol_seventyeight","That one fell seventy-eight percent. And it took until twenty-fifteen to get back to even.","H","",1,0),
 ("REX","b40_rex_fifteen","Fifteen years?!","H","",3,0),
 ("SOL","b41_sol_time","A bubble doesn't cost you money, kid. It costs you time. Watch for cheap money, a story, leverage - and someone who has to sell. You'll see it turning long before the headline does.","E","b_machine_lit",1,0),
]


def dur(line: str) -> int:
    words = len(line.split())
    return max(48, int(round(words / WPS * FPS)) + LEAD)


def build_beats() -> tuple[str, int]:
    at = 0
    out = []
    for i, (spk, vo, line, kind, val, pose, two) in enumerate(B):
        poses = (SOL_POSE if spk == "SOL" else REX_POSE)
        actors = TWO if two else SOLO[spk] % poses[pose % len(poses)]
        key = ""
        if kind == "E":
            key = '   exhibit: "%s",\n' % val
        elif kind == "G":
            key = '   graphic: "%s",\n' % val
        # a gentle push that never lands, alternating direction per beat
        k0, k1 = (1.0, 1.08) if i % 2 == 0 else (1.04, 1.12)
        esc = line.replace('"', '\\"')
        out.append(
            "  {at: %d,\n%s   actors: %s,\n"
            "   shots: [{from: 0, k: %s, kEnd: %s}],\n"
            '   vo: "%s", speaker: "%s",\n   line: "%s"},'
            % (at, key, actors, k0, k1, vo, spk, esc))
        at += dur(line) + GAP
    return "\n\n".join(out), at


def main() -> None:
    src = SRC.read_text("utf-8")
    beats, total = build_beats()

    # ---- swap the beats -------------------------------------------
    a = src.index("const BEATS: Beat[] = [")
    b = src.index("\n];", a)
    src = src[:a] + "const BEATS: Beat[] = [\n" + beats + src[b:]

    # ---- identity --------------------------------------------------
    src = src.replace("EP2_FRAMES", "BUBBLES_FRAMES")
    src = src.replace("FairMarketEp2", "Bubbles")
    src = src.replace("audio/fairmarket_ep2/", "audio/fairmarket_bubbles/")
    src = re.sub(r"export const BUBBLES_FRAMES = \d+;.*",
                 "export const BUBBLES_FRAMES = %d;   // %.0fs"
                 % (total, total / FPS), src, count=1)

    # ---- graphics menu ---------------------------------------------
    src = src.replace(
        'import {CountdownExhibit, StackExhibit, TickerTape} from "../motion/Infographic";',
        'import {BigNumberExhibit, TickerTape} from "../motion/Infographic";\n'
        'import {SeriesExhibit} from "../motion/Series";\n'
        'import {MachineParts, MachineLoop} from "../motion/Machine";')
    src = src.replace(
        '  graphic?: "countdown_16" | "stack_26";',
        '  graphic?: "fedfunds" | "caseshiller" | "drawdown2008" | "unrate"\n'
        '    | "dotcom" | "wealth" | "machine_parts" | "machine_loop";')

    # the render chain: one SeriesExhibit branch covers all five series
    a = src.index('            ) : cur.graphic === "countdown_16" ? (')
    b = src.index('            ) : cur.card ?', a)
    src = src[:a] + """            ) : cur.graphic === "machine_parts" ? (
              <MachineParts since={since} w={WALL.w} h={WALL.h} />
            ) : cur.graphic === "machine_loop" ? (
              <MachineLoop since={since} w={WALL.w} h={WALL.h} />
            ) : cur.graphic === "wealth" ? (
              <BigNumberExhibit since={since} w={WALL.w} h={WALL.h}
                kicker="HOUSEHOLD NET WORTH LOST" value="$11.5 TRILLION"
                caption="peak 2007 Q3 to trough 2009 Q1, a fall of 16.3%"
                foot="Federal Reserve Z.1, households and nonprofits - FRED TNWBSHNO" />
            ) : cur.graphic ? (
              <SeriesExhibit name={cur.graphic as never}
                since={since} w={WALL.w} h={WALL.h} />
""" + src[b:]

    DST.write_text(src, "utf-8")
    print("%d beats, %d frames (%.1fs) -> %s"
          % (len(B), total, total / FPS, DST.name))
    kinds = {}
    for _, _, _, k, v, _, _ in B:
        kinds[k] = kinds.get(k, 0) + 1
    print("  wall:", kinds)
    print("  exhibits:", sorted({v for _, _, _, k, v, _, _ in B if k == "E"}))
    print("  graphics:", sorted({v for _, _, _, k, v, _, _ in B if k == "G"}))
    json.dump([dict(vo=v, speaker=s, line=l) for s, v, l, *_ in B],
              open(REPO / "data/bubbles/lines.json", "w"), indent=1)


if __name__ == "__main__":
    main()
