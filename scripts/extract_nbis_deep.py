"""Deep extraction from NBIS 20-F - focus on named relationships."""
import re
import requests

USER_AGENT = "AIInvestment research (easyresumeai@outlook.fr)"

def fetch_text(url, session):
    resp = session.get(url, timeout=120)
    resp.raise_for_status()
    html = resp.text
    html = re.sub(r'<(script|style|ix:header)[^>]*>.*?</(script|style|ix:header)>', '', html, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    # HTML entity decode basic ones
    text = text.replace('&#160;', ' ').replace('&#8217;', "'").replace('&#8220;', '"').replace('&#8221;', '"')
    text = text.replace('&#8226;', '•').replace('&#8203;', '').replace('&#9679;', '•')
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    return text

session = requests.Session()
session.headers.update({'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xhtml+xml'})

url = "https://www.sec.gov/Archives/edgar/data/1513845/000110465926052948/nbis-20251231x20f.htm"
print(f"Fetching 20-F...", flush=True)
text = fetch_text(url, session)
print(f"Text length: {len(text):,}", flush=True)

# Focus areas
FOCUS_TERMS = [
    ('Meta contract', ['Meta Platforms', 'Meta agreement', 'AI Infrastructure Supply Agreement with Meta', '$12 billion', '12 billion', 'Meta with rights', 'Zuckerberg']),
    ('Microsoft contract', ['Commercial Agreement with Microsoft', '$17', '17,392', 'Vineland', 'Microsoft has committed', 'Microsoft Agreement', 'nine tranches']),
    ('NVIDIA equity', ['Equity Investment with NVIDIA', 'securities purchase agreement', 'Warrant', '21,065', '$2 billion', '2.0 billion', 'private placement']),
    ('NVIDIA partnership', ['strategic partnership with Nvidia', 'NVIDIA Cloud Partner', 'Vera Rubin', 'March 2026', 'NVL72']),
    ('Avride', ['Avride', 'autonomous driving']),
    ('TripleTen', ['TripleTen', 'edtech', 'education']),
    ('Toloka', ['Toloka', 'data labeling', 'crowdsourcing']),
    ('purchase commitments', ['purchase commitment', 'capital commitment', 'committed to purchase', 'commitments to purchase']),
    ('CoreWeave competition', ['CoreWeave', 'CRWV']),
    ('convertible notes', ['2029 Notes', 'Convertible', 'convertible senior']),
    ('Tavily acquisition', ['Tavily', 'AlphaAI Technologies', '$177', '177.3']),
    ('financing', ['revolving credit', 'credit facility', 'loan agreement', 'debt financing', 'Goldman', 'JPMorgan', 'Barclays']),
]

for area, terms in FOCUS_TERMS:
    print(f"\n{'='*70}")
    print(f"AREA: {area}")
    print('='*70, flush=True)

    text_lower = text.lower()
    found_any = False
    seen_pos = []

    for term in terms:
        pos = 0
        while True:
            idx = text_lower.find(term.lower(), pos)
            if idx == -1:
                break
            # Check not near already seen
            if not any(abs(idx - p) < 600 for p in seen_pos):
                start = max(0, idx - 400)
                end = min(len(text), idx + len(term) + 600)
                snippet = text[start:end].strip()
                print(f"\n  [term='{term}' pos={idx}]")
                print(f"  {snippet[:1200]}")
                seen_pos.append(idx)
                found_any = True
            pos = idx + 1

    if not found_any:
        print(f"  (no hits for this area)")
