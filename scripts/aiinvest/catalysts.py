"""Catalyst calendar (Part D) — dated, provenance-stamped events to track.

The 2026 IPO trio, hyperscaler capex guides / earnings, hardware (turbine/SMR) orders,
export-control and permitting updates. Each catalyst carries certainty (filed/reported/
rumored, Rule #5) and provenance. `from_tradingview_earnings` turns live earnings dates
into catalysts so the calendar stays fresh.
"""
from __future__ import annotations

import datetime

VALID_TYPES = {"ipo", "capex_guide", "earnings", "hardware_order",
               "export_control", "permitting", "lockup_expiry"}
VALID_CERTAINTY = {"filed", "reported", "rumored"}

_SRC = "brief Part D (late May 2026)"
_TS = "2026-05-30T12:00:00Z"


def _c(cid, date, title, ctype, entities, layer, certainty="reported",
       precision="day", display=None, note=""):
    return {"id": cid, "date": date, "date_precision": precision,
            "display": display or (date or "rolling"), "title": title, "type": ctype,
            "entities": entities, "layer": layer, "certainty": certainty,
            "source_class": "news-html", "source_url": _SRC, "retrieved_at": _TS, "note": note}


# Seed (dates are best-estimate; precision flags how firm). Verify live before acting.
CATALYSTS = [
    _c("cerebras-ipo", "2026-09-01", "Cerebras IPO (CBRS)", "ipo", ["cerebras"], "L1-chips",
       precision="year", display="2026"),
    _c("anthropic-ipo", "2026-10-01", "Anthropic IPO", "ipo", ["anthropic"], "L3-models",
       precision="month", display="~Oct 2026"),
    _c("openai-ipo", "2026-11-15", "OpenAI IPO", "ipo", ["openai"], "L3-models",
       precision="quarter", display="Q4 2026"),
    _c("spacex-ipo", "2026-12-01", "SpaceX IPO (incl. xAI)", "ipo", ["spacex", "xai"], "L2-infra",
       precision="year", display="2026"),
    _c("export-controls", None, "US/EU GPU export-control updates", "export_control", [], None,
       note="rolling; reshapes China demand + gray markets"),
    _c("turbine-backlog", None, "Gas-turbine order backlogs (GEV/Siemens)", "hardware_order",
       ["GEV"], "L0-energy", note="multi-year backlog; watch new orders"),
    _c("permitting-reform", None, "Interconnection / transmission permitting reform", "permitting",
       [], "L0-energy", note="could accelerate or throttle DC power supply"),
]


def build():
    return list(CATALYSTS)


def validate(cats):
    issues = []
    for c in cats:
        if c.get("type") not in VALID_TYPES:
            issues.append(f"invalid type: {c.get('type')} ({c.get('id')})")
        if c.get("certainty") not in VALID_CERTAINTY:
            issues.append(f"invalid certainty: {c.get('certainty')} ({c.get('id')})")
        for field in ("source_class", "source_url", "retrieved_at"):
            if not c.get(field):
                issues.append(f"missing provenance '{field}' ({c.get('id')})")
        if c.get("date"):
            try:
                datetime.date.fromisoformat(c["date"])
            except ValueError:
                issues.append(f"bad date: {c['date']} ({c.get('id')})")
    return issues


def upcoming(cats, now, horizon_days=180):
    """Dated catalysts in [now, now+horizon], sorted ascending. Undated excluded."""
    n = datetime.date.fromisoformat(now[:10])
    end = n + datetime.timedelta(days=horizon_days)
    dated = [c for c in cats if c.get("date")]
    inwin = [c for c in dated if n <= datetime.date.fromisoformat(c["date"]) <= end]
    return sorted(inwin, key=lambda c: c["date"])


def by_entity(cats, entity):
    return [c for c in cats if entity in c.get("entities", [])]


def by_type(cats, ctype):
    return [c for c in cats if c.get("type") == ctype]


def by_layer(cats, layer):
    return [c for c in cats if c.get("layer") == layer]


def from_tradingview_earnings(records, retrieved_at):
    """Turn TradingView `earnings_release_next_date` values into earnings catalysts."""
    out = []
    for rec in records:
        env = rec.get("metrics", {}).get("earnings_release_next_date", {})
        raw = env.get("value")
        if not raw:
            continue
        is_num = isinstance(raw, (int, float)) or (
            isinstance(raw, str) and raw.strip().lstrip("-").isdigit())
        if is_num:
            date = datetime.datetime.fromtimestamp(
                float(raw), datetime.timezone.utc).date().isoformat()
        else:
            date = str(raw)[:10]
        sym = rec.get("symbol")
        out.append({
            "id": f"{sym}-earnings", "date": date, "date_precision": "day",
            "display": str(date)[:10], "title": f"{sym} earnings / capex guide",
            "type": "earnings", "entities": [sym], "layer": None,
            "certainty": "reported", "source_class": "api",
            "source_url": "tradingview", "retrieved_at": retrieved_at, "note": "",
        })
    return out
