import sys
import requests
import re
import time

sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

USER_AGENT = edgar.USER_AGENT

def fetch_html(url, delay=1.5):
    time.sleep(delay)
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=45)
    resp.raise_for_status()
    return resp.text

def strip_html(html):
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<[^>]+>', ' ', html)
    html = re.sub(r'&#8220;', '"', html)
    html = re.sub(r'&#8221;', '"', html)
    html = re.sub(r'&#8217;', "'", html)
    html = re.sub(r'&#8216;', "'", html)
    html = re.sub(r'&amp;', '&', html)
    html = re.sub(r'&nbsp;', ' ', html)
    html = re.sub(r'&#[0-9]+;', ' ', html)
    html = re.sub(r'[ \t]+', ' ', html)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()

def find_context(text, keyword, window=600):
    """Find all occurrences of keyword and return context windows."""
    results = []
    kw_lower = keyword.lower()
    text_lower = text.lower()
    pos = 0
    while True:
        idx = text_lower.find(kw_lower, pos)
        if idx == -1:
            break
        start = max(0, idx - window)
        end = min(len(text), idx + window)
        snippet = text[start:end].replace('\n', ' ').strip()
        results.append(snippet)
        pos = idx + 1
    return results

# Load the already-saved 10-K plain text
with open('oklo_10k_plain.txt', 'r', encoding='utf-8') as f:
    plain = f.read()

print(f"Loaded 10-K plain text: {len(plain)} chars")
print("="*80)

# Find detailed META context
print("\n\n=== META PREPAYMENT AGREEMENT - FULL CONTEXT ===")
meta_hits = find_context(plain, "Prepayment Agreement", window=1000)
for i, h in enumerate(meta_hits[:5]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:2000])

print("\n\n=== META 1.2 GW CONTEXT ===")
gw_hits = find_context(plain, "1.2 gigawatt", window=1200)
for i, h in enumerate(gw_hits[:3]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:2000])

print("\n\n=== EQUINIX LOI CONTEXT ===")
eqix_hits = find_context(plain, "Equinix", window=800)
for i, h in enumerate(eqix_hits[:5]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:1500])

print("\n\n=== SWITCH 12 GW AGREEMENT CONTEXT ===")
switch_hits = find_context(plain, "Switch", window=800)
for i, h in enumerate(switch_hits[:5]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:1500])

print("\n\n=== RIGHT OF FIRST REFUSAL / LOI CONTEXT ===")
rofr_hits = find_context(plain, "Right of First Refusal", window=800)
for i, h in enumerate(rofr_hits[:3]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:1500])

# Fetch and check the key 8-Ks
print("\n\n=== Fetching 8-K (2026-04-14) - Meta Prepayment ===")
url_8k_meta = "https://www.sec.gov/Archives/edgar/data/1849056/000184905626000006/oklo-20260410.htm"
try:
    html = fetch_html(url_8k_meta, delay=2)
    text = strip_html(html)
    print(f"8-K chars: {len(text)}")
    # Find Meta-related content
    meta_ctx = find_context(text, "Meta", window=1000)
    for i, h in enumerate(meta_ctx[:5]):
        print(f"\n--- 8-K Meta hit {i+1} ---")
        print(h[:2000])
except Exception as e:
    print(f"8-K fetch failed: {e}")
