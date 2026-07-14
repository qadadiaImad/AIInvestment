"""Pull TA-desk data for the 11-instrument FX/METALS/ENERGY/INDEX universe.

REST-first, no browser anywhere (Yahoo keyless chart API only — CLAUDE.md §3). Two
Yahoo chart fetches per instrument (daily 1y/1d, intraday 1mo/60m); every indicator/level
is computed locally in aiinvest/ta.py from those two series. Writes the flat, one-stamp-
per-instrument bundle to web/public/data/ta_desk.json — see
docs/superpowers/specs/undefined-ta-terminal-design.md for the binding contract.

Usage:
    python pull_ta.py                       # whole 11-instrument universe
    python pull_ta.py --symbols EURUSD,GOLD # restrict to a subset (debugging)
    python pull_ta.py --out /tmp/ta_desk.json
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime
import json
import math
import pathlib

from aiinvest import price_history, ta

SCHEMA_VERSION = "ta-desk-v1"
SOURCE = "yahoo-finance-chart-api"
SOURCE_CLASS = "api"
DISCLAIMER = ("Educational research only — not financial advice. Levels are computed, "
              "not predictive.")

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
_DIRTY_STRINGS = {"", ".", "-", "--", "n/a", "na", "none", "null"}

_EMPTY_PIVOTS = {"basis_date": None, "pp": None, "r1": None, "r2": None, "r3": None,
                  "s1": None, "s2": None, "s3": None}
_EMPTY_PREV_DAY = {"date": None, "open": None, "high": None, "low": None, "close": None,
                    "change_pct": None}
_EMPTY_ATR_BANDS = {"upper_1x": None, "lower_1x": None, "upper_2x": None, "lower_2x": None}


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_symbol_bars(yahoo_symbol, session=None):
    """GET daily(1y/1d) + intraday(1mo/60m) chart payloads for one Yahoo symbol.

    Returns (daily_bars, intraday_bars, intraday_ok, daily_url, intraday_url).
    A failed intraday fetch does NOT raise — it's a documented, warned fallback (last
    price falls back to the last daily close). A failed DAILY fetch DOES raise: without
    daily history nothing in the contract is computable.
    """
    import requests
    http = session or requests
    headers = {"User-Agent": _UA}

    daily_url = price_history.chart_url(yahoo_symbol, range="1y", interval="1d")
    daily_resp = http.get(daily_url, headers=headers, timeout=25)
    daily_resp.raise_for_status()
    daily_bars = price_history.parse_chart_ohlc(daily_resp.json(), intraday=False)

    intraday_url = price_history.chart_url(yahoo_symbol, range="1mo", interval="60m")
    intraday_bars, intraday_ok = [], True
    try:
        intraday_resp = http.get(intraday_url, headers=headers, timeout=25)
        intraday_resp.raise_for_status()
        intraday_bars = price_history.parse_chart_ohlc(intraday_resp.json(), intraday=True)
    except Exception:  # noqa: BLE001 — intraday failure is a warned fallback, not fatal
        intraday_ok = False

    return daily_bars, intraday_bars, intraday_ok, daily_url, intraday_url


def build_instrument(symbol, meta, daily_bars, intraday_bars, intraday_ok, daily_url,
                      intraday_url, retrieved_at, generated_at):
    """Assemble one flat instrument record matching the ta_desk.json v1 contract.

    Every uncomputable value is explicit `null` plus a human-readable entry in
    `warnings` — never a silently-omitted key, never a fake number.
    """
    warnings = []
    closes = [b["close"] for b in daily_bars]
    n_daily = len(daily_bars)

    if intraday_bars:
        last = intraday_bars[-1]["close"]
    elif daily_bars:
        last = daily_bars[-1]["close"]
        reason = "intraday fetch failed" if not intraday_ok else "intraday series empty"
        warnings.append(f"price.last: {reason}, fell back to last daily close")
    else:
        last = None
        warnings.append("price.last: no daily or intraday data available")

    as_of_date = generated_at.date().isoformat()
    prev_bar = ta.daily_pivots_basis(daily_bars, as_of_date=as_of_date)
    previous_close = prev_bar["close"] if prev_bar else None
    if prev_bar is None:
        warnings.append("price.previous_close: insufficient daily history "
                         f"(only {n_daily} daily bars)")

    day_change_pct = ta.day_change_pct(last, previous_close) if last is not None else None
    day_change_abs = (last - previous_close) if (last is not None and previous_close is not None) else None

    sma20 = ta.sma(closes, 20)
    sma50 = ta.sma(closes, 50)
    sma200 = ta.sma(closes, 200)
    for name, val, period in (("sma20", sma20, 20), ("sma50", sma50, 50), ("sma200", sma200, 200)):
        if val is None:
            warnings.append(f"{name}: insufficient history (only {n_daily} daily bars, need {period})")
    if last is not None:
        trend = ta.trend_state(last, sma20, sma50, sma200)
    else:
        trend = {"state": "unknown", "price_above_sma20": None, "price_above_sma50": None,
                 "price_above_sma200": None, "sma50_above_sma200": None}
        warnings.append("trend.state: unknown (no last price)")
    trend = {**trend, "sma20": sma20, "sma50": sma50, "sma200": sma200}

    rsi_value = ta.rsi(closes, 14)
    if rsi_value is None:
        warnings.append(f"rsi14: insufficient history (only {n_daily} daily bars)")
    rsi_block = {"value": rsi_value, "state": ta.rsi_state(rsi_value)}

    atr_value = ta.atr(daily_bars, 14)
    if atr_value is None:
        warnings.append(f"atr14: insufficient history (only {n_daily} daily bars)")
    bands = ta.atr_bands(last, atr_value) if (atr_value is not None and last is not None) else None
    atr_block = {"value": atr_value, **(bands or _EMPTY_ATR_BANDS)}

    pivots = ta.classic_pivots(prev_bar["high"], prev_bar["low"], prev_bar["close"]) if prev_bar else None
    if pivots is None:
        warnings.append("levels.daily_pivots: insufficient daily history")
        daily_pivots = dict(_EMPTY_PIVOTS)
    else:
        daily_pivots = {"basis_date": prev_bar["date"], **pivots}

    prev_day = ta.previous_day_ohlc(daily_bars, as_of_date=as_of_date)
    if prev_day is None:
        warnings.append("levels.previous_day_ohlc: insufficient daily history")
        previous_day_ohlc = dict(_EMPTY_PREV_DAY)
    else:
        previous_day_ohlc = prev_day

    if daily_bars and last is not None:
        fifty_two_week = ta.fifty_two_week_stats(daily_bars, last)
    else:
        fifty_two_week = {"high": None, "low": None, "position_pct": None}
        warnings.append("levels.fifty_two_week: no daily data / no last price")

    nearest = ta.nearest_level(last, pivots) if (pivots and last is not None) else None

    if intraday_bars:
        sessions = ta.session_ranges(intraday_bars, as_of=generated_at)
    else:
        sessions = {"date": generated_at.date().isoformat()}
        sessions.update({
            name: {"window_utc": f"{s:02d}:00-{e:02d}:00", "high": None, "low": None,
                   "bar_count": 0, "complete": generated_at.hour >= e}
            for name, (s, e) in ta.SESSION_WINDOWS_UTC.items()
        })
        warnings.append("sessions: no intraday data available")

    sparkline = ta.sparkline_from_intraday(intraday_bars, 48) if intraday_bars else []

    return {
        "symbol": symbol,
        "display_name": meta["display_name"],
        "asset_class": meta["asset_class"],
        "group": meta["group"],
        "yahoo_symbol": meta["yahoo_symbol"],
        "tv_symbol": meta["tv_symbol"],
        "retrieved_at": retrieved_at,
        "source_url_daily": daily_url,
        "source_url_intraday": intraday_url,
        "price": {
            "last": last, "previous_close": previous_close,
            "day_change_pct": day_change_pct, "day_change_abs": day_change_abs,
        },
        "trend": trend,
        "rsi14": rsi_block,
        "atr14": atr_block,
        "levels": {
            "daily_pivots": daily_pivots,
            "previous_day_ohlc": previous_day_ohlc,
            "fifty_two_week": fifty_two_week,
        },
        "nearest_level": nearest,
        "sessions": sessions,
        "sparkline": sparkline,
        "warnings": warnings,
    }


def _one(symbol, meta, generated_at, session=None):
    try:
        daily_bars, intraday_bars, intraday_ok, daily_url, intraday_url = fetch_symbol_bars(
            meta["yahoo_symbol"], session=session)
    except Exception as e:  # noqa: BLE001
        return symbol, None, str(e)
    if not daily_bars:
        return symbol, None, "empty daily series"
    retrieved_at = _iso(_utc_now())
    inst = build_instrument(symbol, meta, daily_bars, intraday_bars, intraday_ok,
                             daily_url, intraday_url, retrieved_at, generated_at)
    return symbol, inst, None


def _walk_numeric_problems(obj, path):
    """Recursively validate: every number finite or None; reject dirty sentinel strings
    (mirrors schema.py's dirty-value doctrine even though this feed skips per-leaf
    envelopes)."""
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


def validate_instrument(inst):
    problems = _walk_numeric_problems(inst, inst.get("symbol", "?"))
    rsi_v = inst["rsi14"]["value"]
    if rsi_v is not None and not (0 <= rsi_v <= 100):
        problems.append(f"rsi14.value out of [0,100]: {rsi_v}")
    pos = inst["levels"]["fifty_two_week"]["position_pct"]
    if pos is not None and not (0 <= pos <= 100):
        problems.append(f"fifty_two_week.position_pct out of [0,100]: {pos}")
    return problems


def build_bundle(instruments, generated_at):
    return {
        "generated_at": _iso(generated_at),
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "source_class": SOURCE_CLASS,
        "disclaimer": DISCLAIMER,
        "groups": list(ta.GROUPS),
        "instruments": instruments,
    }


def _default_out_path():
    repo = pathlib.Path(__file__).resolve().parent.parent
    return str(repo / "web" / "public" / "data" / "ta_desk.json")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Pull TA-desk data (Yahoo keyless chart REST, no browser).")
    ap.add_argument("--symbols", help="Comma-separated subset of ta.UNIVERSE symbols (debug).")
    ap.add_argument("--out", default=_default_out_path(),
                    help="Output path (default: web/public/data/ta_desk.json).")
    ap.add_argument("--max-workers", type=int, default=4)
    args = ap.parse_args(argv)

    universe = ta.UNIVERSE
    if args.symbols:
        wanted = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
        unknown = [s for s in wanted if s not in ta.UNIVERSE]
        if unknown:
            print(f"  unknown symbols ignored: {unknown}")
        universe = {s: ta.UNIVERSE[s] for s in wanted if s in ta.UNIVERSE}

    generated_at = _utc_now()
    order = {s: i for i, s in enumerate(universe)}
    results, fail = [], []

    with cf.ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = {ex.submit(_one, sym, meta, generated_at): sym for sym, meta in universe.items()}
        for fut in cf.as_completed(futs):
            sym, inst, err = fut.result()
            if err:
                fail.append(f"{sym}: {err}")
                continue
            problems = validate_instrument(inst)
            if problems:
                fail.append(f"{sym}: validation failed -> {problems}")
                continue
            results.append(inst)

    results.sort(key=lambda r: order.get(r["symbol"], 999))
    bundle = build_bundle(results, generated_at)

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    print(f"ta_desk: {len(results)}/{len(universe)} ok -> {out_path}")
    if fail:
        print("  failed:")
        for f in fail:
            print(f"    {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
