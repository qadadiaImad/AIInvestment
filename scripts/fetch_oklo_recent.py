import sys
import requests
import re
import time

sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

USER_AGENT = edgar.USER_AGENT

def fetch_html(url, delay=1.5):
    time.sleep(delay)
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
    resp.raise_for_status()
    return resp.text

def strip_html(html):
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<[^>]+>', ' ', html)
    for ent, repl in [('&#8220;', '"'), ('&#8221;', '"'), ('&#8217;', "'"), ('&#8216;', "'"),
                      ('&amp;', '&'), ('&nbsp;', ' '), ('&#8212;', '--'), ('&#8211;', '-')]:
        html = html.replace(ent, repl)
    html = re.sub(r'&#[0-9]+;', ' ', html)
    html = re.sub(r'[ \t]+', ' ', html)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()

def find_context(text, keyword, window=800):
    results = []
    kw_lower = keyword.lower()
    text_lower = text.lower()
    pos = 0
    while True:
        idx = text_lower.find(kw_lower, pos)
        if idx == -1:
            break
        start = max(0, idx - window)
        end = min(len(text), idx + window)
        results.append(text[start:end])
        pos = idx + 1
    return results

# Fetch the 10-Q (latest 2026-05-12) - this will have most recent events
print("=== 10-Q 2026-05-12 (most recent) ===")
url_10q = "https://www.sec.gov/Archives/edgar/data/1849056/000162828026034095/oklo-20260331.htm"
try:
    html = fetch_html(url_10q, delay=2)
    text = strip_html(html)
    print(f"10-Q chars: {len(text)}")

    # Save it
    with open('oklo_10q_plain.txt', 'w', encoding='utf-8') as f:
        f.write(text)

    keywords = ["Meta", "Equinix", "Switch", "Microsoft", "Google", "Amazon",
                "data center", "power purchase", "PPA", "prepayment", "1.2 gigawatt",
                "12 gigawatt", "right of first refusal", "letter of intent", "Sam Altman"]
    for kw in keywords:
        hits = find_context(text, kw, window=600)
        if hits:
            print(f"\n=== '{kw}' ({len(hits)} hits) ===")
            for i, h in enumerate(hits[:2]):
                print(f"  --- hit {i+1}: {h[:1000]}...")
except Exception as e:
    print(f"10-Q fetch failed: {e}")

# Fetch 8-K 2025-04-22
print("\n\n=== 8-K 2025-04-22 ===")
url_8k = "https://www.sec.gov/Archives/edgar/data/1849056/000110465925037472/tm2512904d1_8k.htm"
try:
    html2 = fetch_html(url_8k, delay=2)
    text2 = strip_html(html2)
    print(text2[:3000])
except Exception as e:
    print(f"Error: {e}")

# Fetch 8-K 2025-03-24 (filed same day as 10-K)
print("\n\n=== 8-K 2025-03-24 ===")
url_8k2 = "https://www.sec.gov/Archives/edgar/data/1849056/000110465925027276/tm2510004d1_8k.htm"
try:
    html3 = fetch_html(url_8k2, delay=2)
    text3 = strip_html(html3)
    print(text3[:3000])
except Exception as e:
    print(f"Error: {e}")

# Fetch 8-K 2025-02-05
print("\n\n=== 8-K 2025-02-05 ===")
url_8k3 = "https://www.sec.gov/Archives/edgar/data/1849056/000110465925009756/tm255590d1_8k.htm"
try:
    html4 = fetch_html(url_8k3, delay=2)
    text4 = strip_html(html4)
    print(text4[:3000])
except Exception as e:
    print(f"Error: {e}")
