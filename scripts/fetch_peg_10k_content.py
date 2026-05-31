import sys
import requests
import re
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

UA = edgar.USER_AGENT
HEADERS = {"User-Agent": UA}

def fetch_text(url, max_chars=500000):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.text[:max_chars]

# The peg-20251231.htm is the iXBRL viewer wrapper; need to look at the filing index
# to find the actual document files
cik = "788784"
accession = "000119312526077446"

# Fetch the filing index JSON
index_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/0001193125-26-077446-index.htm"
print("Fetching filing index HTML...")
text = fetch_text(index_url, 50000)
print(text[:5000])
