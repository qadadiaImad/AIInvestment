"""Fetch QCOM SEC filings metadata and document URLs for edge extraction."""
from __future__ import annotations
import json
import requests
import aiinvest.edgar as edgar

UA = edgar.USER_AGENT
sess = requests.Session()
sess.headers.update({"User-Agent": UA})

# 1. Get CIK
mapping = edgar.fetch_company_tickers(session=sess)
cik = edgar.ticker_to_cik("QCOM", mapping)
print(f"QCOM CIK: {cik}")

# 2. Fetch filings list
rows, raw = edgar.fetch_submissions(cik, session=sess)
print(f"Total filings: {len(rows)}")

# 3. Filter to 10-K, 10-Q, 8-K
target_forms = {"10-K", "10-Q", "8-K"}
filtered = edgar.filter_filings(rows, target_forms)
print(f"10-K/10-Q/8-K filings: {len(filtered)}")

# Show latest of each type
for form in ["10-K", "10-Q", "8-K"]:
    latest = next((r for r in filtered if r["form"] == form), None)
    if latest:
        url = edgar.filing_url(cik, latest["accession"], latest["primary_document"])
        print(f"\nLatest {form}: {latest['filing_date']}")
        print(f"  URL: {url}")
        print(f"  Accession: {latest['accession']}")

# Print top 5 of each
print("\n--- 10-K filings ---")
for r in [x for x in filtered if x["form"] == "10-K"][:3]:
    url = edgar.filing_url(cik, r["accession"], r["primary_document"])
    print(f"  {r['filing_date']}: {url}")

print("\n--- 10-Q filings ---")
for r in [x for x in filtered if x["form"] == "10-Q"][:3]:
    url = edgar.filing_url(cik, r["accession"], r["primary_document"])
    print(f"  {r['filing_date']}: {url}")

print("\n--- 8-K filings ---")
for r in [x for x in filtered if x["form"] == "8-K"][:5]:
    url = edgar.filing_url(cik, r["accession"], r["primary_document"])
    print(f"  {r['filing_date']}: {url}")
