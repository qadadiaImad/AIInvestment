import sys
import requests
import re
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

UA = edgar.USER_AGENT
HEADERS = {"User-Agent": UA}

def fetch_text(url, max_chars=400000):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.text[:max_chars]

def extract_text_from_html(html):
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = text.replace('&nbsp;', ' ').replace('&#149;', '•').replace('&#146;', "'")
    text = text.replace('&#147;', '"').replace('&#148;', '"').replace('&#8217;', "'")
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Q3 2025 8-K (2025-11-03)
# accession: 000119312525261789
cik = "788784"
acc = "000119312525261789"
acc_dashes = "0001193125-25-261789"
index_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{acc_dashes}-index.htm"
print(f"Q3 2025 8-K index: {index_url}")
raw = fetch_text(index_url, 20000)
doc_links = re.findall(r'href="(/Archives/edgar/data/[^"]+)"', raw)
print(f"Links: {doc_links[:15]}")
