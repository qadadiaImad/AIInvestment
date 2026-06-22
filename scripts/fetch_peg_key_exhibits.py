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

key_exhibits = [
    # 2024-11-19 material agreements
    ("2024-11-19 Ex10.1", "https://www.sec.gov/Archives/edgar/data/788784/000095017024128681/peg-ex10_1.htm"),
    ("2024-11-19 Ex10.2", "https://www.sec.gov/Archives/edgar/data/788784/000095017024128681/peg-ex10_2.htm"),
    # 2026-01-21 Ex99 press release
    ("2026-01-21 Ex99", "https://www.sec.gov/Archives/edgar/data/788784/000119312526018045/d78622dex99.htm"),
    # 2025-03-10 Exhibit 1 (underwriting agreement?)
    ("2025-03-10 Ex1", "https://www.sec.gov/Archives/edgar/data/788784/000119312525050925/d919591dex1.htm"),
    # 2025-04-25 full 8-K text
    ("2025-04-25 Full txt", "https://www.sec.gov/Archives/edgar/data/788784/000119312525097067/0001193125-25-097067.txt"),
]

ai_dc_keywords = [
    'data center', 'datacenter', 'artificial intelligence', 'hyperscal',
    'power purchase', 'nuclear', 'behind the meter', 'co-locat',
    'Microsoft', 'Amazon', 'Google', 'Meta', 'large load',
    'gigawatt', 'megawatt', 'PPA', 'compute', 'NRG', 'Talen', 'Constellation',
    'load growth', 'generation', 'clean energy', 'tariff', 'energy agreement',
    'economic development', 'large customer', 'load', 'enterprise',
]

for name, url in key_exhibits:
    print(f"\n{'='*60}")
    print(f"{name}: {url}")
    try:
        raw = fetch_text(url, 300000)
        if url.endswith('.txt') or url.endswith('.xml'):
            text = re.sub(r'\s+', ' ', raw)
        else:
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
                start = max(0, pos - 150)
                end = min(len(text), pos + 350)
                snippet = text[start:end].strip()
                snippet_key = snippet[:100]
                if snippet_key not in seen_snippets:
                    seen_snippets.add(snippet_key)
                    print(f"  [KW: {kw}] ...{snippet}...")
                    found_any = True
                pos += len(kw)

        if not found_any:
            print(f"  No AI/DC keywords found")
            print(f"  Preview: {text[:500]}")
    except Exception as e:
        print(f"  Error: {e}")
