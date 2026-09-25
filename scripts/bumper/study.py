"""Run the bumper study end to end and write data/bumper/<date>/.

    cd scripts && python -m bumper.study [--max-controls 300]

1. Winners: US-exchange names >= 5x over 5y or >= 3x over 3y, cap >= $1B (scanner).
2. Controls: same industries, cap $0.2-5B, 5y return in [-80%, +100%].
3. Run start per winner: first 12-month window with >= 2.5x (Yahoo monthly, adjusted).
   Controls get a pseudo run start = the median winner run-start month.
4. Features at run start minus 3 months (a live screen's latest filing) from SEC XBRL.
5. Separation stats (AUC winners vs controls) per feature, era split by run-start year.
Every number is computed here; the narrative layer only reads the JSON.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import pathlib
import statistics

from . import features as F
from . import sources as S

FEATS = ["revenue_ttm", "rev_growth_yoy", "rev_acceleration", "rnd_to_rev", "gross_margin",
         "runway_years", "shares_growth_yoy", "cash", "ocf_ttm"]


def _company_block(rec, cache_dir, run_month=None):
    sym = rec["symbol"]
    closes = S.cache_json(cache_dir / "prices" / f"{sym}.json", lambda: S.yahoo_monthly(sym))
    S.polite(0.1)
    if closes:
        closes = [(k, v) for k, v in closes]
    rs = run_month
    mult = None
    if rec.get("_role") == "winner":
        rs = F.run_start(closes, 12, 2.5) if closes else None
        if closes:
            _, mult = F.best_forward_window(closes, 12)
    cik = S.cik_for(sym)
    q = None
    if cik:
        facts = S.cache_json(cache_dir / "facts" / f"{sym}.json", lambda: S.companyfacts(cik))
        S.polite(0.12)
        q = S.quarterly_series(facts) if facts else None
    feats = None
    if rs and q:
        asof = F.months_before(rs, 3)
        feats = F.features_at(asof, q)
        feats["asof"] = asof
    # market cap at run start (approx): today's cap scaled by price ratio
    cap_at_run = None
    if closes and rs and rec.get("market_cap_basic"):
        px = dict(closes)
        if rs in px and closes[-1][1]:
            cap_at_run = rec["market_cap_basic"] * px[rs] / closes[-1][1]
    return {"symbol": sym, "ticker": rec["ticker"], "name": rec.get("description"), "sector": rec.get("sector"),
            "industry": rec.get("industry"), "role": rec.get("_role"), "cik": cik, "run_start": rs,
            "best_12m_multiple": mult, "cap_at_run_usd": cap_at_run, "cap_now_usd": rec.get("market_cap_basic"),
            "perf_5y": rec.get("Perf.5Y"), "perf_3y": rec.get("Perf.3Y"), "features": feats,
            "has_xbrl": bool(q and q.get("revenue"))}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-controls", type=int, default=300)
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parents[2] / "data" / "bumper"))
    args = ap.parse_args(argv)
    day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    out_dir = pathlib.Path(args.out) / day
    cache = pathlib.Path(args.out) / "cache"
    out_dir.mkdir(parents=True, exist_ok=True)

    win = S.winners()
    for w in win:
        w["_role"] = "winner"
    inds = {w["industry"] for w in win if w.get("industry")}
    ctl = S.controls(inds, limit=args.max_controls)
    for c in ctl:
        c["_role"] = "control"
    print(f"winners={len(win)} industries={len(inds)} controls={len(ctl)}")

    winners = []
    for i, w in enumerate(win):
        winners.append(_company_block(w, cache))
        if i % 25 == 0:
            print(f"  winners {i}/{len(win)}")
    months = [w["run_start"] for w in winners if w["run_start"]]
    pseudo = sorted(months)[len(months) // 2] if months else "2024-01"
    controls = []
    for i, c in enumerate(ctl):
        controls.append(_company_block(c, cache, run_month=pseudo))
        if i % 50 == 0:
            print(f"  controls {i}/{len(ctl)}")

    # separation stats
    def col(rows, k):
        return [r["features"].get(k) for r in rows if r.get("features")]
    wf = [w for w in winners if w["features"] and w["run_start"]]
    cf = [c for c in controls if c["features"]]
    stats = {}
    for k in FEATS:
        pw, pc = col(wf, k), col(cf, k)
        stats[k] = {"auc": F.auc(pw, pc), "median_winners": F.median(pw), "median_controls": F.median(pc),
                    "n_winners": sum(1 for x in pw if x is not None), "n_controls": sum(1 for x in pc if x is not None)}
    # boolean profitable
    pw = [w["features"]["profitable"] for w in wf if w["features"].get("profitable") is not None]
    pc = [c["features"]["profitable"] for c in cf if c["features"].get("profitable") is not None]
    stats["profitable_share"] = {"winners": (sum(pw) / len(pw)) if pw else None, "controls": (sum(pc) / len(pc)) if pc else None,
                                 "n_winners": len(pw), "n_controls": len(pc)}
    # era split of winners by run-start year
    eras = collections.defaultdict(list)
    for w in wf:
        eras[w["run_start"][:4]].append(w)
    era_stats = {}
    for yr, rows in sorted(eras.items()):
        era_stats[yr] = {"n": len(rows), **{k: F.median(col(rows, k)) for k in ["rev_growth_yoy", "rnd_to_rev", "runway_years", "shares_growth_yoy", "gross_margin"]}}
    caps = [w["cap_at_run_usd"] for w in wf if w["cap_at_run_usd"]]
    summary = {
        "generated_at": S.now(), "source": "TradingView scanner + Yahoo monthly closes + SEC XBRL companyfacts",
        "winners_total": len(winners), "winners_with_run_and_xbrl": len(wf), "controls_total": len(controls), "controls_with_xbrl": len(cf),
        "pseudo_run_month_controls": pseudo, "median_cap_at_run_usd": F.median(caps),
        "winners_by_sector": dict(collections.Counter(w["sector"] for w in winners).most_common()),
        "run_start_years": dict(collections.Counter(w["run_start"][:4] for w in wf)),
        "separation": stats, "eras": era_stats,
    }
    (out_dir / "winners.json").write_text(json.dumps(winners, indent=1), encoding="utf-8")
    (out_dir / "controls.json").write_text(json.dumps(controls, indent=1), encoding="utf-8")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("separation", "eras")}, indent=1))
    for k, v in stats.items():
        print(k, v)
    print("eras", json.dumps(era_stats, indent=1))
    print("wrote", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
