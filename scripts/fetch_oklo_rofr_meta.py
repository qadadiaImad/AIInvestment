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

# Load the saved plain text
with open('oklo_10k_plain.txt', 'r', encoding='utf-8') as f:
    plain = f.read()

# Get the full Right of First Refusal section
def find_context(text, keyword, window=1500):
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
        results.append(text[start:end])
        pos = idx + 1
    return results

print("=== RIGHT OF FIRST REFUSAL FULL TEXT ===")
hits = find_context(plain, "right of first refusal liability", window=2000)
for i, h in enumerate(hits[:3]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:4000])

print("\n\n=== LOI with third party / Equinix note 8 ===")
# Search for note 8 Right of First Refusal specifically
hits2 = find_context(plain, "36 months", window=1500)
for i, h in enumerate(hits2[:3]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:3000])

print("\n\n=== Fetch 8-K about Meta January 2026 ===")
# The 8-K from 2026-04-14 is about Meta. Let's check what it says
url_8k_jan26 = "https://www.sec.gov/Archives/edgar/data/1849056/000184905626000006/oklo-20260410.htm"
html = fetch_html(url_8k_jan26, delay=2)
text = strip_html(html)
print(f"8-K text: {text[:3000]}")

print("\n\n=== Fetch 8-K 2025-01-17 ===")
url_8k_jan25 = "https://www.sec.gov/Archives/edgar/data/1849056/000110465925004527/tm253619d1_8k.htm"
try:
    html2 = fetch_html(url_8k_jan25, delay=2)
    text2 = strip_html(html2)
    print(f"8-K text: {text2[:4000]}")
except Exception as e:
    print(f"Error: {e}")

print("\n\n=== Fetch 8-K 2025-03-07 (Switch) ===")
url_8k_switch = "https://www.sec.gov/Archives/edgar/data/1849056/000110465925021750/tm258622d1_8k.htm"
try:
    html3 = fetch_html(url_8k_switch, delay=2)
    text3 = strip_html(html3)
    print(f"8-K text: {text3[:4000]}")
except Exception as e:
    print(f"Error: {e}")
