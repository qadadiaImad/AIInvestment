import sys
import requests
import re
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

UA = edgar.USER_AGENT
HEADERS = {"User-Agent": UA}

def fetch_text(url, max_chars=3000000):
    r = requests.get(url, headers=HEADERS, timeout=120)
    r.raise_for_status()
    return r.text[:max_chars]

def extract_text_from_html(html):
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = text.replace('&nbsp;', ' ').replace('&#149;', '•').replace('&#146;', "'")
    text = text.replace('&#147;', '"').replace('&#148;', '"').replace('&#8217;', "'")
    text = re.sub(r'&#[0-9]+;', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# The 10-Q at that URL only has 66K chars — likely the iXBRL wrapper.
# Let me try to find the filing index and get the actual R documents
cik = "788784"
acc = "000119312526206545"
acc_dashes = "0001193125-26-206545"
index_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{acc_dashes}-index.htm"
print(f"10-Q index: {index_url}")
raw = fetch_text(index_url, 50000)
# Find all document links
doc_links = re.findall(r'href="(/Archives/edgar/data/[^"]+\.htm[l]?)"', raw, re.IGNORECASE)
print(f"Doc links: {doc_links[:30]}")
