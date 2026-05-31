"""Check if Arista 10-Q names Amazon explicitly as a customer."""
import requests
import re
from html.parser import HTMLParser
import sys

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

USER_AGENT = "AIInvestment research (easyresumeai@outlook.fr)"
headers = {"User-Agent": USER_AGENT}
session = requests.Session()

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []
        self.skip_tags = {'script', 'style', 'head'}
        self.current_skip = False
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.skip_tags:
            self.current_skip = True
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in self.skip_tags:
            self.skip_depth -= 1
            if self.skip_depth <= 0:
                self.current_skip = False
                self.skip_depth = 0

    def handle_data(self, data):
        if not self.current_skip:
            stripped = data.strip()
            if stripped:
                self.texts.append(stripped)

    def get_text(self):
        return ' '.join(self.texts)

# Try to fetch Arista 10-K for explicit customer names
# CIK for Arista: 0001596532
# Use their latest 10-K
arista_10k_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001596532&type=10-K&dateb=&owner=include&count=5"

resp = session.get(arista_10k_url, headers=headers, timeout=20)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    parser = TextExtractor()
    parser.feed(resp.text)
    text = parser.get_text()
    print(text[:2000])

# Also check from the Arista 10-Q if any mention of "percent of revenue" or named customers
arista_10q_url = "https://www.sec.gov/Archives/edgar/data/0001596532/000159653226000078/anet-20260331.htm"
resp2 = session.get(arista_10q_url, headers=headers, timeout=30)
print(f"\nArista 10-Q Status: {resp2.status_code}, Length: {len(resp2.text)}")

if resp2.status_code == 200:
    parser2 = TextExtractor()
    parser2.feed(resp2.text)
    text2 = parser2.get_text()

    # Search for percentage customer concentration
    for kw in ['percent of', 'revenue from', 'account for', 'accounted for', 'two customers', 'three customers', 'largest customer', 'Microsoft', 'Meta', 'Google', 'Amazon']:
        patterns = [m for m in re.finditer(re.escape(kw), text2, re.IGNORECASE)]
        if patterns:
            m = patterns[0]
            start = max(0, m.start()-200)
            end = min(len(text2), m.end()+500)
            snip = re.sub(r'\s+', ' ', text2[start:end]).strip()
            print(f"\n  [{kw}]: ...{snip}...")
