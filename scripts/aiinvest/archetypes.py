"""Pure investor-archetype scorecard computations (Graham / Buffett / Lynch).

Zero HTTP, zero I/O — every function here is a pure transform over plain dicts/lists,
unit-tested in isolation (see tests/test_archetypes.py). `build_archetypes.py` is the
thin network-free assembly layer that reads already-retrieved local JSON (site.json) and
calls these. See docs/superpowers/specs/2026-07-14-archetypes-design.md for the binding
archetypes.json v1 contract these functions feed.

DETERMINISTIC, RULE-BASED, ZERO-LLM. Every criterion is a plain arithmetic comparison
against an already-retrieved fundamental. `likes`/`concerns` are fixed sentence templates
(no free text, no generation) so the whole pipeline is byte-for-byte testable.

Design notes on criteria whose real-world rule is two-sided (a band or a floor-and-cap,
e.g. Graham's "0 <= debt/equity <= 0.5"): `comparator`/`threshold` in the output row
describe only the decision-critical bound for display/UI purposes (mirrors the spec's own
precedent for L4's `0 < market_cap <= 200B`, displayed as `le 200B`). `pass` is ALWAYS
computed by the real range/custom rule, never derived from comparator+threshold alone.

G4 (earnings_stability) stores `actual` = the number of trailing annual EPS points
evaluated (not a loss-year count), so the "{n} annual EPS reports" sentence template can
render directly off the row with no extra out-of-band context — `likes_and_concerns`
renders every template purely from a criterion row's own fields.
"""
from __future__ import annotations

import math

# --------------------------------------------------------------------------- constants

SCHEMA_VERSION = "archetypes-v1"
METHODOLOGY_VERSION = "graham-buffett-lynch-v1.0"
SOURCE_CLASS = "computed"
DISCLAIMER = (
    "Rule-based scorecard — not a prediction, not investment advice. Deterministic "
    "checklist against public fundamentals, not an opinion about what "
    "Graham/Buffett/Lynch would actually say about a name today."
)

MIN_EVALUABLE_CRITERIA = 3
MIN_EVALUABLE_WEIGHT_PCT = 50

LAYER_ORDER = ["L0-energy", "L1-chips", "L2-infra", "L3-models", "L4-application"]

TOP_N = 15

# Verbatim from build_risk.py's _DIRTY_STRINGS — do not reinvent a second list.
_DIRTY_STRINGS = {"", ".", "-", "--", "n/a", "na", "none", "null"}


# --------------------------------------------------------------------------- criteria metadata

CRITERIA = {
    "graham": [
        {"key": "earnings_positive", "label": "Positive current earnings",
         "field": "fundamentals.net_margin", "comparator": "gt", "unit": "pct",
         "threshold": 0, "weight": 10},
        {"key": "moderate_pe", "label": "Moderate P/E",
         "field": "valuation.pe", "comparator": "le", "unit": "x",
         "threshold": 15, "weight": 15, "positive_gate": True},
        {"key": "moderate_value_multiple", "label": "Moderate P/B (P/S fallback)",
         "field": "fundamentals.pb", "comparator": "le", "unit": "x",
         "threshold": 1.5, "weight": 15, "kind": "pb_ps_fallback"},
        {"key": "earnings_stability", "label": "No loss year (trailing EPS history)",
         "field": "history.annualDilutedEPS", "comparator": "ge", "unit": "num",
         "threshold": 3, "weight": 15, "kind": "eps_stability"},
        {"key": "current_ratio", "label": "Financial strength (liquidity)",
         "field": "fundamentals.current_ratio", "comparator": "ge", "unit": "x",
         "threshold": 2.0, "weight": 15},
        {"key": "low_leverage", "label": "Conservative leverage",
         "field": "fundamentals.debt_to_equity", "comparator": "le", "unit": "x",
         "threshold": 0.5, "weight": 15, "range": (0, 0.5)},
        {"key": "margin_of_safety", "label": "Margin of safety vs our fundamental value",
         "field": "valuation.fundamental_discount_pct", "comparator": "ge", "unit": "pct",
         "threshold": 25, "weight": 15},
    ],
    "buffett": [
        {"key": "high_roe", "label": "High return on equity",
         "field": "fundamentals.roe", "comparator": "ge", "unit": "pct",
         "threshold": 15, "weight": 20},
        {"key": "high_roic", "label": "High return on invested capital (moat signal)",
         "field": "fundamentals.roic", "comparator": "ge", "unit": "pct",
         "threshold": 12, "weight": 20},
        {"key": "gross_margin_moat", "label": "Gross-margin moat proxy",
         "field": "fundamentals.gross_margin", "comparator": "ge", "unit": "pct",
         "threshold": 40, "weight": 10},
        {"key": "operating_efficiency", "label": "Operating margin (TTM)",
         "field": "fundamentals.operating_margin", "comparator": "ge", "unit": "pct",
         "threshold": 15, "weight": 10},
        {"key": "low_debt", "label": "Conservative balance sheet",
         "field": "fundamentals.debt_to_equity", "comparator": "le", "unit": "x",
         "threshold": 1.0, "weight": 15, "range": (0, 1.0)},
        {"key": "fcf_yield", "label": "FCF yield via P/FCF",
         "field": "fundamentals.pfcf", "comparator": "le", "unit": "x",
         "threshold": 25, "weight": 15, "positive_gate": True},
        {"key": "fair_price", "label": "Not overpaying",
         "field": "valuation.fundamental_discount_pct", "comparator": "ge", "unit": "pct",
         "threshold": -10, "weight": 10},
    ],
    "lynch": [
        {"key": "peg", "label": "PEG (P/E vs EPS growth)",
         "field": "valuation.pe", "comparator": "le", "unit": "num",
         "threshold": 1.5, "weight": 25, "kind": "peg"},
        {"key": "growth_band", "label": "Steady-grower revenue band",
         "field": "fundamentals.rev_growth_yoy", "comparator": "ge", "unit": "pct",
         "threshold": 15, "weight": 20, "range": (15, 50)},
        {"key": "avoid_hot_story", "label": "Avoid story-stock pricing",
         "field": "fundamentals.ps", "comparator": "le", "unit": "x",
         "threshold": 10, "weight": 20, "positive_gate": True},
        {"key": "room_to_grow", "label": "Room to grow (market-cap band)",
         "field": "valuation.market_cap", "comparator": "le", "unit": "num",
         "threshold": 200_000_000_000, "weight": 15, "positive_gate": True},
        {"key": "earnings_backed", "label": "Growth is earnings-backed",
         "field": "fundamentals.net_margin", "comparator": "gt", "unit": "pct",
         "threshold": 0, "weight": 20},
    ],
}

ARCHETYPE_NAMES = {
    "graham": "Graham — Defensive Value",
    "buffett": "Buffett — Quality Moat",
    "lynch": "Lynch — Growth at a Reasonable Price",
}

EXCLUDED_CRITERIA = {
    "graham": [
        "20-year dividend record (no dividend field)",
        "Graham Number P/E x P/B (composite of already-scored P/E and P/B criteria)",
        "adequate size (no revenue-level field; market cap reserved for Lynch)",
    ],
    "buffett": [
        "multi-year margin/ROE consistency (only TTM snapshot available; B2-B4 labeled "
        "single-period proxies)",
    ],
    "lynch": [
        "category classification fast-grower/stalwart/cyclical/turnaround/asset-play "
        "(qualitative judgment; growth-rate band L2 used as quantitative stand-in)",
    ],
}


def _static_criteria_row(spec):
    return {"key": spec["key"], "label": spec["label"], "field": spec["field"],
            "comparator": spec["comparator"], "unit": spec["unit"],
            "threshold": spec["threshold"], "weight": spec["weight"], "note": None}


METHODOLOGY = {
    key: {"name": ARCHETYPE_NAMES[key],
          "criteria": [_static_criteria_row(s) for s in CRITERIA[key]],
          "excluded_criteria": EXCLUDED_CRITERIA[key]}
    for key in ("graham", "buffett", "lynch")
}


# --------------------------------------------------------------------------- extraction / validation


def _is_dirty_string(s):
    return isinstance(s, str) and s.strip().lower() in _DIRTY_STRINGS


def _is_valid_number(v, positive=False):
    """True iff v is a usable (non-dirty, finite, optionally >0) number."""
    if v is None or isinstance(v, bool):
        return False
    if isinstance(v, str):
        return False  # dirty or not, a bare string is never a usable numeric value here
    if not isinstance(v, (int, float)):
        return False
    if not math.isfinite(v):
        return False
    if positive and v <= 0:
        return False
    return True


def _clean(v, positive=False):
    """Return float(v) if usable (not dirty/None/non-finite, optionally >0), else None."""
    if isinstance(v, str):
        return None  # dirty-string sentinel (or any bare string) -> not evaluable
    if not _is_valid_number(v, positive=positive):
        return None
    return float(v)


def _extract(stock, field_path):
    """Dotted-path getter, e.g. "fundamentals.roe" -> stock["fundamentals"]["roe"].
    Defensive .get() chain (mirrors build_risk.py's market_cap read) -- never raises."""
    cur = stock
    for part in field_path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


# --------------------------------------------------------------------------- per-criterion evaluation


def _base_row(spec, field=None):
    return {"key": spec["key"], "label": spec["label"], "field": field or spec["field"],
            "comparator": spec["comparator"], "unit": spec["unit"],
            "threshold": spec["threshold"], "weight": spec["weight"]}


def _eval_simple(stock, spec):
    raw = _extract(stock, spec["field"])
    val = _clean(raw, positive=spec.get("positive_gate", False))
    base = _base_row(spec)
    if val is None:
        return {**base, "actual": None, "evaluable": False, "pass": None, "note": None}
    rng = spec.get("range")
    if rng is not None:
        lo, hi = rng
        passed = lo <= val <= hi
    else:
        comparator = spec["comparator"]
        threshold = spec["threshold"]
        if comparator == "gt":
            passed = val > threshold
        elif comparator == "ge":
            passed = val >= threshold
        elif comparator == "le":
            passed = val <= threshold
        else:  # pragma: no cover - defensive, CRITERIA only uses gt/ge/le
            raise ValueError(f"unknown comparator {comparator!r}")
    return {**base, "actual": val, "evaluable": True, "pass": passed, "note": None}


def _eval_pb_ps_fallback(stock, spec):
    """G3: prefer P/B; fall back to P/S only when P/B itself is unusable."""
    pb = _clean(_extract(stock, "fundamentals.pb"), positive=True)
    if pb is not None:
        return {**_base_row(spec, field="fundamentals.pb"), "threshold": 1.5,
                "actual": pb, "evaluable": True, "pass": pb <= 1.5, "note": None}
    ps = _clean(_extract(stock, "fundamentals.ps"), positive=True)
    if ps is not None:
        return {**_base_row(spec, field="fundamentals.ps"), "threshold": 2.0,
                "actual": ps, "evaluable": True, "pass": ps <= 2.0,
                "note": "P/B unavailable — used P/S <= 2.0"}
    return {**_base_row(spec, field="fundamentals.pb"), "actual": None,
            "evaluable": False, "pass": None, "note": None}


def _eval_eps_stability(stock, spec):
    """G4: needs >=3 trailing annual EPS points, each individually usable; pass iff
    every one is > 0 (no loss year). `actual` = n points evaluated (used verbatim by the
    "{n} annual EPS reports" sentence templates)."""
    base = _base_row(spec)
    raw = _extract(stock, "history.annualDilutedEPS")
    if not isinstance(raw, list) or len(raw) < 3:
        return {**base, "actual": None, "evaluable": False, "pass": None, "note": None}
    values = []
    for point in raw:
        v = point.get("value") if isinstance(point, dict) else None
        cv = _clean(v)
        if cv is None:
            # A dirty/missing point inside the trailing window -> can't confidently
            # judge stability; honest not-evaluable rather than silently skipping it.
            return {**base, "actual": None, "evaluable": False, "pass": None, "note": None}
        values.append(cv)
    n = len(values)
    passed = all(v > 0 for v in values)
    return {**base, "actual": n, "evaluable": True, "pass": passed, "note": None}


def _eval_peg(stock, spec):
    """L1: PEG = P/E / EPS-growth-YoY. Both inputs must be usable AND positive (a
    negative P/E or negative growth rate makes the ratio meaningless, not "cheap")."""
    base = _base_row(spec)
    pe = _clean(_extract(stock, "valuation.pe"), positive=True)
    growth = _clean(_extract(stock, "fundamentals.eps_growth_yoy"), positive=True)
    if pe is None or growth is None:
        return {**base, "actual": None, "evaluable": False, "pass": None, "note": None}
    peg = pe / growth
    return {**base, "actual": peg, "evaluable": True, "pass": peg <= 1.5, "note": None}


_KIND_DISPATCH = {
    "pb_ps_fallback": _eval_pb_ps_fallback,
    "eps_stability": _eval_eps_stability,
    "peg": _eval_peg,
}


def evaluate_criterion(stock, spec):
    """One criterion row (the §6 criteria[] shape) for a single stock dict."""
    fn = _KIND_DISPATCH.get(spec.get("kind"), _eval_simple)
    return fn(stock, spec)


# --------------------------------------------------------------------------- scoring / verdict


def score_archetype(criteria_results):
    """criteria_results: list of criterion rows (evaluable/pass/weight at minimum).
    Returns {score, verdict, n_pass, n_evaluable, n_total, evaluable_weight_pct}.

    score = round(100 * sum(weight of evaluable+passing) / sum(weight of evaluable)),
    None if nothing evaluable. Verdict is a dual gate on (n_evaluable, evaluable_weight):
    below MIN_EVALUABLE_CRITERIA or MIN_EVALUABLE_WEIGHT_PCT -> not_evaluable (score forced
    to None even if a raw score was computable) -- band edges mirror lib/format.ts's
    healthColor(): score>70 strong_fit, 50<=score<=70 partial_fit, <50 poor_fit."""
    n_total = len(criteria_results)
    evaluable = [r for r in criteria_results if r["evaluable"]]
    n_evaluable = len(evaluable)
    n_pass = sum(1 for r in evaluable if r["pass"])
    total_weight = sum(r["weight"] for r in criteria_results)
    evaluable_weight = sum(r["weight"] for r in evaluable)
    evaluable_weight_pct = round(100 * evaluable_weight / total_weight) if total_weight else 0

    raw_score = None
    if evaluable_weight > 0:
        passing_weight = sum(r["weight"] for r in evaluable if r["pass"])
        raw_score = round(100 * passing_weight / evaluable_weight)

    if n_evaluable < MIN_EVALUABLE_CRITERIA or evaluable_weight_pct < MIN_EVALUABLE_WEIGHT_PCT:
        score = None
        verdict = "not_evaluable"
    else:
        score = raw_score
        if score > 70:
            verdict = "strong_fit"
        elif score >= 50:
            verdict = "partial_fit"
        else:
            verdict = "poor_fit"

    return {"score": score, "verdict": verdict, "n_pass": n_pass, "n_evaluable": n_evaluable,
            "n_total": n_total, "evaluable_weight_pct": evaluable_weight_pct}


# --------------------------------------------------------------------------- likes / concerns templates
# Fixed sentence templates only -- no free text, no LLM. Every template renders purely
# from a criterion row's own fields (no external context needed).


def _g3_field_label(row):
    return "P/B" if row["field"] == "fundamentals.pb" else "P/S"


TEMPLATE_FUNCS = {
    ("graham", "earnings_positive"): {
        "like": lambda r: f"Profitable on a trailing-twelve-month basis (net margin {r['actual']:.1f}%).",
        "concern": lambda r: f"Currently unprofitable (net margin {r['actual']:.1f}%) — fails Graham's earnings test.",
    },
    ("graham", "moderate_pe"): {
        "like": lambda r: f"P/E of {r['actual']:.1f} is at or below Graham's defensive ceiling of 15.",
        "concern": lambda r: f"P/E of {r['actual']:.1f} exceeds Graham's defensive ceiling of 15.",
    },
    ("graham", "moderate_value_multiple"): {
        "like": lambda r: f"{_g3_field_label(r)} of {r['actual']:.2f} is within Graham's value-multiple cap.",
        "concern": lambda r: f"{_g3_field_label(r)} of {r['actual']:.2f} exceeds Graham's value-multiple cap.",
    },
    ("graham", "earnings_stability"): {
        "like": lambda r: f"No loss year across the last {r['actual']} annual EPS reports — earnings stability.",
        "concern": lambda r: f"At least one loss year across the last {r['actual']} annual EPS reports.",
    },
    ("graham", "current_ratio"): {
        "like": lambda r: f"Current ratio of {r['actual']:.2f} clears Graham's 2.0x liquidity bar.",
        "concern": lambda r: f"Current ratio of {r['actual']:.2f} is below Graham's 2.0x liquidity bar.",
    },
    ("graham", "low_leverage"): {
        "like": lambda r: f"Debt/equity of {r['actual']:.2f} is conservative (<= 0.5).",
        "concern": lambda r: f"Debt/equity of {r['actual']:.2f} exceeds Graham's 0.5 conservative cap.",
    },
    ("graham", "margin_of_safety"): {
        "like": lambda r: f"Trading at a {r['actual']:.1f}% discount to our fundamental-value estimate — a real margin of safety.",
        "concern": lambda r: f"Only a {r['actual']:.1f}% discount (or a premium) to our fundamental-value estimate — insufficient margin of safety.",
    },
    ("buffett", "high_roe"): {
        "like": lambda r: f"ROE of {r['actual']:.1f}% clears the 15% quality bar.",
        "concern": lambda r: f"ROE of {r['actual']:.1f}% is below the 15% quality bar.",
    },
    ("buffett", "high_roic"): {
        "like": lambda r: f"ROIC of {r['actual']:.1f}% suggests durable capital efficiency (moat signal).",
        "concern": lambda r: f"ROIC of {r['actual']:.1f}% is below the 12% moat threshold.",
    },
    ("buffett", "gross_margin_moat"): {
        "like": lambda r: f"Gross margin of {r['actual']:.1f}% points to pricing power.",
        "concern": lambda r: f"Gross margin of {r['actual']:.1f}% is below the 40% moat-proxy bar.",
    },
    ("buffett", "operating_efficiency"): {
        "like": lambda r: f"Operating margin of {r['actual']:.1f}% (TTM) is solid.",
        "concern": lambda r: f"Operating margin of {r['actual']:.1f}% (TTM) is thin.",
    },
    ("buffett", "low_debt"): {
        "like": lambda r: f"Debt/equity of {r['actual']:.2f} is within Buffett's comfort zone (<= 1.0).",
        "concern": lambda r: f"Debt/equity of {r['actual']:.2f} exceeds Buffett's 1.0 comfort ceiling.",
    },
    ("buffett", "fcf_yield"): {
        "like": lambda r: f"P/FCF of {r['actual']:.1f} implies a ~{100.0 / r['actual']:.1f}% FCF yield.",
        "concern": lambda r: f"P/FCF of {r['actual']:.1f} implies a FCF yield under 4%.",
    },
    ("buffett", "fair_price"): {
        "like": lambda r: f"Priced at or below our fundamental-value estimate ({r['actual']:+.1f}%) — not overpaying.",
        "concern": lambda r: f"Priced {r['actual']:+.1f}% vs our fundamental-value estimate — paying up beyond Buffett's comfort.",
    },
    ("lynch", "peg"): {
        "like": lambda r: f"PEG of {r['actual']:.2f} is at or below Lynch's 1.5 GARP threshold.",
        "concern": lambda r: f"PEG of {r['actual']:.2f} exceeds Lynch's 1.5 GARP threshold.",
    },
    ("lynch", "growth_band"): {
        "like": lambda r: f"Revenue growth of {r['actual']:.1f}% is in Lynch's steady-grower band (15-50%).",
        "concern": lambda r: f"Revenue growth of {r['actual']:.1f}% is outside Lynch's 15-50% steady-grower band.",
    },
    ("lynch", "avoid_hot_story"): {
        "like": lambda r: f"P/S of {r['actual']:.1f} is not priced like a hot story (<= 10).",
        "concern": lambda r: f"P/S of {r['actual']:.1f} is priced like a hot story (> 10) — Lynch would be wary.",
    },
    ("lynch", "room_to_grow"): {
        "like": lambda r: f"Market cap of ${r['actual']:,.0f} still leaves room to grow (<= $200B).",
        "concern": lambda r: f"Market cap of ${r['actual']:,.0f} is mega-cap territory — limited room left to multiply.",
    },
    ("lynch", "earnings_backed"): {
        "like": lambda r: f"Growth is earnings-backed (net margin {r['actual']:.1f}%).",
        "concern": lambda r: f"Unprofitable on a net-margin basis ({r['actual']:.1f}%) — growth isn't earnings-backed yet.",
    },
}


def _margin(row):
    """Normalized distance from threshold, used only to order likes/concerns.
    ge/gt (higher is better): (actual-threshold)/abs(threshold), threshold==0 -> raw diff.
    le (lower is better): (threshold-actual)/abs(threshold), threshold==0 -> raw diff."""
    threshold = row["threshold"]
    actual = row["actual"]
    if row["comparator"] in ("gt", "ge"):
        return (actual - threshold) if threshold == 0 else (actual - threshold) / abs(threshold)
    return (threshold - actual) if threshold == 0 else (threshold - actual) / abs(threshold)


def likes_and_concerns(archetype_key, criteria_results):
    """Returns (likes[], concerns[], warnings[]). likes = passing criteria's template
    sentences sorted margin-desc (best first); concerns = failing criteria's sorted
    margin-asc (worst first); both capped at 3. Not-evaluable criteria produce neither --
    they emit one warnings[] entry each in the fixed
    "{archetype}.{key}: {field} unavailable — criterion skipped" format."""
    likes = []
    concerns = []
    warnings = []
    for row in criteria_results:
        if not row["evaluable"]:
            warnings.append(f"{archetype_key}.{row['key']}: {row['field']} unavailable "
                             f"— criterion skipped")
            continue
        templates = TEMPLATE_FUNCS[(archetype_key, row["key"])]
        margin = _margin(row)
        if row["pass"]:
            likes.append((margin, templates["like"](row)))
        else:
            concerns.append((margin, templates["concern"](row)))
    likes.sort(key=lambda t: -t[0])
    concerns.sort(key=lambda t: t[0])
    return [s for _, s in likes[:3]], [s for _, s in concerns[:3]], warnings


# --------------------------------------------------------------------------- per-stock / bundle assembly


def evaluate_stock(stock):
    """{archetypes: {graham: {...}, buffett: {...}, lynch: {...}}, warnings: [...]}"""
    archetypes = {}
    all_warnings = []
    for key in ("graham", "buffett", "lynch"):
        rows = [evaluate_criterion(stock, spec) for spec in CRITERIA[key]]
        score_info = score_archetype(rows)
        likes, concerns, warns = likes_and_concerns(key, rows)
        archetypes[key] = {**score_info, "criteria": rows, "likes": likes, "concerns": concerns}
        all_warnings.extend(warns)
    return {"archetypes": archetypes, "warnings": all_warnings}


def build_archetypes(site, generated_at):
    """Full archetypes.json bundle (schema §6). Pure -- `site` is an already-loaded dict
    (site.json), `generated_at` an ISO-8601 UTC string supplied by the caller."""
    stocks = site.get("stocks") or {}

    per_stock = []
    for symbol in sorted(stocks.keys()):
        srec = stocks[symbol] or {}
        evaluated = evaluate_stock(srec)
        per_stock.append({
            "symbol": symbol, "layer": srec.get("layer"), "as_of": srec.get("as_of"),
            "archetypes": evaluated["archetypes"], "warnings": evaluated["warnings"],
        })

    counts = {}
    top = {}
    for key in ("graham", "buffett", "lynch"):
        c = {"strong_fit": 0, "partial_fit": 0, "poor_fit": 0, "not_evaluable": 0}
        candidates = []
        for entry in per_stock:
            scorecard = entry["archetypes"][key]
            c[scorecard["verdict"]] += 1
            if scorecard["verdict"] in ("strong_fit", "partial_fit"):
                candidates.append((entry["symbol"], scorecard["score"]))
        candidates.sort(key=lambda t: (-t[1], t[0]))
        top[key] = [{"symbol": s, "score": sc} for s, sc in candidates[:TOP_N]]
        counts[key] = c

    warnings = []
    if not stocks:
        warnings.append("site.json has no stocks — archetypes universe is empty")

    return {
        "schema_version": SCHEMA_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": generated_at,
        "source_class": SOURCE_CLASS,
        "disclaimer": DISCLAIMER,
        "source": {"name": "site.json", "path": "web/public/data/site.json",
                   "generated_at": site.get("generated_at")},
        "min_evaluable_criteria": MIN_EVALUABLE_CRITERIA,
        "min_evaluable_weight_pct": MIN_EVALUABLE_WEIGHT_PCT,
        "universe": {"n_symbols": len(stocks), "layers": list(LAYER_ORDER)},
        "methodology": METHODOLOGY,
        "per_stock": per_stock,
        "top": top,
        "counts": counts,
        "warnings": warnings,
    }
