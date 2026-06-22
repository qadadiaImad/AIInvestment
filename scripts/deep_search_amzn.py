"""Deep targeted search for AMZN AI-sector edges from SEC filings."""
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


def find_context(text, keyword, window=800):
    """Find all occurrences of keyword and return surrounding context."""
    results = []
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    for m in pattern.finditer(text):
        start = max(0, m.start() - window)
        end = min(len(text), m.end() + window)
        snippet = text[start:end]
        snippet = re.sub(r'\s+', ' ', snippet).strip()
        results.append(snippet)
    return results


files = {
    "10-K_2025": "/tmp/amzn_10-K_2025.txt",
    "10-Q_2026Q1": "/tmp/amzn_10-Q_2026Q1.txt",
    "8-K_2026-05-22": "/tmp/amzn_8-K_2026-05-22.txt",
    "8-K_2026-04-29": "/tmp/amzn_8-K_2026-04-29.txt",
}

print("Extracting text...")
texts = {}
for label, path in files.items():
    texts[label] = extract_text(path)

# Targeted deep searches
targeted_searches = [
    # Anthropic investment details
    ("anthropic", "convertible notes", 1000),
    ("anthropic", "preferred stock", 1000),
    ("anthropic", "invested", 800),
    ("anthropic", "billion", 800),
    # OpenAI commitment
    ("openai", "billion", 800),
    ("openai", "commitment", 800),
    ("openai", "AWS", 800),
    # NVIDIA / GPU chips
    ("nvidia", "GPU", 800),
    ("nvidia", "chips", 800),
    ("custom silicon", "Trainium", 800),
    # Energy/infrastructure
    ("nuclear", "power", 600),
    ("renewable energy", "MW", 600),
    ("gigawatt", "energy", 600),
    # Specific company mentions
    ("Salesforce", "customer", 600),
    ("Oracle", "database", 600),
]

print("\n\n=== TARGETED DEEP SEARCHES ===\n")

for keyword_a, keyword_b, window in targeted_searches:
    found_any = False
    for label, text in texts.items():
        # Find passages containing both keywords within window chars
        pattern_a = re.compile(re.escape(keyword_a), re.IGNORECASE)
        for m in pattern_a.finditer(text):
            start = max(0, m.start() - window)
            end = min(len(text), m.end() + window)
            snippet = text[start:end]
            if re.search(re.escape(keyword_b), snippet, re.IGNORECASE):
                snippet_clean = re.sub(r'\s+', ' ', snippet).strip()
                if not found_any:
                    print(f"\n--- [{keyword_a}] + [{keyword_b}] ---")
                    found_any = True
                print(f"  [in {label}]")
                print(f"  ...{snippet_clean[:800]}...")
                break  # one per file

# Also search specifically for capital expenditure numbers
print("\n\n=== CAPEX / INVESTMENT DETAILS ===")
for label, text in texts.items():
    contexts = find_context(text, "capital expenditure", window=600)
    if contexts:
        print(f"\n  [capital expenditure in {label}]:")
        for ctx in contexts[:2]:
            print(f"  ...{ctx[:600]}...")

# Search for NVIDIA supplier relationship
print("\n\n=== NVIDIA SUPPLIER / GPU MENTIONS ===")
for label, text in texts.items():
    for kw in ['NVIDIA', 'Trainium', 'Inferentia', 'Graviton', 'custom silicon', 'AI chips']:
        contexts = find_context(text, kw, window=600)
        if contexts:
            print(f"\n  [{kw} in {label}]: {len(contexts)} occurrences")
            for ctx in contexts[:2]:
                print(f"  ...{ctx[:600]}...")

# Search for energy contracts
print("\n\n=== ENERGY CONTRACTS ===")
for label, text in texts.items():
    for kw in ['energy contract', 'nuclear power', 'small modular', 'SMR', 'renewable', 'electricity supply']:
        contexts = find_context(text, kw, window=600)
        if contexts:
            print(f"\n  [{kw} in {label}]: {len(contexts)} occurrences")
            for ctx in contexts[:2]:
                print(f"  ...{ctx[:600]}...")
