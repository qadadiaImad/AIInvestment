"""Extract relationship/supply chain data from NBIS SEC filings."""
import re
import requests
from html.parser import HTMLParser

USER_AGENT = "AIInvestment research (easyresumeai@outlook.fr)"

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []
        self.in_script = False
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'ix:header'):
            self.in_script = True
        if tag == 'style':
            self.in_style = True

    def handle_endtag(self, tag):
        if tag in ('script', 'ix:header'):
            self.in_script = False
        if tag == 'style':
            self.in_style = False

    def handle_data(self, data):
        if not self.in_script and not self.in_style:
            text = data.strip()
            if text:
                self.texts.append(text)

def fetch_text(url, session):
    resp = session.get(url, timeout=120)
    resp.raise_for_status()
    # Use regex to strip tags - faster than full parse for large docs
    html = resp.text
    # Remove script/style/ix:header blocks
    html = re.sub(r'<(script|style|ix:header)[^>]*>.*?</(script|style|ix:header)>', '', html, flags=re.DOTALL|re.IGNORECASE)
    # Remove tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    return text

def find_context(text, keywords, window=500):
    """Find all occurrences of any keyword, return surrounding context."""
    results = []
    text_lower = text.lower()
    for kw in keywords:
        kw_lower = kw.lower()
        pos = 0
        while True:
            idx = text_lower.find(kw_lower, pos)
            if idx == -1:
                break
            start = max(0, idx - window)
            end = min(len(text), idx + len(kw) + window)
            snippet = text[start:end].strip()
            results.append((kw, idx, snippet))
            pos = idx + 1
    return results

session = requests.Session()
session.headers.update({'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xhtml+xml'})

# Key relationship/supply keywords
KEYWORDS = [
    'NVIDIA', 'Nvidia', 'NVDA',
    'AMD', 'Advanced Micro Devices',
    'Intel', 'INTC',
    'Microsoft', 'Azure', 'MSFT',
    'Amazon', 'AWS', 'AMZN',
    'Google', 'GOOGL', 'GCP',
    'Meta', 'META',
    'TSMC', 'Taiwan Semiconductor',
    'CoreWeave', 'CRWV',
    'Oracle', 'ORCL',
    'customer concentration', 'significant customer', 'major customer',
    'supplier', 'GPU', 'H100', 'H200', 'A100', 'H800',
    'compute cluster', 'data center', 'GPU cluster',
    'purchase commitment', 'capital commitment',
    'equity stake', 'investment', 'invested in',
    'partnership', 'strategic alliance',
    'Sberbank', 'Yandex',
    'FBK', 'FIVB',
    'revenue concentration',
    'license', 'licensing agreement',
    'colocation', 'co-location',
]

DOCS = [
    ("20-F FY2025", "2026-04-30", "https://www.sec.gov/Archives/edgar/data/1513845/000110465926052948/nbis-20251231x20f.htm"),
    ("6-K Q1-2026", "2026-05-20", "https://www.sec.gov/Archives/edgar/data/1513845/000110465926064092/nbis-20260331x6k.htm"),
    ("6-K Feb-2026", "2026-02-12", "https://www.sec.gov/Archives/edgar/data/1513845/000110465926013947/tm266173d2_6k.htm"),
    ("6-K Nov-2025", "2025-11-12", "https://www.sec.gov/Archives/edgar/data/1513845/000110465925110028/tm2530882d3_6k.htm"),
]

for doc_name, date, url in DOCS:
    print(f"\n{'='*80}")
    print(f"DOC: {doc_name} | {date} | {url}")
    print('='*80, flush=True)
    try:
        print(f"Fetching...", flush=True)
        text = fetch_text(url, session)
        print(f"Text length: {len(text):,} chars", flush=True)

        hits = find_context(text, KEYWORDS, window=300)
        # Deduplicate by position (nearby hits merged)
        seen_positions = []
        unique_hits = []
        for kw, pos, snippet in hits:
            # Check if this position is >500 chars from all seen positions
            if not any(abs(pos - p) < 500 for p in seen_positions):
                unique_hits.append((kw, pos, snippet))
                seen_positions.append(pos)

        print(f"Found {len(hits)} raw hits, {len(unique_hits)} unique contexts", flush=True)
        for kw, pos, snippet in unique_hits[:50]:
            print(f"\n--- Keyword: '{kw}' at pos {pos} ---")
            print(snippet[:800])
            print("", flush=True)

    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()
