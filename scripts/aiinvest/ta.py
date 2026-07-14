"""Pure TA computations for the TA desk (pivots / ATR / RSI / SMA / sessions).

Zero HTTP — every function here is a pure transform over plain dicts/floats, unit-tested
in isolation (see tests/test_ta.py). `pull_ta.py` is the thin network + assembly layer
that calls these. See docs/superpowers/specs/undefined-ta-terminal-design.md for the
authoritative 11-instrument universe and the ta_desk.json v1 contract these functions
feed (§0 explains why this feed uses one provenance stamp per instrument instead of the
root CLAUDE.md's per-leaf envelope pattern).

Formulas:
  Classic floor-trader pivots: pp=(H+L+C)/3; r1=2pp-L; s1=2pp-H; r2=pp+(H-L);
    s2=pp-(H-L); r3=H+2(pp-L); s3=L-2(H-pp).
  True range: TR=max(H-L, |H-Cprev|, |L-Cprev|).
  Wilder ATR/RSI: seed = simple mean of the first `period` values, then each later value
    smooths as (prev*(period-1)+x)/period.
"""
from __future__ import annotations

import datetime

# symbol -> {display_name, asset_class, group, yahoo_symbol, tv_symbol}
UNIVERSE = {
    "EURUSD": {"display_name": "EUR/USD", "asset_class": "fx", "group": "FX",
               "yahoo_symbol": "EURUSD=X", "tv_symbol": "OANDA:EURUSD"},
    "GBPUSD": {"display_name": "GBP/USD", "asset_class": "fx", "group": "FX",
               "yahoo_symbol": "GBPUSD=X", "tv_symbol": "OANDA:GBPUSD"},
    "USDJPY": {"display_name": "USD/JPY", "asset_class": "fx", "group": "FX",
               "yahoo_symbol": "USDJPY=X", "tv_symbol": "OANDA:USDJPY"},
    "USDCHF": {"display_name": "USD/CHF", "asset_class": "fx", "group": "FX",
               "yahoo_symbol": "USDCHF=X", "tv_symbol": "OANDA:USDCHF"},
    "AUDUSD": {"display_name": "AUD/USD", "asset_class": "fx", "group": "FX",
               "yahoo_symbol": "AUDUSD=X", "tv_symbol": "OANDA:AUDUSD"},
    "USDCAD": {"display_name": "USD/CAD", "asset_class": "fx", "group": "FX",
               "yahoo_symbol": "USDCAD=X", "tv_symbol": "OANDA:USDCAD"},
    "GOLD": {"display_name": "Gold", "asset_class": "commodity", "group": "METALS",
             "yahoo_symbol": "GC=F", "tv_symbol": "OANDA:XAUUSD"},
    "SILVER": {"display_name": "Silver", "asset_class": "commodity", "group": "METALS",
               "yahoo_symbol": "SI=F", "tv_symbol": "OANDA:XAGUSD"},
    "WTI": {"display_name": "WTI Crude Oil", "asset_class": "commodity", "group": "ENERGY",
            "yahoo_symbol": "CL=F", "tv_symbol": "NYMEX:CL1!"},
    "NATGAS": {"display_name": "Natural Gas", "asset_class": "commodity", "group": "ENERGY",
               "yahoo_symbol": "NG=F", "tv_symbol": "NYMEX:NG1!"},
    "DXY": {"display_name": "US Dollar Index", "asset_class": "index", "group": "INDEX",
            "yahoo_symbol": "DX-Y.NYB", "tv_symbol": "TVC:DXY"},
}

GROUPS = ["FX", "METALS", "ENERGY", "INDEX"]

# name -> (start_hour_inclusive, end_hour_exclusive), UTC. DST-naive by design (v1).
SESSION_WINDOWS_UTC = {"tokyo": (0, 9), "london": (8, 17), "new_york": (13, 22)}

_PIVOT_KEYS = ("pp", "r1", "r2", "r3", "s1", "s2", "s3")


# --------------------------------------------------------------------------- pivots


def classic_pivots(high, low, close):
    """Classic floor-trader pivots from one completed daily bar."""
    pp = (high + low + close) / 3
    r1 = 2 * pp - low
    s1 = 2 * pp - high
    r2 = pp + (high - low)
    s2 = pp - (high - low)
    r3 = high + 2 * (pp - low)
    s3 = low - 2 * (high - pp)
    return {"pp": pp, "r1": r1, "r2": r2, "r3": r3, "s1": s1, "s2": s2, "s3": s3}


def _index_prev_completed_bar(daily_series, as_of_date):
    """Index of the most recent bar with date < as_of_date, or None if none exists."""
    idx = None
    for i, bar in enumerate(daily_series):
        if bar["date"] < as_of_date:
            idx = i
        else:
            break
    return idx


def daily_pivots_basis(daily_series, as_of_date=None):
    """Return the previous COMPLETED daily bar (date < as_of), never the last element
    blindly — the newest bar in `daily_series` may be today's still-forming bar."""
    if not daily_series:
        return None
    if as_of_date is None:
        as_of_date = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    idx = _index_prev_completed_bar(daily_series, as_of_date)
    if idx is None:
        return None
    return daily_series[idx]


# --------------------------------------------------------------------------- ATR


def true_range(high, low, prev_close):
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def atr(daily_series, period=14):
    """Wilder ATR over the full daily series (including today's forming bar)."""
    if len(daily_series) < period + 1:
        return None
    trs = [true_range(daily_series[i]["high"], daily_series[i]["low"],
                       daily_series[i - 1]["close"])
           for i in range(1, len(daily_series))]
    if len(trs) < period:
        return None
    value = sum(trs[:period]) / period
    for tr in trs[period:]:
        value = (value * (period - 1) + tr) / period
    return value


def atr_bands(price, atr_value):
    if atr_value is None:
        return None
    return {
        "upper_1x": price + atr_value, "lower_1x": price - atr_value,
        "upper_2x": price + 2 * atr_value, "lower_2x": price - 2 * atr_value,
    }


# --------------------------------------------------------------------------- RSI


def rsi(closes, period=14):
    """Wilder RSI14 on closes. None if fewer than period+1 closes are available."""
    if len(closes) < period + 1:
        return None
    diffs = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0.0 for d in diffs]
    losses = [-d if d < 0 else 0.0 for d in diffs]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for g, l in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
    if avg_gain == 0 and avg_loss == 0:
        return 50.0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def rsi_state(rsi_value):
    if rsi_value is None:
        return None
    if rsi_value > 70:
        return "overbought"
    if rsi_value < 30:
        return "oversold"
    return "neutral"


# --------------------------------------------------------------------------- SMA / trend


def sma(closes, period):
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


def trend_state(price, sma20, sma50, sma200):
    """Regime STATE (not a crossover-event detector — out of scope for v1)."""
    if sma20 is None or sma50 is None or sma200 is None:
        return {"state": "unknown", "price_above_sma20": None, "price_above_sma50": None,
                "price_above_sma200": None, "sma50_above_sma200": None}
    above20 = price > sma20
    above50 = price > sma50
    above200 = price > sma200
    fifty_above_two_hundred = sma50 > sma200
    if above20 and above50 and above200 and fifty_above_two_hundred:
        state = "bullish"
    elif not above20 and not above50 and not above200 and not fifty_above_two_hundred:
        state = "bearish"
    else:
        state = "mixed"
    return {"state": state, "price_above_sma20": above20, "price_above_sma50": above50,
            "price_above_sma200": above200, "sma50_above_sma200": fifty_above_two_hundred}


# --------------------------------------------------------------------------- levels / price


def fifty_two_week_stats(daily_series, last):
    if not daily_series:
        return {"high": None, "low": None, "position_pct": None}
    high = max(bar["high"] for bar in daily_series)
    low = min(bar["low"] for bar in daily_series)
    if high == low:
        position_pct = 100.0
    else:
        position_pct = max(0.0, min(100.0, (last - low) / (high - low) * 100))
    return {"high": high, "low": low, "position_pct": position_pct}


def previous_day_ohlc(daily_series, as_of_date=None):
    """Previous completed bar's OHLC + its OWN change_pct vs the bar before it."""
    if not daily_series:
        return None
    if as_of_date is None:
        as_of_date = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    idx = _index_prev_completed_bar(daily_series, as_of_date)
    if idx is None:
        return None
    bar = daily_series[idx]
    change_pct = None
    if idx > 0:
        change_pct = day_change_pct(bar["close"], daily_series[idx - 1]["close"])
    return {"date": bar["date"], "open": bar["open"], "high": bar["high"],
            "low": bar["low"], "close": bar["close"], "change_pct": change_pct}


def day_change_pct(last, previous_close):
    if not previous_close:
        return None
    return (last - previous_close) / previous_close * 100


def nearest_level(price, pivots):
    """Closest of {pp,r1-3,s1-3} to `price`. Signed distance_pct: level above price is
    positive."""
    if not pivots:
        return None
    best_label, best_val, best_dist = None, None, None
    for key in _PIVOT_KEYS:
        val = pivots.get(key)
        if val is None:
            continue
        dist = abs(val - price)
        if best_dist is None or dist < best_dist:
            best_dist, best_label, best_val = dist, key.upper(), val
    if best_label is None:
        return None
    distance_pct = (best_val - price) / price * 100 if price else None
    return {"label": best_label, "value": best_val, "distance_pct": distance_pct}


# --------------------------------------------------------------------------- sessions


def _parse_dt(dt):
    if isinstance(dt, str):
        return datetime.datetime.fromisoformat(dt.replace("Z", "+00:00"))
    return dt


def session_ranges(intraday_series, as_of=None, windows=None):
    """Per-window {window_utc, high, low, bar_count, complete} for "today" (UTC date of
    `as_of`). complete=True once the current UTC time has passed the window's close hour.
    """
    if windows is None:
        windows = SESSION_WINDOWS_UTC
    if as_of is None:
        as_of = datetime.datetime.now(datetime.timezone.utc)
    target_date = as_of.date()

    out = {"date": target_date.isoformat()}
    for name, (start_h, end_h) in windows.items():
        bars = []
        for bar in intraday_series:
            dt = _parse_dt(bar["datetime"])
            if dt.date() != target_date:
                continue
            if start_h <= dt.hour < end_h:
                bars.append(bar)
        if bars:
            high = max(b["high"] for b in bars)
            low = min(b["low"] for b in bars)
        else:
            high = low = None
        out[name] = {
            "window_utc": f"{start_h:02d}:00-{end_h:02d}:00",
            "high": high, "low": low,
            "bar_count": len(bars),
            "complete": as_of.hour >= end_h,
        }
    return out


def sparkline_from_intraday(intraday_series, n=48):
    """Last n intraday closes, ascending -> [{t, c}]."""
    tail = intraday_series[-n:] if len(intraday_series) > n else list(intraday_series)
    return [{"t": bar["datetime"], "c": bar["close"]} for bar in tail]
