import sys
import requests
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

UA = edgar.USER_AGENT
HEADERS = {"User-Agent": UA}

def fetch_text(url, max_chars=200000):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text[:max_chars]

# Fetch the 2025 10-K (annual report for fiscal year 2025, filed 2026-02-26)
url_10k = "https://www.sec.gov/Archives/edgar/data/788784/000119312526077446/peg-20251231.htm"
print("=== 10-K 2026-02-26 (FY2025) ===")
text = fetch_text(url_10k)
# Search for relevant AI/datacenter sections
import re
# Look for keywords
keywords = ['data center', 'datacenter', 'artificial intelligence', 'AI', 'power purchase', 'nuclear',
            'hyperscal', 'colocation', 'Microsoft', 'Amazon', 'Google', 'Meta', 'AMZN', 'GOOGL', 'MSFT',
            'META', 'cloud', 'compute', 'PPA', 'agreement', 'customer', 'Constellation', 'NRG', 'Talen',
            'CEG', 'nuclear', 'solar', 'wind']

# Find paragraphs containing multiple keywords
from html.parser import HTMLParser
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_body = True
    def handle_data(self, data):
        if self.in_body:
            self.text.append(data)

parser = TextExtractor()
parser.feed(text)
full_text = ' '.join(parser.text)
# Clean up whitespace
full_text = re.sub(r'\s+', ' ', full_text)

# Search for AI/datacenter related paragraphs
ai_dc_keywords = ['data center', 'datacenter', 'artificial intelligence', ' AI ',
                   'hyperscal', 'colocation', 'power purchase agreement', 'PPA',
                   'Microsoft', 'Amazon', 'Google', 'Meta', 'nuclear power',
                   'clean energy', 'behind the meter', 'co-located']

# Find all sentences around these keywords
sentences = re.split(r'(?<=[.!?])\s+', full_text)
relevant = []
for s in sentences:
    s_lower = s.lower()
    for kw in ai_dc_keywords:
        if kw.lower() in s_lower:
            relevant.append(s.strip())
            break

print(f"Total text length: {len(full_text)}")
print(f"Relevant sentences found: {len(relevant)}")
for i, s in enumerate(relevant[:50]):
    print(f"[{i}] {s[:300]}")
    print()
