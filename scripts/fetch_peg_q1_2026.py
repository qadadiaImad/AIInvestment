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
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Find the Q1 2026 8-K ex99 press release
# Q1 2026 earnings filed 2026-05-05 (accession: 000119312526206545 is the 10-Q)
# The 8-K filed 2026-05-05 accession is 000119312526205254
# Let me check the index
cik = "788784"
acc_8k_q1 = "000119312526205254"
acc_dashes = "0001193125-26-205254"

index_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_8k_q1}/{acc_dashes}-index.htm"
print(f"Q1 2026 8-K index: {index_url}")
try:
    raw = fetch_text(index_url, 20000)
    doc_links = re.findall(r'href="(/Archives/edgar/data/[^"]+)"', raw)
    print(f"Doc links: {doc_links[:15]}")
except Exception as e:
    print(f"Error: {e}")
