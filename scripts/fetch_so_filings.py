import sys
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar
import json

# Fetch company tickers to get SO's CIK
print("Fetching company tickers...")
mapping = edgar.fetch_company_tickers()
cik = edgar.ticker_to_cik("SO", mapping)
print(f"SO CIK: {cik}")

# Fetch submissions
print("Fetching submissions...")
rows, raw = edgar.fetch_submissions(cik)

# Filter for 10-K, 10-Q, 8-K filings
relevant = edgar.filter_filings(rows, {"10-K", "10-Q", "8-K"})
print(f"Total relevant filings: {len(relevant)}")

# Show the 10 most recent
print("\nMost recent filings:")
for r in relevant[:15]:
    url = edgar.filing_url(cik, r['accession'], r['primary_document'])
    print(f"  {r['filing_date']} {r['form']} {url}")

# Get the latest 10-K
tenk = [r for r in relevant if r['form'] == '10-K']
if tenk:
    latest_10k = tenk[0]
    url = edgar.filing_url(cik, latest_10k['accession'], latest_10k['primary_document'])
    print(f"\nLatest 10-K: {latest_10k['filing_date']} {url}")

# Get most recent 8-Ks
eightk = [r for r in relevant if r['form'] == '8-K']
print(f"\nRecent 8-Ks:")
for r in eightk[:10]:
    url = edgar.filing_url(cik, r['accession'], r['primary_document'])
    print(f"  {r['filing_date']} {url}")
