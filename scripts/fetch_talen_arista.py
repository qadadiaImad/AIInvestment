"""Fetch Talen Energy press release and Arista 10-Q with proper user agent."""
import requests
import re
from html.parser import HTMLParser
import sys

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

USER_AGENT = "AIInvestment research (easyresumeai@outlook.fr)"
headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}
session = requests.Session()

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []
        self.skip_tags = {'script', 'style', 'head'}
        self.current_skip = False
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.skip_tags:
            self.current_skip = True
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in self.skip_tags:
            self.skip_depth -= 1
            if self.skip_depth <= 0:
                self.current_skip = False
                self.skip_depth = 0

    def handle_data(self, data):
        if not self.current_skip:
            stripped = data.strip()
            if stripped:
                self.texts.append(stripped)

    def get_text(self):
        return ' '.join(self.texts)

def fetch_and_extract(url, label):
    print(f"\n=== {label} ===")
    try:
        resp = session.get(url, headers=headers, timeout=30)
        print(f"Status: {resp.status_code}, Length: {len(resp.text)}")
        parser = TextExtractor()
        parser.feed(resp.text)
        text = parser.get_text()
        return text
    except Exception as e:
        print(f"ERROR: {e}")
        return ""

def find_context(text, keyword, window=800):
    results = []
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    for m in pattern.finditer(text):
        start = max(0, m.start() - window//2)
        end = min(len(text), m.end() + window//2)
        snippet = re.sub(r'\s+', ' ', text[start:end]).strip()
        results.append(snippet)
    return results

import time

# Talen Energy 8-K press release June 2025
talen_url = "https://www.sec.gov/Archives/edgar/data/0001622536/000162828025030559/a20250611pressreleasebusin.htm"
talen_text = fetch_and_extract(talen_url, "Talen Energy PPA Press Release")
time.sleep(1)

if talen_text:
    print("\n--- Amazon mentions ---")
    ctxs = find_context(talen_text, 'Amazon', window=1000)
    for ctx in ctxs[:5]:
        print(f"  ...{ctx}...\n")

    print("\n--- MW / megawatt mentions ---")
    ctxs = find_context(talen_text, 'megawatt', window=800)
    for ctx in ctxs[:3]:
        print(f"  ...{ctx}...\n")

    print("\n--- nuclear mentions ---")
    ctxs = find_context(talen_text, 'nuclear', window=800)
    for ctx in ctxs[:3]:
        print(f"  ...{ctx}...\n")

# Arista 10-Q
arista_url = "https://www.sec.gov/Archives/edgar/data/0001596532/000159653226000078/anet-20260331.htm"
arista_text = fetch_and_extract(arista_url, "Arista 10-Q Q1 2026")
time.sleep(1)

if arista_text:
    print("\n--- Amazon/AWS mentions in Arista 10-Q ---")
    for kw in ['Amazon', 'AWS', 'customer concentration', 'one customer', 'significant customer']:
        ctxs = find_context(arista_text, kw, window=800)
        if ctxs:
            print(f"\n  [{kw}]:")
            for ctx in ctxs[:2]:
                print(f"    ...{ctx[:600]}...\n")
