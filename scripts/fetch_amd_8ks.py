"""Fetch AMD 8-K SEC filings for OpenAI and Meta deals"""
import sys
import requests
import re
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

HEADERS = {"User-Agent": edgar.USER_AGENT}

def fetch_text(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text

def clean_html(text):
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'&amp;', '&', clean)
    clean = re.sub(r'&nbsp;', ' ', clean)
    clean = re.sub(r'&#\d+;', '', clean)
    clean = re.sub(r'&[a-z]+;', '', clean)
    clean = re.sub(r'\s+', ' ', clean)
    return clean

urls = {
    "8K_openai_oct2025": "https://www.sec.gov/Archives/edgar/data/2488/000119312525230895/d28189d8k.htm",
    "8K_openai_press_release": "https://www.sec.gov/Archives/edgar/data/0000002488/000119312525230895/d28189dex991.htm",
    "8K_meta_feb2026": "https://www.sec.gov/Archives/edgar/data/0000002488/000000248826000045/pressreleasedatedfebruary2.htm",
    "8K_meta_8k_form": "https://www.sec.gov/Archives/edgar/data/0000002488/000000248826000045/amd-20260223.htm",
}

for name, url in urls.items():
    print(f"\n{'='*60}")
    print(f"Fetching {name}: {url}")
    try:
        text = fetch_text(url)
        clean = clean_html(text)
        print(f"  Length: {len(clean)} chars")
        # Save
        with open(f"C:/Users/imadq/AIInvestment/data/enrich/amd_{name}.txt", "w", encoding="utf-8") as f:
            f.write(clean)
        print(f"  Saved: data/enrich/amd_{name}.txt")
        # Print excerpt
        print(f"  Excerpt: {clean[:1000]}")
    except Exception as e:
        print(f"  ERROR: {e}")
