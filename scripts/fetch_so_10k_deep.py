import sys
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar
import requests
import re

UA = edgar.USER_AGENT

def fetch_full(url):
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=60)
    resp.raise_for_status()
    return resp.text

def strip_html(text):
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'&nbsp;', ' ', clean)
    clean = re.sub(r'&amp;', '&', clean)
    clean = re.sub(r'&lt;', '<', clean)
    clean = re.sub(r'&gt;', '>', clean)
    clean = re.sub(r'\s+', ' ', clean)
    return clean

# Fetch 10-K — get the full document (it's large, chunk it)
url_10k = "https://www.sec.gov/Archives/edgar/data/92122/000009212226000006/so-20251231.htm"
print(f"Fetching full 10-K...")
resp = requests.get(url_10k, headers={"User-Agent": UA}, timeout=60)
resp.raise_for_status()
full_text = resp.text
print(f"Total document size: {len(full_text):,} chars")

# Strip HTML tags to get plain text
plain = strip_html(full_text)
print(f"Plain text size: {len(plain):,} chars")

# Search for key AI/data center terms
keywords = [
    'data center', 'artificial intelligence', 'hyperscaler',
    'Microsoft', 'Amazon', 'Google', 'Meta', 'AWS', 'Azure',
    'nuclear power', 'power purchase agreement', 'electricity demand',
    'load growth', 'cryptocurrency', 'bitcoin', 'compute',
    'NVIDIA', 'GPU', 'generative AI', 'machine learning',
    'colocation', 'high-performance computing', 'HPC',
    'Clean Power', 'Advanced Clean Energy', 'emissions-free'
]

found_any = False
for kw in keywords:
    # Find all occurrences
    start = 0
    while True:
        idx = plain.lower().find(kw.lower(), start)
        if idx < 0:
            break
        snippet = plain[max(0,idx-150):idx+400]
        print(f"\n=== '{kw}' at pos {idx} ===")
        print(snippet[:500])
        print("---")
        found_any = True
        start = idx + len(kw)
        # Only show first 3 occurrences per keyword
        if start - idx > 3 * len(plain) // 4:
            break

if not found_any:
    print("No AI/datacenter keywords found in the document.")
    # Show a sample from the middle to understand document structure
    mid = len(plain) // 2
    print(f"\nSample from middle of document (pos {mid}):")
    print(plain[mid:mid+1000])
