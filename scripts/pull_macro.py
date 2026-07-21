"""Pull MACRO-desk data for the 8-series rates/inflation/liquidity/vol/energy universe.

REST-first, no browser anywhere (keyless FRED fredgraph.csv only — CLAUDE.md §3). One CSV
GET per series via aiinvest/fred.py:fetch_csv; every change/1y-comparison/window/sparkline
/regime-chip is computed locally in aiinvest/macro.py from that one series. Writes the
flat, one-stamp-per-series bundle to web/public/data/macro.json — see
docs/superpowers/specs/2026-07-14-macro-desk-design.md for the binding contract.

SANDBOX CAVEAT: fred.stlouisfed.org is egress-blocked in this dev sandbox — this CLI is
integration-tested against mocked CSV text (tests/test_pull_macro.py). The live pull runs
on the owner's machine.

Usage:
    python pull_macro.py                          # whole 8-series universe
    python pull_macro.py --series DGS10,VIXCLS     # restrict to a subset (debugging)
    python pull_macro.py --out /tmp/macro.json
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime
import json
import math
import pathlib

from aiinvest import fred, macro

SCHEMA_VERSION = "macro-desk-v1"
SOURCE = "fred"
SOURCE_CLASS = "api"
DISCLAIMER = ("Educational research only — not financial advice. Regime labels are "
              "rule-based, not predictive.")

SERIES_ORDER = list(macro.SERIES_META.keys())  # DGS2, DGS10, DFF, T10Y2Y, CPIAUCSL, WALCL, VIXCLS, APU000072610

_DIRTY_STRINGS = {"", ".", "-", "--", "n/a", "na", "none", "null"}


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _source_url(series_id):
    return fred.fredgraph_csv_url(series_id)


def _fetch_one(series_id, session=None):
    """Isolated per-series fetch — a failure here is caught by the caller, never aborts
    the run (matches pull_ta.py's per-instrument try/except)."""
    try:
        raw_rows = fred.fetch_csv(series_id, session=session)
    except Exception as e:  # noqa: BLE001
        return series_id, None, str(e)
    return series_id, raw_rows, None


def _walk_numeric_problems(obj, path):
    """Recursively validate: every number finite or None; reject dirty sentinel strings
    (mirrors pull_ta.py's dirty-value doctrine — local copy, not imported, per
    build_risk.py's precedent that these modules aren't shared-library targets)."""
    problems = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            problems += _walk_numeric_problems(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            problems += _walk_numeric_problems(v, f"{path}[{i}]")
    elif isinstance(obj, float):
        if not math.isfinite(obj):
            problems.append(f"{path}: non-finite float {obj!r}")
    elif isinstance(obj, str):
        if obj.strip().lower() in _DIRTY_STRINGS:
            problems.append(f"{path}: dirty sentinel string {obj!r}")
    return problems


def build_bundle(series_ids, generated_at, session=None, max_workers=4):
    """Fetch all requested series concurrently (plain ThreadPoolExecutor — lightweight CSV
    GETs, no browser, no Mode-A/B gating concern per CLAUDE.md §3 scope), transform, and
    assemble the macro.json bundle dict. Pure assembly logic delegates to aiinvest/macro.py."""
    warnings = []
    raw_by_id = {}

    with cf.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_fetch_one, sid, session): sid for sid in series_ids}
        for fut in cf.as_completed(futs):
            sid, raw_rows, err = fut.result()
            if err:
                warnings.append(f"{sid}: fetch failed ({err}); series omitted")
                continue
            raw_by_id[sid] = raw_rows

    series_by_id = {}
    walcl_91d_ago = None

    for sid in series_ids:
        if sid not in raw_by_id:
            continue
        meta = macro.SERIES_META[sid]
        raw_rows = raw_by_id[sid]
        transformed = macro.yoy(raw_rows, tolerance_days=20) if meta["transform"] == "yoy_pct" \
            else raw_rows

        retrieved_at = _iso(_utc_now())
        payload = macro.build_series_payload(sid, transformed, meta, retrieved_at,
                                              _source_url(sid))
        series_by_id[sid] = payload

        if sid == "WALCL":
            as_of = payload.get("as_of")
            if as_of is not None:
                comp = macro.nearest_by_offset(transformed, as_of, offset_days=91,
                                                tolerance_days=10)
                if comp is not None:
                    walcl_91d_ago = comp["value"]

    series_list = [series_by_id[sid] for sid in series_ids if sid in series_by_id]

    regime, regime_warnings = macro.build_regime(series_by_id, walcl_91d_ago=walcl_91d_ago)
    warnings.extend(regime_warnings)

    return {
        "generated_at": _iso(generated_at),
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "source_class": SOURCE_CLASS,
        "disclaimer": DISCLAIMER,
        "series": series_list,
        "regime": regime,
        "warnings": warnings,
    }


def _default_out_path():
    repo = pathlib.Path(__file__).resolve().parent.parent
    return str(repo / "web" / "public" / "data" / "macro.json")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Pull macro-desk data (keyless FRED CSV REST, no browser).")
    ap.add_argument("--series", help="Comma-separated subset of macro.SERIES_META ids (debug).")
    ap.add_argument("--out", default=_default_out_path(),
                    help="Output path (default: web/public/data/macro.json).")
    ap.add_argument("--max-workers", type=int, default=4)
    args = ap.parse_args(argv)

    series_ids = list(SERIES_ORDER)
    if args.series:
        wanted = [s.strip().upper() for s in args.series.split(",") if s.strip()]
        unknown = [s for s in wanted if s not in macro.SERIES_META]
        if unknown:
            print(f"  unknown series ignored: {unknown}")
        series_ids = [s for s in SERIES_ORDER if s in wanted]

    generated_at = _utc_now()
    bundle = build_bundle(series_ids, generated_at, max_workers=args.max_workers)

    problems = _walk_numeric_problems(bundle, "macro")
    if problems:
        bundle["warnings"].append(
            f"validation: {len(problems)} problem(s) found post-assembly (see logs)")
        print("  validation problems:")
        for p in problems[:20]:
            print(f"    {p}")

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    n_ok, n_total = len(bundle["series"]), len(series_ids)
    print(f"macro: {n_ok}/{n_total} series ok -> {out_path}")
    if bundle["warnings"]:
        print("  warnings:")
        for w in bundle["warnings"]:
            print(f"    {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
