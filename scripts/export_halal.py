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


def build(batch, activity):
    """Assemble the halal.json bundle. Pure (no I/O)."""
    verdicts = {}
    for sym, rec in (batch.get("financial_data") or {}).items():
        v = halal.verdict(sym, rec.get("metrics", {}) or {}, activity.get(sym))
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

    bundle = build(batch, activity)

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
