"""Check AMZN 10-K/Q for NVIDIA and TSMC supplier mentions."""
import re
from html.parser import HTMLParser
import sys

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

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

def extract_text(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    parser = TextExtractor()
    parser.feed(content)
    return parser.get_text()

def find_context(text, keyword, window=800):
    results = []
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    for m in pattern.finditer(text):
        start = max(0, m.start() - window//2)
        end = min(len(text), m.end() + window//2)
        snippet = re.sub(r'\s+', ' ', text[start:end]).strip()
        results.append(snippet)
    return results

text_10k = extract_text("/tmp/amzn_10-K_2025.txt")
text_10q = extract_text("/tmp/amzn_10-Q_2026Q1.txt")

print("=== NVIDIA in AMZN 10-K ===")
ctxs = find_context(text_10k, 'NVIDIA', window=600)
for ctx in ctxs[:5]:
    print(f"  ...{ctx[:600]}...\n")

print("\n=== TSMC / Taiwan Semiconductor in AMZN 10-K ===")
for kw in ['TSMC', 'Taiwan Semiconductor', 'foundry', 'Trainium', 'Inferentia']:
    ctxs = find_context(text_10k, kw, window=600)
    if ctxs:
        print(f"\n  [{kw}]:")
        for ctx in ctxs[:2]:
            print(f"    ...{ctx[:500]}...\n")

print("\n=== NVIDIA in AMZN 10-Q ===")
ctxs = find_context(text_10q, 'NVIDIA', window=600)
for ctx in ctxs[:5]:
    print(f"  ...{ctx[:600]}...\n")

print("\n=== Trainium / Inferentia in AMZN 10-K ===")
for kw in ['Trainium', 'Inferentia', 'custom silicon', 'custom chip', 'AWS chips']:
    ctxs = find_context(text_10k, kw, window=600)
    if ctxs:
        print(f"\n  [{kw}]:")
        for ctx in ctxs[:2]:
            print(f"    ...{ctx[:500]}...\n")
