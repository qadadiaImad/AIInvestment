import sys
import requests
import re
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

UA = edgar.USER_AGENT
HEADERS = {"User-Agent": UA}

def fetch_text(url, max_chars=300000):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.text[:max_chars]

def extract_text_from_html(html):
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# These are ex99 press releases from 8-K filings
press_release_urls = [
    # Q4 2025 earnings press release
    ("Q4 2025 press release", "https://www.sec.gov/Archives/edgar/data/788784/000119312526073678/d57788dex99.htm"),
    # Q2 2025 earnings
    ("Q2 2025 press release", "https://www.sec.gov/Archives/edgar/data/788784/000119312525173127/d206274dex99.htm"),
]

ai_dc_keywords = [
    'data center', 'datacenter', 'artificial intelligence', 'hyperscal',
    'power purchase', 'nuclear', 'behind the meter', 'co-locat',
    'Microsoft', 'Amazon', 'Google', 'Meta', 'large load',
    'gigawatt', 'megawatt', 'PPA', 'compute', 'NRG', 'Talen', 'Constellation',
    'load growth', 'clean energy', 'large customer', 'offtake',
    'Amazon Web Services', 'AWS', 'MSFT',
]

for name, url in press_release_urls:
    print(f"\n{'='*60}")
    print(f"{name}: {url}")
    try:
        raw = fetch_text(url, 300000)
        text = extract_text_from_html(raw)
        print(f"  Text length: {len(text)}")

        found_any = False
        seen_snippets = set()
        for kw in ai_dc_keywords:
            pos = 0
            while True:
                pos = text.lower().find(kw.lower(), pos)
                if pos == -1:
                    break
                start = max(0, pos - 200)
                end = min(len(text), pos + 400)
                snippet = text[start:end].strip()
                snippet_key = snippet[:80]
                if snippet_key not in seen_snippets:
                    seen_snippets.add(snippet_key)
                    print(f"\n  [KW: {kw}]")
                    print(f"  ...{snippet}...")
                    found_any = True
                pos += len(kw)

        if not found_any:
            print(f"  No AI/DC keywords found")
            print(f"  Preview: {text[:1000]}")
    except Exception as e:
        print(f"  Error: {e}")
