import sys
import requests
import re
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

UA = edgar.USER_AGENT
HEADERS = {"User-Agent": UA}

def fetch_text(url, max_chars=200000):
    r = requests.get(url, headers=HEADERS, timeout=60)
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

# Q4 2025 slides (ex99.1)
slides_url = "https://www.sec.gov/Archives/edgar/data/81033/000119312526073678/d57788dex991.htm"
print(f"Fetching Q4 2025 slides...")
try:
    raw = fetch_text(slides_url, 200000)
    text = extract_text_from_html(raw)
    print(f"Text length: {len(text)}")

    keywords = [
        'data center', 'large load', '11,800', 'megawatt', 'nuclear offtake',
        'Oracle', 'Google', 'Amazon', 'Microsoft', 'Meta', 'PPA', 'offtake',
        'load pipeline', 'power purchase'
    ]

    seen_snippets = set()
    for kw in keywords:
        pos = 0
        count = 0
        while count < 3:
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
        print("No keywords found")
        print(text[:1000])
except Exception as e:
    print(f"Error: {e}")
