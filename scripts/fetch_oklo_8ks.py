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

# 8-K 2025-12-04 (ATM program + probably Meta LOI news)
print("=== 8-K 2025-12-04 ===")
url1 = "https://www.sec.gov/Archives/edgar/data/1849056/000110465925118494/tm2532691d1_8k.htm"
try:
    text = strip_html(fetch_html(url1, delay=2))
    print(text[:4000])
except Exception as e:
    print(f"Error: {e}")

print("\n\n=== 8-K 2025-09-03 ===")
url2 = "https://www.sec.gov/Archives/edgar/data/1849056/000110465925087034/tm2524815d1_8k.htm"
try:
    text2 = strip_html(fetch_html(url2, delay=2))
    print(text2[:4000])
except Exception as e:
    print(f"Error: {e}")

print("\n\n=== 8-K 2025-06-16 ===")
url3 = "https://www.sec.gov/Archives/edgar/data/1849056/000110465925059855/tm2518068d1_8k.htm"
try:
    text3 = strip_html(fetch_html(url3, delay=2))
    print(text3[:4000])
except Exception as e:
    print(f"Error: {e}")

print("\n\n=== 8-K 2025-06-09 ===")
url4 = "https://www.sec.gov/Archives/edgar/data/1849056/000110465925057630/tm2517317d1_8k.htm"
try:
    text4 = strip_html(fetch_html(url4, delay=2))
    print(text4[:4000])
except Exception as e:
    print(f"Error: {e}")

print("\n\n=== 8-K 2024-11-14 ===")
url5 = "https://www.sec.gov/Archives/edgar/data/1849056/000162828024047882/oklo-20241114.htm"
try:
    text5 = strip_html(fetch_html(url5, delay=2))
    print(text5[:4000])
except Exception as e:
    print(f"Error: {e}")
