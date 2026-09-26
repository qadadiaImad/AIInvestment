"""Turn the bumper-dd-survivors workflow result into a report.

    cd scripts && python -m bumper.dd_report data/bumper/2026-09-25/dd_result.json

Writes references/bumper-report/dd_2026-09-26.md (+ fig/dd_bands.png). Bands, reasons and
citations come straight from the agents' structured outputs; nothing is added by hand except
the layout and the disclaimer.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_MD = ROOT / "references" / "bumper-report" / "dd_2026-09-26.md"
OUT_FIG = ROOT / "references" / "bumper-report" / "fig" / "dd_bands.png"
BANDS = ["avoid-pattern", "watch-thin", "watch-favourable-unvalidated", "abstain"]
COL = {"avoid-pattern": "#ff3b30", "watch-thin": "#f59e0b", "watch-favourable-unvalidated": "#22e07e", "abstain": "#8a94a6"}


def fig(rows, done):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [1, 1.6]})
    for ax in (a1, a2):
        ax.set_facecolor("#0e131d")
    fig.patch.set_facecolor("#0b0f17")
    counts = {b: sum(1 for r in rows if r["band"] == b) for b in BANDS}
    a1.barh(list(counts), list(counts.values()), color=[COL[b] for b in counts])
    a1.set_title("judge bands", color="white")
    a1.tick_params(colors="#9ca3af")
    by = {d["ticker"]: d for d in done}
    t = [r["ticker"] for r in rows]
    checked = [by[x]["verify"]["citations_checked"] if x in by else 0 for x in t]
    failed = [len(by[x]["verify"]["citations_failed"]) if x in by else 0 for x in t]
    a2.bar(t, checked, color="#3b82f6", label="citations checked")
    a2.bar(t, failed, color="#ff3b30", label="failed re-fetch")
    a2.set_title("citation audit per name", color="white")
    a2.tick_params(colors="#9ca3af", rotation=60)
    a2.legend(frameon=False, labelcolor="white")
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=160)


def main(path):
    R = json.load(open(path, encoding="utf-8"))
    done, judge, critic = R["done"], R["judge"], R["critic"]
    by = {d["ticker"]: d for d in done}
    rows = sorted(judge["rows"], key=lambda r: (BANDS.index(r["band"]) if r["band"] in BANDS else 9, r["ticker"]))
    fig(rows, done)
    L = []
    L.append(f"# Bumper Radar: filing-level due diligence on the screen survivors\n\n_{dt.date.today().isoformat()} · sixteen names · investigator + devil's advocate per name, one judge, one completeness critic · every agent on Claude Sonnet, filings via SEC EDGAR REST._\n")
    L.append("**Educational research only, not investment advice.** Bands are the Bumper Radar's own vocabulary: gates remove, they do not rank. "
             "`avoid-pattern` = an explicit graveyard gate is cited; `watch-favourable-unvalidated` = binding demand confirmed by delivered units or recognised revenue in a later filing and no gate; "
             "`watch-thin` = no gate, demand announced only; `abstain` = filings could not be read.\n")
    L.append("![bands](fig/dd_bands.png)\n")
    L.append("## Summary\n\n| ticker | judge band | investigator | auditor | citations ok/failed | binding demand | last raise | gates |\n|---|---|---|---|---|---|---|---|")
    for r in rows:
        d = by.get(r["ticker"])
        inv = d["dd"]["band"] if d else "-"
        aud = d["verify"]["band_recommendation"] if d else "-"
        cit = f"{d['verify']['citations_checked']}/{len(d['verify']['citations_failed'])}" if d else "-"
        L.append(f"| {r['ticker']} | **{r['band']}** | {inv} | {aud} | {cit} | {r['binding_demand']} | {r['last_raise']} | {r['gates']} |")
    L.append("\n## Cross-name observations\n")
    L += [f"- {o}" for o in judge["cross_name_observations"]]
    L.append("\n## Per name\n")
    for r in rows:
        d = by.get(r["ticker"])
        L.append(f"### {r['ticker']} · {r['band']}\n")
        L.append("**Judge's three reasons**")
        L += [f"{i + 1}. {x}" for i, x in enumerate(r["reasons"])]
        if r.get("disagreement_with_investigator"):
            L.append(f"\n_Disagreement / caveat:_ {r['disagreement_with_investigator']}")
        if d:
            dd, v = d["dd"], d["verify"]
            L.append(f"\n**Related parties:** {r['related_parties']}")
            bd = dd["binding_demand"]
            L.append(f"\n**Binding demand ({bd['verdict']}):** concentration: {bd['concentration']}")
            for c in bd["customers"][:6]:
                L.append(f"- {c['name']}: {c['what']} · binding: {c['binding']} · delivered/recognised: {c['delivered_or_recognised']} · {c['citation']}")
            lr = dd["last_raise"]
            L.append(f"\n**Last raise:** {lr['date']} {lr['form']} · {lr['amount_usd']} · {lr['instrument']} · buyers: {lr['buyers']} · {lr['discount_and_warrants']} · shares {lr['shares_out_year_ago']} → {lr['shares_out_now']} · ATM/ELN: {lr['atm_or_eln_in_place']} · {lr['citation']}")
            g = dd["graveyard_gates"]
            L.append(f"\n**Gates:** going-concern: {g['going_concern_explicit']} · listing notice: {g['listing_notice_12m']} · 5.02: {g['item_502_departures_12m']} · material weakness: {g['material_weakness']} · short/litigation: {g['short_seller_or_litigation']} · {g['citation']}")
            h = dd["insiders_and_holders"]
            L.append(f"\n**Insiders/holders:** Form 4 net 12m: {h['form4_net_12m']} · 13D/13G: {h['schedule_13d_13g']} · strategics: {h['strategic_holders']} · {h['citation']}")
            if dd["capital_web_edges"]:
                L.append("\n**Capital-web edges:** " + "; ".join(f"{e['src']} → {e['dst']} ({e['type']})" for e in dd["capital_web_edges"][:8]))
            L.append(f"\n**Auditor:** {v['citations_checked']} citations checked, {len(v['citations_failed'])} failed · confidence {v['confidence']} · {v['band_reason']}")
            for f in v["citations_failed"][:5]:
                L.append(f"- failed citation: {f['url']} · \"{f['quote'][:80]}\" · {f['why']}")
            for x in v["refuted_claims"][:5]:
                L.append(f"- refuted: {x['claim']} · {x['evidence']} · {x['citation']}")
            for x in v["missed_disqualifiers"][:5]:
                L.append(f"- missed disqualifier: {x['gate']} · {x['evidence']} · {x['citation']}")
            if dd["data_gaps"]:
                L.append("\n_Data gaps:_ " + "; ".join(dd["data_gaps"][:6]))
            L.append("\n<details><summary>Sources</summary>\n")
            for s_ in dd["sources"][:12]:
                L.append(f"- {s_['form']} {s_['date']} · {s_['url']} · \"{s_['quote'][:160]}\"")
            L.append("\n</details>\n")
    L.append("\n## Method notes (judge)\n")
    L += [f"- {m}" for m in judge["method_notes"]]
    L.append("\n## Completeness critic\n\n**Gaps**\n")
    L += [f"- {g}" for g in critic["gaps"]]
    L.append("\n**Next round**\n")
    L += [f"- {n}" for n in critic["next_round"]]
    if R.get("skipped"):
        L.append(f"\n_Names dropped by agent failure:_ {', '.join(R['skipped'])}")
    L.append("\n---\n_Not investment advice. Bands describe filing evidence, never expected returns. Numbers in the screen columns are from the TradingView scanner on 2026-09-25; everything else cites an SEC filing by form and date._\n")
    OUT_MD.write_text("\n".join(L), encoding="utf-8")
    print("wrote", OUT_MD, "and", OUT_FIG)


if __name__ == "__main__":
    main(sys.argv[1])
