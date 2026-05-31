"""Fetch AMZN filing content via requests with edgar USER_AGENT (no browser)."""
import requests
from aiinvest import edgar

session = requests.Session()
headers = {"User-Agent": edgar.USER_AGENT, "Accept-Encoding": "gzip, deflate"}

urls = {
    "10-K_2025": "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm",
    "10-Q_2026Q1": "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000014/amzn-20260331.htm",
    "8-K_2026-05-22": "https://www.sec.gov/Archives/edgar/data/1018724/000110465926065717/tm2614288d1_8k.htm",
    "8-K_2026-04-29": "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000012/amzn-20260429.htm",
}

import time

for label, url in urls.items():
    print(f"\n=== {label} === {url}")
    try:
        resp = session.get(url, headers=headers, timeout=30)
        print(f"Status: {resp.status_code}, Length: {len(resp.text)}")
        # Save to temp file
        fname = f"/tmp/amzn_{label}.txt"
        with open(fname, 'w', encoding='utf-8', errors='replace') as f:
            f.write(resp.text)
        print(f"Saved to {fname}")
    except Exception as e:
        print(f"ERROR: {e}")
    time.sleep(1)

print("\nDone fetching.")
