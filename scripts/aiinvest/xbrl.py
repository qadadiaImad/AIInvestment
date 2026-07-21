"""SEC XBRL companyfacts helper — pure extraction, no I/O (network lives in pull_xbrl.py).

Extracts interest_income, interest_expense, and receivables from the SEC
companyfacts JSON endpoint. Picks the most recent annual (10-K, fp=="FY")
USD fact for each field using tag preference lists that include bank fallbacks.

SEC politeness: descriptive User-Agent with contact email, ≤10 req/s, 30-day cache.
"""
from __future__ import annotations

import datetime
import json
import pathlib

# SEC requires a real descriptive UA with contact info.
UA = "AIInvestment research engine (contact: easyresumeai@outlook.fr)"

# companyfacts base URL (CIK must be zero-padded to 10 digits).
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# Tag preference lists (first match wins).
_INTEREST_INCOME_TAGS = [
    "InvestmentIncomeInterest",
    "InterestAndDividendIncomeOperating",  # bank fallback
    "InterestIncomeOperating",             # bank fallback
]
_INTEREST_EXPENSE_TAGS = [
    "InterestExpense",
]
_RECEIVABLES_TAGS = [
    "AccountsReceivableNetCurrent",
    "ReceivablesNetCurrent",
    "AccountsNotesAndLoansReceivableNetCurrent",
]

# Map logical field names to their tag preference lists.
_FIELD_TAGS = {
    "interest_income": _INTEREST_INCOME_TAGS,
    "interest_expense": _INTEREST_EXPENSE_TAGS,
    "receivables": _RECEIVABLES_TAGS,
}


# ---------------------------------------------------------------------------
# CIK resolution
# ---------------------------------------------------------------------------

def cik_for(symbol: str, mapping: dict) -> str | None:
    """Return zero-padded 10-digit CIK string for *symbol*, or None if not found.

    *mapping* is the parsed ``company_tickers.json`` dict (keys are string indices,
    values have "cik_str", "ticker", "title").
    """
    sym = symbol.upper()
    for row in mapping.values():
        if str(row.get("ticker", "")).upper() == sym:
            return str(int(str(row["cik_str"]).lstrip("0") or "0")).zfill(10)
    return None


# ---------------------------------------------------------------------------
# Fact extraction (pure — no I/O)
# ---------------------------------------------------------------------------

def _latest_annual_usd(gaap: dict, tag: str) -> dict | None:
    """Return the most recent FY/10-K USD fact for *tag*, or None."""
    entry = gaap.get(tag)
    if not entry:
        return None
    units = entry.get("units", {}).get("USD", [])
    annual = [
        r for r in units
        if r.get("fp") == "FY" and r.get("form") in ("10-K", "10-K/A")
    ]
    if not annual:
        return None
    best = max(annual, key=lambda r: r.get("end", ""))
    return {
        "value": best["val"],
        "unit": "USD",
        "fy": best.get("fy"),
        "fp": best.get("fp"),
        "end": best.get("end"),
        "accession": best.get("accn"),
        "tag": tag,
    }


def extract_facts(companyfacts_json: dict) -> dict:
    """Extract interest_income, interest_expense, and receivables from a companyfacts payload.

    Returns::

        {
            "interest_income":  {...} | None,
            "interest_expense": {...} | None,
            "receivables":      {...} | None,
        }

    Each non-None value has keys: value, unit, fy, fp, end, accession, tag.
    Picks the most recent annual (fp=="FY", form="10-K") USD fact.
    Uses tag preference lists so bank-specific tags serve as fallbacks.
    Missing or malformed input yields None for that field — never a crash.
    """
    gaap = (companyfacts_json or {}).get("facts", {}).get("us-gaap", {})
    result = {}
    for field, tags in _FIELD_TAGS.items():
        found = None
        for tag in tags:
            found = _latest_annual_usd(gaap, tag)
            if found is not None:
                break
        result[field] = found
    return result


# ---------------------------------------------------------------------------
# Cache helpers (data/xbrl/<SYM>.json, 30-day TTL)
# ---------------------------------------------------------------------------

def _cache_path(sym: str, data_root) -> pathlib.Path:
    return pathlib.Path(data_root) / "xbrl" / f"{sym.upper()}.json"


def load_cached(sym: str, data_root) -> dict | None:
    """Load cached XBRL record for *sym* from *data_root*/xbrl/<SYM>.json.

    Returns the parsed dict (which includes a ``retrieved_at`` key) or None
    if the file does not exist or cannot be parsed.
    """
    path = _cache_path(sym, data_root)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_cache(sym: str, record: dict, data_root) -> pathlib.Path:
    """Write *record* to *data_root*/xbrl/<SYM>.json (creates dirs as needed).

    *record* must already contain a ``retrieved_at`` ISO-8601 UTC timestamp.
    """
    path = _cache_path(sym, data_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return path


def is_stale(record: dict, max_age_days: int = 30) -> bool:
    """Return True when the record's ``retrieved_at`` is older than *max_age_days*.

    Records missing ``retrieved_at`` are treated as stale.
    """
    ts = (record or {}).get("retrieved_at")
    if not ts:
        return True
    try:
        retrieved = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        return (now - retrieved).days >= max_age_days
    except (ValueError, TypeError):
        return True
