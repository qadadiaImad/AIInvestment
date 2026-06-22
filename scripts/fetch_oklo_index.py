import sys
import requests
import re

sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

USER_AGENT = edgar.USER_AGENT

def fetch_text(url):
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.text

# Look at the filing index for 10-K
cik = "1849056"
# accession number from: 000162828026018698
acc_nodash = "000162828026018698"
index_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{acc_nodash}-index.htm"
print(f"Fetching index: {index_url}")
text = fetch_text(index_url)

# Find document links
links = re.findall(r'href="([^"]+\.htm[l]?)"', text, re.IGNORECASE)
print("Documents found in index:")
for l in links[:30]:
    print(f"  {l}")

# Also try the JSON index
json_index = f"https://data.sec.gov/submissions/CIK{edgar.pad_cik(cik)}.json"
# already have submissions, look for the specific accession
import json
resp2 = requests.get(json_index, headers={"User-Agent": USER_AGENT}, timeout=30)
data = resp2.json()
recent = data['filings']['recent']
for i, acc in enumerate(recent['accessionNumber']):
    if acc.replace('-','') == acc_nodash:
        print(f"\nFiling {i}: form={recent['form'][i]}, date={recent['filingDate'][i]}, primary={recent['primaryDocument'][i]}")
        break
