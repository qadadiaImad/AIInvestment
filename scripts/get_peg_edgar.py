import sys
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

# Get tickers mapping
tickers_map = edgar.fetch_company_tickers()
cik = edgar.ticker_to_cik('PEG', tickers_map)
print(f"PEG CIK: {cik}")

# Get filings
rows, raw = edgar.fetch_submissions(cik)
# Filter for 10-K, 10-Q, 8-K
filtered = edgar.filter_filings(rows, {'10-K', '10-Q', '8-K'})
for r in filtered[:20]:
    url = edgar.filing_url(cik, r['accession'], r['primary_document'])
    print(f"{r['form']} {r['filing_date']} -> {url}")
