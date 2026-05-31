import sys
import requests
import re
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

UA = edgar.USER_AGENT
HEADERS = {"User-Agent": UA}

def fetch_text(url, max_chars=500000):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.text[:max_chars]

def extract_text_from_html(html):
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Get 8-K index files to find exhibits (press releases, etc.)
# These may be the HTML or txt exhibits
eight_k_accessions = [
    ("2026-04-23", "788784", "000119312526173855"),
    ("2026-01-21", "788784", "000119312526018045"),
    ("2025-04-25", "788784", "000119312525097067"),
    ("2025-03-10", "788784", "000119312525050925"),
    ("2024-11-19", "788784", "000095017024128681"),
]

for date, cik, acc in eight_k_accessions:
    acc_dashes = f"{acc[:10]}-{acc[10:12]}-{acc[12:]}"
    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{acc_dashes}-index.htm"
    print(f"\n{'='*60}")
    print(f"8-K {date}: index at {index_url}")
    try:
        raw = fetch_text(index_url, 20000)
        # Find all document links
        doc_links = re.findall(r'href="(/Archives/edgar/data/[^"]+)"', raw)
        docs_in_text = re.findall(r'<td[^>]*>([^<]*\.(?:htm|txt|pdf))</td>', raw, re.IGNORECASE)
        print(f"  Doc links found: {doc_links[:10]}")
        print(f"  Docs in text: {docs_in_text[:10]}")

        # Look for exhibit files (press releases are usually ex99.htm or similar)
        for link in doc_links[:10]:
            if any(x in link.lower() for x in ['ex99', 'ex-99', 'exhibit', 'press']):
                print(f"  Possible exhibit: {link}")
    except Exception as e:
        print(f"  Error: {e}")
