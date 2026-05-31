"""Fetch Dominion Energy (D) 10-K and extract plain text for edge analysis."""
import requests
import re
import sys

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

USER_AGENT = "AIInvestment research (easyresumeai@outlook.fr)"
HEADERS = {"User-Agent": USER_AGENT}

def fetch_text(url):
    resp = requests.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.text

def html_to_text(html):
    if HAS_BS4:
        soup = BeautifulSoup(html, 'html.parser')
        # Remove script/style
        for tag in soup(['script', 'style', 'meta', 'link']):
            tag.decompose()
        return soup.get_text(separator='\n')
    else:
        # Simple regex fallback
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&#[0-9]+;', ' ', text)
        return text

def extract_relevant_sentences(text, keywords):
    """Extract sentences that contain any of the keywords."""
    # Split into sentences (rough)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    results = []
    for sent in sentences:
        sent_clean = ' '.join(sent.split())
        if len(sent_clean) < 30:
            continue
        if any(kw.lower() in sent_clean.lower() for kw in keywords):
            results.append(sent_clean[:2000])
    return results

if __name__ == '__main__':
    url = "https://www.sec.gov/Archives/edgar/data/715957/000119312526063120/d-20251231.htm"
    print(f"Fetching 10-K: {url}")
    html = fetch_text(url)
    print(f"HTML length: {len(html)} chars")
    print(f"BeautifulSoup available: {HAS_BS4}")

    text = html_to_text(html)
    print(f"Plain text length: {len(text)} chars")

    # AI-sector keywords
    keywords = [
        'data center', 'datacenter', 'data-center', 'hyperscaler',
        'Amazon', 'AWS', 'Microsoft', 'Azure', 'Google', 'Meta', 'Facebook',
        'nuclear', 'power purchase agreement', 'PPA', 'clean energy',
        'artificial intelligence', 'AI load', 'AI demand',
        'large load', 'campus load', 'co-location',
        'megawatt', 'MW ', 'gigawatt', 'GW ', 'load growth',
        'NRG', 'Constellation', 'Talen', 'nuclear PPA', 'Surry', 'North Anna',
        'Small Modular Reactor', 'SMR', 'Oklo', 'NuScale',
        'NextEra', 'Duke', 'Southern Company',
        'Virginia data', 'Northern Virginia',
        'hyperscale', 'colocation', 'tech customer'
    ]

    relevant = extract_relevant_sentences(text, keywords)
    print(f"\nFound {len(relevant)} relevant sentences\n")
    for i, sent in enumerate(relevant[:100]):
        print(f"--- Sentence {i+1} ---")
        print(sent[:1000])
        print()
