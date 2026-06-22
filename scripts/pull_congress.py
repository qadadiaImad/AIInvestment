"""Pull House Congress-trading PTRs (STOCK Act) -> stamped congress_trade JSON.

REST-first per CLAUDE.md, Mode A (static HTTPS asset, ungated). Pipeline:

    1. GET the House Clerk annual FD ZIP for --year (default 2026)
    2. parse the {YEAR}FD.xml index via aiinvest.congress.parse_fd_index
    3. keep only PTRs (FilingType == 'P')
    4. for each PTR (capped by --limit): download the PTR PDF, extract text with
       pdfplumber, parse transactions via aiinvest.congress.parse_ptr_transactions.
       A scanned-image PTR yields empty text -> FLAG (is_scanned) and SKIP, never guess.
    5. join a SECTOR for each ticker via the TradingView scanner market-scan
       (name in_range [...]) -- works for ANY sector, batched + cached. Unresolved
       tickers get sector=None (a flag), never a crash.
    6. assemble each row via aiinvest.congress.to_record (stamps retrieved_at UTC,
       exact PDF source URL, source_class='filing').
    7. write data/congress/house_{year}.json with a provenance header.

Honesty rails (CLAUDE.md + the congress-trading-feasibility spec):
- House PTR amounts are RANGE BUCKETS, never exact -> amount_range_low/high only.
- reporting_lag_days = filing_date - txn_date (up to ~45 days; NOT real-time).
- Every record stamped retrieved_at (UTC ISO-8601) / source (exact URL) /
  source_class='filing'. Scanned PDFs flagged+skipped. Dirty values rejected.

Educational/research only -- not investment advice. Not an accusation of
wrongdoing against any individual.

Usage:
    python pull_congress.py                      # year=2026, limit=50
    python pull_congress.py --year 2025 --limit 25
    python pull_congress.py --out ../data --delay 1.0
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import pathlib
import time
import zipfile

import requests

from aiinvest import congress

# A real, descriptive User-Agent with a contact email. The House root portal
# 403s generic fetchers; the static asset paths return 200 for an honest UA.
_UA = ("AIInvestment-research/1.0 (educational; data-acquisition; "
       "contact easyresumeai@outlook.fr)")

_ZIP_URL = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip"
_PDF_URL = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{docid}.pdf"

_DISCLAIMER = (
    "Educational/research only -- not investment advice; amounts are reported "
    "ranges; up to 45-day lag. Self-reported, unverified STOCK Act filings with "
    "the U.S. House Clerk. Not an accusation of wrongdoing against any individual."
)


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


# ---------------------------------------------------------------------------
# Network layer (thin; parsing/joining lives in aiinvest.congress + pure helpers)
# ---------------------------------------------------------------------------

def download_fd_index_xml(year, session=None, timeout=60):
    """Download the annual FD ZIP and return the {YEAR}FD.xml bytes."""
    http = session or requests
    url = _ZIP_URL.format(year=year)
    resp = http.get(url, headers={"User-Agent": _UA}, timeout=timeout)
    resp.raise_for_status()
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    name = f"{year}FD.xml"
    if name not in zf.namelist():
        # fall back to whatever .xml the archive carries
        xmls = [n for n in zf.namelist() if n.lower().endswith(".xml")]
        if not xmls:
            raise RuntimeError(f"no XML index in {url}: {zf.namelist()}")
        name = xmls[0]
    return zf.read(name)


def download_ptr_text(year, docid, session=None, timeout=60):
    """Download a PTR PDF and extract its text. Returns (text, pdf_url, status).

    text is "" when the HTTP fetch fails or the PDF carries no extractable text
    (scanned image) -- the caller flags is_scanned and skips, never guesses.
    """
    import pdfplumber

    http = session or requests
    url = _PDF_URL.format(year=year, docid=docid)
    resp = http.get(url, headers={"User-Agent": _UA}, timeout=timeout)
    if resp.status_code != 200:
        return "", url, resp.status_code
    try:
        with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
            text = "\n".join((page.extract_text() or "") for page in pdf.pages)
    except Exception:
        text = ""
    return text, url, resp.status_code


# ---------------------------------------------------------------------------
# Sector join (the sector-recon approach: TradingView market scan, name in_range)
# ---------------------------------------------------------------------------

_SECTOR_SCAN_URL = "https://scanner.tradingview.com/america/scan"
_SECTOR_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def lookup_sectors(tickers, session=None, timeout=25, batch=200):
    """Resolve {ticker -> sector} for ANY sector via the TradingView scanner.

    Uses a market-wide scan filtered by ``name in_range [tickers]`` so bare
    tickers (no exchange prefix) resolve. Batched to respect rate limits; the
    result is a cache the caller reuses across rows. Tickers that don't resolve
    are simply absent from the map -> caller assigns sector=None + a flag.
    """
    http = session or requests
    syms = sorted({t for t in tickers if t})
    out = {}
    for start in range(0, len(syms), batch):
        chunk = syms[start:start + batch]
        payload = {
            "filter": [{"left": "name", "operation": "in_range", "right": chunk}],
            "columns": ["name", "sector", "industry", "description"],
            "range": [0, len(chunk)],
        }
        resp = http.post(_SECTOR_SCAN_URL, json=payload,
                         headers={"User-Agent": _SECTOR_UA}, timeout=timeout)
        resp.raise_for_status()
        for row in resp.json().get("data", []):
            d = row.get("d", []) or []
            if not d:
                continue
            name = d[0]
            out[name] = {
                "sector": d[1] if len(d) > 1 else None,
                "industry": d[2] if len(d) > 2 else None,
                "description": d[3] if len(d) > 3 else None,
                "tv_symbol": row.get("s"),
            }
    return out


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Pull House STOCK Act PTRs -> stamped congress_trade JSON (Mode A, REST).")
    ap.add_argument("--year", type=int, default=_utc_now().year,
                    help="FD index year (default: current year).")
    ap.add_argument("--limit", type=int, default=50,
                    help="Max PTRs to process (polite smoke run; default 50).")
    ap.add_argument("--delay", type=float, default=0.8,
                    help="Seconds to wait between PDF downloads (politeness).")
    ap.add_argument("--out", default=str(
        pathlib.Path(__file__).resolve().parent.parent / "data"),
        help="Output root directory (default: ../data).")
    args = ap.parse_args(argv)

    now = _utc_now()
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    session = requests.Session()

    # 1-3: index -> PTRs
    zip_url = _ZIP_URL.format(year=args.year)
    print(f"Downloading {zip_url} ...")
    index_xml = download_fd_index_xml(args.year, session=session)
    rows = congress.parse_fd_index(index_xml)
    ptrs = congress.filter_ptrs(rows)
    print(f"Index: {len(rows)} filings, {len(ptrs)} PTRs. "
          f"Processing up to {args.limit}.")

    ptrs = ptrs[: args.limit]

    # 4: download + extract + parse each PTR
    parsed = []          # list of (filing, [txn,...], pdf_url)
    scanned_skipped = []  # list of docids flagged is_scanned
    http_failed = []      # docids whose PDF didn't return 200
    for idx, filing in enumerate(ptrs, 1):
        docid = filing.get("DocID")
        if not docid:
            continue
        text, pdf_url, status = download_ptr_text(args.year, docid, session=session)
        if status != 200:
            http_failed.append({"docid": docid, "status": status, "url": pdf_url})
        elif congress.is_scanned(text):
            scanned_skipped.append({"docid": docid, "is_scanned": True, "url": pdf_url})
        else:
            txns = congress.parse_ptr_transactions(text)
            parsed.append((filing, txns, pdf_url))
        if idx < len(ptrs):
            time.sleep(args.delay)

    # 5: sector join (batched + cached) across all tickers seen
    all_tickers = {t["ticker"] for _, txns, _ in parsed for t in txns if t.get("ticker")}
    print(f"Resolving sectors for {len(all_tickers)} distinct tickers ...")
    sector_map = {}
    if all_tickers:
        try:
            sector_map = lookup_sectors(all_tickers, session=session)
        except Exception as exc:  # sector is enrichment; never fail the pull
            print(f"  sector lookup failed ({exc!r}); proceeding with sector=None")

    # 6: assemble stamped records
    records = []
    unresolved_sectors = set()
    for filing, txns, pdf_url in parsed:
        for txn in txns:
            tk = txn.get("ticker")
            sec_info = sector_map.get(tk) if tk else None
            sector = sec_info["sector"] if sec_info else None
            if tk and sec_info is None:
                unresolved_sectors.add(tk)
            try:
                rec = congress.to_record(
                    filing, txn, sector=sector,
                    retrieved_at=stamp, source_url=pdf_url,
                )
            except (ValueError, TypeError):
                continue  # dirty/incomplete txn -> drop, never store garbage
            rec["sector_unresolved"] = bool(tk) and sec_info is None
            rec["industry"] = sec_info["industry"] if sec_info else None
            records.append(rec)

    # 7: write output with a provenance header
    out_dir = pathlib.Path(args.out) / "congress"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"house_{args.year}.json"
    doc = {
        "provenance": {
            "generated_at": stamp,
            "source": zip_url,
            "source_class": "filing",
            "chamber": "House",
            "year": args.year,
            "retrieval_mode": "rest-mode-a",
            "ptrs_in_index": len(congress.filter_ptrs(rows)),
            "ptrs_processed": len(ptrs),
            "ptrs_with_records": len(parsed),
            "scanned_skipped": len(scanned_skipped),
            "http_failed": len(http_failed),
            "trade_records": len(records),
            "tickers_resolved": len(sector_map),
            "tickers_unresolved": sorted(unresolved_sectors),
            "disclaimer": _DISCLAIMER,
        },
        "scanned_skipped": scanned_skipped,
        "http_failed": http_failed,
        "trades": records,
    }
    out_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"  PTRs processed={len(ptrs)} with_records={len(parsed)} "
          f"scanned_skipped={len(scanned_skipped)} http_failed={len(http_failed)} "
          f"trade_records={len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
