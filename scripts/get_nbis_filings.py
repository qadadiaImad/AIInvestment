"""Get NBIS SEC filings."""
import sys
import json
import requests

USER_AGENT = "AIInvestment research (easyresumeai@outlook.fr)"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

def pad_cik(cik):
    return str(int(str(cik).lstrip("0") or "0")).zfill(10)

def filing_url(cik, accession, primary_document):
    cik_int = int(str(cik).lstrip("0") or "0")
    acc = accession.replace("-", "")
    return (f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc}/"
            f"{primary_document}")

session = requests.Session()
session.headers.update({'User-Agent': USER_AGENT})

cik = "0001513845"
url = SUBMISSIONS_URL.format(cik=cik)
print(f"Fetching: {url}", flush=True)
resp = session.get(url, timeout=30)
print(f"Status: {resp.status_code}", flush=True)

data = resp.json()
print(f"Company name: {data.get('name', 'Unknown')}", flush=True)

recent = data.get("filings", {}).get("recent", {})
accessions = recent.get("accessionNumber", [])
filing_dates = recent.get("filingDate", [])
forms = recent.get("form", [])
primary_docs = recent.get("primaryDocument", [])

rows = []
for i in range(len(accessions)):
    rows.append({
        "accession": accessions[i],
        "filing_date": filing_dates[i] if i < len(filing_dates) else "",
        "form": forms[i] if i < len(forms) else "",
        "primary_document": primary_docs[i] if i < len(primary_docs) else "",
    })

target_forms = {"10-K", "10-Q", "8-K", "S-1", "S-1/A", "10-K/A", "10-Q/A"}
filtered = [r for r in rows if r["form"] in target_forms]
print(f"\nTotal filings: {len(rows)}, filtered: {len(filtered)}", flush=True)
for r in filtered[:20]:
    fu = filing_url(cik, r["accession"], r["primary_document"])
    print(f"{r['form']}\t{r['filing_date']}\t{fu}", flush=True)
