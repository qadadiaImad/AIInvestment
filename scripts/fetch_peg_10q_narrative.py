import sys
import requests
import re
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

UA = edgar.USER_AGENT
HEADERS = {"User-Agent": UA}

def fetch_text(url, max_chars=2000000):
    r = requests.get(url, headers=HEADERS, timeout=120)
    r.raise_for_status()
    return r.text[:max_chars]

def extract_text_from_html(html):
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = text.replace('&nbsp;', ' ').replace('&#149;', '•').replace('&#146;', "'")
    text = re.sub(r'&#[0-9]+;', ' ', text)
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Try the 10-Q directly
url_10q = "https://www.sec.gov/Archives/edgar/data/81033/000119312526206545/peg-20260331.htm"
print("Fetching Q1 2026 10-Q (large)...")
raw = fetch_text(url_10q, 2000000)
print(f"Raw size: {len(raw)}")

text = extract_text_from_html(raw)
print(f"Text size: {len(text)}")

keywords = [
    'data center', 'large load', 'nuclear offtake', 'power purchase',
    'Oracle', 'Google', 'Amazon', 'Microsoft', 'Meta',
    '11,', 'megawatt', 'offtake', 'behind the meter', 'coloc',
]

seen_snippets = set()
for kw in keywords:
    pos = 0
    count = 0
    while count < 3:  # limit per keyword
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
        count += 1

if not seen_snippets:
    print("No keywords found. Showing preview:")
    print(text[:2000])
