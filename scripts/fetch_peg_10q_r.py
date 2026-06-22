import sys
import requests
import re
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

UA = edgar.USER_AGENT
HEADERS = {"User-Agent": UA}

def fetch_text(url, max_chars=300000):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.text[:max_chars]

def extract_text_from_html(html):
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = text.replace('&nbsp;', ' ').replace('&#149;', '•').replace('&#146;', "'")
    text = re.sub(r'&#[0-9]+;', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Try fetching R documents from the 10-Q
# The R documents contain the sections of the 10-Q
# First let's look at the full submission text to see what R docs exist
cik = "81033"
acc = "000119312526206545"
base_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/"

# Try R2, R3, R4... to find textual sections
for i in range(1, 10):
    url = f"{base_url}R{i}.htm"
    try:
        raw = fetch_text(url, 10000)
        text = extract_text_from_html(raw)
        print(f"\nR{i} ({len(text)} chars): {text[:500]}")
    except Exception as e:
        print(f"R{i}: {e}")
        if i > 3:
            break
