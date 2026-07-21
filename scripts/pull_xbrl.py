"""Pull SEC XBRL companyfacts for the full universe (AI + Quantum) and cache locally.

Fetches https://www.sec.gov/files/company_tickers.json once per run, then
https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json per symbol at ≤10 req/s
(0.12 s inter-request sleep). Cache TTL is 30 days; fresh records are skipped unless
--force is passed. Symbols with no CIK in the SEC file (foreign listings such as TSM,
ASML, ARM, etc.) are collected in an honest miss list printed at the end.

Output: data/xbrl/<SYM>.json per symbol with keys:
    symbol, cik, retrieved_at, source_url, facts (extract_facts output)

SEC politeness: descriptive User-Agent with contact email, ≤10 req/s, 30-day cache.
Educational/research only — not financial advice.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys
import time

import requests

# Pull in the aiinvest package (scripts/ is the package root).
_SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from aiinvest import ai_stack, quantum_stack, xbrl  # noqa: E402

_TICKERS_URL = xbrl.COMPANY_TICKERS_URL
_FACTS_URL = xbrl.COMPANYFACTS_URL
_REQ_INTERVAL = 0.12  # ≤10 req/s (SEC guidance)


def _universe_bare_symbols():
    """Return bare symbols (no EXCHANGE: prefix) for the full AI + Quantum universe."""
    seen, out = set(), []
    for t in ai_stack.all_tickers() + quantum_stack.all_tickers():
        bare = t.split(":")[-1] if ":" in t else t
        if bare not in seen:
            seen.add(bare)
            out.append(bare)
    return out


def _fetch_company_tickers(session):
    """Download the SEC company-tickers mapping (once per run)."""
    resp = session.get(_TICKERS_URL, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _fetch_companyfacts(session, cik):
    """Download companyfacts JSON for the given zero-padded CIK string."""
    url = _FACTS_URL.format(cik=cik)
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json(), url


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Pull SEC XBRL companyfacts for the AI/Quantum universe."
    )
    ap.add_argument(
        "--limit", type=int, default=None,
        help="Smoke flag: process only the first N symbols."
    )
    ap.add_argument(
        "--force", action="store_true",
        help="Re-fetch even when a fresh cache (<30 days) already exists."
    )
    ap.add_argument(
        "--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "data"),
        help="Output root directory (default: ../data)."
    )
    args = ap.parse_args(argv)

    data_root = pathlib.Path(args.out)
    symbols = _universe_bare_symbols()
    if args.limit is not None:
        symbols = symbols[: args.limit]

    session = requests.Session()
    session.headers["User-Agent"] = xbrl.UA

    print(f"Fetching SEC company-tickers mapping from {_TICKERS_URL} ...")
    mapping = _fetch_company_tickers(session)
    time.sleep(_REQ_INTERVAL)
    print(f"  mapping loaded: {len(mapping)} entries")

    now = datetime.datetime.now(datetime.timezone.utc)
    retrieved_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    ok, skipped, missed, failed = [], [], [], []

    for sym in symbols:
        # Check cache first (unless --force).
        if not args.force:
            cached = xbrl.load_cached(sym, data_root)
            if cached and not xbrl.is_stale(cached):
                skipped.append(sym)
                continue

        # Resolve CIK.
        cik = xbrl.cik_for(sym, mapping)
        if cik is None:
            missed.append(sym)
            continue

        # Fetch companyfacts.
        try:
            time.sleep(_REQ_INTERVAL)
            facts_json, url = _fetch_companyfacts(session, cik)
        except requests.HTTPError as exc:
            print(f"  [HTTP {exc.response.status_code}] {sym} (CIK {cik}) — skipping")
            failed.append(sym)
            continue
        except requests.RequestException as exc:
            print(f"  [error] {sym} (CIK {cik}): {exc} — skipping")
            failed.append(sym)
            continue

        extracted = xbrl.extract_facts(facts_json)
        record = {
            "symbol": sym,
            "cik": cik,
            "retrieved_at": retrieved_at,
            "source_url": url,
            "facts": extracted,
        }
        xbrl.save_cache(sym, record, data_root)
        ok.append(sym)
        print(f"  [{sym}] CIK={cik} interest_income={extracted.get('interest_income')} "
              f"receivables={extracted.get('receivables')}")

    # Summary.
    print(f"\nDone. ok={len(ok)} skipped(fresh)={len(skipped)} "
          f"no-CIK={len(missed)} fetch-errors={len(failed)}")
    if missed:
        print(f"  No-CIK (foreign/unlisted): {', '.join(missed)}")
    if failed:
        print(f"  Fetch errors: {', '.join(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
