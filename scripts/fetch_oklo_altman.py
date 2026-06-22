import sys
import re

sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')

# Load both saved plain texts
with open('oklo_10k_plain.txt', 'r', encoding='utf-8') as f:
    plain_10k = f.read()

with open('oklo_10q_plain.txt', 'r', encoding='utf-8') as f:
    plain_10q = f.read()

def find_context(text, keyword, window=800):
    results = []
    kw_lower = keyword.lower()
    text_lower = text.lower()
    pos = 0
    while True:
        idx = text_lower.find(kw_lower, pos)
        if idx == -1:
            break
        start = max(0, idx - window)
        end = min(len(text), idx + window)
        results.append(text[start:end])
        pos = idx + 1
    return results

print("=== Sam Altman in 10-K ===")
hits = find_context(plain_10k, "altman", window=600)
for i, h in enumerate(hits[:5]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:1500])

print("\n\n=== Sam Altman in 10-Q ===")
hits2 = find_context(plain_10q, "altman", window=600)
for i, h in enumerate(hits2[:3]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:1500])

# Also look for openai in 10-K
print("\n\n=== OpenAI in 10-K ===")
hits3 = find_context(plain_10k, "openai", window=400)
for i, h in enumerate(hits3[:3]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:800])

# Look for any mention of investments in oklo / capital raises
print("\n\n=== 'Chair' context in 10-K ===")
hits4 = find_context(plain_10k, "chairman", window=400)
for i, h in enumerate(hits4[:3]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:800])

# Centrus / LEU supplier
print("\n\n=== Centrus / LEU in 10-K ===")
hits5 = find_context(plain_10k, "centrus", window=400)
for i, h in enumerate(hits5[:3]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:800])
