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
    """Extract plain text from HTML."""
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Key 8-K filings about datacenters
# 2024-11-19 8-K looks promising (nuclear / datacenter announcements were big in 2024)
eight_k_urls = [
    ("2026-05-05", "https://www.sec.gov/Archives/edgar/data/788784/000119312526205254/d63722d8k.htm"),
    ("2026-04-23", "https://www.sec.gov/Archives/edgar/data/788784/000119312526173855/d125718d8k.htm"),
    ("2026-01-21", "https://www.sec.gov/Archives/edgar/data/788784/000119312526018045/d78622d8k.htm"),
    ("2025-11-03", "https://www.sec.gov/Archives/edgar/data/788784/000119312525261789/d36283d8k.htm"),
    ("2025-04-25", "https://www.sec.gov/Archives/edgar/data/788784/000119312525097067/d854626d8k.htm"),
    ("2025-03-10", "https://www.sec.gov/Archives/edgar/data/788784/000119312525050925/d919591d8k.htm"),
    ("2024-11-19", "https://www.sec.gov/Archives/edgar/data/788784/000095017024128681/peg-20241118.htm"),
]

ai_dc_keywords = [
    'data center', 'datacenter', 'artificial intelligence', 'hyperscal',
    'power purchase agreement', 'nuclear', 'behind the meter', 'co-locat',
    'Microsoft', 'Amazon', 'Google', 'Meta', 'clean energy', 'large load',
    'gigawatt', 'megawatt', 'PPA', 'compute', 'NRG', 'Talen', 'Constellation',
    'generation', 'solar', 'wind', 'natural gas', 'load growth',
]

for date, url in eight_k_urls:
    print(f"\n{'='*60}")
    print(f"8-K {date}: {url}")
    try:
        raw = fetch_text(url)
        text = extract_text_from_html(raw)
        found_any = False
        for kw in ai_dc_keywords:
            pos = text.lower().find(kw.lower())
            if pos != -1:
                start = max(0, pos - 100)
                end = min(len(text), pos + 300)
                if not found_any:
                    print(f"  Length: {len(text)}")
                print(f"  [KW: {kw}] ...{text[start:end]}...")
                found_any = True
        if not found_any:
            print(f"  Length: {len(text)} -- no AI/DC keywords found")
            # Print first 500 chars
            print(f"  Preview: {text[:500]}")
    except Exception as e:
        print(f"  Error: {e}")
