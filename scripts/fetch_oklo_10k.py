import sys
import requests

sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

USER_AGENT = edgar.USER_AGENT

def fetch_text(url):
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.text

# Fetch the latest 10-K
url_10k = "https://www.sec.gov/Archives/edgar/data/1849056/000162828026018698/oklo-20251231.htm"
print(f"Fetching 10-K: {url_10k}")
text = fetch_text(url_10k)
print(f"10-K total chars: {len(text)}")

# Search for AI sector / hyperscaler relevant keywords
keywords = [
    "Microsoft", "MSFT", "Google", "GOOGL", "Alphabet", "Amazon", "AWS", "AMZN",
    "Meta", "Oracle", "ORCL", "Constellation", "CEG", "NRG", "Vistra", "VST",
    "data center", "datacenter", "power purchase", "PPA", "offtake", "customer",
    "letter of intent", "LOI", "agreement", "memorandum of understanding", "MOU",
    "Sam Altman", "OpenAI", "nuclear", "reactor", "SMR"
]

print("\n--- Keyword Search in 10-K ---")
lines = text.split('\n')
hits = {}
for kw in keywords:
    kw_lower = kw.lower()
    matching_lines = []
    for i, line in enumerate(lines):
        if kw_lower in line.lower():
            context = ' '.join(lines[max(0,i-1):min(len(lines),i+2)]).strip()
            # Strip HTML tags roughly
            import re
            context = re.sub(r'<[^>]+>', ' ', context)
            context = re.sub(r'\s+', ' ', context).strip()
            if len(context) > 20:
                matching_lines.append(context[:500])
    if matching_lines:
        hits[kw] = matching_lines[:5]

for kw, contexts in hits.items():
    print(f"\n=== '{kw}' ({len(contexts)} hits) ===")
    for c in contexts[:3]:
        print(f"  -> {c[:400]}")
