"""Fed-rate path module: FOMC calendar, market-implied path, scenario bands.

Methodology: references/docs/superpowers/specs/2026-05-31-rate-propagation-methodology.md §2.

Pure functions (unit-tested):
  FOMC_2026                          — static 2026 FOMC meeting dates (8 meetings, 4 SEP)
  _day_weighted_rate(...)            — mid-month FOMC day-weighting math
  implied_path_from_quotes(quotes)   — {(year,month): price} -> {date: expected_dff}
  scenarios(path)                    — base / bull (-25bps) / bear (+25bps)

Thin network functions (not unit-tested; may raise, caller should try/except):
  fetch_zq_quotes()                  — ZQ fed-funds futures via yfinance
  fetch_sep_dots()                   — SEP dot-plot medians via FRED
  build_fed_path()                   — orchestrator with fallback to flat DFF

Educational/research only — not investment advice.
"""
from __future__ import annotations

import calendar
import datetime
from typing import Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# 2026 FOMC meeting dates (final decision day of each 2-day meeting).
# SEP (Summary of Economic Projections) meetings: Mar, Jun, Sep, Dec.
# Source: federalreserve.gov/monetarypolicy/fomccalendars.htm
# ---------------------------------------------------------------------------

FOMC_2026: list[dict] = [
    {"date": datetime.date(2026, 1, 29), "is_sep": False},
    {"date": datetime.date(2026, 3, 18), "is_sep": True},
    {"date": datetime.date(2026, 4, 29), "is_sep": False},
    {"date": datetime.date(2026, 6, 17), "is_sep": True},
    {"date": datetime.date(2026, 7, 29), "is_sep": False},
    {"date": datetime.date(2026, 9, 16), "is_sep": True},
    {"date": datetime.date(2026, 11, 4), "is_sep": False},
    {"date": datetime.date(2026, 12, 16), "is_sep": True},
]

# Map (year, month) -> FOMC meeting date for quick lookup
_MEETING_BY_YM: dict[tuple[int, int], datetime.date] = {
    (m["date"].year, m["date"].month): m["date"]
    for m in FOMC_2026
}


# ---------------------------------------------------------------------------
# PURE math helper
# ---------------------------------------------------------------------------

def _day_weighted_rate(
    avg_rate: float,
    prior_rate: float,
    meeting_day: int,
    days_in_month: int,
) -> float:
    """Extract the post-meeting rate implied by a monthly ZQ futures contract.

    The contract settles on the arithmetic average daily fed funds rate for the
    delivery month. When the FOMC meets on `meeting_day`, the month has two
    regimes:
      • Days 1 … meeting_day-1 : prior_rate  (days_before = meeting_day - 1)
      • Days meeting_day … eom  : new_rate    (days_from   = days_in_month - meeting_day + 1)

    avg_rate = (days_before * prior_rate + days_from * new_rate) / days_in_month
    => new_rate = (avg_rate * days_in_month - days_before * prior_rate) / days_from

    Args:
        avg_rate:       100 - ZQ price (whole-month implied rate, %)
        prior_rate:     DFF rate in effect before the meeting (%)
        meeting_day:    calendar day-of-month of the FOMC decision
        days_in_month:  total days in the contract month

    Returns:
        Post-meeting expected DFF rate (%).
    """
    days_before = meeting_day - 1
    days_from = days_in_month - meeting_day + 1  # always >= 1

    if days_from <= 0:
        # Degenerate: meeting_day > days_in_month — should never happen with
        # real FOMC dates but guard for synthetic test fixtures.
        return avg_rate

    return (avg_rate * days_in_month - days_before * prior_rate) / days_from


# ---------------------------------------------------------------------------
# PURE: implied path from ZQ quotes
# ---------------------------------------------------------------------------

def implied_path_from_quotes(
    quotes: Dict[Tuple[int, int], float],
    prior_rate: float = 5.33,  # historical EFFR before 2024-09 cycle
) -> Dict[datetime.date, float]:
    """Compute per-FOMC-meeting expected DFF from ZQ fed-funds-futures monthly prices.

    Args:
        quotes:      {(year, month): zq_price} — ZQ contract price (100 - rate).
                     Keys for non-meeting months are used only as prior-rate bridges.
        prior_rate:  Rate in effect at the start of the first contract month.
                     Defaults to 5.33 (pre-cut level) but callers should pass the
                     live DFF from FRED for accuracy.

    Returns:
        {datetime.date: float} — one entry per FOMC meeting date whose contract
        month appears in `quotes`.  Non-meeting months are used as running priors
        but produce no output key.

    Day-weighting formula: §2 of the methodology spec.
    """
    if not quotes:
        return {}

    path: Dict[datetime.date, float] = {}
    running_prior = prior_rate

    # Process months in chronological order so priors chain correctly.
    for (year, month) in sorted(quotes.keys()):
        price = quotes[(year, month)]
        avg_rate = 100.0 - price
        days_in_m = calendar.monthrange(year, month)[1]
        meeting_date = _MEETING_BY_YM.get((year, month))

        if meeting_date is not None:
            # Meeting month: day-weight to extract post-meeting rate.
            meeting_day = meeting_date.day
            new_rate = _day_weighted_rate(
                avg_rate=avg_rate,
                prior_rate=running_prior,
                meeting_day=meeting_day,
                days_in_month=days_in_m,
            )
            path[meeting_date] = float(new_rate)
            running_prior = float(new_rate)
        else:
            # Non-meeting month: whole-month implied rate becomes the next prior.
            running_prior = float(avg_rate)

    return path


# ---------------------------------------------------------------------------
# PURE: scenario bands
# ---------------------------------------------------------------------------

def scenarios(
    path: Dict[datetime.date, float],
) -> Dict[str, Dict[datetime.date, float]]:
    """Build base / bull / bear scenario bands from a ZQ-implied rate path.

    Rules:
      base  — the path as-is.
      bull  — -25bps applied from the next hold-priced meeting onward.
      bear  — +25bps applied from the next hold-priced meeting onward.

    "Hold-priced meeting" = first meeting whose rate equals the immediately
    preceding meeting's rate (market prices a hold).  If no such meeting
    exists, the shift is applied to the last meeting only — brackets the
    SEP corridor without requiring paid CME FedWatch probability data.

    Args:
        path: {datetime.date: expected_dff} as returned by implied_path_from_quotes.

    Returns:
        {"base": path, "bull": {...}, "bear": {...}}
    """
    if not path:
        return {"base": {}, "bull": {}, "bear": {}}

    sorted_dates = sorted(path)
    rates = [path[d] for d in sorted_dates]

    # Find the pivot: first meeting where rate == previous meeting rate.
    pivot_idx: Optional[int] = None
    for i in range(1, len(sorted_dates)):
        if abs(rates[i] - rates[i - 1]) < 1e-9:
            pivot_idx = i
            break

    # Fallback: no hold found → shift only the last meeting.
    if pivot_idx is None:
        pivot_idx = len(sorted_dates) - 1

    pivot_date = sorted_dates[pivot_idx]

    bull: Dict[datetime.date, float] = {}
    bear: Dict[datetime.date, float] = {}
    for d in sorted_dates:
        if d >= pivot_date:
            bull[d] = float(path[d] - 0.25)
            bear[d] = float(path[d] + 0.25)
        else:
            bull[d] = float(path[d])
            bear[d] = float(path[d])

    return {"base": dict(path), "bull": bull, "bear": bear}


# ---------------------------------------------------------------------------
# Thin NETWORK functions — not unit-tested; callers wrap in try/except
# ---------------------------------------------------------------------------

# ZQ ticker map: (year, month) -> Yahoo Finance ticker symbol
# CBT = CBOT exchange suffix on Yahoo Finance
_ZQ_TICKERS: dict[tuple[int, int], str] = {
    (2026, 5): "ZQK26.CBT",
    (2026, 6): "ZQM26.CBT",
    (2026, 7): "ZQN26.CBT",
    (2026, 8): "ZQQ26.CBT",
    (2026, 9): "ZQU26.CBT",
    (2026, 10): "ZQV26.CBT",
    (2026, 11): "ZQX26.CBT",
    (2026, 12): "ZQZ26.CBT",
    (2027, 1): "ZQF27.CBT",
    (2027, 2): "ZQG27.CBT",
    (2027, 3): "ZQH27.CBT",
}

# SEP dot-plot FRED series (Mar-2026 SEP: median 3.4%)
_SEP_SERIES = {
    "median": "FEDTARMD",
    "range_high": "FEDTARRH",
    "range_low": "FEDTARRL",
    "neutral": "FEDTARMDLR",
}


def fetch_zq_quotes(tickers: Optional[dict] = None) -> Dict[Tuple[int, int], float]:
    """Fetch ZQ fed-funds-futures closing prices via yfinance.

    Returns {(year, month): price} for available contracts.
    Requires: pip install yfinance

    Network function — not unit-tested.
    """
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError(
            "yfinance is required for ZQ futures: pip install yfinance"
        ) from exc

    import datetime as _dt
    retrieved_at = _dt.datetime.utcnow().isoformat() + "Z"

    ticker_map = tickers or _ZQ_TICKERS
    quotes: Dict[Tuple[int, int], float] = {}

    symbols = list(ticker_map.values())
    # Batch download; yfinance handles missing tickers gracefully.
    data = yf.download(symbols, period="5d", auto_adjust=True, progress=False)

    # yf.download returns a MultiIndex DataFrame when >1 tickers.
    # "Close" level holds EOD prices.
    try:
        close = data["Close"] if "Close" in data.columns.get_level_values(0) else data
    except Exception:
        close = data

    for (year, month), ticker in ticker_map.items():
        try:
            series = close[ticker].dropna()
            if series.empty:
                continue
            price = float(series.iloc[-1])
            quotes[(year, month)] = price
        except (KeyError, IndexError):
            continue

    return quotes


def fetch_sep_dots(api_key: str = "") -> Dict[str, Optional[float]]:
    """Fetch SEP dot-plot summary from FRED.

    Series used (latest observation):
      FEDTARMD  — median projected fed funds rate
      FEDTARRH  — range high
      FEDTARRL  — range low
      FEDTARMDLR — longer-run (neutral) rate

    Args:
        api_key: FRED API key. If empty, falls back to FRED_API_KEY env var.

    Network function — not unit-tested.
    """
    import os
    from . import fred as _fred

    key = api_key or os.environ.get("FRED_API_KEY", "")
    dots: Dict[str, Optional[float]] = {}

    for name, series_id in _SEP_SERIES.items():
        try:
            if key:
                rows = _fred.fetch_observations(series_id, api_key=key)
            else:
                # Keyless CSV path as fallback (may 403 on some FRED series)
                rows = _fred.fetch_csv(series_id)
            valid = [r["value"] for r in rows if r["value"] is not None]
            dots[name] = valid[-1] if valid else None
        except Exception:
            dots[name] = None

    return dots


def build_fed_path(
    zq_quotes: Optional[Dict[Tuple[int, int], float]] = None,
    prior_rate: Optional[float] = None,
    fred_api_key: str = "",
) -> Dict[str, object]:
    """Orchestrate the full fed-path build: ZQ futures → implied path → scenarios.

    Fallback chain:
      1. Fetch ZQ quotes from yfinance.
      2. If ZQ unavailable, fall back to flat DFF from FRED (live).
      3. If FRED also fails, use the last-known DFF from the methodology spec (3.64).

    Returns:
        {
          "path":       {date: rate},   # ZQ-implied or flat fallback
          "scenarios":  {"base":..., "bull":..., "bear":...},
          "sep_dots":   {...},          # from FRED (best-effort)
          "source":     str,            # "zq_futures" | "fred_dff_flat" | "fallback_const"
          "note":       str,            # human-readable provenance
          "retrieved_at": str,          # UTC ISO-8601
        }

    Network function — not unit-tested.
    """
    import datetime as _dt
    retrieved_at = _dt.datetime.utcnow().isoformat() + "Z"
    note_parts: list[str] = []

    # Step 1: ZQ futures
    quotes = zq_quotes
    source = "zq_futures"
    if quotes is None:
        try:
            quotes = fetch_zq_quotes()
            note_parts.append(f"ZQ quotes fetched: {len(quotes)} contracts.")
        except Exception as exc:
            quotes = {}
            source = "fred_dff_flat"
            note_parts.append(f"ZQ fetch failed ({exc}); falling back to FRED DFF.")

    # Step 2: prior_rate (live DFF from FRED)
    live_dff: Optional[float] = prior_rate
    if live_dff is None:
        try:
            from . import fred as _fred
            rows = _fred.fetch_csv("DFF")
            valid = [r["value"] for r in rows if r["value"] is not None]
            live_dff = valid[-1] if valid else None
            if live_dff is not None:
                note_parts.append(f"Live DFF from FRED: {live_dff}%.")
        except Exception as exc:
            note_parts.append(f"FRED DFF fetch failed ({exc}).")

    if live_dff is None:
        # Final fallback from methodology spec §2 note "A0": ~3.64 as of May-2026
        live_dff = 3.64
        source = "fallback_const"
        note_parts.append("Using methodology-spec constant DFF=3.64 (stale; see §A0).")

    # Step 3: implied path
    if quotes:
        path = implied_path_from_quotes(quotes, prior_rate=live_dff)
    else:
        # Flat path at current DFF for all 2026 FOMC meetings
        source = "fred_dff_flat"
        path = {m["date"]: live_dff for m in FOMC_2026}
        note_parts.append("Flat DFF path applied to all 2026 FOMC dates (no ZQ data).")

    # Step 4: scenarios
    scen = scenarios(path)

    # Step 5: SEP dots (best-effort)
    sep_dots: Dict[str, Optional[float]] = {}
    try:
        sep_dots = fetch_sep_dots(api_key=fred_api_key)
    except Exception as exc:
        note_parts.append(f"SEP dots unavailable ({exc}).")

    return {
        "path": path,
        "scenarios": scen,
        "sep_dots": sep_dots,
        "source": source,
        "note": " ".join(note_parts) or "OK.",
        "retrieved_at": retrieved_at,
    }
