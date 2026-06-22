"""Extract exact quotes for AMZN edges from SEC filings."""
import re
from html.parser import HTMLParser

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


def find_sentences_with(text, keywords, window=2000):
    """Find text passages containing ALL given keywords."""
    results = []
    # Find positions of first keyword
    kw0 = keywords[0]
    pattern0 = re.compile(re.escape(kw0), re.IGNORECASE)
    for m in pattern0.finditer(text):
        start = max(0, m.start() - window//2)
        end = min(len(text), m.end() + window//2)
        snippet = text[start:end]
        # Check if all other keywords are present
        if all(re.search(re.escape(kw), snippet, re.IGNORECASE) for kw in keywords[1:]):
            snippet_clean = re.sub(r'\s+', ' ', snippet).strip()
            results.append(snippet_clean)
    return results


files = {
    "10-K_2025": {
        "path": "/tmp/amzn_10-K_2025.txt",
        "url": "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm"
    },
    "10-Q_2026Q1": {
        "path": "/tmp/amzn_10-Q_2026Q1.txt",
        "url": "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000014/amzn-20260331.htm"
    },
    "8-K_2026-04-29": {
        "path": "/tmp/amzn_8-K_2026-04-29.txt",
        "url": "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000012/amzn-20260429.htm"
    },
}

print("Extracting text...")
texts = {}
for label, info in files.items():
    texts[label] = extract_text(info["path"])

# === 1. ANTHROPIC INVESTMENT ===
print("\n\n=== 1. ANTHROPIC INVESTMENT (10-K) ===")
for label, text in texts.items():
    passages = find_sentences_with(text, ['Anthropic', 'billion'], window=2000)
    if passages:
        print(f"\n[{label}]:")
        for p in passages[:3]:
            print(f"  {p[:1500]}\n")

# === 2. ANTHROPIC LINE OF CREDIT (10-Q subsequent event) ===
print("\n\n=== 2. ANTHROPIC LINE OF CREDIT / SUBSEQUENT EVENT ===")
for label, text in texts.items():
    passages = find_sentences_with(text, ['Anthropic', 'credit'], window=2000)
    if passages:
        print(f"\n[{label}]:")
        for p in passages[:3]:
            print(f"  {p[:1500]}\n")

# === 3. OPENAI COMMITMENT ===
print("\n\n=== 3. OPENAI AWS COMMITMENT ===")
for label, text in texts.items():
    passages = find_sentences_with(text, ['OpenAI', 'billion'], window=2000)
    if passages:
        print(f"\n[{label}]:")
        for p in passages[:3]:
            print(f"  {p[:1500]}\n")

# === 4. ENERGY CONTRACTS (nuclear, renewable) ===
print("\n\n=== 4. ENERGY CONTRACTS ===")
for label, text in texts.items():
    # Look for energy contract details with amounts
    passages = find_sentences_with(text, ['energy contract', 'electricity'], window=2000)
    if passages:
        print(f"\n[{label} energy+electricity]:")
        for p in passages[:2]:
            print(f"  {p[:1500]}\n")

# === 5. SPECIFIC CAPEX NUMBERS ===
print("\n\n=== 5. CAPEX NUMBERS ===")
for label, text in texts.items():
    passages = find_sentences_with(text, ['capital expenditure', 'billion'], window=1500)
    if passages:
        print(f"\n[{label}]:")
        for p in passages[:2]:
            print(f"  {p[:1200]}\n")

# === 6. ANTHROPIC FULL INVESTMENT DETAIL ===
print("\n\n=== 6. ANTHROPIC - FULL INVESTMENT SECTION ===")
for label, text in texts.items():
    passages = find_sentences_with(text, ['Anthropic', 'nonvoting', 'preferred'], window=2000)
    if passages:
        print(f"\n[{label}]:")
        for p in passages[:3]:
            print(f"  {p[:2000]}\n")

# === 7. SUBSEQUENT EVENTS - ANTHROPIC ===
print("\n\n=== 7. SUBSEQUENT EVENTS ===")
text_10q = texts["10-Q_2026Q1"]
passages = find_sentences_with(text_10q, ['subsequent', 'Anthropic'], window=3000)
if passages:
    for p in passages[:3]:
        print(f"  {p[:2000]}\n")

# === 8. OPENAI SUBSEQUENT EVENT / EXPANSION ===
print("\n\n=== 8. OPENAI EXPANSION DETAIL ===")
text_10q = texts["10-Q_2026Q1"]
passages = find_sentences_with(text_10q, ['OpenAI', 'expansion', 'billion'], window=3000)
if passages:
    for p in passages[:3]:
        print(f"  {p[:2000]}\n")

# Wider context search for OpenAI
print("\n=== OPENAI WIDER CONTEXT ===")
pattern = re.compile(r'OpenAI', re.IGNORECASE)
for m in pattern.finditer(text_10q):
    start = max(0, m.start() - 1000)
    end = min(len(text_10q), m.end() + 1000)
    snippet = re.sub(r'\s+', ' ', text_10q[start:end]).strip()
    if 'billion' in snippet.lower() or 'AWS' in snippet:
        print(f"\n  OPENAI passage: {snippet[:2000]}")
        break
