import sys
import requests
import re
import time

sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

USER_AGENT = edgar.USER_AGENT

def fetch_text(url, delay=1):
    time.sleep(delay)
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.text

# Try the EDGAR viewer index format
cik = "1849056"
acc_nodash = "000162828026018698"
# Try the correct index URL format
index_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K&dateb=&owner=include&count=10"

# Actually, let's check what files are in the 10-K filing
# EDGAR archives have a specific structure - look for the filing index JSON
filing_index_url = f"https://data.sec.gov/submissions/CIK{edgar.pad_cik(cik)}.json"
resp = requests.get(filing_index_url, headers={"User-Agent": USER_AGENT}, timeout=30)
data = resp.json()

recent = data['filings']['recent']
print("Recent 10-K/10-Q/8-K filings with documents:")
for i, form in enumerate(recent['form'][:50]):
    if form in ('10-K', '8-K', '10-Q'):
        acc = recent['accessionNumber'][i]
        primary = recent['primaryDocument'][i]
        date = recent['filingDate'][i]
        acc_nodash2 = acc.replace('-', '')
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash2}/{primary}"
        print(f"  {form} {date}: {url}")
