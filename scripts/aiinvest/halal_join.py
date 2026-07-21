"""Join web/public/data/halal.json into content-generation shapes (badge, screen card).

Presentation-side ONLY — the engine lives in aiinvest/halal.py. Rails: badge/lines phrase
results as screen outcomes ("AAOIFI SCREEN: PASS"), never as "is halal" claims.
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib

BADGES = {
    "halal": ("AAOIFI SCREEN: PASS", "#34D399"),
    "questionable": ("AAOIFI SCREEN: REVIEW", "#E0A23B"),
    "not_halal": ("AAOIFI SCREEN: FAIL", "#C25E5E"),
    "insufficient_data": ("AAOIFI SCREEN: NO DATA", "#8893A4"),
}


class HalalDataMissing(RuntimeError):
    pass


def load_halal(path, now=None):
    """-> (verdicts dict, warnings list). Raises HalalDataMissing if absent."""
    p = pathlib.Path(path)
    if not p.exists():
        raise HalalDataMissing(
            f"{p} not found — run `python pull_halal.py` then `python export_halal.py` first.")
    doc = json.loads(p.read_text(encoding="utf-8"))
    warnings = []
    now = now or _dt.datetime.now(_dt.timezone.utc)
    gen = doc.get("generated_at")
    if gen:
        ts = _dt.datetime.fromisoformat(gen.replace("Z", "+00:00"))
        if (now - ts).days > 7:
            warnings.append(f"halal.json generated_at {gen} is older than 7 days — regenerate.")
    return doc.get("verdicts", {}), warnings


def _pct(x):
    return f"{x * 100:.1f}%"


def _row(name, std):
    tests = std.get("tests") or []
    if not tests:
        return {"name": name, "ok": std.get("status") == "pass",
                "binding_label": "activity", "ratio": "—", "threshold": "—", "margin": "—"}
    binding = min(tests, key=lambda t: t.get("margin", 0))
    sign = "+" if binding["margin"] >= 0 else "−"
    return {
        "name": name,
        "ok": std.get("status") == "pass",
        "binding_label": binding["label"],
        "ratio": _pct(binding["ratio"]),
        "threshold": _pct(binding["threshold"]),
        "margin": f"{sign}{abs(binding['margin']) * 100:.1f}pt",
    }


def screen_card_data(verdicts, tk):
    v = verdicts.get(tk.upper())
    if not v:
        return None
    text, color = BADGES.get(v.get("overall"), BADGES["insufficient_data"])
    biz = v.get("business") or {}
    pct = biz.get("impermissible_revenue_pct")
    if biz.get("status") == "clean":
        business_line = "Business activity: clean"
    elif pct and pct.get("value") is not None:
        cats = ", ".join(biz.get("categories") or []) or "flagged"
        business_line = f"Business activity: {cats} — {pct['value']}% impermissible ({pct.get('basis', '')})".rstrip(" ()")
    else:
        cats = ", ".join(biz.get("categories") or []) or "flagged"
        business_line = f"Business activity: {cats} — % undisclosed in filings"
    pur = v.get("purification") or {}
    if pur.get("status") == "computed":
        ps = pur.get("per_share") or 0.0
        purification_line = (f"Purification (estimated): ~${ps:.2f}/share" if ps > 0
                             else "Purification (estimated): $0.00/share")
    else:
        purification_line = "Purification: insufficient data"
    return {
        "overall": v.get("overall"),
        "badge": {"text": text, "color": color},
        "standards_rows": [_row(n, v["standards"][n]) for n in ("AAOIFI", "FTSE", "MSCI")
                           if n in (v.get("standards") or {})],
        "business_line": business_line,
        "purification_line": purification_line,
        "inputs_asof": v.get("inputs_asof") or "",
    }
