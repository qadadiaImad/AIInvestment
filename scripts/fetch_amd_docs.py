"""Fetch AMD SEC filings content using edgar USER_AGENT"""
import sys
import requests
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

HEADERS = {"User-Agent": edgar.USER_AGENT}

def fetch_text(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text

urls = {
    "10K_2025": "https://www.sec.gov/Archives/edgar/data/2488/000000248826000018/amd-20251227.htm",
    "10Q_2026Q1": "https://www.sec.gov/Archives/edgar/data/2488/000000248826000076/amd-20260328.htm",
    "8K_20260515": "https://www.sec.gov/Archives/edgar/data/2488/000119312526226746/d118163d8k.htm",
    "8K_20260505": "https://www.sec.gov/Archives/edgar/data/2488/000000248826000072/amd-20260505.htm",
}

for name, url in urls.items():
    print(f"\n{'='*60}")
    print(f"Fetching {name}: {url}")
    try:
        text = fetch_text(url)
        print(f"  Length: {len(text)} chars")
        # Save to file for inspection
        with open(f"C:/Users/imadq/AIInvestment/data/enrich/amd_{name}.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  Saved to data/enrich/amd_{name}.txt")
    except Exception as e:
        print(f"  ERROR: {e}")
