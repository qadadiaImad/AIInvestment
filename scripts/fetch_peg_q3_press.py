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
    text = text.replace('&nbsp;', ' ').replace('&#149;', '•').replace('&#146;', "'")
    text = text.replace('&#147;', '"').replace('&#148;', '"').replace('&#8217;', "'")
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Q3 2025 press release
press_url = "https://www.sec.gov/Archives/edgar/data/81033/000119312525261789/d36283dex99.htm"
slides_url = "https://www.sec.gov/Archives/edgar/data/81033/000119312525261789/d36283dex991.htm"

ai_dc_keywords = [
    'data center', 'Oracle', 'Google', 'Microsoft', 'Amazon', 'large load',
    'nuclear offtake', 'offtake', 'megawatt', 'gigawatt', 'GW', 'MW',
    'power purchase', 'behind the meter', 'coloc', 'pipeline',
    '11,800', '11800', '10,600', '9,400', '9400', 'large load',
    'PPA', 'carbon-free'
]

for name, url in [("Q3 2025 press", press_url), ("Q3 2025 slides", slides_url)]:
    print(f"\n{'='*60}")
    print(f"{name}: {url}")
    try:
        raw = fetch_text(url, 200000)
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
            print(f"  Preview: {text[:500]}")
    except Exception as e:
        print(f"  Error: {e}")
