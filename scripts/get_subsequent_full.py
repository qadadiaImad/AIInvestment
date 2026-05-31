"""Get full subsequent events text from 10-Q."""
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

# Find the passage about $5B invested in Anthropic subsequent event
idx = text_10q.find('invested $ 5.0 billion in Anthropic')
if idx == -1:
    idx = text_10q.find('5.0 billion in Anthropic')
if idx >= 0:
    start = max(0, idx - 500)
    end = min(len(text_10q), idx + 2000)
    snippet = re.sub(r'\s+', ' ', text_10q[start:end]).strip()
    print(f"=== SUBSEQUENT EVENT - Anthropic $5B ===\n{snippet}\n")

# Also look for the 8-K content from April 2026
print("\n\n=== 8-K April 2026 content ===")
text_8k = extract_text("/tmp/amzn_8-K_2026-04-29.txt")
print(f"Length: {len(text_8k)}")
print(text_8k[:5000])
