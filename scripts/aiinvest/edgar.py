"""SEC EDGAR REST helper — the IPO source of truth (S-1s, 10-Ks, filing history).

REST-first, no browser. SEC requires a descriptive User-Agent with contact info and
fair-access ≤10 req/s. Pure logic (pad/map/parse/url) is unit-tested; the `fetch_*`
functions are the thin network layer.
"""
from __future__ import annotations

# SEC asks for a real contact in the UA (project owner's email).
USER_AGENT = "AIInvestment research (easyresumeai@outlook.fr)"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANY_CONCEPT_URL = ("https://data.sec.gov/api/xbrl/companyconcept/"
                       "CIK{cik}/us-gaap/{concept}.json")


def pad_cik(cik):
    """Zero-pad a CIK to the 10 digits EDGAR endpoints require."""
    return str(int(str(cik).lstrip("0") or "0")).zfill(10)


def ticker_to_cik(ticker, mapping):
    """Resolve a ticker to a padded CIK via the company_tickers.json mapping."""
    t = ticker.upper()
    for row in mapping.values():
        if row.get("ticker", "").upper() == t:
            return pad_cik(row["cik_str"])
    return None


def parse_submissions(submissions):
    """Flatten the columnar ``filings.recent`` arrays into a list of filing rows."""
    recent = submissions.get("filings", {}).get("recent", {})
    accessions = recent.get("accessionNumber", [])
    return [
        {
            "accession": accessions[i],
            "filing_date": recent.get("filingDate", [])[i],
            "form": recent.get("form", [])[i],
            "primary_document": recent.get("primaryDocument", [])[i],
        }
        for i in range(len(accessions))
    ]


def filter_filings(rows, forms):
    """Keep only filings whose form is in ``forms`` (e.g. {"S-1", "10-K"})."""
    forms = set(forms)
    return [r for r in rows if r["form"] in forms]


def filing_url(cik, accession, primary_document):
    """Public Archives URL for a filing's primary document."""
    cik_int = int(str(cik).lstrip("0") or "0")
    acc = accession.replace("-", "")
    return (f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc}/"
            f"{primary_document}")


def _get(url, timeout=20, session=None):
    import requests
    http = session or requests
    resp = http.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def fetch_company_tickers(session=None):
    """Download the ticker -> CIK mapping (cache this; it's large-ish)."""
    return _get(COMPANY_TICKERS_URL, session=session)


def fetch_submissions(cik, session=None):
    """Fetch a company's filing history; returns parsed filing rows + the raw doc."""
    raw = _get(SUBMISSIONS_URL.format(cik=pad_cik(cik)), session=session)
    return parse_submissions(raw), raw
