import sys
import requests
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

UA = edgar.USER_AGENT
HEADERS = {"User-Agent": UA}

def fetch_json(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def fetch_text(url, max_chars=300000):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.text[:max_chars]

# Get the filing index for the 10-K
# accession: 000119312526077446
# CIK: 788784
cik = "788784"
accession = "000119312526077446"
acc_dashes = "0001193125-26-077446"

index_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K&dateb=&owner=include&count=5&search_text="
print("Fetching filing index...")

# Try the filing index JSON
index_json_url = f"https://data.sec.gov/submissions/CIK{edgar.pad_cik(cik)}.json"
submissions = fetch_json(index_json_url)

# Find the 10-K documents
recent = submissions.get('filings', {}).get('recent', {})
forms = recent.get('form', [])
dates = recent.get('filingDate', [])
accessions_list = recent.get('accessionNumber', [])
docs = recent.get('primaryDocument', [])

for i, f in enumerate(forms):
    if f == '10-K':
        print(f"Form: {f}, Date: {dates[i]}, Acc: {accessions_list[i]}, Doc: {docs[i]}")

# Get the filing index page for the latest 10-K
acc_no_dash = accession
filing_index_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_dash}/"
print(f"\nFiling index: {filing_index_url}")
text = fetch_text(filing_index_url, 50000)
print(text[:3000])
