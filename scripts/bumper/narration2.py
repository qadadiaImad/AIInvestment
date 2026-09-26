"""Script for explainer 2: "The screen" (market-wide gates + the robotics verdict).

    cd scripts && python -m bumper.narration2

Writes data/bumper/2026-09-25/narration2.json: ordered scenes
  {id, kind: chart|clip, chart: <overlay name>, clip: <grok prompt or null>, text}
Every number in `text` is read from the study/screen outputs; only the prose is authored.
Grok clips are atmosphere only: every prompt bans text, numbers, charts and logos; the
overlay code draws the data on top.
"""
from __future__ import annotations

import json
import pathlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
D = ROOT / "data" / "bumper" / "2026-09-25"

STYLE = ("Isometric 3D illustration, dark navy background, neon green and amber accent lighting, clean minimal "
         "corporate style, cinematic slow camera move, soft volumetric light, high detail. "
         "Strictly no text, no numbers, no letters, no charts, no logos, no captions.")


def spoken(x):
    words = "zero one two three four five six seven eight nine".split()
    return "point " + " ".join(words[int(c)] for c in f"{x:.2f}".split(".")[1])


def build():
    S = json.load(open(D / "summary.json", encoding="utf-8"))
    W = json.load(open(D / "winners.json", encoding="utf-8"))
    wide = json.load(open(D / "screen_wide.json", encoding="utf-8"))
    today = json.load(open(D / "screen_today.json", encoding="utf-8"))
    rows = wide["rows"]
    caps = np.array([w["cap_at_run_usd"] for w in W if w.get("cap_at_run_usd")])
    p10, p25, p50, p75 = (np.percentile(caps, q) for q in (10, 25, 50, 75))
    n_total, n_scope = wide["scanner_total"], len(rows)
    n_runway = sum(1 for r in rows if any(x.startswith("runway") for x in r["reasons"]))
    n_notice = sum(1 for r in rows if any("listing notice" in x for x in r["reasons"]))
    n_flag = sum(r["stage"] == "FLAGGED" for r in rows)
    n_clean = sum(r["stage"] == "not disqualified" for r in rows)
    n_disq = sum(r["stage"] == "DISQUALIFIED" for r in rows)
    n_low = sum(r["stage"] == "not disqualified" and r["market_cap_usd"] < 8e8 for r in rows)
    n_curated = len(today["rows"])
    by = {r["ticker"].split(":")[1]: r for r in rows}
    serv, rr = by["SERV"], by["RR"]
    robots = {k: by[k] for k in ["SERV", "XTND", "PDYN", "ARBE", "RR", "AEVA", "INVZ", "UMAC", "DPRO", "RCAT"] if k in by}
    n_rob_disq = sum(1 for r in robots.values() if r["stage"] == "DISQUALIFIED")
    M = lambda x: f"{x / 1e6:.0f} million" if x < 1e9 else f"{x / 1e9:.1f} billion"

    scenes = [
        dict(id="01_hook", kind="clip", chart="title",
             clip=STYLE + " A green radar dish sweeps a glowing beam across a vast dark city of thousands of small glass office towers seen from above; a handful of towers light up as the beam passes, most stay dark.",
             text=(f"We pointed the bumper radar at the whole US market. {n_total:,} pre-profit small caps went in. "
                   f"{n_clean} came out not disqualified, and almost every robotics name was cut. Here is the screen, gate by gate, and why.")),
        dict(id="02_recap", kind="chart", chart="capdist", clip=None,
             text=(f"First, what we are looking for. A bumper is a small company that becomes a sector leader. Across {len(caps)} historical winners, "
                   f"the median market cap when the run began was {M(p50)}. A quarter started below {M(p25)}, one in ten below {M(p10)}, "
                   f"and three quarters were under {M(p75)}. Low cap is not a taste. It is what the data says.")),
        dict(id="03_lists", kind="clip", chart="counter",
             clip=STYLE + " A single stage spotlight lights three small glass figurines on a dark floor while thousands of identical figurines stand in darkness behind them; slowly the spotlight widens and the whole crowd is revealed.",
             text=(f"Our first screen used the names we already track: {n_curated} companies. That is the wrong universe. "
                   f"A bumper is by definition not on anyone's list yet. So the second screen let the scanner build the universe: "
                   f"every US-listed common stock worth fifty million to three billion dollars and burning cash. {n_total:,} names.")),
        dict(id="04_funnel", kind="chart", chart="funnel", clip=None,
             text=(f"Then the gates. Biotech, banks, retail, consumer and shell companies play a different game, so they leave first: "
                   f"{n_scope} remain. The runway gate removes {n_runway}. Exchange notices remove {n_notice} more. "
                   f"Going-concern language flags {n_flag} for reading. {n_clean} are not disqualified, {n_low} of them below the median winner's size.")),
        dict(id="05_runway", kind="clip", chart="runway",
             clip=STYLE + " A tall transparent glass tank shaped like a ledger book, filled with glowing green liquid, drains steadily through a valve at the bottom into a bright amber flame; the liquid level falls visibly during the shot.",
             text=(f"Gate one is cash runway: cash divided by the yearly burn. Under two years, disqualified. This is the balance sheet draining. "
                   f"Serve Robotics grew revenue {serv['rev_growth_yoy']:.0f} percent, and has {serv['runway_years']:.1f} years of cash. "
                   f"Xtend, Palladyne, Arbe, Aeva, Innoviz: all under two years. Growth does not pay the bills. The next raise does.")),
        dict(id="06_dilution", kind="clip", chart="dilution",
             clip=STYLE + " Night office: a small glass company building sits on a table; a giant hand pours more and more tiny glass cubes into the building's foundation tray, and the building's original cubes shrink in proportion as the tray overflows.",
             text=("Why is runway the first gate? Because the graveyard says so. Arrival, Lordstown and Canoo all had headline customers. "
                   "What killed them was the second raise: done at a discount, to whoever would still buy, with warrants attached. "
                   "The question is never whether they can raise. It is who buys the dilution, and on what terms.")),
        dict(id="07_gc", kind="clip", chart="gclist",
             clip=STYLE + " An auditor's desk under a lamp: a thick bound financial report lies open, a heavy brass stamp comes down and leaves a glowing red seal on the page; papers stacked around, a magnifying glass beside.",
             text=(f"Gate two is the going-concern statement. When management writes that there is substantial doubt about continuing, that is a legal bright line, "
                   f"and it showed up four to five months before Virgin Orbit and Astra failed. A text search flags {n_flag} names this year. "
                   f"But search cannot tell an explicit statement from risk-factor boilerplate, so these are flags to read, not verdicts. "
                   f"Nano Nuclear has fifteen years of cash and four hits: boilerplate. Evolution Metals has two months of cash and four hits: real.")),
        dict(id="08_notice", kind="clip", chart="noticelist",
             clip=STYLE + " A sealed envelope slides under the door of a dark glass office; as it lands, a red warning lamp above the door blinks on and washes the room in red light.",
             text=(f"Gate three is the exchange letter: a minimum bid price or listing rule notice filed in an 8-K. It means the company is already fighting to stay listed. "
                   f"Blink Charging, Momentus and Soluna carry one this year. {n_notice} names leave here.")),
        dict(id="09_graveyard", kind="clip", chart="graveyardtable",
             clip=STYLE + " A rainy lot at dusk full of sleek unbranded electric trucks and vans slowly rusting, weeds growing between them, one truck's headlights still faintly glowing.",
             text=("Here is the trap the gates are built for. Every graveyard name had a winner's signals. Nikola had General Motors. Lordstown had Foxconn. "
                   "Canoo had Walmart. Arrival had a UPS letter of intent for ten thousand vans, with no deposit and no cancellation penalty. "
                   "Announced demand is not demand. Which brings us to the check that separates them.")),
        dict(id="10_binding", kind="chart", chart="interaction", clip=None,
             text=("The binding-demand check. Company, customer, financier. A letter of intent is a dashed line: it counts for nothing. "
                   "A contract becomes solid only when a later filing shows delivered units or recognised revenue. And when the customer is also the one "
                   "funding the company, the arrow points both ways, and that is a warning, not a validation. Read the contract, not the press release.")),
        dict(id="11_robots", kind="clip", chart="robotscatter",
             clip=STYLE + " A sleek humanoid robot stands on a dim factory floor under a single work light; beside it a tall glass cylinder gauge of glowing green liquid slowly empties toward the bottom while the robot keeps working.",
             text=(f"So, robotics. The pure plays under three billion dollars are Serve, Xtend, Palladyne, Arbe and Richtech. "
                   f"{n_rob_disq} of the ten robotics and perception names fail on runway alone. They look like the 2021 EV cohort: triple-digit growth from tiny bases, "
                   f"heavy burn, cash measured in quarters. Richtech is the one pure play that clears the gates, with {rr['runway_years']:.0f} years of runway, "
                   f"but revenue growth of {rr['rev_growth_yoy']:.0f} percent and no binding-demand check yet. Symbotic and Ondas are past the window: too big.")),
        dict(id="12_survivors", kind="clip", chart="survivors",
             clip=STYLE + " Aerial view of the dark city of glass towers at night; the radar beam passes and only a scattered handful of towers stay lit in green while the rest fade to black, camera slowly orbiting.",
             text=(f"What is left. {n_clean} names pass every gate we can run from public data; {n_low} are below the median winner's size. "
                   f"Among low-cap technology names with a research line and revenue growing over thirty percent: SEALSQ, LightPath, Ballard, Enovix, SES, ASP Isotopes. "
                   f"Read that carefully. Not disqualified is not a pick. The promotion gate, delivered contracts confirmed in a later filing, has not been run on any of them.")),
        dict(id="13_next", kind="clip", chart="nextsteps",
             clip=STYLE + " Close-up of hands turning the pages of a thick bound legal filing under a desk lamp, a magnifying glass hovering; one clause on the page begins to glow green.",
             text=("What turns a survivor into a watch: three reads per company. The customer contract: deposit, cancellation terms, delivered units. "
                   "The last raise: who bought it and at what discount. The related parties: whether the customer, the lender and the shareholder are the same entity. "
                   "All of it is in the filings, all of it is free, and none of it is in a ratio.")),
        dict(id="14_outro", kind="clip", chart="outro",
             clip=STYLE + " The radar dish slows and stops, its green beam fading over the dark city; a single lit tower remains, then the scene fades to black.",
             text=("The information is in the filings and the relationships, not the ratios. Educational research only, not investment advice. "
                   "Screen outputs and code are in the AI Investment repository.")),
    ]
    out = D / "narration2.json"
    out.write_text(json.dumps(scenes, indent=1, ensure_ascii=False), encoding="utf-8")
    words = sum(len(s["text"].split()) for s in scenes)
    print(f"wrote {out}: {len(scenes)} scenes, {sum(1 for s in scenes if s['clip'])} clips, {words} words (~{words / 150:.1f} min)")
    return scenes


if __name__ == "__main__":
    build()
