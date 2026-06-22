import sys
import re

sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')

with open('oklo_10k_plain.txt', 'r', encoding='utf-8') as f:
    plain_10k = f.read()

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

print("=== Centrus supplier relationship in 10-K ===")
hits = find_context(plain_10k, "centrus", window=600)
for i, h in enumerate(hits):
    print(f"\n--- Hit {i+1} ---")
    print(h[:1500])
    print()

# Search for Siemens, Kiewit, Amentum as suppliers
print("\n=== Siemens in 10-K ===")
hits2 = find_context(plain_10k, "siemens", window=600)
for i, h in enumerate(hits2[:3]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:800])

# Check if GEV (GE Vernova) is mentioned
print("\n=== GE Vernova / GEV in 10-K ===")
hits3 = find_context(plain_10k, "ge vernova", window=600)
for i, h in enumerate(hits3[:3]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:800])

# Check BWXT
print("\n=== BWXT in 10-K ===")
hits4 = find_context(plain_10k, "bwxt", window=600)
for i, h in enumerate(hits4[:3]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:800])

print("\n=== BWX Technologies in 10-K ===")
hits5 = find_context(plain_10k, "bwx", window=600)
for i, h in enumerate(hits5[:3]):
    print(f"\n--- Hit {i+1} ---")
    print(h[:800])
