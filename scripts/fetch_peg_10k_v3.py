import sys
import requests
import re
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

UA = edgar.USER_AGENT
HEADERS = {"User-Agent": UA}

def fetch_text(url, max_chars=1000000):
    r = requests.get(url, headers=HEADERS, timeout=120)
    r.raise_for_status()
    return r.text[:max_chars]

def extract_text_from_html(html):
    """Extract plain text from HTML."""
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Get the main 10-K document - the peg-20251231.htm is iXBRL inline
# Try the R documents - the actual readable content
# First, let's look at a different approach: use the full submission txt

# Actually let's try fetching the raw 10-K at larger sizes and search for key terms
url_10k = "https://www.sec.gov/Archives/edgar/data/788784/000119312526077446/peg-20251231.htm"
print("Fetching 10-K (1MB)...")
raw = fetch_text(url_10k, 1000000)
print(f"Raw size: {len(raw)}")

# Extract text
text = extract_text_from_html(raw)
print(f"Text size: {len(text)}")

# Search for key terms
ai_dc_keywords = [
    'data center', 'datacenter', 'artificial intelligence', 'hyperscal',
    'power purchase agreement', 'PPA', 'nuclear', 'behind the meter',
    'co-locat', 'coloc', 'Microsoft', 'Amazon', 'Google', 'Meta',
    'clean energy agreement', 'load growth', 'large load', 'gigawatt',
    'megawatt', 'compute', 'NRG', 'Talen', 'Constellation',
]

for kw in ai_dc_keywords:
    pos = text.lower().find(kw.lower())
    if pos != -1:
        start = max(0, pos - 150)
        end = min(len(text), pos + 250)
        print(f"\n[KW: {kw}] ...{text[start:end]}...")
