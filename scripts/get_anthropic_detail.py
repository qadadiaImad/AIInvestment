"""Get exact Anthropic investment note from 10-Q."""
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

# Get detailed Anthropic note from 10-Q
text_10q = extract_text("/tmp/amzn_10-Q_2026Q1.txt")

# Find the Non-Marketable Investments Anthropic section
pattern = re.compile(r'Non-Marketable Investments', re.IGNORECASE)
for m in pattern.finditer(text_10q):
    start = m.start()
    end = min(len(text_10q), m.end() + 3000)
    snippet = re.sub(r'\s+', ' ', text_10q[start:end]).strip()
    print(f"\n=== Non-Marketable Investments section (10-Q) ===\n{snippet}\n")
    break

# Find subsequent events section
print("\n\n=== SUBSEQUENT EVENTS section (10-Q) ===")
pattern2 = re.compile(r'Subsequent Event', re.IGNORECASE)
for m in pattern2.finditer(text_10q):
    start = max(0, m.start() - 200)
    end = min(len(text_10q), m.end() + 3000)
    snippet = re.sub(r'\s+', ' ', text_10q[start:end]).strip()
    print(f"\n{snippet[:3000]}\n")
    break

# Also check 10-K for Anthropic note
text_10k = extract_text("/tmp/amzn_10-K_2025.txt")
pattern3 = re.compile(r'Non-Marketable Investments', re.IGNORECASE)
for m in pattern3.finditer(text_10k):
    start = m.start()
    end = min(len(text_10k), m.end() + 3000)
    snippet = re.sub(r'\s+', ' ', text_10k[start:end]).strip()
    print(f"\n=== Non-Marketable Investments section (10-K) ===\n{snippet[:3000]}\n")
    break
