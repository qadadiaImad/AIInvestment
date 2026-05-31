import sys
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

# Fetch company tickers mapping
print("Fetching company tickers...")
mapping = edgar.fetch_company_tickers()

# Resolve AMD CIK
cik = edgar.ticker_to_cik("AMD", mapping)
print(f"AMD CIK: {cik}")

# Fetch submissions
rows, raw = edgar.fetch_submissions(cik)

# Filter for 10-K, 10-Q, 8-K
filings = edgar.filter_filings(rows, {"10-K", "10-Q", "8-K"})
print(f"Total filings (10-K/10-Q/8-K): {len(filings)}")

# Show latest 10 filings
for f in filings[:10]:
    url = edgar.filing_url(cik, f['accession'], f['primary_document'])
    print(f"  {f['form']} {f['filing_date']}: {url}")
