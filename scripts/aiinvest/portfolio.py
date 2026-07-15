"""Pure portfolio-desk computations (owner positions -> exposure/P&L/risk).

Zero HTTP, zero I/O — every function here is a pure transform over plain dicts/lists/
floats, unit-tested in isolation (see tests/test_portfolio.py). `build_portfolio.py` is
the thin network-free assembly layer that reads already-retrieved local JSON
(data/portfolio/positions.json, web/public/data/site.json,
web/public/data/prices/<SYM>.json) and calls these. See
docs/superpowers/specs/2026-07-15-portfolio-design.md for the binding portfolio.json v1
contract these functions feed.

Vol/VaR/Sharpe/drawdown/beta/correlation/day-change math is NEVER reimplemented here —
every one of those calls straight into `aiinvest.risk` (see `compute_risk` /
`build_portfolio_return_series` / `top_pairwise_correlation`). This module only handles
portfolio-specific glue: validation, lot merging, price resolution, weighting, and
building the synthetic weighted return series that gets fed into risk.py.
"""
from __future__ import annotations

import datetime
import math

from aiinvest import risk

LAYER_ORDER = ["L0-energy", "L1-chips", "L2-infra", "L3-models", "L4-application"]

METHODOLOGY_NOTE = (
    "This portfolio return series applies TODAY'S position weights to each holding's OWN "
    "historical daily-return series ('fixed-weight, as-if-held-at-current-composition' "
    "proxy) — it is NOT a reconstruction of the account's actual historical share counts "
    "or cost basis (true buy-and-hold). Past vol/VaR/Sharpe/beta therefore show what the "
    "CURRENT portfolio composition would have earned or lost historically, not what this "
    "account actually experienced while positions were being built up over time. Cash and "
    "any holding lacking sufficient price history are excluded from the series (see "
    "series_coverage), which is a further departure from the literal book — check "
    "weight_coverage_pct before trusting these numbers on a thin-history portfolio."
)


def _is_finite_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


# --------------------------------------------------------------------------- top-level validation


def validate_base_currency(raw):
    """-> (base_currency, warning_or_None). Only USD supported (no FX in v1)."""
    if raw is None or str(raw).strip() == "":
        return "USD", None
    s = str(raw).strip().upper()
    if s != "USD":
        return "USD", "base_currency: only USD supported, treating as USD"
    return "USD", None


def validate_cash_usd(raw):
    """-> (cash_usd, warning_or_None). Defaults 0.0; negative/invalid clamped to 0.0."""
    if raw is None:
        return 0.0, None
    if not _is_finite_number(raw) or raw < 0:
        return 0.0, "cash_usd: invalid/negative, treated as 0"
    return float(raw), None


# --------------------------------------------------------------------------- row validation / merge


def validate_positions(raw_positions):
    """[{symbol, quantity, cost_basis_per_share, acquired_date, note}, ...] (raw, owner-
    edited) -> (clean_rows, warnings).

    clean_rows: kept rows only, each a dict {symbol, quantity, cost_basis_per_share,
    acquired_date, note, warnings} where `warnings` is that ROW's own issues (e.g. missing
    cost basis) — carried forward through merge_lots/compute_position into the final
    position's warnings array.

    warnings: batch-level list — currently just the DROP reasons (a dropped row has no
    surviving position to attach its warning to, so it goes here instead).
    """
    clean_rows = []
    drop_warnings = []
    for i, row in enumerate(raw_positions or []):
        if not isinstance(row, dict):
            drop_warnings.append(f"row {i}: not an object, dropped")
            continue

        raw_symbol = row.get("symbol")
        symbol = str(raw_symbol).strip().upper() if raw_symbol is not None else ""
        if not symbol:
            drop_warnings.append(f"row {i}: missing/empty symbol, dropped")
            continue

        raw_qty = row.get("quantity")
        if not _is_finite_number(raw_qty) or raw_qty <= 0:
            drop_warnings.append(f"{symbol}: quantity <= 0 or non-numeric, row dropped")
            continue
        quantity = float(raw_qty)

        row_warnings = []

        raw_cb = row.get("cost_basis_per_share")
        cost_basis_per_share = None
        if raw_cb is not None and _is_finite_number(raw_cb) and raw_cb > 0:
            cost_basis_per_share = float(raw_cb)
        else:
            row_warnings.append(
                f"{symbol}: cost_basis_per_share missing/invalid — P&L unavailable for this lot")

        raw_date = row.get("acquired_date")
        acquired_date = None
        if raw_date is not None and str(raw_date).strip():
            try:
                datetime.date.fromisoformat(str(raw_date).strip())
                acquired_date = str(raw_date).strip()
            except ValueError:
                row_warnings.append(f"{symbol}: acquired_date invalid, treated as unknown")

        raw_note = row.get("note")
        note = str(raw_note)[:280] if raw_note is not None and str(raw_note).strip() else None

        clean_rows.append({
            "symbol": symbol, "quantity": quantity,
            "cost_basis_per_share": cost_basis_per_share,
            "acquired_date": acquired_date, "note": note,
            "warnings": row_warnings,
        })

    return clean_rows, drop_warnings


def merge_lots(clean_rows):
    """Merge rows sharing a symbol into one per-symbol position (§1 lot-merge rules)."""
    order = []
    groups = {}
    for row in clean_rows:
        sym = row["symbol"]
        if sym not in groups:
            groups[sym] = []
            order.append(sym)
        groups[sym].append(row)

    merged = []
    for sym in order:
        lots = groups[sym]
        quantity = sum(l["quantity"] for l in lots)

        cb_lots = [l for l in lots if l["cost_basis_per_share"] is not None]
        if cb_lots:
            total_cb_qty = sum(l["quantity"] for l in cb_lots)
            cost_basis_per_share = (
                sum(l["quantity"] * l["cost_basis_per_share"] for l in cb_lots) / total_cb_qty
            )
        else:
            cost_basis_per_share = None

        dates = [l["acquired_date"] for l in lots if l["acquired_date"]]
        acquired_date = min(dates) if dates else None

        notes = [l["note"] for l in lots if l["note"]]
        note = "; ".join(notes) if notes else None

        warnings = []
        for l in lots:
            warnings.extend(l["warnings"])
        lots_merged = len(lots)
        if lots_merged > 1:
            warnings.append(f"{sym}: {lots_merged} lots merged")

        merged.append({
            "symbol": sym, "quantity": quantity, "lots_merged": lots_merged,
            "cost_basis_per_share": cost_basis_per_share, "acquired_date": acquired_date,
            "note": note, "warnings": warnings,
        })
    return merged


# --------------------------------------------------------------------------- price resolution


def _valid_bars(series):
    """[{"date","close"}, ...] filtered to finite, positive closes only (mirrors
    build_risk.py's _valid_bars; duplicated locally since this module is zero-I/O and not
    a cross-import target)."""
    out = []
    for b in series or []:
        c = b.get("close")
        if _is_finite_number(c) and c > 0:
            out.append({"date": b.get("date"), "close": float(c)})
    return out


def resolve_price(symbol, prices_json_or_None, site_stock_or_None):
    """3-tier fallback (§2): prices_file > site_json_fallback > None.

    Returns PriceInfo: {last_price, price_as_of, price_source, prev_close}.
    """
    if prices_json_or_None:
        series = prices_json_or_None.get("series") or []
        valid = _valid_bars(series)
        if valid:
            last = valid[-1]
            prev_close = valid[-2]["close"] if len(valid) >= 2 else None
            return {"last_price": last["close"], "price_as_of": last["date"],
                    "price_source": "prices_file", "prev_close": prev_close}

    if site_stock_or_None:
        val = site_stock_or_None.get("valuation") or {}
        price = val.get("price")
        if _is_finite_number(price) and price > 0:
            return {"last_price": float(price),
                    "price_as_of": site_stock_or_None.get("as_of"),
                    "price_source": "site_json_fallback", "prev_close": None}

    return {"last_price": None, "price_as_of": None, "price_source": None, "prev_close": None}


# --------------------------------------------------------------------------- per-position


def compute_position(merged_row, price_info, layer, total_value_usd):
    """merged_row (from merge_lots) + price_info (from resolve_price) + layer +
    total_value_usd (portfolio total INCLUDING cash) -> the final position dict (§2)."""
    symbol = merged_row["symbol"]
    quantity = merged_row["quantity"]
    cost_basis_per_share = merged_row.get("cost_basis_per_share")
    cost_basis_total_usd = (
        quantity * cost_basis_per_share if cost_basis_per_share is not None else None
    )

    last_price = price_info.get("last_price")
    price_as_of = price_info.get("price_as_of")
    price_source = price_info.get("price_source")
    prev_close = price_info.get("prev_close")

    market_value_usd = quantity * last_price if last_price is not None else None
    weight_pct = (
        market_value_usd / total_value_usd * 100
        if market_value_usd is not None and total_value_usd else None
    )
    unrealized_pnl_usd = (
        market_value_usd - cost_basis_total_usd
        if market_value_usd is not None and cost_basis_total_usd is not None else None
    )
    unrealized_pnl_pct = (
        unrealized_pnl_usd / cost_basis_total_usd * 100
        if unrealized_pnl_usd is not None and cost_basis_total_usd else None
    )

    day_change_pct = None
    day_change_usd = None
    if price_source == "prices_file" and last_price is not None and prev_close is not None:
        # REUSE risk.day_change_pct verbatim — never reimplement.
        day_change_pct = risk.day_change_pct([{"close": prev_close}, {"close": last_price}])
        # day_change_usd is quantity*(last-prev), NOT market_value_usd*day_change_pct/100:
        # market_value_usd is priced at TODAY's close while day_change_pct is relative to
        # YESTERDAY's close — they don't compose multiplicatively (see Fixture C).
        day_change_usd = quantity * (last_price - prev_close)

    warnings = list(merged_row.get("warnings", []))
    if last_price is None:
        warnings.append(
            f"{symbol}: no price data available (not in AI-stack universe, no price "
            f"file) — excluded from valued aggregates")
    elif price_source == "site_json_fallback":
        warnings.append(
            f"{symbol}: no price history file, using latest site.json quote (no "
            f"day-change, excluded from risk series)")

    return {
        "symbol": symbol, "quantity": quantity, "lots_merged": merged_row.get("lots_merged", 1),
        "cost_basis_per_share": cost_basis_per_share, "cost_basis_total_usd": cost_basis_total_usd,
        "acquired_date": merged_row.get("acquired_date"), "note": merged_row.get("note"),
        "layer": layer, "last_price": last_price, "price_as_of": price_as_of,
        "price_source": price_source, "market_value_usd": market_value_usd,
        "weight_pct": weight_pct, "unrealized_pnl_usd": unrealized_pnl_usd,
        "unrealized_pnl_pct": unrealized_pnl_pct, "day_change_pct": day_change_pct,
        "day_change_usd": day_change_usd, "warnings": warnings,
    }


# --------------------------------------------------------------------------- aggregates


def compute_aggregates(positions, cash_usd):
    """positions: list of compute_position() dicts. -> aggregates dict (§3)."""
    priced = [p for p in positions if p["market_value_usd"] is not None]
    invested_value_usd = float(sum(p["market_value_usd"] for p in priced))
    total_value_usd = cash_usd + invested_value_usd
    cash_weight_pct = cash_usd / total_value_usd * 100 if total_value_usd else None

    cost_subset = [p for p in priced if p["cost_basis_total_usd"] is not None]
    if cost_subset:
        total_cost_basis_usd = sum(p["cost_basis_total_usd"] for p in cost_subset)
        total_unrealized_pnl_usd = sum(p["unrealized_pnl_usd"] for p in cost_subset)
        total_unrealized_pnl_pct = (
            total_unrealized_pnl_usd / total_cost_basis_usd * 100
            if total_cost_basis_usd else None
        )
    else:
        total_cost_basis_usd = None
        total_unrealized_pnl_usd = None
        total_unrealized_pnl_pct = None

    day_subset = [p for p in priced if p["day_change_usd"] is not None]
    if day_subset:
        day_pnl_usd = sum(p["day_change_usd"] for p in day_subset)
        denom = total_value_usd - day_pnl_usd
        day_pnl_pct = day_pnl_usd / denom * 100 if denom else None
    else:
        day_pnl_usd = None
        day_pnl_pct = None

    n_positions = len(positions)
    n_positions_priced = len(priced)
    n_positions_unpriced = n_positions - n_positions_priced

    buckets = {layer: {"mv": 0.0, "n": 0} for layer in LAYER_ORDER}
    buckets["unclassified"] = {"mv": 0.0, "n": 0}
    for p in priced:
        key = p.get("layer") if p.get("layer") in buckets else "unclassified"
        buckets[key]["mv"] += p["market_value_usd"]
        buckets[key]["n"] += 1

    layer_exposure = []
    for key in LAYER_ORDER + ["unclassified"]:
        mv = buckets[key]["mv"]
        wt = mv / total_value_usd * 100 if total_value_usd else 0.0
        layer_exposure.append({"layer": key, "weight_pct": wt, "market_value_usd": mv,
                                "n_positions": buckets[key]["n"]})
    layer_exposure.append({
        "layer": "cash", "weight_pct": cash_weight_pct if cash_weight_pct is not None else 0.0,
        "market_value_usd": cash_usd, "n_positions": 0,
    })

    if priced and invested_value_usd:
        sorted_mv = sorted((p["market_value_usd"] for p in priced), reverse=True)
        top1_weight_pct = sorted_mv[0] / invested_value_usd * 100
        top3_weight_pct = sum(sorted_mv[:3]) / invested_value_usd * 100
        hhi = sum((mv / invested_value_usd) ** 2 for mv in sorted_mv)
    else:
        top1_weight_pct = None
        top3_weight_pct = None
        hhi = None
    concentration = {"top1_weight_pct": top1_weight_pct, "top3_weight_pct": top3_weight_pct,
                      "hhi": hhi, "basis": "invested_value_excluding_cash"}

    return {
        "total_value_usd": total_value_usd, "invested_value_usd": invested_value_usd,
        "cash_usd": cash_usd, "cash_weight_pct": cash_weight_pct,
        "total_cost_basis_usd": total_cost_basis_usd,
        "total_unrealized_pnl_usd": total_unrealized_pnl_usd,
        "total_unrealized_pnl_pct": total_unrealized_pnl_pct,
        "day_pnl_usd": day_pnl_usd, "day_pnl_pct": day_pnl_pct,
        "n_positions": n_positions, "n_positions_priced": n_positions_priced,
        "n_positions_unpriced": n_positions_unpriced,
        "layer_exposure": layer_exposure, "concentration": concentration,
    }


# --------------------------------------------------------------------------- risk series


def _windowed_map(ret_map, window):
    """dict[date->ret] -> dict restricted to its own last `window` dates (by date).
    Mirrors build_risk.py's private _windowed_map helper."""
    items = sorted((ret_map or {}).items())
    if len(items) > window:
        items = items[-window:]
    return dict(items)


def _classify_eligibility(positions, per_symbol_full_ret, window, min_bars):
    """-> (eligible: [{"symbol","market_value_usd","ret_map"}], excluded: [{"symbol","reason"}]).

    Eligible = priced, price_source=="prices_file", >=min_bars return bars in the
    trailing window. Positions with no market value at all (unpriced) are not part of
    this reckoning (they were never "priced" to begin with)."""
    eligible = []
    excluded = []
    for p in positions:
        if p.get("market_value_usd") is None:
            continue
        sym = p["symbol"]
        if p.get("price_source") != "prices_file":
            excluded.append({"symbol": sym,
                              "reason": "no price history file (site_json_fallback only)"})
            continue
        windowed = _windowed_map(per_symbol_full_ret.get(sym), window)
        n = len(windowed)
        if n < min_bars:
            excluded.append({"symbol": sym,
                              "reason": f"insufficient history ({n} bars, need >={min_bars})"})
            continue
        eligible.append({"symbol": sym, "market_value_usd": p["market_value_usd"],
                          "ret_map": windowed})
    return eligible, excluded


def build_portfolio_return_series(positions, per_symbol_full_ret, window=risk.WINDOW,
                                   min_bars=risk.MIN_BARS):
    """-> (window_vals, dates, included, coverage_pct). §4: renormalized weights within the
    included set S, combined ONLY over the intersection of dates common to all of S."""
    eligible, _excluded = _classify_eligibility(positions, per_symbol_full_ret, window, min_bars)

    total_priced_mv = sum(p["market_value_usd"] for p in positions
                           if p.get("market_value_usd") is not None)

    if not eligible:
        return [], [], [], 0.0

    included_mv = sum(e["market_value_usd"] for e in eligible)
    coverage_pct = included_mv / total_priced_mv * 100 if total_priced_mv else 0.0
    weights = {e["symbol"]: e["market_value_usd"] / included_mv for e in eligible}

    common_dates = set(eligible[0]["ret_map"].keys())
    for e in eligible[1:]:
        common_dates &= set(e["ret_map"].keys())
    dates = sorted(common_dates)

    window_vals = [
        sum(weights[e["symbol"]] * e["ret_map"][d] for e in eligible)
        for d in dates
    ]
    included = [e["symbol"] for e in eligible]
    return window_vals, dates, included, coverage_pct


def top_pairwise_correlation(included_symbols_by_weight_desc, per_symbol_full_ret, top_n,
                              window=risk.WINDOW, min_bars=risk.MIN_BARS):
    """Among the top-N (by weight) included symbols, the max-|correlation| pair (tie-break
    alphabetical). None if fewer than 2 candidates or no pair has enough overlap."""
    candidates = list(included_symbols_by_weight_desc)[:top_n]
    if len(candidates) < 2:
        return None

    best = None  # (a, b, value) with a<b alphabetically
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            sym_a, sym_b = candidates[i], candidates[j]
            wa = _windowed_map(per_symbol_full_ret.get(sym_a), window)
            wb = _windowed_map(per_symbol_full_ret.get(sym_b), window)
            xs, ys = risk.align_series(wa, wb)
            if len(xs) < min_bars:
                continue
            val = risk.pearson_correlation(xs, ys)
            if val is None:
                continue
            a, b = sorted([sym_a, sym_b])
            if best is None or abs(val) > abs(best[2]) or (
                    math.isclose(abs(val), abs(best[2]), abs_tol=1e-12) and (a, b) < (best[0], best[1])):
                best = (a, b, val)
    if best is None:
        return None
    return {"a": best[0], "b": best[1], "value": best[2]}


def compute_risk(positions, per_symbol_full_ret, spy_full_ret, rf_annual,
                  window=risk.WINDOW, min_bars=risk.MIN_BARS, top_n_correlation=5,
                  var_confidence=0.95, periods_per_year=252):
    """§4: build the weighted synthetic series and feed it straight into risk.py's
    existing functions. -> risk dict (null-filled + one warning if |S|==0)."""
    eligible, excluded = _classify_eligibility(positions, per_symbol_full_ret, window, min_bars)
    n_priced = sum(1 for p in positions if p.get("market_value_usd") is not None)

    if not eligible:
        return {
            "vol_annualized_pct": None, "var95_1d_pct": None, "sharpe_1y": None,
            "beta_vs_spy": None, "max_pairwise_correlation": None,
            "series_coverage": {"n_holdings_included": 0, "n_holdings_total_priced": n_priced,
                                 "weight_coverage_pct": 0.0, "excluded": excluded},
            "methodology_note": METHODOLOGY_NOTE,
            "warnings": [f"no holdings have sufficient price history for a risk series "
                         f"(need >={min_bars} return bars each)"],
        }

    window_vals, dates, included, coverage_pct = build_portfolio_return_series(
        positions, per_symbol_full_ret, window, min_bars)

    warnings = []

    vol = risk.annualized_vol_pct(window_vals, periods_per_year)
    var95 = risk.historical_var_pct(window_vals, var_confidence)
    sharpe = risk.sharpe_ratio(window_vals, rf_annual=rf_annual, periods_per_year=periods_per_year)
    if sharpe is None and vol is not None:
        warnings.append("sharpe_1y: zero-variance return series, sharpe undefined")

    beta_vs_spy = None
    if spy_full_ret:
        portfolio_ret_map = dict(zip(dates, window_vals))
        spy_windowed = _windowed_map(spy_full_ret, window)
        xs, ys = risk.align_series(portfolio_ret_map, spy_windowed)
        if len(xs) >= min_bars:
            beta_vs_spy = risk.beta(xs, ys)
        else:
            warnings.append(f"beta_vs_spy: insufficient aligned overlap with SPY "
                             f"(n={len(xs)}, need >={min_bars})")
    else:
        warnings.append("beta_vs_spy: SPY price history unavailable")

    mv_by_symbol = {p["symbol"]: p["market_value_usd"] for p in positions}
    included_by_weight = sorted(included, key=lambda s: (-(mv_by_symbol.get(s) or 0), s))
    max_pairwise_correlation = top_pairwise_correlation(
        included_by_weight, per_symbol_full_ret, top_n_correlation, window, min_bars)

    if coverage_pct < 80:
        warnings.append(
            f"risk series covers only {coverage_pct:.1f}% of invested value by weight — "
            f"treat vol/VaR/Sharpe/beta as indicative only")

    series_coverage = {"n_holdings_included": len(included), "n_holdings_total_priced": n_priced,
                        "weight_coverage_pct": coverage_pct, "excluded": excluded}

    return {
        "vol_annualized_pct": vol, "var95_1d_pct": var95, "sharpe_1y": sharpe,
        "beta_vs_spy": beta_vs_spy, "max_pairwise_correlation": max_pairwise_correlation,
        "series_coverage": series_coverage, "methodology_note": METHODOLOGY_NOTE,
        "warnings": warnings,
    }
