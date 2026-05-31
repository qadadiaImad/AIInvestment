"""Search AMZN filing content for AI-sector relationship edges."""
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


def find_context(text, keyword, window=500):
    """Find all occurrences of keyword and return surrounding context."""
    results = []
    # Case-insensitive search
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    for m in pattern.finditer(text):
        start = max(0, m.start() - window)
        end = min(len(text), m.end() + window)
        snippet = text[start:end]
        # Clean up whitespace
        snippet = re.sub(r'\s+', ' ', snippet).strip()
        results.append(snippet)
    return results


# Allowed node IDs from capital_web (AI-sector entities)
ALLOWED_IDS = {
    'ADBE', 'ADI', 'AEP', 'AI', 'AMAT', 'AMD', 'AMZN', 'ANET', 'APP', 'ARM',
    'ASML', 'AVGO', 'BWXT', 'CCJ', 'CDNS', 'CEG', 'CIEN', 'COHR', 'CRDO',
    'CRM', 'CRWD', 'CRWV', 'CSCO', 'D', 'DDOG', 'DELL', 'DLR', 'DUK', 'DUOL',
    'EMR', 'ENTG', 'EQIX', 'ET', 'ETN', 'EXC', 'FIG', 'GEV', 'GOOGL', 'HPE',
    'HUBB', 'IBM', 'INTC', 'INTU', 'IREN', 'KLAC', 'KMI', 'LEU', 'LNG', 'LRCX',
    'MCHP', 'MDB', 'META', 'MPWR', 'MRVL', 'MSFT', 'MU', 'NBIS', 'NEE', 'NET',
    'NNE', 'NOW', 'NRG', 'NTAP', 'NVDA', 'NVT', 'NXPI', 'OKE', 'OKLO', 'ON',
    'ORCL', 'PANW', 'PATH', 'PEG', 'PH', 'PLTR', 'PWR', 'QCOM', 'S', 'SMCI',
    'SMR', 'SNOW', 'SNPS', 'SO', 'STX', 'TEAM', 'TER', 'TLN', 'TRGP', 'TSM',
    'TXN', 'VRT', 'VST', 'WDAY', 'WDC', 'WMB', 'XEL', 'ZS',
    'anthropic', 'cohere', 'crusoe', 'lambda', 'mistral', 'musk', 'openai', 'spacex', 'xai'
}

# Keyword map: search term -> (node_id, company_name)
KEYWORD_MAP = {
    'NVIDIA': 'NVDA',
    'NVIDIA Corporation': 'NVDA',
    'TSMC': 'TSM',
    'Taiwan Semiconductor': 'TSM',
    'Microsoft': 'MSFT',
    'Google': 'GOOGL',
    'Alphabet': 'GOOGL',
    'Meta': 'META',
    'Anthropic': 'anthropic',
    'OpenAI': 'openai',
    'NVIDIA GPUs': 'NVDA',
    'Trainium': 'AMZN',  # Amazon's own chip
    'Graviton': 'AMZN',
    'Inferentia': 'AMZN',
    'Intel': 'INTC',
    'AMD': 'AMD',
    'Broadcom': 'AVGO',
    'Marvell': 'MRVL',
    'Salesforce': 'CRM',
    'Oracle': 'ORCL',
    'Dell': 'DELL',
    'HP Enterprise': 'HPE',
    'HPE': 'HPE',
    'Cohere': 'cohere',
    'Mistral': 'mistral',
    'xAI': 'xai',
    'Arista': 'ANET',
    'Cisco': 'CSCO',
    'Snowflake': 'SNOW',
    'MongoDB': 'MDB',
    'Datadog': 'DDOG',
    'CrowdStrike': 'CRWD',
    'Palo Alto': 'PANW',
    'ServiceNow': 'NOW',
    'Workday': 'WDAY',
    'Palantir': 'PLTR',
    'NetApp': 'NTAP',
    'Western Digital': 'WDC',
    'Seagate': 'STX',
    'Micron': 'MU',
    'Qualcomm': 'QCOM',
    'Equinix': 'EQIX',
    'Digital Realty': 'DLR',
    'CoreWeave': 'CRWV',
    'Lambda Labs': 'lambda',
    'Crusoe': 'crusoe',
}

files = {
    "10-K_2025": "/tmp/amzn_10-K_2025.txt",
    "10-Q_2026Q1": "/tmp/amzn_10-Q_2026Q1.txt",
    "8-K_2026-05-22": "/tmp/amzn_8-K_2026-05-22.txt",
    "8-K_2026-04-29": "/tmp/amzn_8-K_2026-04-29.txt",
}

print("Extracting text from filings...")
texts = {}
for label, path in files.items():
    print(f"  Processing {label}...")
    texts[label] = extract_text(path)
    print(f"  Text length: {len(texts[label])} chars")

print("\n\nSearching for relationship keywords...\n")
for label, text in texts.items():
    print(f"\n{'='*60}")
    print(f"FILE: {label}")
    print(f"{'='*60}")
    for keyword, node_id in KEYWORD_MAP.items():
        if node_id in ALLOWED_IDS and node_id != 'AMZN':
            contexts = find_context(text, keyword, window=400)
            if contexts:
                print(f"\n  [{keyword} -> {node_id}] {len(contexts)} occurrence(s):")
                for i, ctx in enumerate(contexts[:3]):  # limit to 3 per keyword
                    print(f"    [{i+1}] ...{ctx}...")
