"""Pure transforms for the MACRO desk (rates/inflation/liquidity/vol/energy regime).

Zero HTTP — every function here is a pure transform over plain dicts/floats, unit-tested
in isolation (see tests/test_macro.py). `pull_macro.py` is the thin network + assembly
layer that calls these, mirroring the aiinvest/ta.py + pull_ta.py split. See
docs/superpowers/specs/2026-07-14-macro-desk-design.md for the binding macro.json v1
contract (schema_version "macro-desk-v1") these functions feed.

Series set is FINAL (8, keyless FRED CSV via aiinvest/fred.py:fetch_csv): DGS2, DGS10,
DFF, T10Y2Y, CPIAUCSL (transform=yoy_pct), WALCL, VIXCLS, APU000072610.

Regime rules are FINAL (locked thresholds/vocab, spec §4):
  curve:      T10Y2Y.last < 0 -> inverted; 0..0.25 -> flat; >=0.25 -> normal
  real_rate:  (DGS10.last - CPI_YoY.last) > 2.0 -> restrictive; 0..2.0 -> neutral;
              < 0.0 -> accommodative
  liquidity:  WALCL 91-day %change > +1.0% -> expanding; -1.0..+1.0 -> flat;
              < -1.0% -> contracting
  vix:        VIXCLS.last < 15 -> complacent; 15-20 -> normal; 20-30 -> elevated;
              >= 30 -> stressed
"""
from __future__ import annotations

import datetime

# series_id -> static metadata (spec §1 table). Dict insertion order IS the fixed
# series[] output order in macro.json.
SERIES_META = {
    "DGS2": {
        "symbol": "2Y", "display_name": "2-Year Treasury Yield", "group": "RATES",
        "frequency": "daily", "unit": "%", "unit_kind": "pct", "decimals": 2,
        "transform": "level", "history_window_days": 365,
    },
    "DGS10": {
        "symbol": "10Y", "display_name": "10-Year Treasury Yield", "group": "RATES",
        "frequency": "daily", "unit": "%", "unit_kind": "pct", "decimals": 2,
        "transform": "level", "history_window_days": 365,
    },
    "DFF": {
        "symbol": "FEDFUNDS", "display_name": "Fed Funds Effective Rate", "group": "RATES",
        "frequency": "daily", "unit": "%", "unit_kind": "pct", "decimals": 2,
        "transform": "level", "history_window_days": 365,
    },
    "T10Y2Y": {
        "symbol": "2S10S", "display_name": "10Y–2Y Curve Spread", "group": "RATES",
        "frequency": "daily", "unit": "%", "unit_kind": "pct", "decimals": 2,
        "transform": "level", "history_window_days": 365,
    },
    "CPIAUCSL": {
        "symbol": "CPI", "display_name": "CPI, Year-over-Year", "group": "INFLATION",
        "frequency": "monthly", "unit": "%", "unit_kind": "pct", "decimals": 2,
        "transform": "yoy_pct", "history_window_days": 1825,
    },
    "WALCL": {
        "symbol": "FEDBS", "display_name": "Fed Total Assets (Balance Sheet)",
        "group": "LIQUIDITY_VOL", "frequency": "weekly", "unit": "$M",
        "unit_kind": "usd_millions", "decimals": 0, "transform": "level",
        "history_window_days": 365,
    },
    "VIXCLS": {
        "symbol": "VIX", "display_name": "CBOE Volatility Index", "group": "LIQUIDITY_VOL",
        "frequency": "daily", "unit": "index", "unit_kind": "index", "decimals": 1,
        "transform": "level", "history_window_days": 365,
    },
    "APU000072610": {
        "symbol": "ELEC", "display_name": "US Avg Electricity Price", "group": "ENERGY",
        "frequency": "monthly", "unit": "$/kWh", "unit_kind": "usd_small", "decimals": 3,
        "transform": "level", "history_window_days": 1825,
    },
}

CHIP_ORDER = ("curve", "real_rate", "liquidity", "vix")


def _parse_date(s):
    return datetime.date.fromisoformat(s)


# --------------------------------------------------------------------------- downsample


def downsample(rows, target_n=60):
    """Evenly-spaced index-pick, endpoints always preserved. No averaging/binning — every
    plotted point is a real observation."""
    n = len(rows)
    if n <= target_n:
        return rows
    if target_n <= 1:
        return [rows[0]]
    step = (n - 1) / (target_n - 1)
    idxs = sorted({round(i * step) for i in range(target_n)})
    return [rows[i] for i in idxs]


# --------------------------------------------------------------------------- nearest_by_offset


def nearest_by_offset(rows, from_date, offset_days, tolerance_days):
    """rows: [{"date","value"}], value may be None (skipped). Returns the row whose date
    is nearest to from_date - offset_days, within +/- tolerance_days. None if nothing
    qualifies."""
    valid = [r for r in rows if r.get("value") is not None]
    if not valid:
        return None
    target = _parse_date(from_date) - datetime.timedelta(days=offset_days)
    best, best_dist = None, None
    for r in valid:
        dist = abs((_parse_date(r["date"]) - target).days)
        if dist <= tolerance_days and (best_dist is None or dist < best_dist):
            best, best_dist = r, dist
    return best


# --------------------------------------------------------------------------- yoy


def yoy(rows, tolerance_days=20):
    """CPIAUCSL-style raw index -> YoY %, calendar-proximity match (not index arithmetic).
    Rows with no valid comparator ~365d back are dropped, never zero/None-filled."""
    out = []
    for r in rows:
        if r.get("value") is None:
            continue
        comparator = nearest_by_offset(rows, r["date"], offset_days=365,
                                        tolerance_days=tolerance_days)
        if comparator is None or not comparator.get("value"):
            continue
        pct = (r["value"] - comparator["value"]) / comparator["value"] * 100
        out.append({"date": r["date"], "value": pct})
    return out


# --------------------------------------------------------------------------- series payload


def build_series_payload(series_id, raw_rows, meta, retrieved_at, source_url):
    """Assemble one flat per-series dict (spec §2). `raw_rows` is the ALREADY-TRANSFORMED
    series (yoy() output for CPIAUCSL, identity for everything else) — this function does
    NOT apply the transform itself, it only computes change/1y-comparison/windowing/
    sparkline on top of it. Every uncomputable value is explicit `null` plus a
    human-readable warnings[] entry — never a silently-omitted key, never a fake number."""
    warnings = []
    valid = [r for r in raw_rows if r.get("value") is not None]

    base = {
        "series_id": series_id, "symbol": meta["symbol"], "display_name": meta["display_name"],
        "group": meta["group"], "frequency": meta["frequency"], "unit": meta["unit"],
        "unit_kind": meta["unit_kind"], "decimals": meta["decimals"], "transform": meta["transform"],
        "history_window_days": meta["history_window_days"],
        "retrieved_at": retrieved_at, "source": "fred", "source_class": "api",
        "source_url": source_url,
    }

    if not valid:
        warnings.append(f"{series_id}: no valid observations available")
        return {
            **base, "last": None, "previous": None, "change_abs": None, "change_pct": None,
            "value_1y_ago": None, "change_1y_pct": None, "as_of": None, "sparkline": [],
            "warnings": warnings,
        }

    last_row = valid[-1]
    prev_row = valid[-2] if len(valid) >= 2 else None
    last = last_row["value"]
    as_of = last_row["date"]
    previous = prev_row["value"] if prev_row else None

    if previous is None:
        change_abs = None
        change_pct = None
    else:
        change_abs = last - previous
        change_pct = (change_abs / previous * 100) if previous != 0 else None

    year_ago_row = nearest_by_offset(valid, as_of, offset_days=365, tolerance_days=20)
    if year_ago_row is None:
        value_1y_ago = None
        change_1y_pct = None
        warnings.append(f"{series_id}: value_1y_ago unavailable (no observation within "
                         f"tolerance of 365d prior)")
    else:
        value_1y_ago = year_ago_row["value"]
        change_1y_pct = ((last - value_1y_ago) / value_1y_ago * 100) if value_1y_ago else None

    cutoff = _parse_date(as_of) - datetime.timedelta(days=meta["history_window_days"])
    windowed = [r for r in valid if _parse_date(r["date"]) >= cutoff]
    spark_rows = downsample(windowed, 60)
    sparkline = [{"t": r["date"], "v": r["value"]} for r in spark_rows]

    return {
        **base, "last": last, "previous": previous, "change_abs": change_abs,
        "change_pct": change_pct, "value_1y_ago": value_1y_ago, "change_1y_pct": change_1y_pct,
        "as_of": as_of, "sparkline": sparkline, "warnings": warnings,
    }


# --------------------------------------------------------------------------- regime chips


def curve_chip(t10y2y_value, as_of):
    """10Y-2Y curve regime. Returns (chip, warning_or_None)."""
    key, label = "curve", "10Y–2Y Curve"
    basis = "T10Y2Y latest"
    rule = "T10Y2Y < 0 -> inverted; 0-0.25 -> flat; >=0.25 -> normal"
    if t10y2y_value is None:
        chip = {"key": key, "label": label, "state": None, "value": None,
                "value_label": None, "basis": "T10Y2Y unavailable", "rule": rule,
                "as_of": None}
        return chip, "curve chip: T10Y2Y unavailable"
    if t10y2y_value < 0:
        state = "inverted"
    elif t10y2y_value < 0.25:
        state = "flat"
    else:
        state = "normal"
    chip = {"key": key, "label": label, "state": state, "value": t10y2y_value,
            "value_label": f"{t10y2y_value:.2f} pts", "basis": basis, "rule": rule,
            "as_of": as_of}
    return chip, None


def real_rate_chip(dgs10_value, cpi_yoy_value, as_of):
    """Real-rate proxy (Fisher approximation): DGS10 - CPI YoY. Returns (chip, warning)."""
    key, label = "real_rate", "Real Rate (10Y − CPI YoY)"
    rule = "DGS10 - CPI_YoY; >2.0 restrictive, 0-2.0 neutral, <0.0 accommodative"
    if dgs10_value is None or cpi_yoy_value is None:
        chip = {"key": key, "label": label, "state": None, "value": None,
                "value_label": None, "basis": "DGS10 or CPI YoY unavailable", "rule": rule,
                "as_of": None}
        return chip, "real_rate chip: DGS10 or CPI YoY unavailable"
    real_rate = dgs10_value - cpi_yoy_value
    if real_rate > 2.0:
        state = "restrictive"
    elif real_rate < 0.0:
        state = "accommodative"
    else:
        state = "neutral"
    basis = f"DGS10 {dgs10_value:.2f}% − CPI YoY {cpi_yoy_value:.2f}%"
    chip = {"key": key, "label": label, "state": state, "value": real_rate,
            "value_label": f"{real_rate:+.2f} pts", "basis": basis, "rule": rule,
            "as_of": as_of}
    return chip, None


def liquidity_chip(latest, past_91d, as_of):
    """Fed balance sheet 91-day direction. Returns (chip, warning)."""
    key, label = "liquidity", "Fed Balance Sheet"
    basis = "WALCL 91d % change"
    rule = "WALCL 91d %chg; >+1.0 expanding, -1.0..+1.0 flat, <-1.0 contracting"
    if latest is None or not past_91d:
        chip = {"key": key, "label": label, "state": None, "value": None,
                "value_label": None, "basis": "WALCL latest or 91d-prior observation unavailable",
                "rule": rule, "as_of": None}
        return chip, "liquidity chip: WALCL latest or 91d-prior observation unavailable"
    pct_change_91d = (latest - past_91d) / past_91d * 100
    if pct_change_91d > 1.0:
        state = "expanding"
    elif pct_change_91d < -1.0:
        state = "contracting"
    else:
        state = "flat"
    chip = {"key": key, "label": label, "state": state, "value": pct_change_91d,
            "value_label": f"{pct_change_91d:.1f}%", "basis": basis, "rule": rule,
            "as_of": as_of}
    return chip, None


def vix_chip(vix_value, as_of):
    """VIX bucket. Returns (chip, warning)."""
    key, label = "vix", "VIX"
    basis = "VIXCLS latest level"
    rule = "VIX <15 complacent, 15-20 normal, 20-30 elevated, >=30 stressed"
    if vix_value is None:
        chip = {"key": key, "label": label, "state": None, "value": None,
                "value_label": None, "basis": "VIXCLS unavailable", "rule": rule,
                "as_of": None}
        return chip, "vix chip: VIXCLS unavailable"
    if vix_value < 15:
        state = "complacent"
    elif vix_value < 20:
        state = "normal"
    elif vix_value < 30:
        state = "elevated"
    else:
        state = "stressed"
    chip = {"key": key, "label": label, "state": state, "value": vix_value,
            "value_label": f"{vix_value:.1f}", "basis": basis, "rule": rule, "as_of": as_of}
    return chip, None


# --------------------------------------------------------------------------- headline


_NEUTRAL = {"curve": "normal", "real_rate": "neutral", "liquidity": "flat"}
_VIX_NEUTRAL = {"normal", "complacent"}


def build_headline(chips_by_key):
    """Deterministic string composition — fixed priority order curve/real_rate/liquidity/
    vix; a family is mentioned only when its state is non-null AND non-neutral (vix's
    "complacent" also counts as neutral, not a stress flag)."""
    parts = []
    for key in CHIP_ORDER:
        chip = chips_by_key[key]
        state = chip["state"]
        if state is None:
            continue
        if key == "vix":
            if state in _VIX_NEUTRAL:
                continue
        elif state == _NEUTRAL[key]:
            continue
        parts.append(f"{chip['label']} {state}")
    return " · ".join(parts) if parts else "No macro stress signals"


# --------------------------------------------------------------------------- regime assembly


def build_regime(series_by_id, walcl_91d_ago=None):
    """Assembles the 4-chip array (always length 4, fixed order curve/real_rate/liquidity/
    vix) + headline. `walcl_91d_ago` is the WALCL observation ~91 days prior to WALCL's
    latest reading (computed by the caller via nearest_by_offset against WALCL's full raw
    series — this function has no access to full history, only per-series `last`/`as_of`).
    Returns (regime_dict, warnings_list) — warnings name any chip that went null for lack
    of input; the chip itself always stays in the array."""
    warnings = []

    t10y2y = series_by_id.get("T10Y2Y")
    curve, w = curve_chip(t10y2y["last"] if t10y2y else None, t10y2y["as_of"] if t10y2y else None)
    if w:
        warnings.append(w)

    dgs10 = series_by_id.get("DGS10")
    cpi = series_by_id.get("CPIAUCSL")
    real_rate_as_of = (dgs10 or {}).get("as_of") or (cpi or {}).get("as_of")
    real_rate, w = real_rate_chip(dgs10["last"] if dgs10 else None,
                                   cpi["last"] if cpi else None, real_rate_as_of)
    if w:
        warnings.append(w)

    walcl = series_by_id.get("WALCL")
    liquidity, w = liquidity_chip(walcl["last"] if walcl else None, walcl_91d_ago,
                                   walcl["as_of"] if walcl else None)
    if w:
        warnings.append(w)

    vixcls = series_by_id.get("VIXCLS")
    vix, w = vix_chip(vixcls["last"] if vixcls else None, vixcls["as_of"] if vixcls else None)
    if w:
        warnings.append(w)

    chips_by_key = {"curve": curve, "real_rate": real_rate, "liquidity": liquidity, "vix": vix}
    headline = build_headline(chips_by_key)
    chips = [chips_by_key[k] for k in CHIP_ORDER]
    return {"headline": headline, "chips": chips}, warnings
