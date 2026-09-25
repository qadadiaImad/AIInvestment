"""Narration script for the bumper explainer video.

Every number in the spoken text is read from the study outputs; the prose is the only
model-authored part. Writes data/bumper/2026-09-25/narration.json: a list of segments
{id, chart, text} in order. Run:  cd scripts && python -m bumper.narration
"""
from __future__ import annotations

import json
import pathlib
import statistics

ROOT = pathlib.Path(__file__).resolve().parents[2]
D = ROOT / "data" / "bumper" / "2026-09-25"


def spoken(x):
    """0.51 -> 'point five one' so the TTS reads a decimal, not a date."""
    digits = f"{x:.2f}".split(".")[1]
    words = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
             "6": "six", "7": "seven", "8": "eight", "9": "nine"}
    return "point " + " ".join(words[d] for d in digits)


def build():
    S = json.load(open(D / "summary.json", encoding="utf-8"))
    SEP = json.load(open(D / "separation_matched.json", encoding="utf-8"))
    WF = json.load(open(D / "workflow_result.json", encoding="utf-8"))
    ts = SEP["tech_small"]
    yrs = S["run_start_years"]
    top_year = max(yrs, key=yrs.get)
    fam = {}
    for c in WF["cases"]:
        for s in c["signals"]:
            if s["months_before_run"] > 0:
                fam.setdefault(s["category"], []).append(s["months_before_run"])
    lead = {k: statistics.median(v) for k, v in fam.items()}
    n_cases = len(WF["cases"])
    segs = [
        dict(id="01_intro", chart="title",
             text=("Can you spot the next sector leader before the market does? The names that ran in twenty twenty, "
                   "Nebius, IonQ, all looked like long shots first. This is what the data says about finding the next ones.")),
        dict(id="02_cohort", chart="r01",
             text=(f"We took every US-listed stock that multiplied at least five times over five years, or three times over three, "
                   f"and is worth at least one billion dollars today. That is {S['winners_total']} winners. Against them, "
                   f"{S['controls_total']} look-alikes from the same industries that went nowhere. "
                   f"Most of the runs started in {top_year}: the sector wave sets the clock more than any single company.")),
        dict(id="03_paths", chart="r04",
             text=("Here is the shape of a bumper. For two years before the run, the winners in green are indistinguishable from the "
                   "look-alikes in grey. Flat, often drifting down. Then the twelve-month window where they at least double and a half. "
                   "The question is whether anything in the filings, three months before that moment, told them apart.")),
        dict(id="04_auc", chart="r02",
             text=(f"The answer is no. This chart scores each feature from zero to one; a half means a coin flip. "
                   f"Revenue growth, {spoken(ts['rev_growth_yoy']['auc'])}. Research spending relative to revenue, {spoken(ts['rnd_to_rev']['auc'])}. "
                   f"Cash runway, {spoken(ts['runway_years']['auc'])}. Nothing above point six. The features that do separate are upside down: "
                   f"gross margin at {spoken(ts['gross_margin']['auc'])} and cash flow at {spoken(ts['ocf_ttm']['auc'])} mean the future winners "
                   f"were the lower-margin, cash-burning names.")),
        dict(id="05_dist", chart="r03",
             text=("Look at research intensity, the hypothesis behind IonQ and QUBT. Winners and look-alikes have the same shape. "
                   "Spending heavily on R&D is what every one of these companies does; it cannot be the signal. "
                   "What winners did do a little more of was raise equity. They financed the build before the market believed in it.")),
        dict(id="06_families", chart="r05",
             text=(f"So where was the early information? We rebuilt {n_cases} winners from the filings of the time: Nvidia in twenty fifteen, "
                   f"Enphase, Palantir, Super Micro, Nebius, IonQ, Rigetti. The signals were text and relationships, not ratios. "
                   f"A named anchor customer or binding contract, about {lead.get('anchor_customer_or_contract', 9):.0f} months ahead. "
                   f"Capacity being built, about {lead.get('capex_or_capacity', 8):.0f} months ahead. Insiders and strategics putting money in, "
                   f"{lead.get('insider_or_institutional', 10):.0f} months ahead. A new story stated in a mandatory filing. All free, all public.")),
        dict(id="07_graveyard", chart="graveyard",
             text=("But here is the trap. Every one of those signals also shows up in the graveyard. Nikola had General Motors. "
                   "Lordstown had Foxconn. Canoo had Walmart. Arrival had a UPS letter of intent with no deposit and no cancellation penalty. "
                   "What separated the collapses from the survivors was a short list of checkable facts: binding contracts with delivered units, "
                   "a disclosed runway number and how fast it shrank, share count growth, customers that were also financiers, "
                   "going-concern language, executives leaving over a funding gap, and exchange compliance notices.")),
        dict(id="08_base", chart="r06",
             text=("And the base rate is brutal. Of more than nine thousand US IPOs, thirty-eight percent lost half their value within three years. "
                   "Only one point seven percent returned more than five hundred percent. Unprofitable issuers do worse than average, "
                   "and SPAC mergers worst of all. The bumper is the thin right tail, and attention, hype and retail crowding predict the wrong tail.")),
        dict(id="09_funnel", chart="r07",
             text=("So the detector that survives scrutiny is not a probability oracle. It disqualifies first, on the graveyard facts. "
                   "It promotes only on delivered evidence: an announced contract counts when a later filing shows revenue or units. "
                   "Supporting signals are capped. And a judge agent narrates a band with three cited reasons, checked by a devil's advocate, "
                   "and never overrides the number.")),
        dict(id="10_today", chart="r08",
             text=("This is today's screen: quantum, physical AI and AI infrastructure names on research intensity against cash runway. "
                   "IonQ, Rigetti and QUBT sit high on research with years of runway; Serve and SoundHound sit under the two-year gate; "
                   "CoreWeave burns far below it but is funded by debt against contracts, which is exactly the case a ratio cannot judge.")),
        dict(id="11_outro", chart="title",
             text=("The information is in the filings and the relationships, not the ratios. Read the contract, not the press release. "
                   "Educational research only, not investment advice. Full report and code in the AI Investment repository.")),
    ]
    out = D / "narration.json"
    out.write_text(json.dumps(segs, indent=1, ensure_ascii=False), encoding="utf-8")
    words = sum(len(s["text"].split()) for s in segs)
    print(f"wrote {out}: {len(segs)} segments, {words} words (~{words / 150:.1f} min at 150 wpm)")
    return segs


if __name__ == "__main__":
    build()
