"""Fetch AMZN SEC filings (10-K, 10-Q, 8-K) and print URLs + snippets."""
import requests
from aiinvest import edgar

session = requests.Session()

# Step 1: resolve CIK
mapping = edgar.fetch_company_tickers(session=session)
cik = edgar.ticker_to_cik('AMZN', mapping)
print(f"AMZN CIK: {cik}")

# Step 2: fetch filings list
filings, raw = edgar.fetch_submissions(cik, session=session)
print(f"Total filings in recent history: {len(filings)}")

# Step 3: filter for 10-K, 10-Q, 8-K
target_forms = {'10-K', '10-Q', '8-K'}
relevant = edgar.filter_filings(filings, target_forms)
print(f"Relevant filings (10-K/10-Q/8-K): {len(relevant)}")

# Step 4: show top 10 with URLs
for f in relevant[:10]:
    url = edgar.filing_url(cik, f['accession'], f['primary_document'])
    print(f"  {f['form']} | {f['filing_date']} | {url}")
