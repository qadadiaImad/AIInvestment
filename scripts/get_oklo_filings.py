import sys
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

# Fetch ticker->CIK mapping
mapping = edgar.fetch_company_tickers()
cik = edgar.ticker_to_cik("OKLO", mapping)
print(f"OKLO CIK: {cik}")

# Fetch filing history
rows, raw = edgar.fetch_submissions(cik)
# Get recent 10-K, 10-Q, 8-K filings
relevant = edgar.filter_filings(rows, {"10-K", "10-Q", "8-K", "S-1", "S-4", "20-F"})
print(f"Total recent filings: {len(rows)}")
print(f"10-K/10-Q/8-K/S-1 filings: {len(relevant)}")
for r in relevant[:20]:
    url = edgar.filing_url(cik, r['accession'], r['primary_document'])
    print(f"  {r['form']} {r['filing_date']} -> {url}")
