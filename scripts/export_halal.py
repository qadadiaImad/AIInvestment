"""Export the halal-screening bundle: web/public/data/halal.json.

Joins the latest pull_halal.py batch (ratio inputs) with the curated
business-activity file into per-ticker verdicts (aiinvest.halal.verdict).
Optional bundle — the site builds without it (quantum.json pattern).

Verdicts are computed methodology results, NOT fatwas. Educational only.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import pathlib

from aiinvest import ai_stack, halal, quantum_stack

DISCLAIMER = (
    "Computed from published screening methodologies (AAOIFI SS 21, FTSE "
    "Yasaar, MSCI Islamic) — we are not a Sharia board and this is not a "
    "fatwa, not financial advice, and not a recommendation to buy or sell "
    "any security. Every figure is date-stamped and decays; missing data is "
    "shown as 'insufficient data', never guessed. Verify against primary "
    "sources and consult a qualified scholar before acting.")

METHODOLOGY_NOTE = (
    "Overall verdict basis: AAOIFI SS 21. FTSE Yasaar and MSCI Islamic "
    "results are shown side by side because the standards genuinely disagree "
    "(denominators, thresholds, sector exclusions) — the same company can "
    "pass one and fail another. Expand any test to see the worked math.")


def _layer_of(ticker):
    return ai_stack.layer_of(ticker) or quantum_stack.layer_of(ticker)


def build(batch, activity, xbrl=None, price_series=None):
    """Assemble the halal.json bundle. Pure (no I/O).

    xbrl: optional dict mapping symbol -> xbrl facts dict (as produced by
    aiinvest.xbrl.extract_facts). When present, exact XBRL receivables replace
    the turnover proxy and interest income is added to the activity screen.

    price_series: optional dict mapping symbol -> list of {"date", "close"} dicts
    (the "series" array from web/public/data/prices/<SYM>.json). When present,
    trailing-average market caps are computed for SP/DJIM screens.
    """
    verdicts = {}
    xbrl = xbrl or {}
    price_series = price_series or {}
    for sym, rec in (batch.get("financial_data") or {}).items():
        metrics = rec.get("metrics", {}) or {}

        # Compute trailing-average market caps for S&P (36m) and DJIM (24m) screens.
        series = price_series.get(sym)
        spot_mcap = (metrics.get("market_cap_basic") or {}).get("value")
        spot_close = (metrics.get("close") or {}).get("value")
        avg_mcap_36m = halal.avg_market_cap(series, 36, spot_mcap, spot_close) if series else None
        avg_mcap_24m = halal.avg_market_cap(series, 24, spot_mcap, spot_close) if series else None

        v = halal.verdict(sym, metrics, activity.get(sym),
                          xbrl_facts=xbrl.get(sym),
                          avg_mcap_36m=avg_mcap_36m, avg_mcap_24m=avg_mcap_24m)
        v["layer"] = _layer_of(rec.get("ticker"))
        verdicts[sym] = v
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"generated_at": now, "disclaimer": DISCLAIMER,
            "methodology_note": METHODOLOGY_NOTE,
            "conventions": halal.CONVENTIONS, "verdicts": verdicts}


def write_history_snapshot(bundle, data_root, date_str):
    """Persist today's bundle under data/halal/history/ (Task-12 alerts diff input)."""
    out = pathlib.Path(data_root) / "halal" / "history" / f"halal_{date_str}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return out


def _latest_batch(data_root):
    paths = sorted(glob.glob(str(data_root / "halal" / "*" / "tradingview_halal_*.json")))
    if not paths:
        return None
    return json.loads(pathlib.Path(paths[-1]).read_text(encoding="utf-8"))


def main(argv=None):
    repo = pathlib.Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description="Export the halal-screening bundle.")
    ap.add_argument("--data", default=str(repo / "data"))
    ap.add_argument("--out", default=str(repo / "web" / "public" / "data" / "halal.json"))
    args = ap.parse_args(argv)

    batch = _latest_batch(pathlib.Path(args.data))
    if batch is None:
        print("No halal batch found — run pull_halal.py first.")
        return 2

    activity = halal.load_business_activity()
    universe = sorted({t.split(":")[-1] for t in
                       ai_stack.all_tickers() + quantum_stack.all_tickers()})
    problems = halal.validate_business_activity(activity, universe)
    if problems:
        print("business_activity.json INVALID — refusing to export:")
        for p in problems:
            print(f"  - {p}")
        return 2

    # Load XBRL facts cache (data/xbrl/<SYM>.json). Absent dir or missing files
    # degrade silently — the engine falls back to the turnover proxy (convention #4).
    xbrl_cache = {}
    xbrl_dir = pathlib.Path(args.data) / "xbrl"
    if xbrl_dir.is_dir():
        for xf in xbrl_dir.glob("*.json"):
            try:
                rec = json.loads(xf.read_text(encoding="utf-8"))
                sym = xf.stem  # filename is <SYM>.json
                xbrl_cache[sym] = rec.get("facts", {})
            except Exception:
                pass  # corrupt cache file — skip, use proxy

    # Load price series cache (web/public/data/prices/<SYM>.json) for S&P/DJIM
    # trailing-average market cap computation. Absent dir or missing files degrade
    # silently — the SP/DJIM screens show "unknown" (disclosed approximation).
    price_series_cache = {}
    prices_dir = repo / "web" / "public" / "data" / "prices"
    if prices_dir.is_dir():
        for pf in prices_dir.glob("*.json"):
            try:
                rec = json.loads(pf.read_text(encoding="utf-8"))
                sym = pf.stem  # filename is <SYM>.json
                if isinstance(rec.get("series"), list):
                    price_series_cache[sym] = rec["series"]
            except Exception:
                pass  # corrupt price file — skip, SP/DJIM will show unknown

    bundle = build(batch, activity, xbrl=xbrl_cache, price_series=price_series_cache)

    # Provenance-mandatory: any verdict with computed ratios must carry inputs_asof.
    unstamped = [s for s, v in bundle["verdicts"].items()
                 if v.get("inputs_asof") is None
                 and any(t["ratio"] is not None
                         for std in v["standards"].values() for t in std["tests"])]
    if unstamped:
        print(f"UNSTAMPED verdicts (refusing to export): {unstamped}")
        return 2

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    write_history_snapshot(bundle, pathlib.Path(args.data), date_str)

    counts = {}
    for v in bundle["verdicts"].values():
        counts[v["overall"]] = counts.get(v["overall"], 0) + 1
    print(f"Wrote {out}")
    print(f"  verdicts={len(bundle['verdicts'])} breakdown={counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
