import sys
import requests
import re
import time

sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import edgar

USER_AGENT = edgar.USER_AGENT

def fetch_html(url, delay=1.5):
    time.sleep(delay)
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=45)
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

# 8-K 2026-05-13 (most recent)
print("=== 8-K 2026-05-13 ===")
url = "https://www.sec.gov/Archives/edgar/data/1849056/000110465926060385/tm2614461d1_8k.htm"
try:
    html = fetch_html(url, delay=2)
    text = strip_html(html)
    print(text[:5000])
except Exception as e:
    print(f"Error: {e}")

# Also check 8-K 2024-12-27 which might be the Switch PPA announcement
print("\n\n=== 8-K 2024-12-27 (Switch PPA?) ===")
url2 = "https://www.sec.gov/Archives/edgar/data/1849056/000110465924132172/tm2432154d1_8k.htm"
try:
    html2 = fetch_html(url2, delay=2)
    text2 = strip_html(html2)
    print(text2[:5000])
except Exception as e:
    print(f"Error: {e}")
