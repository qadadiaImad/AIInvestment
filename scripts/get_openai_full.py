"""Get full OpenAI investment detail from 10-Q subsequent events."""
import re
import sys
from html.parser import HTMLParser

# Force UTF-8 output
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

text_10q = extract_text("/tmp/amzn_10-Q_2026Q1.txt")

# Get full OpenAI subsequent events section
idx = text_10q.find('OpenAI')
while idx >= 0:
    start = max(0, idx - 100)
    end = min(len(text_10q), idx + 3000)
    snippet = re.sub(r'\s+', ' ', text_10q[start:end]).strip()
    if 'Series C' in snippet or '15.0 billion' in snippet or '35.0 billion' in snippet:
        print(f"=== OpenAI Investment Section ===")
        print(snippet[:4000])
        break
    idx = text_10q.find('OpenAI', idx+1)

# Get 8-K April 2026
print("\n\n=== 8-K April 29, 2026 ===")
text_8k_apr = extract_text("/tmp/amzn_8-K_2026-04-29.txt")
print(text_8k_apr[:4000].encode('ascii', 'replace').decode('ascii'))
