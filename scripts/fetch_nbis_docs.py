"""Fetch NBIS SEC documents using proper User-Agent."""
import sys
import requests

USER_AGENT = "AIInvestment research (easyresumeai@outlook.fr)"

DOCS = [
    # Latest 20-F annual report (FY2025)
    ("20-F", "2026-04-30", "https://www.sec.gov/Archives/edgar/data/1513845/000110465926052948/nbis-20251231x20f.htm"),
    # Latest 20-F/A amendment
    ("20-F/A", "2026-05-22", "https://www.sec.gov/Archives/edgar/data/1513845/000110465926065681/nbis-20251231x20fa.htm"),
    # Q1 2026 results 6-K (May 2026)
    ("6-K", "2026-05-20", "https://www.sec.gov/Archives/edgar/data/1513845/000110465926064092/nbis-20260331x6k.htm"),
    # Feb 2026 6-K
    ("6-K", "2026-02-12", "https://www.sec.gov/Archives/edgar/data/1513845/000110465926013947/tm266173d2_6k.htm"),
    # Nov 2025 6-K (Q3 results)
    ("6-K", "2025-11-12", "https://www.sec.gov/Archives/edgar/data/1513845/000110465925110028/tm2530882d3_6k.htm"),
]

session = requests.Session()
session.headers.update({'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xhtml+xml'})

for form, date, url in DOCS:
    print(f"\n{'='*80}")
    print(f"FORM: {form} | DATE: {date}")
    print(f"URL: {url}")
    print('='*80, flush=True)
    try:
        resp = session.get(url, timeout=60)
        print(f"Status: {resp.status_code}", flush=True)
        if resp.status_code == 200:
            # Print first 20000 chars
            text = resp.text
            print(f"Length: {len(text)} chars")
            print(text[:25000])
        else:
            print(f"ERROR: {resp.status_code} {resp.reason}")
    except Exception as e:
        print(f"EXCEPTION: {e}")
    print("", flush=True)
