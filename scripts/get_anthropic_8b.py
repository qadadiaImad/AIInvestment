"""Search for Anthropic $8 billion and line of credit in 10-Q text."""
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

text_10q = extract_text("/tmp/amzn_10-Q_2026Q1.txt")

# Search for "$8.0 billion" or "8.0 billion" in context with Anthropic
print("=== '8.0 billion' in 10-Q ===")
pattern = re.compile(r'8\.0 billion', re.IGNORECASE)
for m in pattern.finditer(text_10q):
    start = max(0, m.start() - 500)
    end = min(len(text_10q), m.end() + 1000)
    snippet = re.sub(r'\s+', ' ', text_10q[start:end]).strip()
    print(f"\n  ...{snippet}...")

# Search for "line of credit" + Anthropic
print("\n\n=== 'line of credit' + 'Anthropic' in 10-Q ===")
pattern2 = re.compile(r'line of credit', re.IGNORECASE)
for m in pattern2.finditer(text_10q):
    start = max(0, m.start() - 500)
    end = min(len(text_10q), m.end() + 1000)
    snippet = re.sub(r'\s+', ' ', text_10q[start:end]).strip()
    if 'anthropic' in snippet.lower():
        print(f"\n  ...{snippet}...")

# Search for "Subsequent Events" section
print("\n\n=== 'Subsequent Events' note ===")
pattern3 = re.compile(r'Note \d+.*?Subsequent', re.IGNORECASE)
for m in pattern3.finditer(text_10q):
    start = m.start()
    end = min(len(text_10q), m.end() + 3000)
    snippet = re.sub(r'\s+', ' ', text_10q[start:end]).strip()
    print(f"\n  ...{snippet[:3000]}...")
    break

# Search for the word "subsequent" in ALL positions
print("\n\n=== All 'subsequent' mentions ===")
pattern4 = re.compile(r'subsequent', re.IGNORECASE)
count = 0
for m in pattern4.finditer(text_10q):
    start = max(0, m.start() - 200)
    end = min(len(text_10q), m.end() + 500)
    snippet = re.sub(r'\s+', ' ', text_10q[start:end]).strip()
    if 'anthropic' in snippet.lower() or 'credit' in snippet.lower() or 'note' in snippet.lower():
        print(f"\n  [{count}] ...{snippet[:800]}...")
        count += 1
        if count > 10:
            break

# Search Anthropic + "invested" in 10-Q
print("\n\n=== 'invested' + 'Anthropic' in 10-Q ===")
pattern5 = re.compile(r'invested.*?Anthropic|Anthropic.*?invested', re.IGNORECASE | re.DOTALL)
for m in pattern5.finditer(text_10q):
    snippet = re.sub(r'\s+', ' ', m.group()[:1000]).strip()
    print(f"  {snippet}\n")
    break

# Search for "8.0 billion" context where it mentions "invested in convertible notes"
print("\n\n=== Anthropic $8B in 10-Q ===")
idx = text_10q.find('invested $ 8.0 billion')
if idx == -1:
    idx = text_10q.find('invested $8.0 billion')
if idx == -1:
    idx = text_10q.find('8.0 billion in convertible')
if idx >= 0:
    snippet = re.sub(r'\s+', ' ', text_10q[max(0,idx-200):idx+1500]).strip()
    print(snippet)
else:
    # Try just "8.0 billion" within context of Anthropic
    for kw in ['8 billion', '8.0 billion', '$8']:
        positions = [m.start() for m in re.finditer(re.escape(kw), text_10q, re.IGNORECASE)]
        if positions:
            print(f"  '{kw}' found at {len(positions)} positions")
            for pos in positions[:3]:
                snip = re.sub(r'\s+', ' ', text_10q[max(0,pos-100):pos+400]).strip()
                print(f"    ...{snip}...")
