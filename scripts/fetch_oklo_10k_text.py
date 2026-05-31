import sys
import requests
import re
import time
import json

sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

USER_AGENT = edgar.USER_AGENT

def fetch_text(url, delay=1.0):
    time.sleep(delay)
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=45)
    resp.raise_for_status()
    return resp.text

# Get the filing index to find all documents in the 10-K
cik = "1849056"
acc_10k = "0001628280-26-018698"
acc_nodash = "000162828026018698"

# Use EDGAR full index API
index_api_url = f"https://data.sec.gov/submissions/CIK{edgar.pad_cik(cik)}.json"
resp = requests.get(index_api_url, headers={"User-Agent": USER_AGENT}, timeout=30)
data = resp.json()

# Find the 10-K in the filings
recent = data['filings']['recent']
for i, acc in enumerate(recent['accessionNumber']):
    if recent['form'][i] == '10-K' and '2026-03' in recent['filingDate'][i]:
        print(f"Found 10-K: acc={acc}, primary={recent['primaryDocument'][i]}")
        break

# The htm file IS the 10-K - let's fetch it differently
# Actually the 10-K uses inline XBRL but has readable content too
# Let's look for the text version (often a .txt file)
acc_clean = acc_nodash

# Try fetching the raw text filing
txt_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_clean}/{acc_clean}.txt"
print(f"\nTrying txt version: {txt_url}")
try:
    text = fetch_text(txt_url, delay=2)
    print(f"Got {len(text)} chars from txt")
except Exception as e:
    print(f"txt failed: {e}")
    text = None

# If no txt, let's just parse the big htm file properly
if not text:
    url_10k = "https://www.sec.gov/Archives/edgar/data/1849056/000162828026018698/oklo-20251231.htm"
    print(f"\nFetching 10-K htm: {url_10k}")
    text = fetch_text(url_10k, delay=2)
    print(f"Got {len(text)} chars from htm")

# Strip HTML and search for key terms
def strip_html(html):
    # Remove script/style blocks
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    # Remove all other tags
    html = re.sub(r'<[^>]+>', ' ', html)
    # Normalize whitespace
    html = re.sub(r'[ \t]+', ' ', html)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()

print("\nStripping HTML...")
plain = strip_html(text)
print(f"Plain text: {len(plain)} chars")

# Save plain text for inspection
with open('oklo_10k_plain.txt', 'w', encoding='utf-8') as f:
    f.write(plain)
print("Saved to oklo_10k_plain.txt")

# Search for AI-sector relevant keywords
keywords = [
    "data center", "datacenter", "hyperscaler", "Microsoft", "Google", "Alphabet",
    "Amazon", "Meta", "Oracle", "OpenAI", "Sam Altman", "Anthropic",
    "power purchase", "PPA", "offtake", "letter of intent", "LOI", "MOU",
    "memorandum of understanding", "customer", "agreement", "contract",
    "Constellation", "NRG", "Vistra", "Talen", "AI", "artificial intelligence",
    "SMR", "small modular", "reactor", "nuclear", "GW", "MW",
    "Defense Advanced", "DARPA", "Department of Energy", "DOE",
    "Wythe", "Idaho", "Switch", "Equinix", "Digital Realty"
]

print("\n--- Keyword Search in 10-K ---")
for kw in keywords:
    kw_lower = kw.lower()
    # Find positions
    positions = [m.start() for m in re.finditer(re.escape(kw_lower), plain.lower())]
    if positions:
        print(f"\n=== '{kw}' ({len(positions)} hits) ===")
        for pos in positions[:3]:
            start = max(0, pos-200)
            end = min(len(plain), pos+400)
            snippet = plain[start:end].replace('\n', ' ').strip()
            print(f"  -> ...{snippet}...")
