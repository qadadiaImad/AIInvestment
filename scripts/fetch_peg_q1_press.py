import sys
import requests
import re
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

UA = edgar.USER_AGENT
HEADERS = {"User-Agent": UA}

def fetch_text(url, max_chars=400000):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.text[:max_chars]

def extract_text_from_html(html):
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    # Clean HTML entities
    text = text.replace('&nbsp;', ' ').replace('&#149;', '•').replace('&#146;', "'")
    text = text.replace('&#147;', '"').replace('&#148;', '"').replace('&#8217;', "'")
    text = text.replace('&#8220;', '"').replace('&#8221;', '"').replace('&#8211;', '-')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Q1 2026 press release (the ex99)
press_urls = [
    ("Q1 2026 ex99", "https://www.sec.gov/Archives/edgar/data/81033/000119312526205254/d63722dex99.htm"),
    ("Q1 2026 ex99.1 (slides?)", "https://www.sec.gov/Archives/edgar/data/81033/000119312526205254/d63722dex991.htm"),
    # Q3 2025 (the 8-K on 2025-11-03, see if it has ex99)
]

ai_dc_keywords = [
    'data center', 'datacenter', 'Oracle', 'Google', 'Microsoft', 'Amazon',
    'large load', 'nuclear offtake', 'megawatt', 'gigawatt', 'GW', 'MW',
    'power purchase', 'behind the meter', 'coloc', 'carbon-free',
    'New Jersey', 'Hope Creek', 'Salem', 'Peach Bottom',
    'pipeline', '11,800', '11800', '1.4', '1 GW', 'offtake',
]

for name, url in press_urls:
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
                end = min(len(text), pos + 500)
                snippet = text[start:end].strip()
                snippet_key = snippet[:80]
                if snippet_key not in seen_snippets:
                    seen_snippets.add(snippet_key)
                    print(f"\n  [KW: {kw}]")
                    print(f"  ...{snippet}...")
                    found_any = True
                pos += len(kw)

        if not found_any:
            print(f"  No keywords found")
            print(f"  Preview: {text[:1000]}")
    except Exception as e:
        print(f"  Error: {e}")
