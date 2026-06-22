import sys
import requests
import re
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

USER_AGENT = edgar.USER_AGENT
headers = {"User-Agent": USER_AGENT}

# Get the latest 8-Ks
mapping = edgar.fetch_company_tickers()
cik = edgar.ticker_to_cik("NRG", mapping)
rows, raw = edgar.fetch_submissions(cik)

# Get latest 8-K filings
eightks = edgar.filter_filings(rows, {"8-K"})
print(f"Total 8-K filings: {len(eightks)}")

# Look at the most recent 5
for f in eightks[:5]:
    url = edgar.filing_url(cik, f['accession'], f['primary_document'])
    print(f"\n8-K filed {f['filing_date']}: {url}")

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            text = resp.text
            clean = re.sub(r'<[^>]+>', ' ', text)
            clean = re.sub(r'\s+', ' ', clean)

            # Check for AI/datacenter/deal keywords
            kws = ['data center', 'hyperscal', 'Microsoft', 'Google', 'Amazon', 'Meta',
                   'AI', 'artificial intelligence', 'power purchase', 'GW', 'MW',
                   'GE Vernova', 'agreement', 'partnership', 'PPA']
            found_any = False
            for kw in kws:
                if kw.lower() in clean.lower():
                    idx = clean.lower().find(kw.lower())
                    start = max(0, idx - 150)
                    end = min(len(clean), idx + 300)
                    if not found_any:
                        print(f"  Content preview (first 500 chars): {clean[:500]}")
                        found_any = True
                    print(f"  KW '{kw}': ...{clean[start:end].strip()}...")
                    break
            if not found_any:
                print(f"  (no relevant keywords found)")
        else:
            print(f"  Status: {resp.status_code}")
    except Exception as e:
        print(f"  Error: {e}")
