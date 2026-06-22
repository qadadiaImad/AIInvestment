"""Fetch Dominion Energy (D) SEC filings for edge extraction."""
import requests
import re
import sys

USER_AGENT = "AIInvestment research (easyresumeai@outlook.fr)"
HEADERS = {"User-Agent": USER_AGENT}

def fetch_text(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text

def extract_relevant_sections(text, keywords):
    """Extract paragraphs/sentences that contain any of the keywords."""
    results = []
    # Split into paragraphs
    paragraphs = re.split(r'\n{2,}', text)
    for para in paragraphs:
        para_clean = ' '.join(para.split())
        if any(kw.lower() in para_clean.lower() for kw in keywords):
            if len(para_clean) > 50:
                results.append(para_clean[:2000])
    return results

if __name__ == '__main__':
    filing_url = sys.argv[1]
    print(f"Fetching: {filing_url}")
    text = fetch_text(filing_url)
    print(f"Document length: {len(text)} chars")

    # AI-sector keywords
    keywords = [
        'data center', 'datacenter', 'hyperscaler', 'Amazon', 'AWS', 'Microsoft', 'Azure',
        'Google', 'Meta', 'Facebook', 'nuclear', 'power purchase agreement', 'PPA',
        'clean energy', 'renewable', 'natural gas', 'pipeline', 'AI', 'artificial intelligence',
        'MSFT', 'AMZN', 'GOOGL', 'META', 'Virginia', 'Northern Virginia',
        'capacity', 'megawatt', 'MW', 'gigawatt', 'GW', 'load growth',
        'large load', 'campus', 'co-location', 'interconnection',
        'NRG', 'Constellation', 'Talen', 'nuclear PPA', 'Surry', 'North Anna',
        'Small Modular Reactor', 'SMR', 'Oklo', 'NuScale',
        'ERCOT', 'transmission', 'NextEra'
    ]

    relevant = extract_relevant_sections(text, keywords)
    print(f"\nFound {len(relevant)} relevant paragraphs\n")
    for i, para in enumerate(relevant[:60]):
        print(f"--- Para {i+1} ---")
        print(para[:1500])
        print()
