"""Assemble the portfolio desk bundle: web/data/portfolio.json (schema "portfolio-v1").

NETWORK-FREE. Every number here is a pure function of already-retrieved local files:
  data/portfolio/positions.json       (owner hand-edited, gitignored — NEVER committed)
  web/public/data/site.json           (stocks + layers, from export_site.py)
  web/public/data/prices/<SYM>.json   (5y daily closes, from pull_prices.py, incl. SPY)
  web/public/data/graph_analysis.json (optional; macro.snapshot.dff -> risk-free rate)

PRIVACY: output goes to web/data/portfolio.json — NOT web/public/data/. Anything under
web/public/** is served as a static asset by literal URL, bypassing the /terminal proxy
gate entirely. web/data/ is read server-side only (fs.readFileSync) and is gitignored.
See docs/superpowers/specs/2026-07-15-portfolio-design.md for the binding contract.

Usage:
    python build_portfolio.py                       # default paths
    python build_portfolio.py --positions /tmp/p.json --out /tmp/portfolio.json  # debugging

A missing positions.json is a NORMAL state (fresh clone, owner hasn't set up the file
yet) — the pipeline degrades to the empty-state bundle and exits 0, not an error.
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import pathlib

from aiinvest import portfolio, risk

SCHEMA_VERSION = "portfolio-v1"
SOURCE_CLASS = "computed"
DISCLAIMER = ("Educational research only — not financial advice. Historical risk "
              "measures do not predict future losses.")
PRICES_PROVIDER = "yahoo-finance-chart-api"
PRICES_SOURCE_CLASS = "api"
POSITIONS_REL_PATH = "data/portfolio/positions.json"
MISSING_POSITIONS_WARNING = (
    "no positions file found at data/portfolio/positions.json — copy "
    "positions.example.json and edit it with your holdings")

_DIRTY_STRINGS = {"", ".", "-", "--", "n/a", "na", "none", "null"}


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _mtime_iso(path):
    try:
        ts = path.stat().st_mtime
        return _iso(datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc))
    except OSError:
        return None


def _load_json(path):
    p = pathlib.Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


# --------------------------------------------------------------------------- validation
# Local copy of build_risk.py's dirty/non-finite walker — not imported, this module isn't
# a shared-library target (per the build brief).


def _walk_numeric_problems(obj, path):
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


def validate_bundle(bundle):
    return _walk_numeric_problems(bundle, "portfolio")


# --------------------------------------------------------------------------- params helper


def _default_params(args, base_currency="USD", rf_annual=0.04, rf_source="cli-default"):
    return {
        "base_currency": base_currency,
        "window_trading_days": args.window,
        "min_bars": args.min_bars,
        "rf_annual": rf_annual,
        "rf_source": rf_source,
        "top_n_correlation": args.top_n_correlation,
        "var_confidence": 0.95,
    }


def _empty_bundle(generated_at, args, extra_warnings=None, found=False,
                   n_raw_rows=0, n_after_merge=0, mtime=None, site=None):
    warnings = list(extra_warnings or [])
    return {
        "generated_at": _iso(generated_at),
        "schema_version": SCHEMA_VERSION,
        "source_class": SOURCE_CLASS,
        "disclaimer": DISCLAIMER,
        "positions_source": {
            "path": _display_path(args.positions), "mtime": mtime, "n_raw_rows": n_raw_rows,
            "n_positions_after_merge": n_after_merge, "found": found,
        },
        "prices_source": {"provider": PRICES_PROVIDER, "source_class": PRICES_SOURCE_CLASS,
                           "batch_retrieved_at": None},
        "site_source": {"generated_at": (site or {}).get("generated_at")},
        "params": _default_params(args),
        "positions": [],
        "aggregates": None,
        "risk": None,
        "warnings": warnings,
    }


# --------------------------------------------------------------------------- assembly


def build_bundle(args):
    """Pure-ish assembly (reads local files, no network): returns the full
    portfolio.json dict."""
    generated_at = _utc_now()
    data_root = pathlib.Path(args.data)
    positions_path = pathlib.Path(args.positions)

    site = _load_json(str(data_root / "site.json"))

    if not positions_path.exists():
        return _empty_bundle(generated_at, args, [MISSING_POSITIONS_WARNING], found=False,
                              site=site)

    raw = _load_json(str(positions_path))
    if raw is None or not isinstance(raw, dict):
        return _empty_bundle(
            generated_at, args,
            [f"{POSITIONS_REL_PATH} exists but could not be parsed as JSON"],
            found=False, mtime=_mtime_iso(positions_path), site=site)

    top_warnings = []
    base_currency, cur_warn = portfolio.validate_base_currency(raw.get("base_currency"))
    if cur_warn:
        top_warnings.append(cur_warn)
    cash_usd, cash_warn = portfolio.validate_cash_usd(raw.get("cash_usd"))
    if cash_warn:
        top_warnings.append(cash_warn)

    raw_positions = raw.get("positions") or []
    n_raw_rows = len(raw_positions)
    clean_rows, drop_warnings = portfolio.validate_positions(raw_positions)
    top_warnings.extend(drop_warnings)
    merged_rows = portfolio.merge_lots(clean_rows)
    n_after_merge = len(merged_rows)

    stocks = (site or {}).get("stocks") or {}
    prices_dir = data_root / "prices"

    if site is None:
        top_warnings.append("site.json not found — layer classification and prices_file "
                             "lookups will be limited to raw price files")

    # --- pass 1: resolve prices for every merged row (once), so pass 2 can reuse them
    row_price_info = {}
    prices_batch_retrieved_at = None
    for row in merged_rows:
        sym = row["symbol"]
        pf = prices_dir / f"{sym}.json"
        price_json = _load_json(str(pf)) if pf.exists() else None
        site_stock = stocks.get(sym)
        info = portfolio.resolve_price(sym, price_json, site_stock)
        row_price_info[sym] = info
        if price_json and prices_batch_retrieved_at is None:
            prices_batch_retrieved_at = price_json.get("retrieved_at")

    prelim_total = cash_usd
    for row in merged_rows:
        info = row_price_info[row["symbol"]]
        if info["last_price"] is not None:
            prelim_total += row["quantity"] * info["last_price"]

    # --- pass 2: build final position dicts now that total_value_usd is known
    positions = []
    for row in merged_rows:
        sym = row["symbol"]
        info = row_price_info[sym]
        layer = (stocks.get(sym) or {}).get("layer")
        positions.append(portfolio.compute_position(row, info, layer, prelim_total))

    aggregates = portfolio.compute_aggregates(positions, cash_usd)

    # --- risk block: full (unwindowed) daily-return maps for prices_file-sourced symbols
    per_symbol_full_ret = {}
    for row in merged_rows:
        sym = row["symbol"]
        info = row_price_info[sym]
        if info["price_source"] != "prices_file":
            continue
        pf = prices_dir / f"{sym}.json"
        rec = _load_json(str(pf))
        if not rec:
            continue
        series = rec.get("series") or []
        ret_list = risk.daily_returns(series)
        per_symbol_full_ret[sym] = {r["date"]: r["ret"] for r in ret_list}

    spy_rec = _load_json(str(prices_dir / "SPY.json"))
    spy_full_ret = None
    if spy_rec:
        spy_series = spy_rec.get("series") or []
        spy_ret_list = risk.daily_returns(spy_series)
        spy_full_ret = {r["date"]: r["ret"] for r in spy_ret_list}
        if prices_batch_retrieved_at is None:
            prices_batch_retrieved_at = spy_rec.get("retrieved_at")

    # risk-free rate: graph_analysis.json:macro.snapshot.dff, else --rf-annual (mirrors
    # build_risk.py's fallback logic exactly)
    ga = _load_json(str(data_root / "graph_analysis.json"))
    rf_annual = None
    rf_source = None
    if ga:
        dff = (((ga.get("macro") or {}).get("snapshot") or {}) or {}).get("dff")
        if isinstance(dff, (int, float)) and not isinstance(dff, bool) and math.isfinite(dff):
            rf_annual = dff / 100.0
            rf_source = "graph_analysis.json:macro.snapshot.dff"
    if rf_annual is None:
        rf_annual = args.rf_annual
        rf_source = "cli-default"
        top_warnings.append("rf_annual: graph_analysis.json unavailable, using "
                             "--rf-annual default")

    risk_block = portfolio.compute_risk(
        positions, per_symbol_full_ret, spy_full_ret, rf_annual,
        window=args.window, min_bars=args.min_bars,
        top_n_correlation=args.top_n_correlation)

    bundle = {
        "generated_at": _iso(generated_at),
        "schema_version": SCHEMA_VERSION,
        "source_class": SOURCE_CLASS,
        "disclaimer": DISCLAIMER,
        "positions_source": {
            "path": _display_path(args.positions), "mtime": _mtime_iso(positions_path),
            "n_raw_rows": n_raw_rows, "n_positions_after_merge": n_after_merge,
            "found": True,
        },
        "prices_source": {"provider": PRICES_PROVIDER, "source_class": PRICES_SOURCE_CLASS,
                           "batch_retrieved_at": prices_batch_retrieved_at},
        "site_source": {"generated_at": (site or {}).get("generated_at")},
        "params": _default_params(args, base_currency=base_currency, rf_annual=rf_annual,
                                   rf_source=rf_source),
        "positions": positions,
        "aggregates": aggregates,
        "risk": risk_block,
        "warnings": top_warnings,
    }
    return bundle


# --------------------------------------------------------------------------- CLI


def _repo_root():
    return pathlib.Path(__file__).resolve().parent.parent


def _display_path(raw):
    """Repo-relative form for stamping into the bundle (never leak an absolute
    local path/username onto the gated page); non-repo paths pass through."""
    try:
        return str(pathlib.Path(raw).resolve().relative_to(_repo_root())).replace("\\", "/")
    except ValueError:
        return str(raw)


def _default_positions_path():
    return str(_repo_root() / "data" / "portfolio" / "positions.json")


def _default_data_dir():
    return str(_repo_root() / "web" / "public" / "data")


def _default_out_path():
    return str(_repo_root() / "web" / "data" / "portfolio.json")


def build_arg_namespace(positions=None, data=None, out=None, rf_annual=0.04, window=252,
                         min_bars=60, top_n_correlation=5):
    """Test helper: build an argparse.Namespace identical in shape to what main()'s parser
    produces, without going through sys.argv."""
    return argparse.Namespace(
        positions=positions if positions is not None else _default_positions_path(),
        data=data if data is not None else _default_data_dir(),
        out=out if out is not None else _default_out_path(),
        rf_annual=rf_annual, window=window, min_bars=min_bars,
        top_n_correlation=top_n_correlation,
    )


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Assemble portfolio.json from already-retrieved local files (no network).")
    ap.add_argument("--positions", default=_default_positions_path(),
                    help="Owner-edited positions file (default: data/portfolio/positions.json).")
    ap.add_argument("--data", default=_default_data_dir(),
                    help="Root data dir containing site.json + prices/ (default: web/public/data).")
    ap.add_argument("--out", default=_default_out_path(),
                    help="Output path (default: web/data/portfolio.json — NOT web/public/data/).")
    ap.add_argument("--rf-annual", type=float, default=0.04,
                    help="Fallback annual risk-free rate if graph_analysis.json unavailable.")
    ap.add_argument("--window", type=int, default=252, help="Trailing return window (days).")
    ap.add_argument("--min-bars", type=int, default=60,
                    help="Minimum return bars required to compute risk stats.")
    ap.add_argument("--top-n-correlation", type=int, default=5,
                    help="Max holdings (by weight) considered for max_pairwise_correlation.")
    args = ap.parse_args(argv)

    bundle = build_bundle(args)

    problems = validate_bundle(bundle)
    if problems:
        bundle.setdefault("warnings", []).append(
            f"validation: {len(problems)} problem(s) found post-assembly (see logs)")
        print("  validation problems:")
        for p in problems[:20]:
            print(f"    {p}")

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    found = bundle["positions_source"]["found"]
    n_pos = len(bundle["positions"])
    print(f"portfolio: found={found} n_positions={n_pos} -> {out_path}")
    print(f"  warnings: {len(bundle.get('warnings', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
