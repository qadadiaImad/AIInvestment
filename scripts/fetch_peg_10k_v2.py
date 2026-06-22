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

def extract_text_from_html(html):
    """Extract plain text from HTML."""
    # Remove scripts and styles
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    # Remove tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def search_relevant(text, keywords, context_chars=300):
    """Find passages around keywords."""
    found = []
    text_lower = text.lower()
    for kw in keywords:
        start = 0
        while True:
            pos = text_lower.find(kw.lower(), start)
            if pos == -1:
                break
            snippet_start = max(0, pos - context_chars//2)
            snippet_end = min(len(text), pos + context_chars//2)
            snippet = text[snippet_start:snippet_end].strip()
            found.append((kw, snippet))
            start = pos + len(kw)
    return found

# The 10-K filing has the main document - let's look for R-type documents in the index
# to find the actual 10-K text document
# Try getting the EDGAR full submission text file
full_text_url = "https://www.sec.gov/Archives/edgar/data/788784/000119312526077446/0001193125-26-077446.txt"
print("Fetching full submission text...")
try:
    text = fetch_text(full_text_url, 50000)
    print("File listing:")
    # Find document links
    docs = re.findall(r'<FILENAME>(.*?)\n', text)
    desc = re.findall(r'<DESCRIPTION>(.*?)\n', text)
    for d, desc_val in zip(docs[:30], desc[:30]+['']*(30-len(desc))):
        print(f"  {d} -- {desc_val}")
except Exception as e:
    print(f"Error: {e}")
