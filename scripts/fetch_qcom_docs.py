"""Fetch QCOM SEC filing documents for edge extraction analysis."""
from __future__ import annotations
import requests
import aiinvest.edgar as edgar
import time
import re

UA = edgar.USER_AGENT
sess = requests.Session()
sess.headers.update({"User-Agent": UA})

URLS = {
    "10-K_2025": "https://www.sec.gov/Archives/edgar/data/804328/000080432825000085/qcom-20250928.htm",
    "10-Q_2026Q2": "https://www.sec.gov/Archives/edgar/data/804328/000080432826000061/qcom-20260329.htm",
    "10-Q_2026Q1": "https://www.sec.gov/Archives/edgar/data/804328/000080432826000017/qcom-20251228.htm",
    "8-K_2026Apr": "https://www.sec.gov/Archives/edgar/data/804328/000080432826000060/qcom-20260429.htm",
}

def clean_text(html: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    # Remove scripts and style blocks
    html = re.sub(r'<(script|style)[^>]*>.*?</(script|style)>', ' ', html, flags=re.DOTALL|re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_relevant_sections(text: str, keywords: list) -> list:
    """Find paragraphs that contain any of the keywords."""
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    relevant = []
    for i, s in enumerate(sentences):
        s_lower = s.lower()
        if any(kw.lower() in s_lower for kw in keywords):
            # Include surrounding context
            start = max(0, i-1)
            end = min(len(sentences), i+2)
            context = ' '.join(sentences[start:end])
            if len(context) > 50:  # Skip tiny fragments
                relevant.append(context)
    return relevant

# Keywords for companies in node_ids that QCOM might have relationships with
RELATIONSHIP_KEYWORDS = [
    # Key potential partners/customers/suppliers in node_ids
    "Apple", "Samsung", "Microsoft", "MSFT", "Amazon", "AWS", "Google", "Alphabet",
    "Meta", "Nvidia", "NVDA", "AMD", "Intel", "INTC", "ARM", "TSMC", "TSM",
    "Broadcom", "AVGO", "Marvell", "MRVL", "NXP", "NXPI", "Texas Instruments", "TXN",
    "Microchip", "MCHP", "Analog Devices", "ADI", "ON Semiconductor",
    "ASML", "Applied Materials", "AMAT", "Lam Research", "KLA",
    "Dell", "HPE", "Cisco", "CSCO", "IBM",
    "Synopsys", "SNPS", "Cadence", "CDNS",
    "foundry", "fabricat", "manufacture", "supply agreement",
    "customer concentration", "revenue concentration", "one customer",
    "license", "royalt", "partner", "agreement", "acqui", "invest",
    "compute", "data center", "AI", "artificial intelligence", "machine learning",
    "automotive", "IoT", "edge computing", "5G", "handset", "smartphone",
    "OpenAI", "Anthropic", "xAI", "Mistral", "Cohere",
    "CoreWeave", "Crusoe", "Lambda",
]

for name, url in URLS.items():
    print(f"\n{'='*60}")
    print(f"Fetching: {name}")
    print(f"URL: {url}")

    try:
        resp = sess.get(url, timeout=60)
        resp.raise_for_status()
        raw_html = resp.text
        print(f"  Size: {len(raw_html):,} chars")

        text = clean_text(raw_html)
        print(f"  Cleaned text: {len(text):,} chars")

        relevant = extract_relevant_sections(text, RELATIONSHIP_KEYWORDS)
        print(f"  Relevant passages: {len(relevant)}")

        # Save to file for inspection
        out_path = f"C:/Users/imadq/AIInvestment/data/enrich/QCOM_{name}_passages.txt"
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"SOURCE: {url}\n")
            f.write(f"DOC: {name}\n\n")
            for i, passage in enumerate(relevant):
                f.write(f"--- PASSAGE {i+1} ---\n")
                f.write(passage + "\n\n")
        print(f"  Saved to: {out_path}")

    except Exception as ex:
        print(f"  ERROR: {ex}")

    time.sleep(1)  # polite rate limit

print("\nDone.")
