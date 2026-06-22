import sys
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar
import requests

UA = edgar.USER_AGENT

def fetch_text(url, max_chars=200000):
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    resp.raise_for_status()
    text = resp.text
    return text[:max_chars]

# Fetch 10-K
url_10k = "https://www.sec.gov/Archives/edgar/data/92122/000009212226000006/so-20251231.htm"
print(f"Fetching 10-K from {url_10k}")
text = fetch_text(url_10k, max_chars=500000)
print(f"Got {len(text)} chars")

# Search for AI-related keywords
keywords = ['data center', 'datacenter', 'artificial intelligence', 'hyperscaler',
            'Microsoft', 'Amazon', 'Google', 'Meta', 'Apple', 'AWS', 'Azure',
            'nuclear', 'PPA', 'power purchase', 'colocation', 'computing',
            'NVIDIA', 'GPU', 'load growth', 'AI']

for kw in keywords:
    idx = text.lower().find(kw.lower())
    if idx >= 0:
        snippet = text[max(0, idx-100):idx+300]
        # strip HTML tags roughly
        import re
        clean = re.sub(r'<[^>]+>', ' ', snippet)
        clean = re.sub(r'\s+', ' ', clean).strip()
        print(f"\n=== Found '{kw}' at position {idx} ===")
        print(clean[:400])
