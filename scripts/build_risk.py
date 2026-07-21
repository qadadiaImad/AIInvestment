"""Assemble the risk desk bundle: web/public/data/risk.json (schema "risk-desk-v1").

NETWORK-FREE. Every number here is a pure function of already-retrieved local files:
  web/public/data/site.json           (stocks + layers, from export_site.py)
  web/public/data/prices/<SYM>.json   (5y daily closes, from pull_prices.py, incl. SPY)
  web/public/data/graph_analysis.json (optional; macro.snapshot.dff -> risk-free rate)

source_class="computed" at the top level is deliberate: this feed performs zero new
retrieval. `prices_source` names the real underlying retrieval class ("api", Yahoo chart)
so provenance isn't lost, just relocated. See
docs/superpowers/specs/2026-07-14-risk-desk-design.md for the binding contract.

Usage:
    python build_risk.py                      # default paths under web/public/data
    python build_risk.py --out /tmp/risk.json  # debugging
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import pathlib
import statistics

from aiinvest import risk

SCHEMA_VERSION = "risk-desk-v1"
SOURCE_CLASS = "computed"
DISCLAIMER = ("Educational research only — not financial advice. Historical risk "
              "measures do not predict future losses.")
PRICES_PROVIDER = "yahoo-finance-chart-api"
PRICES_SOURCE_CLASS = "api"
BENCHMARK = "SPY"
PERIODS_PER_YEAR = 252
VAR_CONFIDENCE_LEVELS = [0.95, 0.99]

LAYER_ORDER = ["L0-energy", "L1-chips", "L2-infra", "L3-models", "L4-application"]
L3_PROXY_MEMBERS = ["GOOGL", "MSFT", "AMZN", "META"]
L3_MODELS_NOTE = (
    "L3-MODELS has no pure-play public equity — its correlation series is proxied via "
    "the equal-weighted hyperscaler capex basket (GOOGL/MSFT/AMZN/META), reused from "
    "L2-infra membership only for this calculation."
)
L3_NO_TICKERS_WARNING = (
    "L3-models has no public tickers in the AI-stack universe (private labs only) — "
    "no risk aggregate possible"
)

_DIRTY_STRINGS = {"", ".", "-", "--", "n/a", "na", "none", "null"}

_EMPTY_STOCK_METRICS = {
    "prices_retrieved_at": None, "last_price_date": None, "n_bars_total": 0,
    "n_returns_window": 0, "day_change_pct": None, "vol_annualized_pct": None,
    "var95_1d_pct": None, "var99_1d_pct": None, "sharpe_1y": None,
    "max_drawdown_1y_pct": None, "beta_vs_spy": None,
}
_EMPTY_LAYER_METRICS = {
    "day_change_pct": None, "day_change_basis": None,
    "vol_equal_weighted_pct": None, "vol_cap_weighted_pct": None,
    "vol_cap_weighted_basis": None, "median_var95_1d_pct": None,
    "median_var99_1d_pct": None, "worst_var95_1d_pct": None, "worst_var95_symbol": None,
    "best_sharpe_symbol": None, "best_sharpe_1y": None, "worst_sharpe_symbol": None,
    "worst_sharpe_1y": None, "worst_drawdown_symbol": None, "worst_drawdown_1y_pct": None,
}


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path):
    p = pathlib.Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


# --------------------------------------------------------------------------- validation
# Local copy of pull_ta.py's dirty/non-finite walker — not imported, this module isn't a
# shared-library target (per the build brief).


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
    return _walk_numeric_problems(bundle, "risk")


# --------------------------------------------------------------------------- small helpers


def _valid_bars(series):
    """[{"date","close"}, ...] filtered to finite, positive closes only."""
    out = []
    for b in series:
        c = b.get("close")
        if isinstance(c, (int, float)) and not isinstance(c, bool) and math.isfinite(c) and c > 0:
            out.append({"date": b["date"], "close": float(c)})
    return out


def _windowed_map(ret_map, window):
    """dict[date->ret] -> dict restricted to its own last `window` dates (by date)."""
    items = sorted(ret_map.items())
    if len(items) > window:
        items = items[-window:]
    return dict(items)


def _weighted_or_fallback(items):
    """items: [{"value","market_cap"}]. Cap-weighted mean if >=2 have market_cap AND
    that's >=50% of the item count; else equal-weighted mean + fallback basis + a
    human-readable reason. Returns (value, basis, warning_or_None). (None, None, None)
    if `items` is empty."""
    n = len(items)
    if n == 0:
        return None, None, None
    with_cap = [it for it in items
                if isinstance(it.get("market_cap"), (int, float))
                and not isinstance(it.get("market_cap"), bool)
                and math.isfinite(it["market_cap"]) and it["market_cap"] > 0]
    if len(with_cap) >= 2 and len(with_cap) >= 0.5 * n:
        total = sum(it["market_cap"] for it in with_cap)
        val = sum(it["value"] * it["market_cap"] for it in with_cap) / total
        return val, "market_cap", None
    val = sum(it["value"] for it in items) / n
    return val, "equal_weighted_fallback", "insufficient market-cap coverage, used equal-weighted fallback"


def _pick_extreme(entries, field, maximize):
    """entries: list of per_stock dicts. Pick the extreme non-None `field`, tie-broken
    alphabetically by symbol. Returns (symbol, value) or (None, None)."""
    candidates = [(e["symbol"], e[field]) for e in entries if e.get(field) is not None]
    if not candidates:
        return None, None
    target = max(v for _, v in candidates) if maximize else min(v for _, v in candidates)
    tied = sorted(s for s, v in candidates if v == target)
    return tied[0], target


# --------------------------------------------------------------------------- per-stock


def _null_stock_entry(sym, layer, market_cap, warnings):
    entry = {"symbol": sym, "layer": layer, **_EMPTY_STOCK_METRICS,
              "market_cap": market_cap, "warnings": warnings}
    return entry


def _compute_beta(full_ret_map, spy_full_ret, window, min_bars, warnings):
    if not spy_full_ret or len(spy_full_ret) < min_bars:
        warnings.append("beta_vs_spy: SPY price history unavailable or insufficient")
        return None
    xs_full, ys_full = risk.align_series(full_ret_map, spy_full_ret)
    n_full = len(xs_full)
    if n_full > window:
        xs_w, ys_w = xs_full[-window:], ys_full[-window:]
    else:
        xs_w, ys_w = xs_full, ys_full
    if len(xs_w) < min_bars:
        warnings.append(f"beta_vs_spy: insufficient aligned overlap with SPY "
                         f"(n={len(xs_w)}, need >={min_bars})")
        return None
    return risk.beta(xs_w, ys_w)


def _build_per_stock(sym, layer, market_cap, prices_dir, args, rf_annual, spy_full_ret,
                      generated_at):
    """Returns (entry_dict, full_ret_map[date->ret]). full_ret_map is {} if unusable."""
    warnings = []
    pf = prices_dir / f"{sym}.json"
    if not pf.exists():
        warnings.append(f"no price history file found for {sym}")
        return _null_stock_entry(sym, layer, market_cap, warnings), {}

    rec = _load_json(str(pf))
    if rec is None:
        warnings.append(f"no price history file found for {sym}")
        return _null_stock_entry(sym, layer, market_cap, warnings), {}

    series = rec.get("series") or []
    retrieved_at = rec.get("retrieved_at")
    if not series:
        warnings.append(f"empty price series for {sym}")
        entry = _null_stock_entry(sym, layer, market_cap, warnings)
        entry["prices_retrieved_at"] = retrieved_at
        return entry, {}

    valid_bars = _valid_bars(series)
    n_dropped = len(series) - len(valid_bars)
    if n_dropped > 0:
        warnings.append(f"{n_dropped} invalid closes dropped (non-finite/non-positive)")

    n_bars_total = len(series)
    last_price_date = valid_bars[-1]["date"] if valid_bars else None

    dcp = risk.day_change_pct(valid_bars)
    if dcp is None:
        warnings.append(f"day_change_pct: insufficient history (only {len(valid_bars)} "
                         f"bars, need >=2)")

    full_returns_list = risk.daily_returns(series)
    full_ret_map = {r["date"]: r["ret"] for r in full_returns_list}
    window_list = risk.trailing_window(full_returns_list, args.window)
    n_returns_window = len(window_list)
    window_vals = [r["ret"] for r in window_list]

    vol = var95 = var99 = sharpe = max_dd = beta_vs_spy = None

    if n_returns_window < args.min_bars:
        warnings.append(f"insufficient history: only {n_returns_window} return bars, "
                         f"need >={args.min_bars}")
    else:
        vol = risk.annualized_vol_pct(window_vals, PERIODS_PER_YEAR)
        var95 = risk.historical_var_pct(window_vals, 0.95)
        var99 = risk.historical_var_pct(window_vals, 0.99)
        if n_returns_window < 100:
            warnings.append(f"var99_1d_pct: only {n_returns_window} return bars — "
                             f"historical VaR tail estimate is noisy below 100 bars")
        sharpe = risk.sharpe_ratio(window_vals, rf_annual=rf_annual,
                                    periods_per_year=PERIODS_PER_YEAR)
        if sharpe is None and vol is not None:
            warnings.append("sharpe_1y: zero-variance return series, sharpe undefined")
        closes_window = [b["close"] for b in valid_bars[-(n_returns_window + 1):]]
        max_dd = risk.max_drawdown_pct(closes_window)
        beta_vs_spy = _compute_beta(full_ret_map, spy_full_ret, args.window,
                                     args.min_bars, warnings)

    if last_price_date:
        try:
            d = datetime.date.fromisoformat(last_price_date)
            age_days = (generated_at.date() - d).days
            if age_days > 7:
                warnings.append(f"prices: last bar is {age_days} days old (stale)")
        except ValueError:
            pass

    entry = {
        "symbol": sym, "layer": layer, "prices_retrieved_at": retrieved_at,
        "last_price_date": last_price_date, "n_bars_total": n_bars_total,
        "n_returns_window": n_returns_window, "day_change_pct": dcp,
        "vol_annualized_pct": vol, "var95_1d_pct": var95, "var99_1d_pct": var99,
        "sharpe_1y": sharpe, "max_drawdown_1y_pct": max_dd, "beta_vs_spy": beta_vs_spy,
        "market_cap": market_cap, "warnings": warnings,
    }
    return entry, full_ret_map


# --------------------------------------------------------------------------- per-layer


def _layer_entry(layer, constituents, per_stock_by_sym):
    n_constituents = len(constituents)
    entries = [per_stock_by_sym[s] for s in constituents if s in per_stock_by_sym]

    if layer == "L3-models":
        return {"layer": layer, "n_constituents": 0, "n_with_metrics": 0,
                **_EMPTY_LAYER_METRICS, "warnings": [L3_NO_TICKERS_WARNING]}

    with_metrics = [e for e in entries if e["vol_annualized_pct"] is not None]
    n_with_metrics = len(with_metrics)

    # day_change_pct needs only a fresh quote, not MIN_BARS of history — compute it
    # from ALL entries before (and independent of) the no-metrics short-circuit.
    dc_warnings = []
    dc_items = [{"value": e["day_change_pct"], "market_cap": e["market_cap"]}
                for e in entries if e["day_change_pct"] is not None]
    dc_val, dc_basis, dc_warn = _weighted_or_fallback(dc_items)
    if dc_warn:
        dc_warnings.append(f"day_change_pct: {dc_warn}")

    if n_with_metrics == 0:
        warnings = [] if n_constituents == 0 else \
            [f"{layer}: no constituents have usable risk metrics"]
        return {"layer": layer, "n_constituents": n_constituents,
                "n_with_metrics": 0, **_EMPTY_LAYER_METRICS,
                "day_change_pct": dc_val, "day_change_basis": dc_basis,
                "warnings": warnings + dc_warnings}

    warnings = list(dc_warnings)

    vol_items = [{"value": e["vol_annualized_pct"], "market_cap": e["market_cap"]}
                 for e in with_metrics]
    vol_eq = risk.mean([it["value"] for it in vol_items])
    vol_cap, vol_basis, vol_warn = _weighted_or_fallback(vol_items)
    if vol_warn:
        warnings.append(f"vol_cap_weighted_pct: {vol_warn}")

    var95_vals = [e["var95_1d_pct"] for e in with_metrics if e["var95_1d_pct"] is not None]
    var99_vals = [e["var99_1d_pct"] for e in with_metrics if e["var99_1d_pct"] is not None]
    median95 = statistics.median(var95_vals) if var95_vals else None
    median99 = statistics.median(var99_vals) if var99_vals else None

    worst_var95_symbol, worst_var95_val = _pick_extreme(with_metrics, "var95_1d_pct", True)
    best_sharpe_symbol, best_sharpe_val = _pick_extreme(with_metrics, "sharpe_1y", True)
    worst_sharpe_symbol, worst_sharpe_val = _pick_extreme(with_metrics, "sharpe_1y", False)
    worst_dd_symbol, worst_dd_val = _pick_extreme(with_metrics, "max_drawdown_1y_pct", False)

    return {
        "layer": layer, "n_constituents": n_constituents, "n_with_metrics": n_with_metrics,
        "day_change_pct": dc_val, "day_change_basis": dc_basis,
        "vol_equal_weighted_pct": vol_eq, "vol_cap_weighted_pct": vol_cap,
        "vol_cap_weighted_basis": vol_basis,
        "median_var95_1d_pct": median95, "median_var99_1d_pct": median99,
        "worst_var95_1d_pct": worst_var95_val, "worst_var95_symbol": worst_var95_symbol,
        "best_sharpe_symbol": best_sharpe_symbol, "best_sharpe_1y": best_sharpe_val,
        "worst_sharpe_symbol": worst_sharpe_symbol, "worst_sharpe_1y": worst_sharpe_val,
        "worst_drawdown_symbol": worst_dd_symbol, "worst_drawdown_1y_pct": worst_dd_val,
        "warnings": warnings,
    }


# --------------------------------------------------------------------------- correlations


def _build_layer_series(layer, layers_map, per_symbol_full_ret):
    members = L3_PROXY_MEMBERS if layer == "L3-models" else layers_map.get(layer, [])
    return risk.layer_return_series(per_symbol_full_ret, members)


def _build_correlations_layers(layers_map, per_symbol_full_ret, spy_full_ret, args):
    warnings = []
    candidate_series = {}
    for layer in LAYER_ORDER:
        s = _build_layer_series(layer, layers_map, per_symbol_full_ret)
        candidate_series[layer] = _windowed_map(s, args.window)
    candidate_series["SPY"] = _windowed_map(spy_full_ret, args.window) if spy_full_ret else {}

    order = []
    for name in LAYER_ORDER + ["SPY"]:
        n = len(candidate_series[name])
        if n >= args.min_bars:
            order.append(name)
        else:
            warnings.append(f"{name}: excluded from correlations.layers (own series has "
                             f"{n} return bars, need >={args.min_bars})")

    matrix = []
    for i, a in enumerate(order):
        row = []
        for j, b in enumerate(order):
            if i == j:
                row.append(1.0)
                continue
            xs, ys = risk.align_series(candidate_series[a], candidate_series[b])
            if len(xs) < args.min_bars:
                row.append(None)
                if i < j:
                    warnings.append(f"{a}/{b}: correlation cell null — overlap "
                                     f"{len(xs)} bars, need >={args.min_bars}")
                continue
            row.append(risk.pearson_correlation(xs, ys))
        matrix.append(row)

    return {
        "order": order, "matrix": matrix, "l3_models_note": L3_MODELS_NOTE,
        "window_trading_days": args.window, "min_overlap_days": args.min_bars,
        "warnings": warnings,
    }


def _rank_symbols_for_top_stocks(stocks, per_stock_by_sym):
    syms = list(stocks.keys())
    n_total = len(syms)

    def _cap(s):
        v = (per_stock_by_sym.get(s) or {}).get("market_cap")
        return v if isinstance(v, (int, float)) and not isinstance(v, bool) \
            and math.isfinite(v) and v > 0 else None

    n_with_cap = sum(1 for s in syms if _cap(s) is not None)
    if n_total > 0 and n_with_cap >= 0.5 * n_total:
        ranked = sorted(syms, key=lambda s: (0 if _cap(s) is not None else 1,
                                              -(_cap(s) or 0), s))
        return ranked, "market_cap"
    ranked = sorted(syms, key=lambda s: (
        -((per_stock_by_sym.get(s) or {}).get("n_returns_window") or 0), s))
    return ranked, "n_returns_window_fallback"


def _build_top_stocks(stocks, per_stock_by_sym, per_symbol_full_ret, args):
    order_candidates, ranked_by = _rank_symbols_for_top_stocks(stocks, per_stock_by_sym)

    admitted = []
    skipped = []
    candidate_series = {}
    considered = 0
    for sym in order_candidates:
        if len(admitted) >= args.correlation_top_n:
            break
        considered += 1
        wmap = _windowed_map(per_symbol_full_ret.get(sym) or {}, args.window)
        n = len(wmap)
        if n < args.min_bars:
            skipped.append({"symbol": sym,
                             "reason": f"insufficient history ({n} return bars, "
                                       f"need >={args.min_bars})"})
            continue
        admitted.append(sym)
        candidate_series[sym] = wmap

    matrix = []
    for a in admitted:
        row = []
        for b in admitted:
            if a == b:
                row.append(1.0)
                continue
            xs, ys = risk.align_series(candidate_series[a], candidate_series[b])
            if len(xs) < args.min_bars:
                row.append(None)
                continue
            row.append(risk.pearson_correlation(xs, ys))
        matrix.append(row)

    return {
        "order": admitted, "ranked_by": ranked_by, "matrix": matrix,
        "window_trading_days": args.window, "min_overlap_days": args.min_bars,
        "candidates_considered": considered, "candidates_skipped": skipped,
        "warnings": [],
    }


# --------------------------------------------------------------------------- headline


def _headline_worst_layer(per_layer_entries):
    candidates = [(e["layer"], e["day_change_pct"]) for e in per_layer_entries
                  if e["layer"] in LAYER_ORDER and e["day_change_pct"] is not None]
    if not candidates:
        return None
    worst_val = min(v for _, v in candidates)
    tied = sorted(l for l, v in candidates if v == worst_val)
    return {"layer": tied[0], "day_change_pct": worst_val}


def _headline_universe_var95(per_stock_entries):
    items = [{"value": e["var95_1d_pct"], "market_cap": e["market_cap"]}
             for e in per_stock_entries if e["var95_1d_pct"] is not None]
    val, _basis, _warn = _weighted_or_fallback(items)
    return val


def _headline_top_correlation_pair(layers_block):
    order = layers_block["order"]
    matrix = layers_block["matrix"]
    real = [(i, name) for i, name in enumerate(order) if name in LAYER_ORDER]
    best = None
    for x in range(len(real)):
        for y in range(x + 1, len(real)):
            i, a = real[x]
            j, b = real[y]
            val = matrix[i][j]
            if val is None:
                continue
            if best is None or abs(val) > abs(best[2]):
                best = (a, b, val)
    if best is None:
        return None
    return {"a": best[0], "b": best[1], "value": best[2]}


# --------------------------------------------------------------------------- top-level assembly


def _empty_layer_entry(layer):
    if layer == "L3-models":
        return {"layer": layer, "n_constituents": 0, "n_with_metrics": 0,
                **_EMPTY_LAYER_METRICS, "warnings": [L3_NO_TICKERS_WARNING]}
    return {"layer": layer, "n_constituents": 0, "n_with_metrics": 0,
            **_EMPTY_LAYER_METRICS, "warnings": []}


def _empty_bundle(generated_at, args, top_warning):
    return {
        "generated_at": _iso(generated_at),
        "schema_version": SCHEMA_VERSION,
        "source_class": SOURCE_CLASS,
        "disclaimer": DISCLAIMER,
        "params": {
            "risk_free_rate_annual": args.rf_annual,
            "risk_free_source": "cli-default",
            "window_trading_days": args.window,
            "min_bars": args.min_bars,
            "periods_per_year": PERIODS_PER_YEAR,
            "var_confidence_levels": VAR_CONFIDENCE_LEVELS,
            "correlation_top_n": args.correlation_top_n,
            "min_overlap_days": args.min_bars,
        },
        "prices_source": {"provider": PRICES_PROVIDER, "source_class": PRICES_SOURCE_CLASS,
                           "batch_retrieved_at": None},
        "benchmark_symbol": BENCHMARK,
        "universe": {"n_symbols_total": 0, "n_symbols_with_metrics": 0,
                     "layers": list(LAYER_ORDER)},
        "warnings": [top_warning],
        "per_stock": [],
        "per_layer": [_empty_layer_entry(l) for l in LAYER_ORDER],
        "correlations": {
            "layers": {"order": [], "matrix": [], "l3_models_note": L3_MODELS_NOTE,
                       "window_trading_days": args.window, "min_overlap_days": args.min_bars,
                       "warnings": []},
            "top_stocks": {"order": [], "ranked_by": "market_cap", "matrix": [],
                           "window_trading_days": args.window,
                           "min_overlap_days": args.min_bars,
                           "candidates_considered": 0, "candidates_skipped": [],
                           "warnings": []},
        },
        "headline": {"worst_layer": None, "universe_var95_1d_pct": None,
                     "top_correlation_pair": None},
    }


def _default_data_dir():
    repo = pathlib.Path(__file__).resolve().parent.parent
    return str(repo / "web" / "public" / "data")


def build_bundle(args):
    """Pure-ish assembly (reads local files, no network): returns the full risk.json dict."""
    generated_at = _utc_now()
    data_root = pathlib.Path(args.data)

    site = _load_json(str(data_root / "site.json"))
    if site is None:
        return _empty_bundle(generated_at, args, "site.json not found — risk universe empty")

    stocks = site.get("stocks") or {}
    layers_map = site.get("layers") or {}

    warnings = []

    # risk-free rate
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
        warnings.append("risk_free_rate_annual: graph_analysis.json unavailable, "
                         "using --rf-annual default")

    prices_dir = data_root / "prices"

    spy_rec = _load_json(str(prices_dir / "SPY.json"))
    spy_full_ret = {}
    spy_batch_retrieved_at = None
    if spy_rec:
        spy_batch_retrieved_at = spy_rec.get("retrieved_at")
        spy_series = spy_rec.get("series") or []
        spy_returns_list = risk.daily_returns(spy_series)
        spy_full_ret = {r["date"]: r["ret"] for r in spy_returns_list}
    else:
        warnings.append("benchmark: prices/SPY.json not found — beta_vs_spy unavailable "
                         "for all stocks, SPY excluded from correlations.layers")

    per_stock_entries = []
    per_symbol_full_ret = {}
    prices_batch_retrieved_at = None
    for sym, srec in stocks.items():
        layer = srec.get("layer")
        market_cap = ((srec.get("valuation") or {}).get("market_cap"))
        entry, full_ret_map = _build_per_stock(sym, layer, market_cap, prices_dir, args,
                                                rf_annual, spy_full_ret, generated_at)
        per_stock_entries.append(entry)
        per_symbol_full_ret[sym] = full_ret_map
        if prices_batch_retrieved_at is None and entry.get("prices_retrieved_at"):
            prices_batch_retrieved_at = entry["prices_retrieved_at"]

    if prices_batch_retrieved_at is None:
        prices_batch_retrieved_at = spy_batch_retrieved_at

    per_stock_by_sym = {e["symbol"]: e for e in per_stock_entries}

    per_layer_entries = [_layer_entry(layer, layers_map.get(layer, []), per_stock_by_sym)
                          for layer in LAYER_ORDER]

    corr_layers = _build_correlations_layers(layers_map, per_symbol_full_ret, spy_full_ret, args)
    corr_top = _build_top_stocks(stocks, per_stock_by_sym, per_symbol_full_ret, args)

    headline = {
        "worst_layer": _headline_worst_layer(per_layer_entries),
        "universe_var95_1d_pct": _headline_universe_var95(per_stock_entries),
        "top_correlation_pair": _headline_top_correlation_pair(corr_layers),
    }

    n_with_metrics = sum(1 for e in per_stock_entries if e["vol_annualized_pct"] is not None)

    bundle = {
        "generated_at": _iso(generated_at),
        "schema_version": SCHEMA_VERSION,
        "source_class": SOURCE_CLASS,
        "disclaimer": DISCLAIMER,
        "params": {
            "risk_free_rate_annual": rf_annual,
            "risk_free_source": rf_source,
            "window_trading_days": args.window,
            "min_bars": args.min_bars,
            "periods_per_year": PERIODS_PER_YEAR,
            "var_confidence_levels": VAR_CONFIDENCE_LEVELS,
            "correlation_top_n": args.correlation_top_n,
            "min_overlap_days": args.min_bars,
        },
        "prices_source": {"provider": PRICES_PROVIDER, "source_class": PRICES_SOURCE_CLASS,
                           "batch_retrieved_at": prices_batch_retrieved_at},
        "benchmark_symbol": BENCHMARK,
        "universe": {"n_symbols_total": len(stocks), "n_symbols_with_metrics": n_with_metrics,
                     "layers": list(LAYER_ORDER)},
        "warnings": warnings,
        "per_stock": per_stock_entries,
        "per_layer": per_layer_entries,
        "correlations": {"layers": corr_layers, "top_stocks": corr_top},
        "headline": headline,
    }
    return bundle


def _default_out_path():
    repo = pathlib.Path(__file__).resolve().parent.parent
    return str(repo / "web" / "public" / "data" / "risk.json")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Assemble risk.json from already-retrieved local files (no network).")
    ap.add_argument("--data", default=_default_data_dir(),
                    help="Root data dir containing site.json + prices/ (default: web/public/data).")
    ap.add_argument("--out", default=_default_out_path(),
                    help="Output path (default: web/public/data/risk.json).")
    ap.add_argument("--rf-annual", type=float, default=0.04,
                    help="Fallback annual risk-free rate if graph_analysis.json unavailable.")
    ap.add_argument("--window", type=int, default=252, help="Trailing return window (days).")
    ap.add_argument("--min-bars", type=int, default=60,
                    help="Minimum return bars required to compute risk stats.")
    ap.add_argument("--correlation-top-n", type=int, default=15,
                    help="Max stocks ranked for correlations.top_stocks.")
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

    n_total = bundle["universe"]["n_symbols_total"]
    n_ok = bundle["universe"]["n_symbols_with_metrics"]
    print(f"risk: {n_ok}/{n_total} symbols with metrics -> {out_path}")
    print(f"  warnings: {len(bundle.get('warnings', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
