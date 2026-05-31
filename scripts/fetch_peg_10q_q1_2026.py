import sys
import requests
import re
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

UA = edgar.USER_AGENT
HEADERS = {"User-Agent": UA}

def fetch_text(url, max_chars=500000):
    r = requests.get(url, headers=HEADERS, timeout=90)
    r.raise_for_status()
    return r.text[:max_chars]

def extract_text_from_html(html):
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = text.replace('&nbsp;', ' ').replace('&#149;', '•').replace('&#146;', "'")
    text = text.replace('&#147;', '"').replace('&#148;', '"').replace('&#8217;', "'")
    text = re.sub(r'&#[0-9]+;', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Get the Q1 2026 10-Q (filed 2026-05-05, accession 000119312526206545)
# peg-20260331.htm is the main document
url_10q = "https://www.sec.gov/Archives/edgar/data/788784/000119312526206545/peg-20260331.htm"
print(f"Fetching Q1 2026 10-Q...")
raw = fetch_text(url_10q, 500000)
text = extract_text_from_html(raw)
print(f"Text length: {len(text)}")

# Search for data center / large load / nuclear offtake content
keywords = [
    'data center', 'large load', 'nuclear offtake', 'power purchase agreement',
    'Oracle', 'Google', 'Amazon', 'Microsoft', 'Meta', 'large customer',
    'megawatt', '11,800', '11800', 'offtake', 'behind the meter',
    'data centers'
]

seen_snippets = set()
for kw in keywords:
    pos = 0
    while True:
        pos = text.lower().find(kw.lower(), pos)
        if pos == -1:
            break
        start = max(0, pos - 200)
        end = min(len(text), pos + 500)
        snippet = text[start:end].strip()
        key = snippet[:80]
        if key not in seen_snippets:
            seen_snippets.add(key)
            print(f"\n[KW: {kw}]")
            print(f"...{snippet}...")
        pos += len(kw)
