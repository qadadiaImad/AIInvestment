"""House Congress-trading PTR parser — PURE FUNCTIONS, NO NETWORK.

Parses already-fetched House Financial Disclosure index bytes/text and
already-extracted Periodic Transaction Report (PTR) PDF text into canonical,
stamped ``congress_trade`` records.

Honesty rails (CLAUDE.md + 2026-05-31-congress-trading-feasibility spec):
- House STOCK Act PTR amounts are RANGE BUCKETS, never exact -> we store
  ``amount_range_low`` / ``amount_range_high`` (high=None for the open-ended
  ``$50,000,001 +`` bucket). Never invent a precise number.
- ``reporting_lag_days`` = filing_date - transaction_date (can reach ~45 days;
  these are DELAYED disclosures, NOT real-time trades).
- Scope: HOUSE only, TEXT PDFs only. A scanned-image PTR yields empty extracted
  text -> ``is_scanned`` True and ``parse_ptr_transactions`` returns [] (we FLAG
  and skip; we never guess values).
- Reject dirty values ('.', '', 'N/A'). Stamp every record with ``retrieved_at``
  (UTC ISO-8601), ``source`` (exact PTR PDF URL) and ``source_class`` = 'filing'.

Educational/research only — not investment advice. No conflict-of-interest
signal in this slice.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import date

from .schema import clean

# ---------------------------------------------------------------------------
# Index field order (House FD annual index: {YEAR}FD.xml / {YEAR}FD.txt)
# ---------------------------------------------------------------------------
INDEX_FIELDS = [
    "Prefix", "Last", "First", "Suffix", "FilingType",
    "StateDst", "Year", "FilingDate", "DocID",
]

# ---------------------------------------------------------------------------
# Verified STOCK Act amount buckets (House schedule). high=None == open-ended.
# ---------------------------------------------------------------------------
AMOUNT_BUCKETS = {
    "$1,001 - $15,000": (1001, 15000),
    "$15,001 - $50,000": (15001, 50000),
    "$50,001 - $100,000": (50001, 100000),
    "$100,001 - $250,000": (100001, 250000),
    "$250,001 - $500,000": (250001, 500000),
    "$500,001 - $1,000,000": (500001, 1000000),
    "$1,000,001 - $5,000,000": (1000001, 5000000),
    "$5,000,001 - $25,000,000": (5000001, 25000000),
    "$25,000,001 - $50,000,000": (25000001, 50000000),
    "$50,000,001 +": (50000001, None),
}

# Build a normalized lookup: collapse internal whitespace to a single space.
_BUCKET_NORM = {
    re.sub(r"\s+", " ", label).strip(): val for label, val in AMOUNT_BUCKETS.items()
}


def parse_amount_bucket(label):
    """Map a House PTR amount-range label to ``(low, high)`` integers.

    ``high`` is None for the open-ended top bucket (``"$50,000,001 +"``).
    Raises ValueError on any unknown / dirty / off-schedule string and TypeError
    on None — we never fabricate a precise number from garbage.
    """
    if label is None:
        raise TypeError("amount label is None")
    s = clean(label)
    if s is None:
        raise ValueError("amount label is dirty/empty")
    s = re.sub(r"\s+", " ", s).strip()
    if s not in _BUCKET_NORM:
        raise ValueError(f"unknown amount bucket: {label!r}")
    return _BUCKET_NORM[s]


# ---------------------------------------------------------------------------
# Index parsing
# ---------------------------------------------------------------------------

def _as_text(data):
    if isinstance(data, (bytes, bytearray)):
        return data.decode("utf-8-sig")
    return data


def parse_fd_index(index_bytes_or_text):
    """Parse an annual FD index (XML or tab-delimited TXT) into filing dicts.

    Each dict has the 9 ``INDEX_FIELDS`` keys; empty values are cleaned to None.
    Detects format by sniffing for an XML prolog / ``<FinancialDisclosure>``.
    """
    text = _as_text(index_bytes_or_text)
    stripped = text.lstrip("﻿").lstrip()
    if stripped.startswith("<"):
        return _parse_index_xml(text)
    return _parse_index_txt(text)


def _parse_index_xml(text):
    root = ET.fromstring(text)
    rows = []
    for member in root.findall(".//Member"):
        row = {}
        for field in INDEX_FIELDS:
            el = member.find(field)
            row[field] = clean(el.text) if el is not None else None
        rows.append(row)
    return rows


def _parse_index_txt(text):
    lines = [ln for ln in text.splitlines() if ln.strip() != ""]
    if not lines:
        return []
    header = lines[0].split("\t")
    rows = []
    for ln in lines[1:]:
        cells = ln.split("\t")
        # pad short rows so every field exists
        cells += [""] * (len(header) - len(cells))
        row = {}
        for field in INDEX_FIELDS:
            try:
                idx = header.index(field)
                row[field] = clean(cells[idx])
            except ValueError:
                row[field] = None
        rows.append(row)
    return rows


def filter_ptrs(rows):
    """Keep only Periodic Transaction Reports (FilingType == 'P')."""
    return [r for r in rows if (r.get("FilingType") or "").strip() == "P"]


# ---------------------------------------------------------------------------
# PTR transaction parsing
# ---------------------------------------------------------------------------

_NUL = "\x00"

# Lines that are page chrome / repeated table headers — never part of a txn.
_HEADER_FRAGMENTS = (
    "ID Owner Asset Transaction Date Notification Amount",
    "Type Date Gains",
    "$200?",
)

# A primary transaction line carries: txn-type token, txn date, notification
# date, and the START of an amount range ("$nnn,nnn -" with high possibly on
# the next physical line, OR a full "$nnn - $nnn").
_OWNER = r"(?:SP|JT|DC)"
_DATE = r"\d{1,2}/\d{1,2}/\d{4}"
_TYPE = r"(?:P|S \(partial\)|S)"
# amount-low then either the rest-of-range on this line or a trailing dash.
_AMT = r"\$[\d,]+\s*-(?:\s*\$[\d,]+)?"

_PRIMARY_RE = re.compile(
    r"(?P<type>" + _TYPE + r")\s+"
    r"(?P<txn_date>" + _DATE + r")\s+"
    r"(?P<notif>" + _DATE + r")\s+"
    r"(?P<amt>" + _AMT + r")\s*$"
)

_TICKER_RE = re.compile(r"\(([A-Z][A-Z0-9.\-]{0,9})\)")
# amount-high wraps to a continuation line, often after the asset-type code,
# e.g. "[ST] $50,000" or "12/15/26 (91282CJP7) [GS] $250,000" — grab trailing $.
_AMT_HIGH_RE = re.compile(r"\$[\d,]+\s*$")
_BUCKET_INLINE_RE = re.compile(r"\$[\d,]+\s*-\s*\$[\d,]+|\$[\d,]+\s*\+|\$[\d,]+\s*-")


def is_scanned(pdf_text):
    """True when the extracted PTR text is effectively empty (scanned image).

    Scanned PTRs (DocIDs not starting with '2') yield no extractable text;
    we strip NUL bytes/whitespace and treat the remainder as the signal.
    """
    if pdf_text is None:
        return True
    return pdf_text.replace(_NUL, "").strip() == ""


def _is_header(line):
    return any(frag in line for frag in _HEADER_FRAGMENTS)


def _clean_lines(pdf_text):
    text = pdf_text.replace(_NUL, "")
    out = []
    for raw in text.splitlines():
        ln = raw.rstrip()
        if ln.strip() == "":
            continue
        if _is_header(ln):
            continue
        out.append(ln)
    return out


def parse_ptr_transactions(pdf_text):
    """Parse extracted PTR PDF text into a list of transaction dicts.

    Each dict: ``ticker`` (str or None for assets with no ticker, e.g. treasuries),
    ``asset_name`` (str), ``txn_type`` (P | S | S (partial)), ``txn_date``
    (MM/DD/YYYY), ``amount_label`` (canonical bucket string).

    Returns ``[]`` for scanned/empty input (caller should flag ``is_scanned``).
    Reflows wrapped amount-high and asset-name continuation lines per record.
    Rejects any record that would carry a dirty value.
    """
    if is_scanned(pdf_text):
        return []

    lines = _clean_lines(pdf_text)
    txns = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        m = _PRIMARY_RE.search(line)
        if not m:
            i += 1
            continue

        # --- assemble the amount label (may wrap to following lines) ---
        amt = re.sub(r"\s+", " ", m.group("amt")).strip()
        # collect the descriptive head (owner + asset start) before the match
        head = line[: m.start()].strip()

        # gather continuation lines until the next sub-line / primary / chrome
        j = i + 1
        cont = []
        while j < n:
            nxt = lines[j]
            if nxt.startswith(("F S:", "S O:", "D:", "I V D", "I P O")):
                break
            if _PRIMARY_RE.search(nxt):
                break
            cont.append(nxt.strip())
            j += 1

        # if amount ended in a bare dash, the high is on a continuation line
        # (often after the asset-type code, e.g. "[ST] $50,000"). Pull just the
        # trailing "$nnn" token off that line; keep the rest as asset text.
        if amt.endswith("-"):
            for k, c in enumerate(cont):
                hm = _AMT_HIGH_RE.search(c)
                if hm:
                    amt = (amt + " " + hm.group(0)).strip()
                    cont[k] = c[: hm.start()].strip()
                    break

        # --- build the full asset/description text (head + continuations) ---
        # strip a leading owner code off the head for asset name purposes
        asset_src = head
        owner_m = re.match(r"^(" + _OWNER + r")\s+(.*)$", asset_src)
        if owner_m:
            asset_src = owner_m.group(2)
        full_desc = " ".join([asset_src] + cont).strip()
        # drop any stray amount-high tokens left in the description
        full_desc = re.sub(r"\$[\d,]+\s*$", "", full_desc).strip()

        # --- ticker: first (TICKER) group in head or continuations ---
        ticker = None
        for src in [head] + cont:
            tm = _TICKER_RE.search(src)
            if tm:
                ticker = tm.group(1)
                break

        # --- canonicalize the amount label to a known bucket ---
        amount_label = _canonical_amount(amt)

        txn = {
            "ticker": clean(ticker),
            "asset_name": clean(full_desc),
            "txn_type": clean(m.group("type")),
            "txn_date": clean(m.group("txn_date")),
            "amount_label": amount_label,
        }
        # reject a record with any dirty REQUIRED value (ticker may be None)
        if (txn["asset_name"] and txn["txn_type"] and txn["txn_date"]
                and txn["amount_label"]):
            try:
                parse_amount_bucket(txn["amount_label"])
                txns.append(txn)
            except (ValueError, TypeError):
                pass  # off-schedule amount -> drop rather than store garbage

        i = j

    return txns


def _canonical_amount(amt):
    """Normalize a raw extracted amount fragment to a canonical bucket label."""
    s = re.sub(r"\s+", " ", amt).strip()
    # normalize spacing around the dash / plus to match bucket keys
    s = re.sub(r"\s*-\s*", " - ", s)
    s = re.sub(r"\s*\+\s*", " +", s)
    # match against known buckets directly
    norm = re.sub(r"\s+", " ", s).strip()
    if norm in _BUCKET_NORM:
        return norm
    return s


# ---------------------------------------------------------------------------
# Reporting lag
# ---------------------------------------------------------------------------

def _parse_mdy(s):
    s = clean(s)
    if s is None:
        raise ValueError("empty date")
    mo, da, yr = s.split("/")
    return date(int(yr), int(mo), int(da))


def reporting_lag_days(txn_date, filing_date):
    """Days between transaction and filing: filing_date - transaction_date.

    Both dates are MM/DD/YYYY (zero-padding optional). Delayed disclosures —
    this lag can reach ~45 days; the trades are NOT real-time.
    """
    t = _parse_mdy(txn_date)
    f = _parse_mdy(filing_date)
    return (f - t).days


# ---------------------------------------------------------------------------
# Canonical record
# ---------------------------------------------------------------------------

def to_record(filing, txn, sector, retrieved_at, source_url):
    """Build the canonical, validated ``congress_trade`` record.

    Combines an index ``filing`` row with a parsed ``txn`` dict. Validates
    required fields and the amount bucket before returning; raises ValueError on
    dirty data or a missing provenance stamp.
    """
    if not clean(retrieved_at) or not clean(source_url):
        raise ValueError("retrieved_at and source_url stamps are required")

    ticker = clean(txn.get("ticker"))
    asset = clean(txn.get("asset_name"))
    txn_type = clean(txn.get("txn_type"))
    txn_date = clean(txn.get("txn_date"))
    amount_label = clean(txn.get("amount_label"))

    if not asset or not txn_type or not txn_date or not amount_label:
        raise ValueError(f"dirty/incomplete transaction: {txn!r}")

    low, high = parse_amount_bucket(amount_label)  # raises on garbage

    filing_date = clean(filing.get("FilingDate"))
    if not filing_date:
        raise ValueError("filing row missing FilingDate")

    first = clean(filing.get("First")) or ""
    last = clean(filing.get("Last")) or ""
    politician = (first + " " + last).strip()
    if not politician:
        raise ValueError("filing row missing politician name")

    return {
        "politician": politician,
        "chamber": "House",
        "state": clean(filing.get("StateDst")),
        "party": clean(filing.get("Party")),  # not in House FD index -> None
        "ticker": ticker,
        "sector": clean(sector),
        "asset": asset,
        "txn_type": txn_type,
        "txn_date": txn_date,
        "filing_date": filing_date,
        "reporting_lag_days": reporting_lag_days(txn_date, filing_date),
        "amount_range_low": low,
        "amount_range_high": high,
        "source": clean(source_url),
        "source_class": "filing",
        "retrieved_at": clean(retrieved_at),
    }
